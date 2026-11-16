# Informe final — Agente inteligente Fútbol Inform

## Objetivo y alcance

El integrador transforma el RAG de Entrega 3 en un agente que decide entre buscar
informes, leer notas o guardar una observación solicitada por el usuario. Se
expone mediante FastAPI y mantiene contexto conversacional después de reiniciar.
Se conserva el repositorio y el corpus de las entregas anteriores.

## Diseño y decisiones

- **Reutilización:** la herramienta `buscar_informes_scouting` llama al pipeline
  RAG básico de E3 con la colección original de E2. Se recuperan dos documentos
  y se exige citar fuentes. El RAG avanzado no es el valor por defecto.
- **Agente:** `create_react_agent` enlaza modelo y herramientas. El presupuesto
  de cinco iteraciones se traduce a `recursion_limit=11`; un agotamiento se
  devuelve como HTTP 503.
- **Memorias separadas:** LangGraph persiste mensajes por `thread_id`; el sensor
  y actuador comparten una base distinta de notas. Las métricas también persisten.
- **Control de escritura:** autorización por turno mediante `ContextVar`, con
  orden imperativa explícita. El modelo no puede habilitarla por sí mismo.
- **Seguridad:** longitud y patrones de inyección se validan antes del modelo;
  respuestas e historial se enmascaran. La API admite token compartido opcional.
- **Observabilidad:** logs JSON, métricas persistentes y trazas anidadas de
  LangSmith con ID de ejecución en la respuesta HTTP.

La [ficha técnica](ficha_tecnica.md) describe arquitectura, endpoints, configuración
y límites. El [README](README.md) contiene la instalación desde cero.

## Correcciones realizadas durante el cierre

1. El detector anterior autorizaba escritura al mencionar «seguimiento» y ante
   «No guardar ninguna nota». Se reemplazó por una gramática conservadora de
   órdenes iniciales y se agregaron cinco casos de regresión.
2. Los rechazos de longitud de Pydantic no llegaban al contador del handler.
   Ahora un manejador de validación registra consulta, error y bloqueo sin
   devolver al cliente el texto completo rechazado.
3. La validación del identificador de hilo se integra al esquema de entrada.
4. Los tests se aíslan del token local y deshabilitan tracing durante ejecución,
   para que las credenciales personales no alteren sus resultados.
5. El README configura `.env` antes de crear Chroma e incluye ejemplos con
   `X-API-Key` y codificación UTF-8 en PowerShell.
6. Se incorpora `security_tests.py`, archivo de dependencias en raíz y versiones
   exactas del entorno para facilitar la reproducción.

## Resultados de pruebas locales

En el cierre se creó `.venv_e4` con Python 3.12.14 y se instalaron 122 paquetes.
La corrida final local dio **26 tests aprobados**, registrada en
[`pytest.txt`](entrega_4/evidencias/pytest.txt) y
[`pytest.xml`](entrega_4/evidencias/pytest.xml). `uv pip check`
informó que las dependencias instaladas son compatibles.
La ejecución final de `security_tests.py` aprobó **22 pruebas** de seguridad y API.

La suite cubre herramientas con RAG simulado, persistencia SQLite, API con
agentes de prueba, recuperación del historial tras reiniciar el ciclo de vida,
inyección, longitud, privacidad de respuestas e historial, autenticación,
autorización del actuador y cálculo persistente de métricas.

Estas pruebas comprueban la lógica local. No equivalen a una medición de la
calidad del modelo ni a una prueba del proveedor externo.

## Validación real reproducible

`python -m entrega_4.validacion_real` inicia su propio Uvicorn en localhost,
usa un directorio SQLite nuevo y ejecuta recuperación, escritura, lectura,
reinicio del proceso, continuación de conversación y guardrails. Verifica las
herramientas elegidas mediante diferencias de sus contadores. Exporta únicamente
los casos sintéticos de demostración y las métricas seleccionadas.

La evidencia se guarda en `entrega_4/evidencias/validacion_http.json` al ejecutar
el script, incluso ante fallo; `aprobado` distingue éxito de ejecución incompleta.
No asumir que el script pasó por el solo hecho de que exista.

La validación real del 16 de noviembre de 2026 terminó con **todos los escenarios
aprobados**. Se reconstruyó Chroma desde el corpus con Gemini. Resultados en
[`validacion_http.json`](entrega_4/evidencias/validacion_http.json):

| Escenario | HTTP | Tiempo del cliente | Resultado observado |
|---|---|---|---|
| RAG | 200 | 37,369 s | Usa el retriever y cita DOC-006 |
| Actuador | 200 | 20,716 s | Guarda nota para Jugador Demo con ID 1 |
| Sensor | 200 | 23,602 s | Recupera «revisar juego aéreo» sin ejecutar escritura |
| Memoria después de reinicio | 200 | 25,483 s | Recuerda Jugador Demo sin llamar herramientas |
| Inyección | 422 | 0,008 s | Bloqueada sin herramientas |
| Longitud | 422 | 0,007 s | Bloqueada sin herramientas |

