import chromadb


ID_PRUEBA = "__B3_UPSERT_DEMO__"
ID_REFERENCIA = "DOC-001"

chroma_client = chromadb.PersistentClient(path="./chroma_db")
coleccion = chroma_client.get_collection(name="futbol_inform_scouting")

if coleccion.get(ids=[ID_PRUEBA])["ids"]:
    raise RuntimeError(f"El ID temporal {ID_PRUEBA} ya existe; no se modificó.")

referencia = coleccion.get(ids=[ID_REFERENCIA], include=["embeddings"])
if not referencia["ids"]:
    raise RuntimeError(f"No se encontró el documento de referencia {ID_REFERENCIA}.")

insertado = False
try:
    coleccion.upsert(
        ids=[ID_PRUEBA],
        embeddings=[referencia["embeddings"][0]],
        documents=["Informe temporal para demostrar un upsert de negocio."],
        metadatas=[{"posicion": "Extremo", "vigente": False, "tags": "demo"}],
    )
    insertado = True

    verificacion = coleccion.get(ids=[ID_PRUEBA], include=["documents", "metadatas"])
    print(f"Upsert verificado para {verificacion['ids'][0]}.")
    print(f"Documento: {verificacion['documents'][0]}")
    print(f"Metadatos: {verificacion['metadatas'][0]}")
finally:
    if insertado:
        coleccion.delete(ids=[ID_PRUEBA])
        print(f"Registro temporal {ID_PRUEBA} eliminado; colección restaurada.")
