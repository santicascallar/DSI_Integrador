import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core.exceptions import GoogleAPICallError, RetryError
from pydantic import ValidationError
from schemas import ConsultaScoutingSchema

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("No se encontró la GEMINI_API_KEY en las variables de entorno")

genai.configure(api_key=api_key)

SYSTEM_PROMPT = """
Sos el componente de interpretación de lenguaje natural del sistema Futbol_Inform, una plataforma de análisis y scouting de futbolistas.
Tu única función es analizar la consulta del usuario y devolver un objeto JSON estructurado según el esquema provisto.
Las únicas intenciones permitidas son: CONSULTA_PERFIL, CONSULTA_INFORMES, ALTA_JUGADOR_SCOUTING.
No inventes información y utilizá únicamente los datos de la consulta.
"""

user_input = "¿Tiene el perfil del jugador Neymar Jr.?"

try:
    print(f"Enviando consulta a Gemini: '{user_input}'...\n")
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=SYSTEM_PROMPT,
        generation_config={
            "response_mime_type": "application/json",
            "response_schema": ConsultaScoutingSchema,
        }
    )

    response = model.generate_content(user_input)

    resultado_validado = ConsultaScoutingSchema.model_validate_json(response.text)

    print("RESULTADO EXTRAÍDO:")
    print(f"Intención: {resultado_validado.intencion}")
    print(f"Jugador: {resultado_validado.jugador}")
    print(f"Criterio: {resultado_validado.criterio}")
    print(f"Posición: {resultado_validado.posicion}")
    print(f"Fuente: {resultado_validado.fuente}")
    print(f"Archivo: {resultado_validado.archivo}")

except ValidationError as e:
    print(f"El modelo devolvió datos que no cumplen con el esquema: {e}")
except (GoogleAPICallError, RetryError) as e:
    print(f"Ocurrió un problema al comunicarse con los servidores de Google: {e}")
except Exception as e:
    print(f"[ERROR INESPERADO]: {e}")