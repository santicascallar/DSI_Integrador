## A.1 — Autopsia del contexto estático

Desangre de tokens: La base de conocimientos maneja más de 5.000 informes de scouting y PDFs tácticos. Pasarlos todos enteros en el System Prompt en cada consulta generaría un costo insostenible en tokens de entrada y latencias muy altas.

Lost in the middle: Si el informe clave sobre la presión alta de un lateral se encuentra enterrado en medio de 50 páginas de estadísticas masivas, el modelo de lenguaje tenderá a ignorarlo u omitirlo por la fatiga del contexto largo.

Inconsistencia de estado concurrente: Las lesiones de última hora, las cotizaciones de mercado y las estadísticas de los partidos del fin de semana cambian constantemente mientras el usuario está en la sesión. También si un analista sube un nuevo informe en PDF de un jugador o actualiza sus métricas justo en el momento en que otro usuario está consultando su perfil o sus estadísticas, se genera una inconsistencia de estado concurrente.

Una búsqueda relacional usando LIKE depende estrictamente de coincidencias exactas de strings y carece de comprensión semántica. Si el scout busca "problemas en la salida baja" y el informe dice "dificultades para iniciar el juego desde el arco", la consulta SQL fallará totalmente, mientras que la búsqueda vectorial captura la similitud conceptual.

## A.2 - Similitud coseno a mano
Eje X --> Nivel de intensidad defensiva (0-10)
Eje Y --> Nivel de volumen ofensivo (0-10)

Vector de consulta C: (4,3) --> Se busca un perfil equilibrado, pero con un poco más de intesidad defensiva
Vector de Documento A: (3,4)
Vector de Documento B: (0,5)

Similitud(C,A) = C x A/|C| x |A|
Se multiplica coordenada a coordeanada y se suman los resultados: 24
Con el teorema de pitágoras se calcula las magnitudes de C Y B
Similitud(C,A) = 24/(5 x 5)
Similitud(C,A) = 24/25 = 0.96

Esto signifca que hay una alta relación entre lo que busca el scout y el documento analizado.

Similitud(C,B) = C x B/|C| x |B|
Se multiplica coordenada a coordeanada y se suman los resultados: 15
Con el teorema de pitágoras se calcula las magnitudes de C Y B
Similitud(C,B) = 15/(5 x 5)
Similitud(C,B) = 15/25 = 0.60

Esto significa que no hay una alta relación entre C y B ya que queda por debajo del umbral de aceptación que es de 0.75

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

## B.2 - Los tres límites de FAISS que ChromaDB resuelve

Límite de FAISS:
A. Sin persistencia transaccional/atomicidad
B. Sin filtrado híbrido nativo
C. CRUD ineficiente / sin concurrencia

Cómo se manifiesta en su dominio:
A. Si el servidor se interrumpe o apaga a mitad de una ingesta masiva de informes de scouting, el archivo del índice FAISS puede corromperse o quedar desincronizado.
B. Cuando el analista realiza una búsqueda compleja (por ejemplo: "Buscar un extremo rápido, pero que obligatoriamente tenga vigente: true"), FAISS por sí solo no puede filtrar por metadatos relacionales al mismo tiempo.
C. Si un scout necesita actualizar el puntaje o eliminar un informe desactualizado de un jugador específico (Update / Delete), FAISS no permite modificar registros individuales de forma sencilla, exigiendo en la mayoría de los casos reconstruir y reindexar toda la matriz vectorial desde cero.

Cómo lo resuelve ChromaDB
A. Lo resuelve creando una carpeta llamada chroma_db en mi directorio para guardar los datos.
B. Lo resuelve integrando filtrado híbrido nativo mediante su parámetro where, permitiendo combinar la similitud vectorial con condiciones estrictas sobre los metadatos en una sola consulta.
C. Lo resuelve ofreciendo un motor con soporte CRUD completo a través de métodos como upsert, lo que permite modificar o actualizar informes de jugadores de forma individual y eficiente sin necesidad de reindexar toda la base de datos.

## B.3 - Evento de negocio en caliente
id_objetivo = "DOC-001"
print(f"\nSimulando evento en caliente para el documento {id_objetivo}...")

### Actualiza el estado o la descripción
coleccion.upsert(
    ids=[id_objetivo],
    documents=["[ACTUALIZADO] Nuevo informe táctico profundo sobre la presión alta, con ajustes tácticos post-partido y revisión de rendimiento."],
    metadatas=[{"posicion": "Extremo", "vigente": "False", "tags": "pressing, actualizado"}]
)
resultado_verificacion = coleccion.get(ids=[id_objetivo])
print("Documento actualizado verificado con get():")
print(resultado_verificacion)

Se utiliza upsert porque actúa como una operación idempotente (crea el registro si no existe o lo actualiza si ya existe), evitando los errores de ID duplicado que arrojaría add y la falla de no encontrar el registro que daría update si el documento aún no fue creado.

## B.5 - ETL y purga semántica
Se eliminó uno de los dos casi-duplicados que había. Al tener redacciones distintas, descripciones con jerga variada e IDs diferentes, el motor relacional (SELECT DISTINCT) los interpreta como registros completamente únicos e independientes, permitiendo que la redundancia pase desapercibida. Solo un enfoque semántico basado en espacio vectorial y distancia coseno permite comprender que conceptualmente expresan exactamente la misma información.

## B.6 - Killer Queries

### 1
Consulta: Preciso un wing eléctrico que desborde por la raya y tire centros venenosos
Que pone a prueba: Poder semántico: jerga sin palabras exactas del documento
Resultado esperado: Debe encontrar el informe de extremo (DOC-008)
Resultado real: DOC-008 | Distancia: 0.3198
¿Pasó?: Si

### 2
Consulta: Revisión táctica de defensor central tiempista y fuerte
Que pone a prueba: El metadato salva el día: la semántica cruda traería un desastre, el filtro lo bloquea.
Resultado esperado: El sistema no debe traer al defensor central, sino restringirse estrictamente al filtro de delanteros.
Resultado real: DOC-004 (Delantero) | Distancia: 0.2420
¿Pasó?: Si

### 3
Consulta: Necesito un base armador con buen manejo de pick and roll para jugadas de tres puntos
Que pone a prueba: Prueba de estrés: consulta fuera del catálogo — debe responder “no tengo eso”
Resultado esperado: El sistema debe arrojar distancia muy alta o resultados vacíos / irrelevantes (equivalente a "no tengo eso").
Resultado real: ID: DOC-010 | Distancia: 0.2857
¿Pasó?: No

C