## A.1 — Autopsia del contexto estático

Desangre de tokens: La base de conocimientos maneja 17 informes de scouting y PDFs tácticos. Pasarlos todos enteros en el System Prompt en cada consulta generaría un costo insostenible en tokens de entrada y latencias muy altas.

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
La demostración está implementada y es ejecutable con `python evento_negocio.py`. Usa la colección persistente, crea un ID temporal, verifica el resultado con `get()` y lo elimina al finalizar.

Salida capturada:

Upsert verificado para __B3_UPSERT_DEMO__.
Documento: Informe temporal para demostrar un upsert de negocio.
Metadatos: {'posicion': 'Extremo', 'tags': 'demo', 'vigente': False}
Registro temporal __B3_UPSERT_DEMO__ eliminado; colección restaurada.

`upsert` crea o reemplaza el registro por ID; `get()` comprueba la escritura. El ejemplo usa un ID temporal para no sobrescribir un informe real.

## B.5 - ETL y purga semántica
La ETL corrige cuatro problemas del dataset antes de persistirlo:

- Mapea la clave real `position` de DOC-014 a `posicion`.
- Normaliza `vigente` a booleano, incluso cuando la entrada llega como texto `"true"` o `"false"`.
- Si encuentra IDs repetidos, conserva el primero y agrega sufijos deterministas (`-2`, `-3`, etc.) a los siguientes; los embeddings ya no se pisan en un diccionario por colisión de ID.
- Compara todos los pares cercanos y conserva un único documento por grupo de duplicados relacionados, en vez de saltarse comparaciones cuando un documento ya fue marcado.

El corte de distancia coseno deja de ser el valor fijo `0.08`: se calcula en cada corrida como el punto medio entre DOC-016/DOC-017 (par etiquetado como duplicado) y los pares de control DOC-016/DOC-005 y DOC-017/DOC-006 (etiquetados como distintos). Se exige una separación mínima de `0.01`; si no se cumple, la ETL se detiene sin purgar. Así el umbral se basa en distancias de los embeddings actuales, no en una constante sin calibrar. La base JSON actual contiene 17 IDs únicos; el caso de colisión queda cubierto en la transformación para cuando aparezca.

## B.6 - Killer Queries

Las siguientes salidas fueron generadas por `killer_queries.py` y están registradas en `resultados_reales.md`.

### Consulta 1: 'Preciso un wing eléctrico que desborde por la raya y tire centros venenosos'
Resultado: DOC-008 | Distancia coseno: 0.3198.
Evaluación: recupera el informe del extremo ante una consulta expresada con jerga distinta a la descripción del documento.

### Consulta 2: 'Revisión táctica de defensor central tiempista y fuerte'
Sin filtro: DOC-005 | Distancia coseno: 0.0835.
Con filtro `posicion=Delantero`: DOC-004 | Distancia coseno: 0.2420.
Evaluación: sin filtro gana el defensor semánticamente más cercano; con el filtro estricto se devuelve un delantero, demostrando el contraste solicitado.

### Consulta 3: 'Necesito un base armador con buen manejo de pick and roll para jugadas de tres puntos'
Resultado: rechazada por estar fuera del dominio; no se generó embedding ni se consultó ChromaDB.
Evaluación: no se acepta un informe futbolístico por proximidad vectorial para responder una consulta de básquet.

## C.1 - Cadena de coherencia con la Entrega 1

Base de Conocimiento del PEAS: En la Entrega 1 se definió un repositorio documental de informes de scouting. En la Entrega 2 se implementa mediante la colección persistente de ChromaDB, donde se almacenan los documentos vectorizados junto con sus metadatos.

Campos de filtrado de la Matriz de Intenciones: En la Entrega 1 se definieron parámetros como posicion y fuente para CONSULTA_INFORMES. En la Entrega 2 estos campos pasan a utilizarse como metadatos de ChromaDB para realizar filtros duros mediante where.

Parámetros extraídos del texto_libre: El LLM extrae jugador, criterio, posicion, fuente y archivo mediante ConsultaScoutingSchema. Estos parámetros pueden utilizarse para realizar la búsqueda semántica y construir los filtros de la consulta a ChromaDB.

El vector_search planteado en la Entrega 1 para buscar informes se implementa en esta entrega mediante coleccion.query(), combinando la búsqueda por similitud semántica con filtros sobre los metadatos.

De esta manera, la Entrega 2 implementa la Base de Conocimiento que en la Entrega 1 se había definido a nivel de diseño.

## C.2 - El umbral de aceptación

`killer_queries.py` define una distancia coseno máxima inicial de `0.33` para aceptar un resultado de recuperación. Se eligió para conservar la consulta futbolística válida cuyo último resultado guardado fue 0.3198, con aproximadamente 0.01 de margen. No equivale al umbral teórico de similitud 0.75 de A.2: ese valor todavía no está calibrado para los embeddings y consultas de este corpus.

La Killer Query 3 tuvo distancia 0.2857 en la corrida anterior, por debajo de 0.33. Por tanto, la distancia por sí sola no separa consultas válidas de consultas fuera del dominio. El código rechaza este caso por sus términos explícitos de básquet antes de buscar. El límite de 0.33 es provisional y debe recalibrarse con un conjunto mayor de consultas futbolísticas y ajenas al dominio; la regla de palabras no cubre todas las formas posibles de una consulta fuera de alcance.

## C.3 - Cierre: dónde se conecta

Actualmente la búsqueda híbrida devuelve los documentos encontrados en ChromaDB como datos de Python.

Para convertir estos resultados en una respuesta real al usuario falta incorporar un orquestador RAG.

El orquestador conectaría la interpretación de la consulta realizada por el LLM con la búsqueda en ChromaDB y posteriormente enviaría los documentos recuperados al LLM para generar la respuesta final utilizando únicamente la información obtenida de la Base de Conocimiento.