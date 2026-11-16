# Futbol_Inform — Módulo de Inteligencia Artificial

## Dominio: Sistema diseñado para la gestión, análisis táctico y scouting de jugadores de fútbol, automatizando la clasificación de consultas en lenguaje natural (perfiles, informes y cargas de datos) mediante modelos de lenguaje e interfaces tipadas.

## Integrantes: Lautaro Luciani Conde y Santiago Ariel Cascallar

## Guía de Instalación y Ejecución:

### Instalación y ejecución

Desde la raíz del repositorio, con Python 3.10 o superior:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r "entrega 1\requirements.txt"
.venv\Scripts\python "entrega 1\app.py"
.venv\Scripts\python "entrega 1\lote_pruebas.py"
```

Configurar `GEMINI_API_KEY` en el `.env` de la raíz. No subir ese archivo; el
repositorio conserva un `.env.example` sin claves.

La Entrega 1 define el contrato de consulta y su validación. La base vectorial de
la Entrega 2 está en [su carpeta](<../entrega 2/README.md>), y el RAG de la
Entrega 3 en [entrega_3/](../entrega_3/README.md).
