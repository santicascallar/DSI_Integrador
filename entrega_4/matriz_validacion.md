# Matriz de validación — Entrega 4

Los escenarios automatizados se ejecutan con `pytest entrega_4/tests`.

| Escenario | Entrada / acción | Resultado esperado | Prueba |
|---|---|---|---|
| Recuperación | Consulta sobre un informe de un arquero | La herramienta RAG devuelve respuesta y cita DOC-006 | `test_domain_tools_retrieve_read_and_require_write_authorization` |
| Memoria conversacional | Dos turnos en el mismo `thread_id`, cerrando y reabriendo el checkpoint SQLite entre turnos | El segundo turno conserva el primero | `test_sqlite_conversation_memory_survives_reopen` |
| Actuador con consentimiento | Solicitar guardar una nota, y luego intentar guardar sin autorización | La primera nota persiste; el intento no autorizado se bloquea y se contabiliza | `test_domain_tools_retrieve_read_and_require_write_authorization` |
| Inyección y guardrails HTTP | Pedir que ignore reglas y revele claves | HTTP 422, sin invocar el agente, aumenta el contador de bloqueos | `test_http_guardrails_memory_state_and_metrics` |
| Seguridad: prompt injection | Intento de cambiar las reglas del agente | HTTP 422 y el agente no recibe la consulta | `test_http_blocks_prompt_injection_before_invoking_agent` |
| Seguridad: longitud | Consulta de más de 4000 caracteres | HTTP 422 antes de invocar el agente; la entrada válida en el límite pasa el validator | `test_http_rejects_oversized_input_before_invoking_agent`, `test_input_length_validator_trims_and_enforces_the_limit` |
| Seguridad: privacidad de salida | Respuesta con email, teléfono y DNI | Se enmascaran en `/consultar` y en `/estado`; se conservan citas `DOC-*` | `test_consultar_masks_personal_data_in_agent_output`, `test_estado_masks_personal_data_in_persisted_messages`, `test_output_validator_masks_email_phone_and_personal_identifiers` |

La demostración manual de persistencia HTTP después de reiniciar el servidor está
documentada en `README.md`: usar el mismo `thread_id`, reiniciar Uvicorn y consultar
`GET /estado/{thread_id}`.

## Resultados observados en el cierre

La suite local final aprobó **26 pruebas**. Evidencia:
[salida de pytest](evidencias/pytest.txt) y [reporte JUnit](evidencias/pytest.xml).
Los agentes y el RAG de estos tests son dobles; SQLite, la API y los validadores
sí se ejecutan. Esto no acredita por sí solo elección autónoma del modelo real.

| Escenario adicional | Resultado observado | Prueba |
|---|---|---|
| Lectura o negación no habilitan escritura | Cinco variantes rechazadas como autorización | `test_mentions_and_negations_do_not_authorize_writes` |
| Entrada larga se registra | Una consulta, un error y un bloqueo; no se llama al agente | `test_http_rejects_oversized_input_before_invoking_agent` |
| Hilo inválido | 422 y bloqueo contado; no se refleja email de la entrada | `test_invalid_thread_is_counted_without_echoing_input` |
| Errores de ejecución | 503 por límite y 502 por fallo; contador de errores incrementado | `test_execution_errors_are_counted_and_do_not_expose_details` |
| Persistencia vía HTTP | Historial conserva cuatro mensajes al reabrir la aplicación | `test_http_memory_survives_server_restart` |

## Validación del modelo real

`python -m entrega_4.validacion_real` comprueba los siguientes escenarios y
exporta `evidencias/validacion_http.json` con estados, tiempos, respuestas y
herramientas observadas. `aprobado=true` acredita que sus aserciones terminaron.

| Escenario | Comprobación automática |
|---|---|
| RAG | Llamada a `buscar_informes_scouting` y cita DOC-006 |
| Actuador | Llamada a `registrar_nota_seguimiento` |
| Sensor | Llamada a `consultar_notas_seguimiento`, sin nueva escritura |
| Reinicio y memoria | Dos procesos Uvicorn consecutivos, historial idéntico y respuesta que recuerda Jugador Demo |
| Guardrails | Inyección y exceso de longitud devuelven 422 |

La corrida real del 16/11/2026 aprobó los seis escenarios: cuatro respuestas
HTTP 200 y dos bloqueos HTTP 422, con historial idéntico de seis mensajes después
de reiniciar. Evidencia: [validacion_http.json](evidencias/validacion_http.json).
La traza posterior con destino corregido fue leída y verificada remotamente:
[langsmith.json](evidencias/langsmith.json). Incluye agente, herramienta RAG y
tres llamadas al modelo, sin error, con 2.261 tokens y costo USD 0,0009515.
Comando: `python -m entrega_4.exportar_trazas --evidence comprobacion_tracing.json`.
Las trazas de la corrida HTTP original no se recuperaron en este workspace.
