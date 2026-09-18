## A.1 — Autopsia del contexto estático

Desangre de tokens: La base de conocimientos maneja más de 5.000 informes de scouting y PDFs tácticos. Pasarlos todos enteros en el System Prompt en cada consulta generaría un costo insostenible en tokens de entrada y latencias muy altas.

Lost in the middle: Si el informe clave sobre la presión alta de un lateral se encuentra enterrado en medio de 50 páginas de estadísticas masivas, el modelo de lenguaje tenderá a ignorarlo u omitirlo por la fatiga del contexto largo.

Inconsistencia de estado concurrente: Las lesiones de última hora, las cotizaciones de mercado y las estadísticas de los partidos del fin de semana cambian constantemente mientras el usuario está en la sesión. También si un analista sube un nuevo informe en PDF de un jugador o actualiza sus métricas justo en el momento en que otro usuario está consultando su perfil o sus estadísticas, se genera una inconsistencia de estado concurrente.

Una búsqueda relacional usando LIKE depende estrictamente de coincidencias exactas de strings y carece de comprensión semántica. Si el scout busca "problemas en la salida baja" y el informe dice "dificultades para iniciar el juego desde el arco", la consulta SQL fallará totalmente, mientras que la búsqueda vectorial captura la similitud conceptual.

## A.2 


## A.5 - Prueba destructiva: volatilidad de la RAM

### Sin write_index()
python pipeline_vectorial.py
Cargando base_conocimiento.json...
Generando embeddings con la API de Google (15 documentos procesados)...
Construyendo índice en memoria RAM...
[INFO] Índice listo para buscar.
--- (Simula reinicio del sistema / cierre de la terminal) ---
python pipeline_vectorial.py (Nueva ejecución)
Cargando base_conocimiento.json...
[WARN] Archivo 'vector_index.faiss' no encontrado.
Generando embeddings con la API de Google... ¡NUEVO CONSUMO DE TOKENS! (Se vuelve a gastar cuota de la API innecesariamente).

### Con write_index()
python pipeline_vectorial.py (Primera ejecución)
Cargando base_conocimiento.json...
Generando embeddings y guardando con faiss.write_index()...
Índice persistido correctamente en 'vector_index.faiss'.
--- (Simula reinicio del sistema / cierre de la terminal) ---
python pipeline_vectorial.py (Segunda ejecución)
Cargando base_conocimiento.json...
Cargando índice FAISS existente desde 'vector_index.faiss'...
[EXITO] Índice recargado desde disco de forma instantánea. [0 tokens consumidos a la API].

Lo que pasa en producción si el servidor se reinicia es que hay un nuevo consumo de tokens, en cambio si cuenta con persistencia en disco, el sistema se recupera de manera automática e instantánea al recargar el archivo .faiss, evitando costos adicionales de tokens.

Si hubiera dos servidores un archivo local en disco genera inconsistencias (cada servidor tendría su propio índice aislado).

