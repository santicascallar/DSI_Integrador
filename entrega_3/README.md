# Entrega 3 — Futbol Inform

Esta carpeta contiene el material para subir al repositorio:

- `rag_pipeline.py`: RAG básico y avanzado con LCEL, chunking y reranking.
- `evaluacion_ragas.py` y `golden_dataset.json`: evaluación de diez preguntas con RAGAS.
- `validacion.py`: pruebas de resiliencia y casos de falla.
- `informe.md`: resultados medidos, fuentes, comparación y diagnóstico.
- `traza_langsmith.py`: generación de la traza requerida por B.4.
- `requirements.txt`: dependencias.

La traza real se mantiene privada. La captura `langsmith_trace.png` documenta
los tiempos, tokens y la selección de contexto. Ver B.4 del informe.

## Instalación

Desde la raíz `DSI_Integrador`, con Python 3.12:

```powershell
py -3.12 -m venv .venv
.venv/Scripts/python -m pip install -r entrega_3/requirements.txt
```

Configurar `GEMINI_API_KEY` en el `.env` de la raíz y conservar la base original
`chroma_db/`, colección `futbol_inform_scouting`. El código no vuelve a ingestar ni
modifica esa base. Los modelos generador y evaluador predeterminados son
`gemini-3.1-flash-lite`, configurables con `GEMINI_MODEL` y `RAGAS_MODEL`.
El embedding es `gemini-embedding-001`, como en Entrega 2.

## Ejecutar

```powershell
.venv/Scripts/python entrega_3/rag_pipeline.py
.venv/Scripts/python entrega_3/rag_pipeline.py --reindex --chunk-size 180 --overlap 40
.venv/Scripts/python entrega_3/rag_pipeline.py --advanced
.venv/Scripts/python entrega_3/validacion.py
.venv/Scripts/python entrega_3/evaluacion_ragas.py
```

Los archivos auxiliares, checkpoints, caché e índice avanzado se guardan en
`DSI_Integrador/.entrega3_local/`, **fuera de esta carpeta y excluidos de Git**.
No hay que subirlos. La nueva tabla de métricas se genera en
`.entrega3_local/ejecuciones/comparativa.md`; si repetís la evaluación, revisá y
actualizá manualmente el informe con los nuevos resultados.

Las ejecuciones consumen cuota de Gemini. Ejecutar los scripts de a uno. Los
intervalos predeterminados son de siete segundos, configurables mediante
`GEMINI_INTERVAL` y `RAGAS_INTERVAL`. Si cambiás código, modelos o corpus y ya
existe una evaluación local, usar `evaluacion_ragas.py --nueva-corrida` para archivar
los checkpoints anteriores y repetir ambos pipelines. Si cambia el corpus,
reindexar primero y revisar las respuestas esperadas del dataset.

## Repetir la traza de LangSmith

Crear una cuenta y configurar `LANGSMITH_API_KEY` y `LANGSMITH_PROJECT` en `.env`.
Luego ejecutar:

```powershell
.venv/Scripts/python entrega_3/traza_langsmith.py
```

Abrir el enlace privado y capturar la traza, mostrando duración, tokens y la
diferencia entre `retrieved` y `sources`. Guardarla como
`entrega_3/langsmith_trace.png` y completar B.4 en el informe.

La traza se conserva privada. No subir `.env`, claves ni entornos virtuales.
