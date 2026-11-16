# Defensa en vivo — 15 minutos

## Preparación previa

Seguir el README desde un clon limpio. Verificar cuota de Gemini, proyecto
LangSmith y acceso a Internet. Ejecutar tests y validación real. Abrir README,
ficha técnica, matriz, Swagger y LangSmith. No mostrar `.env` ni claves.
Usar un hilo nuevo para que el contexto anterior no altere la demostración.

## Guion cronometrado

| Minutos | Mostrar y explicar |
|---|---|
| 0–2 | Problema de scouting, corpus y alcance. E2 almacena, E3 recupera y responde, E4 decide herramientas. |
| 2–4 | Diagrama de ficha técnica, tres herramientas, límite del grafo y memoria por hilo. |
| 4–6 | `/health`; `/consultar`: «¿Qué habilidades tiene el arquero moderno?». Mostrar cita DOC-006 y herramienta en LangSmith. |
| 6–8 | «Registrá una nota para Jugador Demo: revisar juego aéreo»; después «Mostrame las notas de seguimiento de Jugador Demo». Mostrar ID persistido y selección de actuador/sensor. |
| 8–10 | Mostrar `/estado`, detener servidor y reiniciarlo. Mismo historial, luego «¿De qué jugador acabamos de guardar una nota?» con el mismo hilo. |
| 10–12 | Inyección devuelve 422; entrada de 4001 caracteres devuelve 422; mostrar tests de privacidad y negación de escritura. |
| 12–13 | `/metricas`, logs JSON y traza LangSmith. Explicar tokens, latencia y costo estimado frente a facturación real. |
| 13–15 | Limitaciones y preguntas. |

## Preguntas probables

- **¿Por qué es un agente?** El modelo elige herramientas y puede encadenarlas;
  no todas las consultas ejecutan el mismo RAG.
- **¿Sensor y actuador?** El sensor lee notas, el actuador las inserta y devuelve
  un ID. La autorización se comprueba fuera del modelo.
- **¿Qué persiste?** Conversaciones por hilo, notas de dominio y métricas, en
  almacenes distintos. Reiniciar el proceso no borra esos archivos.
- **¿Cómo evitás alucinaciones?** Evidencia recuperada, citas y abstención en el
  prompt; son mitigaciones, no una garantía.
- **¿Los tests llaman a Gemini?** La suite local usa dobles; el script real usa
  el modelo, sockets HTTP y dos procesos consecutivos de Uvicorn.
- **¿Por qué `null` en costo?** Faltan tarifas configuradas o uso no disponible;
  no equivale a gratuidad. Embeddings se presupuestan por separado.
- **¿Está listo para múltiples usuarios públicos?** La demo tiene token compartido;
  no implementa permisos por hilo, TLS ni pruebas de carga.

Si el proveedor falla en vivo, mostrar la evidencia guardada indicando que es una
corrida anterior. No presentar respuestas simuladas como ejecución real.
