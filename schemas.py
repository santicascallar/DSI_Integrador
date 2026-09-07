from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

class ConsultaScoutingSchema(BaseModel):
    intencion: Literal["CONSULTA_PERFIL", "CONSULTA_INFORMES", "ALTA_JUGADOR_SCOUTING"] = Field(
        description="Intención detectada en la consulta del usuario."
    )
    jugador: Optional[str] = Field(default=None, description="Nombre del futbolista")
    criterio: Optional[str] = Field(default=None, description="Criterio buscado")
    posicion: Optional[str] = Field(default=None, description="Posición del jugador")
    fuente: Optional[str] = Field(default=None, description="Origen o región del informe")
    archivo: Optional[str] = Field(default=None, description="Nombre del archivo PDF adjunto")

    @field_validator("archivo")
    @classmethod
    def validar_extension_archivo(cls, v: Optional[str]) -> Optional[str]:
        """Valida que si se adjunta un archivo, este sea obligatoriamente un PDF"""
        if v is not None:
            v_limpio = v.strip()
            if v_limpio and not v_limpio.lower().endswith(".pdf"):
                raise ValueError("El archivo adjunto debe tener una extensión .pdf válida")
            return v_limpio
        return v

    @field_validator("jugador")
    @classmethod
    def normalizar_nombre_jugador(cls, v: Optional[str]) -> Optional[str]:
        """Limpia los espacios y normaliza el formato del nombre del jugador"""
        if v is not None:
            return v.strip().title()
        return v