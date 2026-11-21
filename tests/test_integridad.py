from datetime import datetime, timedelta, timezone

import pytest

from app.models.lectura import Lectura
from app.services.integridad import (
    DISPOSITIVOS_ESPERADOS,
    analizar_integridad,
)


def crear_lectura(
    id_dispositivo: str,
    id_ciclo: str = "ciclo_prueba_001",
    estado: str = "encendido",
    potencia: float = 100,
    consumo: float = 0.05,
) -> Lectura:
    """Construye una lectura válida para las pruebas de integridad."""
    inicio = datetime(2026, 11, 21, 10, 0, tzinfo=timezone.utc)

    return Lectura.model_validate(
        {
            "id_dispositivo": id_dispositivo,
            "zona": "Laboratorio_A",
            "tipo": "Equipo de prueba",
            "id_ciclo": id_ciclo,
            "cantidad_equipos": 1,
            "estado": estado,
            "potencia_estimada_w": potencia,
            "consumo_kwh": consumo,
            "timestamp_inicio": inicio.isoformat(),
            "timestamp_fin": (inicio + timedelta(minutes=1)).isoformat(),
        }
    )


def crear_ciclo_completo(id_ciclo: str = "ciclo_prueba_001") -> list[Lectura]:
    return [
        crear_lectura(dispositivo, id_ciclo=id_ciclo)
        for dispositivo in sorted(DISPOSITIVOS_ESPERADOS)
    ]


def test_ciclo_con_16_dispositivos_es_completo():
    resultado = analizar_integridad(crear_ciclo_completo())

    assert resultado["total_registros"] == 16
    assert resultado["total_ciclos"] == 1
    assert resultado["ciclos_completos"] == 1
    assert resultado["ciclos_incompletos"] == 0
    assert resultado["total_incidencias"] == 0
    assert resultado["ciclos"][0]["estado"] == "COMPLETO"


def test_ciclo_con_15_dispositivos_es_incompleto():
    lecturas = crear_ciclo_completo()[:-1]

    resultado = analizar_integridad(lecturas)

    assert resultado["ciclos_completos"] == 0
    assert resultado["ciclos_incompletos"] == 1
    assert resultado["total_incidencias"] == 1
    assert len(resultado["ciclos"][0]["faltantes"]) == 1
    assert resultado["ciclos"][0]["estado"] == "INCOMPLETO"


def test_dispositivo_apagado_con_valores_cero_cuenta_como_presente():
    lecturas = crear_ciclo_completo()
    dispositivo = "lab_a_pc_grupo"

    lecturas = [
        crear_lectura(
            lectura.id_dispositivo,
            estado="apagado" if lectura.id_dispositivo == dispositivo else lectura.estado,
            potencia=0 if lectura.id_dispositivo == dispositivo else lectura.potencia_estimada_w,
            consumo=0 if lectura.id_dispositivo == dispositivo else lectura.consumo_kwh,
        )
        for lectura in lecturas
    ]

    resultado = analizar_integridad(lecturas)

    assert resultado["ciclos_completos"] == 1
    assert resultado["ciclos"][0]["estado"] == "COMPLETO"
    assert resultado["ciclos"][0]["faltantes"] == []


def test_dispositivo_duplicado_en_un_ciclo_es_incidencia():
    lecturas = crear_ciclo_completo()
    lecturas.append(crear_lectura("lab_a_pc_grupo"))

    resultado = analizar_integridad(lecturas)

    assert resultado["ciclos_incompletos"] == 1
    assert resultado["ciclos"][0]["estado"] == "INCOMPLETO"
    assert resultado["ciclos"][0]["duplicados"] == [
        {"id_dispositivo": "lab_a_pc_grupo", "cantidad": 2}
    ]
    assert resultado["total_incidencias"] == 1


def test_dispositivo_no_esperado_es_incidencia():
    lecturas = crear_ciclo_completo()
    lecturas.append(crear_lectura("dispositivo_desconocido"))

    resultado = analizar_integridad(lecturas)

    assert resultado["ciclos_incompletos"] == 1
    assert resultado["ciclos"][0]["estado"] == "INCOMPLETO"
    assert resultado["ciclos"][0]["dispositivos_no_esperados"] == [
        "dispositivo_desconocido"
    ]
    assert resultado["total_incidencias"] == 1


def test_dos_ciclos_se_analizan_independientemente():
    ciclo_completo = crear_ciclo_completo("ciclo_completo")
    ciclo_incompleto = [
        crear_lectura(dispositivo, id_ciclo="ciclo_incompleto")
        for dispositivo in sorted(DISPOSITIVOS_ESPERADOS)[:-1]
    ]

    resultado = analizar_integridad(ciclo_completo + ciclo_incompleto)

    assert resultado["total_ciclos"] == 2
    assert resultado["ciclos_completos"] == 1
    assert resultado["ciclos_incompletos"] == 1
    assert resultado["total_registros"] == 31
    assert resultado["total_incidencias"] == 1


def test_sin_lecturas_devuelve_cero_ciclos_e_incidencias():
    resultado = analizar_integridad([])

    assert resultado["total_registros"] == 0
    assert resultado["total_ciclos"] == 0
    assert resultado["ciclos_completos"] == 0
    assert resultado["ciclos_incompletos"] == 0
    assert resultado["total_incidencias"] == 0
    assert resultado["total_ciclos_con_incidencias"] == 0
    assert resultado["ciclos"] == []
    assert resultado["incidencias"] == []
