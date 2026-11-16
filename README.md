# Fútbol Inform — TP Final Integrador

Agente de scouting con LangGraph, RAG de Entrega 3, API FastAPI, memoria SQLite,
guardrails y observabilidad. Ejecutar los comandos desde la raíz del repositorio.

## Instalación desde cero (Windows / PowerShell)

Requisitos: Git, Python 3.12, clave de Google Gemini con cuota y una cuenta de
LangSmith para demostrar las trazas exigidas por la consigna.

```powershell
git clone https://github.com/santicascallar/DSI_Integrador.git
cd DSI_Integrador
py -3.12 -m venv .venv_e4
.venv_e4\Scripts\python.exe -m pip install -r entrega_4/requirements-lock.txt
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Editar `.env` antes de generar la base:

- `GEMINI_API_KEY`: clave de Gemini.
- `GEMINI_MODEL`: modelo con soporte de herramientas; el ejemplo configura `gemini-3.1-flash-lite`.
- `LANGSMITH_API_KEY`, `LANGSMITH_TRACING=true`. Registrar el agente
  `futbol-inform-entrega-4` en LangSmith y configurar
  `LANGSMITH_AGENT_ID=futbol-inform-entrega-4`, `LANGSMITH_AGENT_ENVIRONMENT=production`.
  E4 elimina del proceso los destinos legacy cargados por E3; `LANGSMITH_PROJECT_E4`
  queda como referencia histórica y ya no selecciona el destino.
- `API_ACCESS_TOKEN`: token compartido opcional; si se completa, enviar `X-API-Key`.
- `GEMINI_INPUT_USD_PER_MILLION` y `GEMINI_OUTPUT_USD_PER_MILLION`: tarifas del modelo
  contratado. Los valores del ejemplo son parámetros de estimación, no una garantía de precio.

No subir `.env`. La generación de embeddings envía el corpus a Gemini y consume
cuota; con tracing habilitado, las ejecuciones se registran en LangSmith.

```powershell
.venv_e4\Scripts\python.exe "entrega 2\vector_db.py"
.venv_e4\Scripts\python.exe -m pytest entrega_4/tests -q
.venv_e4\Scripts\python.exe security_tests.py
.venv_e4\Scripts\python.exe -m uvicorn entrega_4.api:app --host 127.0.0.1 --port 8000
```

La base se regenera desde `entrega 2/base_conocimiento.json`; no hace falta copiar
ninguna base privada. La configuración queda antes de este paso deliberadamente.
`requirements.txt` permite instalar rangos compatibles; `entrega_4/requirements-lock.txt`
conserva las versiones exactas utilizadas para validar esta entrega.

En Linux/macOS usar `python3.12 -m venv .venv_e4`, el ejecutable
`.venv_e4/bin/python` y rutas con `/`; las instrucciones restantes son equivalentes.

## Demostración HTTP

Abrir otra terminal. Si se configuró token, asignar en `$headers` el mismo valor
local de `API_ACCESS_TOKEN`; no incluirlo en capturas ni en archivos de evidencia.

```powershell
$headers = @{}
# Solo si se configuró token:
# $headers = @{ 'X-API-Key' = 'TU_TOKEN_LOCAL' }
Invoke-RestMethod http://127.0.0.1:8000/health
$body = @{consulta='¿Qué habilidades tiene el arquero moderno?'; thread_id='demo-scout'} | ConvertTo-Json
Invoke-RestMethod -Method Post http://127.0.0.1:8000/consultar -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
$body = @{consulta='¿Y cómo es su juego aéreo?'; thread_id='demo-scout'} | ConvertTo-Json
Invoke-RestMethod -Method Post http://127.0.0.1:8000/consultar -Headers $headers -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($body))
Invoke-RestMethod http://127.0.0.1:8000/estado/demo-scout -Headers $headers
Invoke-RestMethod http://127.0.0.1:8000/metricas -Headers $headers
```

Detener Uvicorn con Ctrl+C y repetir su comando de inicio. Volver a consultar
`/estado/demo-scout`: el historial persiste. Swagger está en `/docs`.

Para ejecutar la validación real automáticamente (consume cuota), cerrar otras
validaciones y ejecutar:

```powershell
.venv_e4\Scripts\python.exe -m entrega_4.validacion_real
.venv_e4\Scripts\python.exe -m entrega_4.exportar_trazas
```

El script usa un puerto local libre y bases separadas, comprueba las tres
herramientas, mata y reinicia su proceso servidor, verifica historial y memoria,
y prueba rechazos por inyección y longitud. Guarda resultados en
`entrega_4/evidencias/validacion_http.json`. Un fallo produce salida no cero.
El segundo comando verifica las trazas en LangSmith y exporta sus metadatos y
enlaces privados en `entrega_4/evidencias/langsmith.json`; no publica las trazas.
Si LangSmith responde 403 porque la clave solo permite tracing, configurar
`LANGSMITH_READ_API_KEY` con permiso `runs:read` en `.env` y repetir solo el
exportador. También se pueden revisar los `trace_id` desde la interfaz de
LangSmith con una cuenta autorizada. No hace falta repetir las consultas pagas.

Para comprobar un nuevo destino con una consulta real, ejecutar
`python -m entrega_4.comprobar_tracing`. Exporta la respuesta y los códigos de
recepción de LangSmith en `entrega_4/evidencias/comprobacion_tracing.json`.
Aceptar el envío no equivale a leer de vuelta la traza almacenada.

## Documentación de entrega

- [Resumen PDF para presentación y defensa (12 diapositivas)](docs/Resumen_Presentacion_Futbol_Inform.pdf).
- [Informe y resultados](informe.md).
- [Ficha técnica](ficha_tecnica.md).
- [Matriz de validación](entrega_4/matriz_validacion.md).
- [Guion de defensa de 15 minutos](entrega_4/defensa.md).
- [Implementación de Entrega 4](entrega_4/README.md).

Entregas anteriores: [1](entrega%201/README.md), [2](entrega%202/README.md),
[3](entrega_3/README.md). El agente reutiliza el RAG de E3 y la colección original
de E2; E1 aporta el diseño conceptual, no una dependencia de ejecución.

## Problemas comunes

- Falta de colección: ejecutar `vector_db.py` después de configurar `.env`.
- 401: revisar el encabezado `X-API-Key` y el token local.
- 422: consulta vacía, demasiado larga, identificador inválido o inyección bloqueada.
- 502: revisar `.entrega4_local/logs.jsonl`, cuota, claves y disponibilidad del modelo.
- 503: se alcanzó el límite de pasos del agente; reformular la consulta.
- Costo `null`: faltan tarifas válidas; no significa que la llamada sea gratuita.
- Puerto ocupado: cambiar `--port` y la URL del cliente.

Las bases, logs y credenciales quedan excluidos de Git. El token compartido no
implementa autorización por usuario; para esta entrega se usa una demo local.
