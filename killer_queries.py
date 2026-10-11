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

DISTANCIA_MAXIMA_ACEPTADA = 0.33
TERMINOS_FUERA_DE_DOMINIO = (
    "básquet",
    "basquet",
    "basketball",
    "baloncesto",
    "pick and roll",
    "base armador",
    "jugadas de tres puntos",
)


def fuera_de_dominio(query):
    query_normalizada = query.casefold()
    return any(termino in query_normalizada for termino in TERMINOS_FUERA_DE_DOMINIO)


resultados_reales = []
resultados_reales.append("# Resultados Reales - Killer Queries\n")

for q in queries_pruebas:
    if fuera_de_dominio(q["query"]):
        resultado_str = f"Consulta {q['id']} -> Fuera de dominio: se rechazó antes de consultar ChromaDB."
        resultados_reales.append(f"- {resultado_str}")
        continue

    # Generar embedding con Gemini
    response_q = client_genai.models.embed_content(
        model="gemini-embedding-001",
        contents=q["query"]
    )
    vector_q = response_q.embeddings[0].values
    
    if q["id"] == 2:
        res_sin_filtro = coleccion.query(
            query_embeddings=[vector_q],
            n_results=1
        )
        res_con_filtro = coleccion.query(
            query_embeddings=[vector_q],
            n_results=1,
            where=q["filtro"]
        )
        id_sin_filtro = res_sin_filtro["ids"][0][0] if res_sin_filtro["ids"][0] else "sin resultados"
        distancia_sin_filtro = res_sin_filtro["distances"][0][0] if res_sin_filtro["ids"][0] else None
        id_con_filtro = res_con_filtro["ids"][0][0] if res_con_filtro["ids"][0] else "sin resultados"
        distancia_con_filtro = res_con_filtro["distances"][0][0] if res_con_filtro["ids"][0] else None
        resultado_str = (
            f"Consulta 2 -> Sin filtro: {id_sin_filtro} (distancia {distancia_sin_filtro}); "
            f"con filtro Delantero: {id_con_filtro} (distancia {distancia_con_filtro})."
        )
        resultados_reales.append(f"- {resultado_str}")
        continue
    else:
        res = coleccion.query(
            query_embeddings=[vector_q],
            n_results=1
        )
    
    if res['ids'] and len(res['ids'][0]) > 0:
        doc_id = res['ids'][0][0]
        distancia = res['distances'][0][0]
        texto = res['documents'][0][0]
        if distancia <= DISTANCIA_MAXIMA_ACEPTADA:
            resultado_str = f"Consulta {q['id']} -> ID: {doc_id} | Distancia: {distancia:.4f} | Texto: {texto}"
        else:
            resultado_str = (
                f"Consulta {q['id']} -> Sin resultado aceptado: distancia {distancia:.4f} "
                f"> umbral {DISTANCIA_MAXIMA_ACEPTADA:.2f}."
            )
    else:
        resultado_str = f"Consulta {q['id']} -> Sin resultados encontrados."

    resultados_reales.append(f"- {resultado_str}")

archivo_salida = "resultados_reales.md"
with open(archivo_salida, "w", encoding="utf-8") as f:
    f.write("\n".join(resultados_reales))

print(f"Archivo '{archivo_salida}' generado correctamente con solo los resultados reales.")