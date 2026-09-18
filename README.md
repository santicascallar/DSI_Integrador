# Futbol_Inform — Módulo de Inteligencia Artificial

## Dominio: Sistema diseñado para la gestión, análisis táctico y scouting de jugadores de fútbol, automatizando la clasificación de consultas en lenguaje natural (perfiles, informes y cargas de datos) mediante modelos de lenguaje e interfaces tipadas.

## Integrantes: Lautaro Luciani Conde y Santiago Ariel Cascallar

## Guía de Instalación y Ejecución:

### Tener instalado Python (versión 3.10 o superior)
### Instalar dependencias: python -m pip install google-genai pydantic python-dotenv
### python -m pip install google-genai faiss-cpu numpy python-dotenv
### python -m pip install chromadb

### Pipeline FAISS: python pipeline_vectorial.py
### Pipeline ChromaDB e Ingesta con Upsert: python vector_db.py
### ETL y purga: python etl_purga.py
### Killer queries: python killer_queries.py