"""Export trace metadata for synthetic validation requests, never credentials."""
import json
import os
from pathlib import Path
import time
import argparse

from dotenv import load_dotenv
from langsmith import Client

ROOT = Path(__file__).resolve().parents[1]


def main():
    load_dotenv(ROOT / ".env", encoding="utf-8-sig")
    folder = ROOT / "entrega_4" / "evidencias"
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", default="validacion_http.json")
    args = parser.parse_args()
    report = json.loads((folder / args.evidence).read_text(encoding="utf-8"))
    client = Client(api_key=os.getenv("LANGSMITH_READ_API_KEY") or os.getenv("LANGSMITH_API_KEY"))
    rows = []
    cases = report.get("casos") or [{"escenario": "RAG con destino verificado", "resultado": report["resultado"]}]
    for case in cases:
        trace_id = case["resultado"].get("trace_id")
        if not trace_id:
            continue
        for attempt in range(6):
            try:
                run = client.read_run(trace_id, load_child_runs=True)
                if run.end_time is None:
                    raise RuntimeError("Traza aún sin finalizar")
                break
            except Exception as exc:
                if "runs:read" in str(exc) or "403" in str(exc) or "401" in str(exc):
                    raise RuntimeError(
                        "LangSmith no permite leer las trazas. Configurar LANGSMITH_READ_API_KEY "
                        "con permiso runs:read en .env, o revisarlas manualmente en la interfaz. "
                        "No es necesario repetir las consultas a Gemini."
                    ) from None
                if attempt == 5:
                    raise RuntimeError(f"No se pudo verificar la traza {trace_id}") from None
                time.sleep(5)
        descendants = []

        def collect(node):
            for child in node.child_runs or []:
                descendants.append({"name": child.name, "run_type": child.run_type,
                                    "total_tokens": child.total_tokens})
                collect(child)

        collect(run)
        rows.append({
            "escenario": case["escenario"], "trace_id": str(run.id),
            "url_privada": client.get_run_url(run=run),
            "name": run.name, "error": bool(run.error),
            "seconds": (run.end_time - run.start_time).total_seconds(),
            "prompt_tokens": run.prompt_tokens, "completion_tokens": run.completion_tokens,
            "total_tokens": run.total_tokens,
            "costo_langsmith_usd": str(run.total_cost) if run.total_cost is not None else None,
            "costo_estimado_api_usd": case["resultado"].get("costo_estimado_usd"),
            "llamadas": descendants,
        })
    if not rows:
        raise RuntimeError("La validación no contiene trazas para verificar")
    data = {"agent_id": os.getenv("LANGSMITH_AGENT_ID", "futbol-inform-entrega-4"),
            "environment": os.getenv("LANGSMITH_AGENT_ENVIRONMENT", "production"),
            "evidencia_origen": args.evidence,
            "trazas_verificadas": rows}
    (folder / "langsmith.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Verificadas {len(rows)} trazas: entrega_4/evidencias/langsmith.json")


if __name__ == "__main__":
    main()
