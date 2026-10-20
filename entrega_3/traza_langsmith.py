"""Crea evidencia B.4 real cuando se configure una cuenta LangSmith."""
import os
from datetime import datetime, timezone
from langchain_core.tracers.langchain import wait_for_all_tracers
from langsmith import Client
from rag_pipeline import OUT, build_chain, run_query, save_json


def main():
    if not os.getenv('LANGSMITH_API_KEY'):
        raise SystemExit('Falta LANGSMITH_API_KEY en .env. Crear cuenta y configurar la clave para completar B.4.')
    os.environ['LANGSMITH_TRACING'] = 'true'
    result = run_query(build_chain(advanced=True), '¿Qué habilidades tiene el arquero moderno?')
    wait_for_all_tracers()
    client = Client()
    run = client.read_run(result['run_id'], load_child_runs=True)
    evidence = {'run_id': result['run_id'], 'private_url': client.get_run_url(run=run),
                'start': run.start_time.isoformat(), 'end': run.end_time.isoformat() if run.end_time else None,
                'total_tokens': run.total_tokens, 'prompt_tokens': run.prompt_tokens,
                'completion_tokens': run.completion_tokens, 'query': result,
                'timestamp_utc': datetime.now(timezone.utc).isoformat()}
    save_json(OUT / 'langsmith_trace.json', evidence)
    print(evidence['private_url'])


if __name__ == '__main__':
    main()
