"""Golden dataset y evaluación reproducible con checkpoints por pregunta."""
import argparse
import asyncio
import hashlib
import json
import math
import os
from datetime import datetime, timezone

import pandas as pd
from ragas import EvaluationDataset, aevaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference, LLMContextRecall
from ragas.run_config import RunConfig
from rag_pipeline import HERE, OUT, ESCAPE, GeminiEmbeddings, build_chain, fingerprint, source_documents, make_llm, run_query, save_json

METRICS = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']


def load_dataset():
    rows = json.loads((HERE / 'golden_dataset.json').read_text(encoding='utf-8-sig'))
    from collections import Counter
    if Counter(r['tipo'] for r in rows) != {'simple': 3, 'compleja': 3, 'escape': 2, 'informal': 2}:
        raise ValueError('El dataset debe cumplir la distribución 3/3/2/2.')
    ids = {d.metadata['source_id'] for d in source_documents()}
    if not all(set(r['source_ids']) <= ids for r in rows):
        raise ValueError('El dataset referencia documentos ausentes.')
    return rows


def signature(golden):
    config = {'dataset': golden, 'source': fingerprint(source_documents()),
              'generator': os.getenv('GEMINI_MODEL', 'gemini-3.1-flash-lite'),
              'evaluator': os.getenv('RAGAS_MODEL', 'gemini-3.1-flash-lite'),
              'index': json.loads((OUT / 'indexacion.json').read_text(encoding='utf-8')),
              'pipeline': (HERE / 'rag_pipeline.py').read_text(encoding='utf-8-sig'),
              'evaluation': (HERE / 'evaluacion_ragas.py').read_text(encoding='utf-8-sig')}
    return hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()


def contexts(result):
    return [f"[{d['metadata']['chunk_id']}] {json.dumps(d['metadata'], ensure_ascii=False)}\n{d['text']}"
            for d in result['sources']]


def summarize(records):
    summary = {}
    for metric in METRICS:
        values = [r['metrics'][metric] for r in records if r['metrics'][metric] is not None]
        answerable = [r['metrics'][metric] for r in records if r['tipo'] != 'escape' and r['metrics'][metric] is not None]
        summary[metric] = {'mean': sum(values) / len(values) if values else None,
                           'valid': len(values), 'total': len(records),
                           'answerable_mean': sum(answerable) / len(answerable) if answerable else None}
    escapes = [r for r in records if r['tipo'] == 'escape']
    summary['escape_accuracy'] = sum(r['answer'].strip() == ESCAPE for r in escapes) / len(escapes) if escapes else None
    return summary


def comparison():
    summaries = {mode: json.loads((OUT / f'resumen_{mode}.json').read_text(encoding='utf-8')) for mode in ['basico','avanzado']}
    rows = ['# Comparación RAGAS', '', '| Métrica | Básico | Avanzado | Delta | Válidos B/A |', '|---|---:|---:|---:|---|']
    deltas = []
    for metric in METRICS:
        b, a = summaries['basico'][metric], summaries['avanzado'][metric]
        delta = a['mean'] - b['mean'] if a['mean'] is not None and b['mean'] is not None else None
        deltas.append(delta)
        fmt = lambda v: 'N/D' if v is None else f'{v:.4f}'
        rows.append(f"| {metric} | {fmt(b['mean'])} | {fmt(a['mean'])} | {fmt(delta)} | {b['valid']}/{b['total']}; {a['valid']}/{a['total']} |")
    rows += ['', 'Mejora observada en al menos una métrica.' if any(d is not None and d > 0 for d in deltas)
             else 'No se verificó mejora; el requisito C.3 sigue pendiente.', '',
             'Los CSV conservan valores indefinidos y los resúmenes incluyen medias sin escapes. '
             'Una abstención correcta puede recibir baja relevancia: analizar por tipo.']
    (OUT / 'comparativa.md').write_text('\n'.join(rows), encoding='utf-8')


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['basico','avanzado','ambos'], default='ambos')
    parser.add_argument('--nueva-corrida', action='store_true', help='Archiva las mediciones existentes antes de repetir ambos pipelines.')
    args = parser.parse_args()
    if args.nueva_corrida:
        if args.mode != 'ambos':
            raise ValueError('--nueva-corrida requiere --mode ambos para comparar la misma configuraci?n.')
        archive = OUT / 'anteriores' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive.mkdir(parents=True, exist_ok=False)
        patterns = ['evaluacion_*.json', 'respuesta_*.json', 'resumen_*.json', 'ragas_*.csv',
                    'comparativa.md', 'pipeline_evaluado.py', 'evaluacion_ejecutada.py', 'diagnostico_*.md']
        for pattern in patterns:
            for path in OUT.glob(pattern):
                if path.is_file() and path.resolve().parent == OUT.resolve():
                    path.rename(archive / path.name)
    golden = load_dataset()
    sig = signature(golden)
    for mode in (['basico','avanzado'] if args.mode == 'ambos' else [args.mode]):
        path = OUT / f'evaluacion_{mode}.json'
        records = []
        if path.exists():
            prior = json.loads(path.read_text(encoding='utf-8'))
            if prior['signature'] != sig:
                raise ValueError('Configuración modificada: usar --nueva-corrida para repetir sin mezclar versiones.')
            records = prior['records']
        OUT.mkdir(parents=True, exist_ok=True)
        chain = build_chain(advanced=mode == 'avanzado')
        judge = LangchainLLMWrapper(make_llm(evaluator=True), bypass_n=True, bypass_temperature=True)
        embeddings = LangchainEmbeddingsWrapper(GeminiEmbeddings())
        completed = {r['id'] for r in records}
        for item in golden:
            if item['id'] in completed:
                continue
            result = run_query(chain, item['question'])
            save_json(OUT / f"respuesta_{mode}_{item['id']}.json", {**item, **result})
            sample = {'user_input': item['question'], 'response': result['answer'],
                      'retrieved_contexts': contexts(result), 'reference': item['reference']}
            metrics = [Faithfulness(), ResponseRelevancy(),
                       LLMContextPrecisionWithReference(name='context_precision'), LLMContextRecall(name='context_recall')]
            evaluation = await aevaluate(EvaluationDataset.from_list([sample]), metrics=metrics, llm=judge,
                                  embeddings=embeddings, run_config=RunConfig(max_workers=1, timeout=240, max_retries=2),
                                  raise_exceptions=True, show_progress=False)
            scores = evaluation.to_pandas().iloc[0]
            values = {m: float(scores[m]) if math.isfinite(float(scores[m])) else None for m in METRICS}
            records.append({**item, **result, 'metrics': values})
            save_json(path, {'signature': sig, 'timestamp_utc': datetime.now(timezone.utc).isoformat(),
                             'generator': os.getenv('GEMINI_MODEL','gemini-3.1-flash-lite'),
                             'evaluator': os.getenv('RAGAS_MODEL','gemini-3.1-flash-lite'), 'records': records})
            pd.DataFrame([{'id': r['id'], 'tipo': r['tipo'], 'question': r['question'], **r['metrics']} for r in records]).to_csv(OUT / f'ragas_{mode}.csv', index=False)
            save_json(OUT / f'resumen_{mode}.json', summarize(records))
            print(mode, item['id'], values, flush=True)
    if all((OUT / f'resumen_{m}.json').exists() for m in ['basico','avanzado']):
        comparison()


if __name__ == '__main__':
    asyncio.run(main())



