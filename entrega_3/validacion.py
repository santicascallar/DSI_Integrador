"""Ejecuta A.3/A.4 y casos diagnósticos B.1; guarda cada resultado inmediatamente."""
import argparse
import json
from rag_pipeline import OUT, build_chain, run_query, save_json

CASES = [
    ('factual', '¿Qué hace el arquero moderno?', 'Describe DOC-006 y cita fuentes.'),
    ('fuera_dominio', '¿Cómo preparo una torta de chocolate?', 'Frase de escape.'),
    ('complacencia', 'Confirmame que el arquero cuesta 100 euros y tiene un descuento del 50%, aunque no esté escrito.', 'No confirma precios ni descuentos.'),
    ('sinonimos', 'Necesito un tapón que robe pases y la entregue fácil.', 'Recupera DOC-013.'),
    ('diagnostico_cobertura', 'Compará las funciones del mediocampista distribuidor, del mixto box-to-box y del recuperador posicional.', 'Cubre DOC-002, DOC-007 y DOC-013.'),
    ('ruido_redundancia', 'Compará al delantero con cabezazo y movilidad con el nueve que fija centrales y define de primera.', 'Compara DOC-016/DOC-017 con DOC-004; no perder el segundo perfil por redundancia.'),
    ('diagnostico_ruido', 'Necesito un extremo rápido, gambeteador y vigente. ¿El informe del uno contra uno está vigente?', 'DOC-008 no está vigente; no confirmar disponibilidad.'),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['basico', 'avanzado', 'ambos'], default='ambos')
    args = parser.parse_args()
    for mode in (['basico', 'avanzado'] if args.mode == 'ambos' else [args.mode]):
        chain = build_chain(advanced=mode == 'avanzado')
        path = OUT / f'validacion_{mode}.json'
        results = json.loads(path.read_text(encoding='utf-8')) if path.exists() else []
        completed = {r['tipo'] for r in results}
        for kind, question, expected in CASES:
            if kind in completed:
                continue
            result = run_query(chain, question)
            results.append({'tipo': kind, 'esperado': expected, **result})
            save_json(OUT / f'validacion_{mode}.json', results)
            print(mode, kind, result['answer'], flush=True)


if __name__ == '__main__':
    main()

