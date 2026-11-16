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
