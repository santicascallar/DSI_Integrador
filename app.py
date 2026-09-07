import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError
from pydantic import ValidationError
from schemas import ConsultaScoutingSchema

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró la GEMINI_API_KEY en las variables de entorno.")

client = genai.Client(api_key=api_key)

SYSTEM_PROMPT = """
Sos el componente de interpretación de lenguaje natural del sistema Futbol_Inform, una plataforma de análisis y scouting de futbolistas.
Tu única función es analizar la consulta del usuario y devolver un objeto JSON estructurado según el esquema provisto.
Las únicas intenciones permitidas son: CONSULTA_PERFIL, CONSULTA_INFORMES, ALTA_JUGADOR_SCOUTING.
No inventes información y utilizá únicamente los datos de la consulta.
"""

#Input de prueba inicial
user_input = "Pasame los datos de Julián Álvarez"

try:
    print(f"Enviando consulta a Gemini: '{user_input}'...\n")
    
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=user_input,
        config={
            "system_instruction": SYSTEM_PROMPT,
            "response_mime_type": "application/json",
            "response_schema": ConsultaScoutingSchema,
        },
    )

    resultado_validado = ConsultaScoutingSchema.model_validate_json(response.text)

    print("-- RESULTADO EXTRAÍDO --")
    print(f"Intención: {resultado_validado.intencion}")
    print(f"Jugador: {resultado_validado.jugador}")
    print(f"Criterio: {resultado_validado.criterio}")
    print(f"Posición: {resultado_validado.posicion}")
    print(f"Fuente: {resultado_validado.fuente}")
    print(f"Archivo: {resultado_validado.archivo}")

except ValidationError as e:
    print(f"El modelo devolvió datos que no cumplen con el esquema: {e}")
except APIError as e:
    print(f"Ocurrió un problema al comunicarse con los servidores de Google: {e}")
except Exception as e:
    print(f"{e}")