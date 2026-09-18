import os
import json
from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró la GEMINI_API_KEY en las variables de entorno.")

client_genai = genai.Client(api_key=api_key)

print("Cargando base_conocimiento.json...")
with open("base_conocimiento.json", "r", encoding="utf-8") as f:
    documentos = json.load(f)

print("Inicializando ChromaDB (PersistentClient)...")
chroma_client = chromadb.PersistentClient(path="./chroma_db")

coleccion = chroma_client.get_or_create_collection(
    name="futbol_inform_scouting",
    metadata={"hnsw:space": "cosine"}
)

print("Generando embeddings con la API de Google y preparando datos...")
ids = []
embeddings = []
metadatos = []
textos = []

for doc in documentos:
    texto = doc["descripcion_semantica"]
    doc_id = doc["id"]
    
    response = client_genai.models.embed_content(
        model="gemini-embedding-001",
        contents=texto
    )
    vector = response.embeddings[0].values
    
    ids.append(doc_id)
    embeddings.append(vector)
    textos.append(texto)
    
    meta_plana = {
        "posicion": doc["metadatos"]["posicion"],
        "vigente": str(doc["metadatos"]["vigente"]),
        "tags": ", ".join(doc["metadatos"]["tags_regionales"])
    }
    metadatos.append(meta_plana)

print("Realizando la ingesta de datos con upsert")
coleccion.upsert(
    ids=ids,
    embeddings=embeddings,
    documents=textos,
    metadatas=metadatos
)

consulta_prueba = "Necesito un extremo rápido que haga la banda y desequilibre"
print(f"\nProbando consulta en ChromaDB: '{consulta_prueba}'")

response_q = client_genai.models.embed_content(
    model="gemini-embedding-001",
    contents=consulta_prueba
)
vector_q = response_q.embeddings[0].values

resultados = coleccion.query(
    query_embeddings=[vector_q],
    n_results=2
)

print("Resultados obtenidos:")
for i in range(len(resultados['ids'][0])):
    print(f"  -> ID: {resultados['ids'][0][i]} | Distancia: {resultados['distances'][0][i]:.4f}")
    print(f"     Texto: {resultados['documents'][0][i][:80]}...")


def buscar_jugadores(query_semantica: str, posicion_filtro: str, solo_activos: bool = True, n_results: int = 2):
    """
    Realiza una búsqueda híbrida combinando similitud semántica y filtrado duro nativo en ChromaDB.
    """
    filtro_where = {
        "$and": [
            {"posicion": {"$eq": posicion_filtro}},
            {"vigente": {"$eq": str(solo_activos)}}
        ]
    }
    
    print(f"\n- BÚSQUEDA HÍBRIDA -")
    print(f"Consulta: '{query_semantica}' | Filtro: Posición = {posicion_filtro}, Vigente = {solo_activos}")

    resultados = coleccion.query(
        query_embeddings=[vector_q],
        n_results=n_results,
        where=filtro_where
    )
    
    return resultados

res_hibrida = buscar_jugadores(
    query_semantica="Extremo rápido y desequilibrante", 
    posicion_filtro="Extremo", 
    solo_activos=True, 
    n_results=2
)

print("Resultados híbridos obtenidos:", res_hibrida['ids'])