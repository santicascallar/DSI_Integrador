# Entrega 2 — Base de conocimiento vectorial

Esta carpeta contiene los artefactos de las Clases 4 y 5:

- `base_conocimiento.json`: documentos fuente de la colección.
- `pipeline_vectorial.py`: embeddings e índice FAISS persistido.
- `vector_db.py`: ingesta ChromaDB y búsqueda híbrida.
- `etl_purga.py`: normalización y purga semántica.
- `evento_negocio.py`: demostración de upsert verificado.
- `killer_queries.py`: consultas de prueba y resultados.
- `informe_entrega2.md` y `resultados_killer_queries.md`: informe y evidencia.
- `requirements.txt`: dependencias de esta entrega.

## Preparación

Ejecutar desde la raíz del repositorio. Crear el entorno e instalar dependencias:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r "entrega 2\requirements.txt"
```

Configurar `GEMINI_API_KEY` en el `.env` de la raíz. El `.env`, `.env.example` y
`.gitignore` son compartidos por el repositorio y no se duplican aquí.

## Ejecutar

```powershell
.venv\Scripts\python "entrega 2\pipeline_vectorial.py"
.venv\Scripts\python "entrega 2\vector_db.py"
.venv\Scripts\python "entrega 2\etl_purga.py"
.venv\Scripts\python "entrega 2\killer_queries.py"
.venv\Scripts\python "entrega 2\evento_negocio.py"
```

`killer_queries.py` usa la colección purgada; ejecutar primero `etl_purga.py`.
Los índices y las bases persistentes (`vector_index.faiss`, `chroma_db/` y
`chroma_db_purgada/`) se generan localmente y están excluidos de Git.
La Entrega 3 reutiliza `chroma_db/` como base original.
