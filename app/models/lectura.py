
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Lectura(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id_dispositivo: str = Field(min_length=1)
    zona: str = Field(min_length=1)
    tipo: str = Field(min_length=1)

    cantidad_equipos: int = Field(gt=0)
    estado: Literal["encendido", "apagado", "falla"]

    potencia_estimada_w: int | float = Field(ge=0)
    consumo_kwh: int | float = Field(ge=0)

    timestamp_inicio: datetime
    timestamp_fin: datetime

    @field_validator("timestamp_inicio", "timestamp_fin")
    @classmethod
    def validar_zona_horaria(cls, value):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("El timestamp debe incluir zona horaria")
        return value

    @model_validator(mode="after")
    def validar_intervalo(self):
        if self.timestamp_fin <= self.timestamp_inicio:
            raise ValueError(
                "timestamp_fin debe ser posterior a timestamp_inicio"
            )
        return self
