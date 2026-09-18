import os
import json
from dotenv import load_dotenv
from google import genai
import numpy as np
import chromadb

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
client_genai = genai.Client(api_key=api_key)

print("Cargando base de conocimiento cruda...")
with open("base_conocimiento.json", "r", encoding="utf-8") as f:
    documentos_raw = json.load(f)

print("\n[ETL] Normalizando claves mal nombradas y tipos de datos")
documentos_limpios = []

for doc in documentos_raw:
    d = doc.copy()
    meta = d.get("metadatos", {}).copy()

    if "position" in meta and "posicion" not in meta:
        meta["posicion"] = meta.pop("position")

    vigente_val = meta.get("vigente", "true")
    if isinstance(vigente_val, bool):
        meta["vigente"] = str(vigente_val).lower()
    else:
        meta["vigente"] = str(vigente_val).lower()

    d["metadatos"] = meta
    documentos_limpios.append(d)

print(f"[ETL] Total de documentos tras normalización estructural: {len(documentos_limpios)}")

print("\n[ETL] Generando embeddings para purga semántica...")
embeddings_dict = {}

for doc in documentos_limpios:
    doc_id = doc["id"]
    texto = doc["descripcion_semantica"]
    
    response = client_genai.models.embed_content(
        model="gemini-embedding-001",
        contents=texto
    )
    embeddings_dict[doc_id] = np.array(response.embeddings[0].values)

UMBRAL_DISTANCIA = 0.08 
ids_a_eliminar = set()
ids_procesados = list(embeddings_dict.keys())

print(f"\n[ETL] Analizando duplicados con umbral de distancia coseno < {UMBRAL_DISTANCIA}")

for i in range(len(ids_procesados)):
    for j in range(i + 1, len(ids_procesados)):
        id_a = ids_procesados[i]
        id_b = ids_procesados[j]
        
        if id_a in ids_a_eliminar or id_b in ids_a_eliminar:
            continue
            
        vec_a = embeddings_dict[id_a]
        vec_b = embeddings_dict[id_b]
        
        cosine_sim = np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))
        cosine_dist = 1.0 - cosine_sim
        
        if cosine_dist < UMBRAL_DISTANCIA:
            print(f"  [DUPLICADO DETECTADO] '{id_a}' y '{id_b}' tienen una distancia de {cosine_dist:.4f}")
            print(f"     -> Marcando '{id_b}' para purga semántica.")
            ids_a_eliminar.add(id_b)

documentos_finales = [doc for doc in documentos_limpios if doc["id"] not in ids_a_eliminar]
print(f"\n[ETL] Purga finalizada. Documentos eliminados: {list(ids_a_eliminar)}")
print(f"[ETL] Total de documentos listos para persistir: {len(documentos_finales)}")


print("\n[ETL] Guardando dataset purgado y normalizado en ChromaDB...")
chroma_client = chromadb.PersistentClient(path="./chroma_db_purgada")
coleccion = chroma_client.get_or_create_collection(
    name="futbol_inform_purgado",
    metadata={"hnsw:space": "cosine"}
)

ids = [doc["id"] for doc in documentos_finales]
textos = [doc["descripcion_semantica"] for doc in documentos_finales]
vectores = [embeddings_dict[doc["id"]].tolist() for doc in documentos_finales]
metadatos = [{
    "posicion": doc["metadatos"]["posicion"],
    "vigente": doc["metadatos"]["vigente"],
    "tags": ", ".join(doc["metadatos"]["tags_regionales"])
} for doc in documentos_finales]

coleccion.upsert(
    ids=ids,
    embeddings=vectores,
    documents=textos,
    metadatas=metadatos
)

print(f"Proceso ETL y purga completado. Total en ChromaDB purgada: {coleccion.count()}")