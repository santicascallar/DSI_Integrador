import json
import logging
import math
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """Format each log record as one structured JSON object."""

    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("event", "request_id", "thread_id", "status_code", "latency_ms", "error_type"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging(log_path: Path) -> None:
    """Configure console and persistent JSON-line logging."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("entrega4")
    logger.setLevel(logging.INFO)
    for existing in logger.handlers[:]:
        existing.close()
        logger.removeHandler(existing)
    formatter = JsonFormatter()
    for handler in (logging.StreamHandler(), logging.FileHandler(log_path, encoding="utf-8")):
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.propagate = False


class MetricsStore:
    """Persist request, latency, tool-use, block, and token-cost measurements."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    latency_ms REAL NOT NULL,
                    is_error INTEGER NOT NULL,
                    is_blocked INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_cost_usd REAL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_calls (
                    name TEXT PRIMARY KEY,
                    count INTEGER NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS blocked_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL
                )
                """
            )

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.path, timeout=30)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def record_request(
        self,
        latency_ms: float,
        *,
        is_error: bool = False,
        is_blocked: bool = False,
        input_tokens: int = 0,
        output_tokens: int = 0,
        estimated_cost_usd: float | None = None,
    ) -> None:
        """Persist one API request outcome and its observed usage."""
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO requests
                    (created_at, latency_ms, is_error, is_blocked, input_tokens, output_tokens, estimated_cost_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    max(0.0, latency_ms),
                    int(is_error),
                    int(is_blocked),
                    max(0, input_tokens),
                    max(0, output_tokens),
                    estimated_cost_usd,
                ),
            )

    def record_tool(self, name: str) -> None:
        """Increment the persisted invocation count for a named tool."""
        with self._lock, self._connect() as connection:
            connection.execute(
                """
                INSERT INTO tool_calls (name, count) VALUES (?, 1)
                ON CONFLICT(name) DO UPDATE SET count = count + 1
                """,
                (name,),
            )

    def record_block(self) -> None:
        """Record a blocked tool call without counting it as another API request."""
        with self._lock, self._connect() as connection:
            connection.execute(
                "INSERT INTO blocked_events (created_at) VALUES (?)",
                (datetime.now(timezone.utc).isoformat(),),
            )

    def snapshot(self) -> dict[str, object]:
        """Return persisted request totals, latency percentiles, tools, and usage."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT latency_ms, is_error, is_blocked, input_tokens, output_tokens, estimated_cost_usd
                FROM requests ORDER BY id
                """
            ).fetchall()
            tools = dict(connection.execute("SELECT name, count FROM tool_calls ORDER BY name").fetchall())
            blocked_tool_calls = connection.execute("SELECT COUNT(*) FROM blocked_events").fetchone()[0]

        latencies = sorted(row[0] for row in rows)
        p95 = latencies[max(0, math.ceil(len(latencies) * 0.95) - 1)] if latencies else 0.0
        known_costs = [row[5] for row in rows if row[5] is not None]
        return {
            "consultas": len(rows),
            "errores": sum(row[1] for row in rows),
            "bloqueos": sum(row[2] for row in rows) + blocked_tool_calls,
            "latencia_promedio_ms": sum(latencies) / len(latencies) if latencies else 0.0,
            "latencia_p95_ms": p95,
            "herramientas": tools,
            "tokens_entrada": sum(row[3] for row in rows),
            "tokens_salida": sum(row[4] for row in rows),
            "costo_estimado_usd": sum(known_costs) if known_costs else None,
            "solicitudes_con_costo": len(known_costs),
        }