Se terminaron y arrancaron dos procesos Uvicorn consecutivos. Los seis mensajes
previos fueron idénticos después del reinicio. Una lectura directa posterior de
SQLite confirmó una única nota persistida, ID 1, Jugador Demo, «revisar juego aéreo».
La latencia media reportada por `/metricas` fue 17.855,48 ms y el p95 37.359,60 ms;
incluyen las dos solicitudes bloqueadas casi inmediatamente. Seis casos no
constituyen un benchmark de rendimiento.
Los eventos JSON de esta corrida están en
[`logs_validacion.jsonl`](entrega_4/evidencias/logs_validacion.jsonl).

## Costos y trazabilidad

Cada respuesta exitosa devuelve `trace_id`, tokens de entrada/salida y costo
estimado. El callback acumula llamadas LLM anidadas (agente y generación RAG).
Una consulta RAG puede requerir más de una llamada: decisión de herramienta,
respuesta del RAG y respuesta final del agente. Una consulta a notas puede
evitar embeddings y generación RAG; comparar ambos tipos es más representativo
que informar un único precio fijo por consulta.

La fórmula es `(entrada × tarifa_entrada + salida × tarifa_salida) / 1_000_000`.
Las tarifas son configuración, no precios verificados por el programa. El costo
no incluye embeddings, impuestos ni consumo perdido en ejecuciones fallidas.
`null` indica falta de estimación, no costo cero. El costo agregado suma solo
solicitudes con estimación conocida y expone su cantidad.

En la corrida real se observaron **8.183 tokens de entrada y 418 de salida**.
Con las tarifas configuradas de USD 0,25 y USD 1,50 por millón, respectivamente,
el costo LLM estimado fue **USD 0,00267275** para cuatro respuestas exitosas:

| Escenario | Entrada | Salida | Estimación USD |
|---|---:|---:|---:|
| RAG | 1.930 | 283 | 0,00090700 |
| Actuador | 2.329 | 49 | 0,00065575 |
| Sensor | 2.544 | 71 | 0,00074250 |
| Memoria | 1.380 | 15 | 0,00036750 |

La consulta RAG fue la más costosa y lenta de esta muestra. Los turnos siguientes
incluyen el historial acumulado, por lo que sus entradas no son comparables como
consultas independientes. Los dos rechazos no invocaron herramientas ni el LLM.
El contador de errores fue 1 por la entrada de longitud inválida; no hubo fallos
de ejecución del agente. Los bloqueos fueron 2.

### Traza remota verificada

Se verificó por lectura de la API de LangSmith la ejecución completa
`ff1bb6da-c95a-476f-9d22-121c8e93ae91` de `futbol_inform_agente`, en el agente
`futbol-inform-entrega-4`, entorno Production.
Evidencia: [langsmith.json](entrega_4/evidencias/langsmith.json) y
[comprobacion_tracing.json](entrega_4/evidencias/comprobacion_tracing.json).

Terminó sin error en 36,143 segundos. Incluye `buscar_informes_scouting`,
recuperación, selección de contexto y tres llamadas a Gemini. LangSmith midió
1.952 tokens de entrada y 309 de salida (2.261 en total), con costo USD 0,0009515,
coincidente con la estimación de la API. Las tres llamadas LLM suman 611, 507 y
1.143 tokens; no sumar agregados de nodos padre e hijo, porque duplicaría el uso.

[Ver ejecución privada en LangSmith](https://smith.langchain.com/o/7d384bbb-09b7-41d2-b850-2bee1e88e57c/projects/p/01a1e589-991d-7e65-9c28-b2a58f4ef23a/r/ff1bb6da-c95a-476f-9d22-121c8e93ae91?poll=true). Requiere acceso al
workspace del equipo; la traza no se publicó.

La clave anterior aceptó envíos pero rechazó escribir al workspace correcto
al indicarlo explícitamente (403). Se configuró la clave personal autorizada
y el workspace explícito; la nueva ejecución se confirmó por envío y lectura.
Los IDs de la primera corrida HTTP no se recuperaron en este workspace: sus
resultados funcionales son evidencia local, no trazas remotas verificadas.

## Límites y reproducibilidad

- Se preparó un entorno limpio de dependencias en esta máquina. Ejecutarlo en
  una segunda máquina física es una comprobación diferente y no se afirma aquí.
- Las pruebas locales usan dobles; las reales dependen de cuota, red y proveedor.
- La memoria puede crecer con los turnos y aumentar costo y latencia; no se
  implementó resumen automático ni pruebas de carga.
- Guardrails por patrones tienen falsos positivos y falsos negativos. No hay
  aislamiento por usuario; la demo utiliza un token compartido.
- Citas y prompts reducen invenciones, pero no certifican veracidad del corpus.
- El enmascarado se aplica a la salida HTTP, no cifra las bases internas ni
  elimina automáticamente información del servicio de trazas.

## Entrega y defensa

La API pública de GitHub confirmó que el repositorio es público y su rama
predeterminada es `main`. Los cambios de este cierre están en el directorio de
trabajo; todavía no se crearon commits ni se enviaron al remoto.

Los archivos exigidos están en raíz o referenciados desde el README: código,
`security_tests.py`, `requirements.txt`, `.env.example`, `.gitignore`,
`README.md`, `informe.md` y `ficha_tecnica.md`. La [matriz](entrega_4/matriz_validacion.md)
relaciona escenarios y pruebas; el [guion](entrega_4/defensa.md) distribuye los
15 minutos de presentación, demostración y preguntas. La defensa en vivo debe
realizarla el equipo; preparar sus materiales no equivale a haberla rendido.
