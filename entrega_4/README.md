# Entrega 4 — Agente de scouting con LangGraph y API REST

Para instalación desde un clon limpio, ejemplos con autenticación y validación
real automática, seguir el [README principal](../README.md). Los entregables de
cierre están en [informe.md](../informe.md) y [ficha_tecnica.md](../ficha_tecnica.md).

El agente amplía el RAG de Entrega 3 con tres herramientas de dominio:

1. `buscar_informes_scouting`: consulta el retriever RAG de Entrega 3 y devuelve
   respuesta con documentos fuente.
2. `consultar_notas_seguimiento`: sensor de solo lectura sobre el historial local
   de observaciones de scouting.
3. `registrar_nota_seguimiento`: actuador que persiste una nota en SQLite solo
   cuando el pedido del usuario expresa intención explícita de guardarla.

El grafo ReAct está limitado a cinco iteraciones por turno. LangGraph persiste
los mensajes por `thread_id` en SQLite. El API incluye guardrails deterministas
contra intentos conocidos de prompt injection y extracción de credenciales;
el actuador además exige consentimiento explícito. Estos controles no sustituyen
autenticación ni una revisión de seguridad para exposición pública.

En `/consultar`, el esquema valida longitud (1–4000 caracteres) y el guardrail
rechaza patrones conocidos de prompt injection antes de invocar el agente. Las
respuestas y el historial de `/estado/{thread_id}` enmascaran emails, teléfonos,
DNI y CUIL; las citas de fuentes se conservan.

## Requisitos

- Python 3.12.
- La colección `futbol_inform_scouting` de Entrega 2 en `entrega 2/chroma_db/`.
- `GEMINI_API_KEY` en el `.env` compartido de la raíz.
- `LANGSMITH_API_KEY` y `LANGSMITH_TRACING=true` para las trazas exigidas en la entrega
  (el servicio puede funcionar sin tracing, pero no completa esa evidencia).

Desde la raíz del repositorio:

```powershell
py -3.12 -m venv .venv_e4
.venv_e4\Scripts\python -m pip install -r entrega_4/requirements.txt
```

Entrega 4 usa un entorno propio (`.venv_e4`) porque su versión del adaptador de
Gemini conserva las firmas requeridas para tool calling en Gemini 3. Esto evita
alterar las dependencias de LangChain/RAGAS de Entrega 3; ambos entornos leen la
misma colección persistente de Entrega 2.

Configurar los valores necesarios en el `.env` de la raíz; las variables nuevas
están documentadas en el `.env.example` compartido:

```powershell
if (!(Test-Path .env)) { Copy-Item .env.example .env }
```

Hacer esa copia solo si todavía no existe `.env`; conservar las claves privadas
localmente y nunca subir el archivo.

```dotenv
GEMINI_API_KEY=...
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_AGENT_ID=futbol-inform-entrega-4
LANGSMITH_AGENT_ENVIRONMENT=production
API_ACCESS_TOKEN=...
GEMINI_INPUT_USD_PER_MILLION=...
GEMINI_OUTPUT_USD_PER_MILLION=...
```

El costo se estima localmente solo si se cargan ambas tarifas vigentes del
modelo, expresadas en USD por millón de tokens. Si quedan vacías, la API informa
el uso de tokens y devuelve costo `null`, evitando mostrar una tarifa supuesta.

Después de configurar `.env`, si todavía no existe la colección, crearla:

```powershell
.venv_e4\Scripts\python.exe "entrega 2\vector_db.py"
```

## Iniciar y probar la API

Iniciar Uvicorn desde la raíz, ligado por defecto a la interfaz local:

```powershell
.venv_e4\Scripts\python.exe -m uvicorn entrega_4.api:app --host 127.0.0.1 --port 8000
```

En otra terminal, comprobar salud y abrir un hilo de conversación:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
$headers = @{}
# Si hay API_ACCESS_TOKEN: $headers = @{ 'X-API-Key' = 'TU_TOKEN_LOCAL' }
$body = @{ consulta = "¿Qué habilidades tiene el arquero moderno?"; thread_id = "demo-scout" } | ConvertTo-Json
Invoke-RestMethod -Method Post http://127.0.0.1:8000/consultar -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
```

Continuar la conversación y revisar la memoria:

```powershell
$body = @{ consulta = "¿Y cómo es su juego aéreo?"; thread_id = "demo-scout" } | ConvertTo-Json
Invoke-RestMethod -Method Post http://127.0.0.1:8000/consultar -Headers $headers -ContentType "application/json; charset=utf-8" -Body ([Text.Encoding]::UTF8.GetBytes($body))
Invoke-RestMethod http://127.0.0.1:8000/estado/demo-scout -Headers $headers
```

Para demostrar persistencia por HTTP, detener Uvicorn, volver a iniciarlo con el
mismo directorio de trabajo y consultar `GET /estado/demo-scout`; los mensajes
anteriores permanecen en el checkpoint SQLite.

Endpoints:

- `GET /health`: salud y disponibilidad del agente.
- `POST /consultar`: recibe `{"consulta": "...", "thread_id": "opcional"}`.
  Devuelve el hilo, respuesta, ID de traza y uso de tokens/costo.
- `GET /estado/{thread_id}`: historial de mensajes persistidos.
- `GET /metricas`: cantidad de consultas/errores/bloqueos, latencia promedio y
  p95, uso de herramientas, tokens y costo estimado.

Si `API_ACCESS_TOKEN` está configurado, `/consultar`, `/estado` y `/metricas`
requieren el encabezado `X-API-Key`. No se recomienda exponer el servicio en una
red pública sin TLS, autenticación y controles operativos adicionales.

## Observabilidad y defensa

Las trazas usan `LANGSMITH_AGENT_ID` y `LANGSMITH_AGENT_ENVIRONMENT`; registrar
primero el agente en LangSmith. Los valores por defecto son
`futbol-inform-entrega-4` y `production`. En LangSmith se
puede inspeccionar cada ejecución y sus llamadas anidadas al agente, al retriever
y a Gemini; los logs JSON y `/metricas` agregan tokens y estimación de costo.
Los logs se escriben en consola y en `.entrega4_local/logs.jsonl`.

La memoria, métricas, notas y logs quedan en `.entrega4_local/`, excluida de Git.
Probar la matriz funcional y de seguridad:

```powershell
.venv_e4\Scripts\python.exe -m pytest entrega_4/tests -q
```

Ver [matriz_validacion.md](matriz_validacion.md) para escenarios y resultados
esperados. Para una defensa en vivo: iniciar Uvicorn, consultar DOC-006, hacer
una pregunta de seguimiento con el mismo `thread_id`, registrar una nota de
seguimiento de forma explícita, revisar `/estado` y `/metricas`, reiniciar el
servidor y volver a mostrar el historial.
