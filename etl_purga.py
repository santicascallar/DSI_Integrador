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
ids_utilizados = set()

for doc in documentos_raw:
    d = doc.copy()
    meta = d.get("metadatos", {}).copy()

    if "position" in meta and "posicion" not in meta:
        meta["posicion"] = meta.pop("position")

    vigente_val = meta.get("vigente", True)
    if isinstance(vigente_val, str):
        vigente_val = vigente_val.strip().lower()
        if vigente_val not in {"true", "false"}:
            raise ValueError(f"Valor inválido para vigente en {d['id']}: {vigente_val!r}")
        vigente_val = vigente_val == "true"
    elif not isinstance(vigente_val, bool):
        raise TypeError(f"vigente debe ser bool o str en {d['id']}")
    meta["vigente"] = vigente_val

    id_original = str(d["id"])
    id_unico = id_original
    sufijo = 2
    while id_unico in ids_utilizados:
        id_unico = f"{id_original}-{sufijo}"
        sufijo += 1
    if id_unico != id_original:
        print(f"[ETL] ID duplicado '{id_original}' reasignado como '{id_unico}'")
    d["id"] = id_unico
    ids_utilizados.add(id_unico)

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

PARES_DUPLICADOS_CONFIRMADOS = [("DOC-016", "DOC-017")]
PARES_DISTINTOS_CONFIRMADOS = [("DOC-016", "DOC-005"), ("DOC-017", "DOC-006")]
MARGEN_CALIBRACION = 0.01
ids_a_eliminar = set()
ids_procesados = list(embeddings_dict.keys())


def distancia_coseno(vec_a, vec_b):
    return 1.0 - np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


distancias_duplicados = [
    distancia_coseno(embeddings_dict[id_a], embeddings_dict[id_b])
    for id_a, id_b in PARES_DUPLICADOS_CONFIRMADOS
]
distancias_distintos = [
    distancia_coseno(embeddings_dict[id_a], embeddings_dict[id_b])
    for id_a, id_b in PARES_DISTINTOS_CONFIRMADOS
]
distancia_duplicado_maxima = max(distancias_duplicados)
distancia_distinto_minima = min(distancias_distintos)

if distancia_distinto_minima - distancia_duplicado_maxima < MARGEN_CALIBRACION:
    raise ValueError(
        "Los pares etiquetados como duplicados y distintos no se separan "
        "con el margen requerido; revise las etiquetas antes de purgar."
    )

UMBRAL_DISTANCIA = (distancia_duplicado_maxima + distancia_distinto_minima) / 2
print(f"\n[ETL] Analizando duplicados con umbral de distancia coseno < {UMBRAL_DISTANCIA:.4f}")
print(
    f"[ETL] Umbral calibrado entre el par duplicado conocido "
    f"({distancia_duplicado_maxima:.4f}) y el par distinto más cercano "
    f"({distancia_distinto_minima:.4f}); margen mínimo: {MARGEN_CALIBRACION:.2f}"
)

representante = {doc_id: doc_id for doc_id in ids_procesados}


def buscar_representante(doc_id):
    if representante[doc_id] != doc_id:
        representante[doc_id] = buscar_representante(representante[doc_id])
    return representante[doc_id]


for i in range(len(ids_procesados)):
    for j in range(i + 1, len(ids_procesados)):
        id_a = ids_procesados[i]
        id_b = ids_procesados[j]
        cosine_dist = distancia_coseno(embeddings_dict[id_a], embeddings_dict[id_b])
        if cosine_dist < UMBRAL_DISTANCIA:
            print(f"  [DUPLICADO DETECTADO] '{id_a}' y '{id_b}' tienen una distancia de {cosine_dist:.4f}")
            raiz_a = buscar_representante(id_a)
            raiz_b = buscar_representante(id_b)
            if raiz_a != raiz_b:
                representante[raiz_b] = raiz_a

for doc_id in ids_procesados:
    if buscar_representante(doc_id) != doc_id:
        ids_a_eliminar.add(doc_id)

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