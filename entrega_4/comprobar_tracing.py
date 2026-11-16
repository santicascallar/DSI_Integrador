"""Send one real HTTP consultation and record trace ingestion acknowledgements."""
import json
import os
from pathlib import Path
from uuid import uuid4
from urllib.parse import urlsplit

from fastapi.testclient import TestClient
from langchain_core.tracers.langchain import get_client, wait_for_all_tracers
from langsmith import Client, run_trees
from requests import Session

from .api import create_app


def main():
    root = Path(__file__).resolve().parents[1]
    receipts = []
    # Dedicated process: use an explicit requests session to observe ingestion
    # receipts, without recording authorization headers or response bodies.
    session = Session()
    run_trees._CLIENT = Client(session=session)
    client = get_client()

    def receipt(response, *args, **kwargs):
        path = urlsplit(response.url).path
        if response.request.method == "POST" and "runs" in path:
            receipts.append({"path": path, "status": response.status_code})

    session.hooks.setdefault("response", []).append(receipt)
    headers = {"X-API-Key": os.environ["API_ACCESS_TOKEN"]} if os.getenv("API_ACCESS_TOKEN") else {}
    app = create_app(data_dir=root / ".entrega4_local" / "tracing" / uuid4().hex)
    with TestClient(app) as http:
        response = http.post("/consultar", headers=headers, json={
            "consulta": "¿Qué habilidades tiene el arquero moderno? Citá el informe.",
            "thread_id": "demo-tracing",
        })
        wait_for_all_tracers()
    report = {
        "agent_id": os.environ["LANGSMITH_AGENT_ID"],
        "environment": os.environ["LANGSMITH_AGENT_ENVIRONMENT"],
        "http_status": response.status_code,
        "resultado": response.json(),
        "recepcion_langsmith": receipts,
        "lectura_remota_verificada": False,
    }
    path = root / "entrega_4/evidencias/comprobacion_tracing.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    assert response.status_code == 200
    assert receipts and all(200 <= r["status"] < 300 for r in receipts), "LangSmith no confirmó todos los envíos"


if __name__ == "__main__":
    main()
