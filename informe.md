A.1
Futbol_Inform es una plataforma de análisis de scouting que centraliza informes tácticos y cualitativos de futbolistas elaborados por ojeadores de diferentes paises. El proceso manual que busca automatizar es la lectura y extracción de valor de los reportes en texto libre para cruzarlos con métricas estructuradas de rendimiento, permitiendo a la secretaría técnica responder consultas complejas de mercado sin tener que leer carpetas enteras de documentos desestructurados.

A.2
Prompt utilizado:
Actuá como el sistema de atención de Futbol_Inform. Un usuario pregunta: Necesito un informe completo de scouting sobre Franco Mastantuono que incluya sus estadísticas en el último semestre, las observaciones tácticas de nuestros ojeadores en Europa y si el club actual aceptaría negociar por debajo de la cláusula de rescisión. Respondé como lo haría el sistema.

Respuesta del modelo:
"Hola. Franco Mastantuono es un mediocampista ofensivo que actualmente juega en River Plate. **En el último semestre ha tenido destacadas actuaciones, registrando aproximadamente 5 goles y 3 asistencias en competiciones locales e internacionales.** Según los informes de los ojeadores en Europa, se destaca por su gran pegada de media distancia, visión de juego y desequilibrio en el uno contra uno, aunque señalan que debe mejorar la intensidad en el retroceso defensivo y la toma de decisiones bajo presión alta. Respecto a la negociación, se estima que su cláusula de rescisión ronda los 45 millones de euros, y aunque su club prefiere ejecutarla completa, **existen sondeos de que podrían aceptar una oferta estructurada cercana a los 30-35 millones más bonus por objetivos."**

**Parte inventada**

Nivel de confianza con el que la presentó: 
Alto. El modelo respondió con un tono corporativo, asertivo y totalmente seguro de los datos, sin advertir que carecía de la base de datos interna de la empresa o de los informes privados de los ojeadores.

Qué le faltó al modelo para responder bien:
- Acceso a la base de datos estructurada de rendimiento (fuente de verdad cuantitativa).
- Contexto actualizado de las negociaciones de mercado reales y contractuales del jugador en tiempo real


A.3 - PEAS extendido
Performance: Precisión y relevancia en la extracción de información de los informes, reducción del tiempo de búsqueda y minimización de alucinaciones al responder consultas sobre jugadores.

Environment: Opera en la nube para el equipo de scouting y directiva del club. Se integra con bases de datos relacionales de estadísticas de jugadores y sistemas de gestión interna de la secretaría técnica.

Actuators: Generar reportes comparativos en PDF, enviar alertas automáticas por correo sobre nuevos perfiles de jugadores.

Sensors: Recibe consultas en lenguaje natural (texto/chat) de los analistas, documentos PDF con informes de ojeadores, y flujos de datos estructurados (métricas de rendimiento y estadísticas de partidos).

Base de conocimiento: Repositorio documental de informes de scouting cualitativos, base de datos SQL con estadísticas cuantitativas de los futbolistas y perfiles históricos de mercado (como jugadores retirados).

A.4
ES: 27 tokens
EN: 22 tokens
El español consume una mayor cantidad de tokens por consulta en comparación con el inglés debido a la codificación del vocabulario. Si el sistema procesa miles de consultas diarias, esta diferencia genera un incremento acumulativo significativo en los costos.

B.1
Los analistas sufren una enorme carga cognitiva al tener que leer, interpretar y contrastar notas de ojeadores de múltiples fuentes, lo que genera una alta latencia (semanas) para procesar un perfil completo de un jugador antes de una decisión de mercado.
Lo sufre la secretaría técnica y los directores deportivos del club de manera diaria y continua, especialmente en los períodos previos y durante los mercados de pases.
Se pierden oportunidades de fichaje a tiempo frente a otros clubes competidores, se toman decisiones basadas en sesgos o lecturas incompletas de informes dispersos, y se desaprovecha el conocimiento histórico acumulado en documentos de texto no estructurados.

B.2
El sistema lo utilizarían secretarios técnicos, analistas de scouting y directores deportivos.
Hoy en día el usuario debe buscar manualmente en carpetas compartidas o sistemas de archivos, leer decenas de páginas de notas subjetivas escritas por diferentes ojeadores, y cruzar esos datos de forma mental o mediante planillas rudimentarias con estadísticas de rendimiento para armar un perfil básico del jugador.

B.3

Entrada del usuario(caos): ¿Tiene el perfil del jugador Neymar Jr.?
Intención(LLM): CONSULTA_PERFIL
Parámetros(LLM): {"jugador": "Neymar Jr."}
Acción de backend(determinista): SELECT * FROM jugadores WHERE nombre = 'Neymar Jr.'
Riesgo: Bajo (consulta basica de lectura)

Entrada del usuario(caos): Buscame los informes tácticos que hablan sobre la presión alta de los extremos en el informe de Europa.
Intención(LLM): CONSULTA_INFORMES
Parámetros(LLM): {"criterio": "presión alta", "posicion": "extremos", "fuente": "Europa"}
Acción de backend(determinista): vector_search(query="presión alta", filter={"posicion": "extremos", "fuente": "Europa"})
Riesgo: Bajo (búsqueda sobre repositorio vectorial de documentos cualitativos)

Entrada del usuario(caos): Subí este nuevo archivo PDF con el informe de scouting del juvenil Aranda y actualizá sus datos.
Intención(LLM): ALTA_JUGADOR_SCOUTING
Parámetros(LLM): {"jugador": "Aranda", "archivo": "informe_aranda.pdf", "posicion": "Mediocampista"}
Acción de backend(determinista): INSERT INTO informes_scouting (nombre_jugador, posicion, archivo_pdf) VALUES ('Aranda', 'Mediocampista', 'informe_aranda.pdf') + chunking_and_vectorize(pdf)
Riesgo: Alto (operación de escritura)