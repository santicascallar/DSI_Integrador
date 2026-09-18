import os
from dotenv import load_dotenv
from google import genai
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client_genai = genai.Client(api_key=api_key)

chroma_client = chromadb.PersistentClient(path="./chroma_db_purgada")
try:
    coleccion = chroma_client.get_collection(name="futbol_inform_purgado")
except:
    coleccion = chroma_client.get_collection(name="futbol_inform_scouting")

queries_pruebas = [
    {
        "id": 1,
        "query": "Preciso un wing eléctrico que desborde por la raya y tire centros venenosos",
        "filtro": None
    },
    {
        "id": 2,
        "query": "Revisión táctica de defensor central tiempista y fuerte",
        "filtro": {"posicion": {"$eq": "Delantero"}}
    },
    {
        "id": 3,
        "query": "Necesito un base armador con buen manejo de pick and roll para jugadas de tres puntos",
        "filtro": None
    }
]

resultados_reales = []
resultados_reales.append("# Resultados Reales - Killer Queries\n")

for q in queries_pruebas:
    # Generar embedding con Gemini
    response_q = client_genai.models.embed_content(
        model="gemini-embedding-001",
        contents=q["query"]
    )
    vector_q = response_q.embeddings[0].values
    
    if q["filtro"]:
        res = coleccion.query(
            query_embeddings=[vector_q],
            n_results=1,
            where=q["filtro"]
        )
    else:
        res = coleccion.query(
            query_embeddings=[vector_q],
            n_results=1
        )
    
    if res['ids'] and len(res['ids'][0]) > 0:
        doc_id = res['ids'][0][0]
        distancia = res['distances'][0][0]
        texto = res['documents'][0][0]
        resultado_str = f"Consulta {q['id']} -> ID: {doc_id} | Distancia: {distancia:.4f} | Texto: {texto}"
    else:
        resultado_str = f"Consulta {q['id']} -> Sin resultados encontrados."

    resultados_reales.append(f"- {resultado_str}")

archivo_salida = "resultados_reales.md"
with open(archivo_salida, "w", encoding="utf-8") as f:
    f.write("\n".join(resultados_reales))

print(f"Archivo '{archivo_salida}' generado correctamente con solo los resultados reales.")