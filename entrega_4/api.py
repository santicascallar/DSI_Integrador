import hmac
import logging
import os
import re
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.errors import GraphRecursionError
from pydantic import BaseModel, Field, field_validator

from .agent import ScoutAgent, build_agent
from .domain_store import ScoutingStore
from .guardrails import (
    MAX_INPUT_LENGTH,
    GuardrailBlock,
    mask_personal_data,
    validate_input_length,
    validate_request,
)
from .metrics import MetricsStore, configure_logging

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / ".entrega4_local"
load_dotenv(ROOT / ".env", encoding="utf-8-sig")
logger = logging.getLogger("entrega4")
_THREAD_ID_PATTERN = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")


class ConsultationRequest(BaseModel):
    """Validated request body for a single agent turn."""

    consulta: str = Field(min_length=1, max_length=MAX_INPUT_LENGTH)
    thread_id: str | None = Field(default=None, min_length=1, max_length=128)

    @field_validator("consulta", mode="before")
    @classmethod
    def validate_query_length(cls, value):
        """Trim a query and reject empty or oversized input before the handler runs."""
        if isinstance(value, str):
            return validate_input_length(value)
        return value


class ConsultationResponse(BaseModel):
    """Validated and privacy-filtered response from the agent."""

    thread_id: str
    respuesta: str
    trace_id: str
    tokens_entrada: int
    tokens_salida: int
    costo_estimado_usd: float | None

    @field_validator("respuesta")
    @classmethod
    def redact_personal_data(cls, value: str) -> str:
        """Mask personal identifiers before returning agent text over HTTP."""
        return mask_personal_data(value)


class ConversationMessage(BaseModel):
    """One message in a thread history with output privacy filtering."""

    rol: str
    contenido: str

    @field_validator("contenido")
    @classmethod
    def redact_personal_data(cls, value: str) -> str:
        """Mask personal identifiers in messages returned by the state endpoint."""
        return mask_personal_data(value)


class ConversationState(BaseModel):
    """Validated public representation of a persisted conversation."""

    thread_id: str
    mensajes: list[ConversationMessage]


def _check_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Require the optional shared API token when one is configured."""
    expected = os.getenv("API_ACCESS_TOKEN")
    if expected and (
        not x_api_key
        or not hmac.compare_digest(x_api_key.encode("utf-8"), expected.encode("utf-8"))
    ):
        raise HTTPException(status_code=401, detail="API key inválida o ausente.")


def create_app(
    *,
    data_dir: Path = DATA_DIR,
    runtime_factory: Callable[[SqliteSaver, ScoutingStore, MetricsStore], ScoutAgent] = build_agent,
) -> FastAPI:
    """Create the REST API, allowing isolated data paths and runtime injection in tests."""
    data_dir = Path(data_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        data_dir.mkdir(parents=True, exist_ok=True)
        configure_logging(data_dir / "logs.jsonl")
        metrics = MetricsStore(data_dir / "metrics.sqlite3")
        scouting_store = ScoutingStore(data_dir / "scouting.sqlite3")
        app.state.metrics = metrics
        with SqliteSaver.from_conn_string(str(data_dir / "memory.sqlite3")) as checkpointer:
            app.state.runtime = runtime_factory(checkpointer, scouting_store, metrics)
            logger.info("API y agente inicializados", extra={"event": "startup"})
            yield
            app.state.runtime = None

    app = FastAPI(title="Futbol Inform — Agente de scouting", version="1.0.0", lifespan=lifespan)

    @app.middleware("http")
    async def request_logging(request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid4())
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "Solicitud HTTP",
            extra={
                "event": "http_request",
                "request_id": request_id,
                "status_code": response.status_code,
                "latency_ms": round(latency_ms, 2),
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response

    @app.get("/health")
    def health():
        """Report service readiness without exposing credentials or local state."""
        ready = getattr(app.state, "runtime", None) is not None
        return {"status": "ok" if ready else "starting", "agent_ready": ready}

    @app.post("/consultar", dependencies=[Depends(_check_api_key)])
    def consultar(body: ConsultationRequest):
        """Run a guarded agent turn and persist conversation state by thread ID."""
        request_id = str(uuid4())
        thread_id = body.thread_id or str(uuid4())
        if not _THREAD_ID_PATTERN.fullmatch(thread_id):
            raise HTTPException(status_code=422, detail="thread_id tiene caracteres no permitidos.")

        start = time.perf_counter()
        usage = {
            "tokens_entrada": 0,
            "tokens_salida": 0,
            "costo_estimado_usd": None,
        }
        error = False
        blocked = False
        try:
            validate_request(body.consulta)
            usage = app.state.runtime.invoke(body.consulta, thread_id)
            response = ConsultationResponse(thread_id=thread_id, **usage)
            logger.info(
                "Consulta completada",
                extra={
                    "event": "consultation_completed",
                    "request_id": request_id,
                    "thread_id": thread_id,
                    "status_code": 200,
                    "latency_ms": round((time.perf_counter() - start) * 1000, 2),
                },
            )
            return response.model_dump()
        except GuardrailBlock as exc:
            blocked = True
            logger.warning(
                "Consulta bloqueada por guardrail",
                extra={
                    "event": "guardrail_block",
                    "request_id": request_id,
                    "thread_id": thread_id,
                    "status_code": 422,
                },
            )
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except GraphRecursionError as exc:
            error = True
            logger.exception(
                "Agente alcanzó el límite de iteraciones",
                extra={"event": "agent_iteration_limit", "request_id": request_id, "thread_id": thread_id},
            )
            raise HTTPException(status_code=503, detail="El agente alcanzó el límite de iteraciones.") from exc
        except HTTPException:
            raise
        except Exception as exc:
            error = True
            logger.exception(
                "Error al ejecutar la consulta",
                extra={"event": "consultation_error", "request_id": request_id, "thread_id": thread_id},
            )
            raise HTTPException(status_code=502, detail="No se pudo completar la consulta.") from exc
        finally:
            latency_ms = (time.perf_counter() - start) * 1000
            app.state.metrics.record_request(
                latency_ms,
                is_error=error,
                is_blocked=blocked,
                input_tokens=int(usage.get("tokens_entrada", 0)),
                output_tokens=int(usage.get("tokens_salida", 0)),
                estimated_cost_usd=usage.get("costo_estimado_usd"),
            )

    @app.get("/estado/{thread_id}", dependencies=[Depends(_check_api_key)])
    def estado(thread_id: str):
        """Read persisted conversation history for one validated thread ID."""
        if not _THREAD_ID_PATTERN.fullmatch(thread_id):
            raise HTTPException(status_code=422, detail="thread_id tiene caracteres no permitidos.")
        state = app.state.runtime.get_state(thread_id)
        if state is None:
            raise HTTPException(status_code=404, detail="No existe memoria para ese thread_id.")
        return ConversationState.model_validate(state).model_dump()

    @app.get("/metricas", dependencies=[Depends(_check_api_key)])
    def metricas():
        """Return persisted request, latency, tool, block, token, and cost metrics."""
        return app.state.metrics.snapshot()

    return app


app = create_app()
