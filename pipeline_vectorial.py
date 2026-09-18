import os
import json
import numpy as np
import faiss
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró la GEMINI_API_KEY en las variables de entorno del archivo .env.")

client = genai.Client(api_key=api_key)
INDEX_FILE = "vector_index.faiss"

print("Cargando base_conocimiento.json...")
with open("base_conocimiento.json", "r", encoding="utf-8") as f:
    documentos = json.load(f)

textos = [doc["descripcion_semantica"] for doc in documentos]
ids = [doc["id"] for doc in documentos]

if os.path.exists(INDEX_FILE):
    print(f"Cargando índice FAISS existente desde '{INDEX_FILE}'...")
    index = faiss.read_index(INDEX_FILE)
else:
    print("Generando embeddings con la API de Google...")
    
    embeddings = []
    for texto in textos:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=texto
        )
        embeddings.append(response.embeddings[0].values)

    matriz_vectores = np.array(embeddings, dtype=np.float32)
    dimension = matriz_vectores.shape[1]

    print(f"Construyendo índice IndexFlatL2 (Dimensión: {dimension})...")
    index = faiss.IndexFlatL2(dimension)
    index.add(matriz_vectores)

    faiss.write_index(index, INDEX_FILE)
    print(f"Índice persistido correctamente en '{INDEX_FILE}'.")

consultas_prueba = [
    "Necesito un extremo rápido que haga la banda y desequilibre en el uno contra uno",
    "Buscame un volante central con gran capacidad de distribución y salida limpia",
    "Quiero un defensor central expeditivo y fuerte en el juego aéreo defensivo"
]

K = 2

print("\n Ejecución de busquedas semanticas (top-K)")
for idx_c, query in enumerate(consultas_prueba, start=1):
    print(f"\nConsulta {idx_c}: '{query}'")
    
    response_query = client.models.embed_content(
        model="gemini-embedding-001",
        contents=query
    )
    vector_query = np.array([response_query.embeddings[0].values], dtype=np.float32)
    
    distancias, indices = index.search(vector_query, K)
    
    for rank in range(K):
        doc_idx = indices[0][rank]
        distancia = distancias[0][rank]
        doc_match = documentos[doc_idx]
        print(f"  -> Resultado #{rank + 1} [ID: {doc_match['id']}] (Distancia L2: {distancia:.4f})")
        print(f"     Texto: {doc_match['descripcion_semantica'][:90]}...")