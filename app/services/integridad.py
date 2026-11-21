from collections import Counter, defaultdict
from typing import Any, Iterable

from app.models.lectura import Lectura


# Inventario provisional obtenido de los registros de Firebase.
# Debe contrastarse con el inventario oficial del simulador antes de
# considerarlo definitivo.
DISPOSITIVOS_ESPERADOS = {
    "aula_ilum_grupo",
    "aula_lap_docente",
    "aula_proy_01",
    "aula_vent_grupo",
    "lab_a_clima_01",
    "lab_a_ilum_grupo",
    "lab_a_pc_grupo",
    "lab_a_proy_01",
    "lab_b_clima_01",
    "lab_b_ilum_grupo",
    "lab_b_pc_grupo",
    "lab_b_proy_01",
    "oficina_clima_01",
    "oficina_ilum_grupo",
    "oficina_imp_01",
    "oficina_pc_grupo",
}


def analizar_integridad(
    lecturas: Iterable[Lectura],
) -> dict[str, Any]:
    """
    Analiza la integridad de las lecturas agrupándolas por id_ciclo.

    Un dispositivo se considera presente si existe su registro en el ciclo,
    independientemente de que esté encendido o apagado. Una lectura apagada
    con potencia y consumo en cero cuenta como registro presente.

    Esta función solo analiza ciclos presentes en `lecturas`. Para detectar
    un ciclo que no generó ningún registro se necesitaría recibir, además,
    un inventario de ciclos esperados.
    """

    ciclos: dict[str, list[str]] = defaultdict(list)

    # Conservar cada aparición permite detectar duplicados por ciclo.
    for lectura in lecturas:
        ciclos[lectura.id_ciclo].append(lectura.id_dispositivo)

    resultados = []
    incidencias = []

    ciclos_completos = 0
    ciclos_incompletos = 0
    total_incidencias = 0
    total_registros = 0
    ciclos_con_incidencias = 0

    for id_ciclo, dispositivos in sorted(ciclos.items()):
        conteo = Counter(dispositivos)
        recibidos = set(dispositivos)

        faltantes = sorted(DISPOSITIVOS_ESPERADOS - recibidos)

        duplicados = [
            {
                "id_dispositivo": dispositivo,
                "cantidad": cantidad,
            }
            for dispositivo, cantidad in sorted(conteo.items())
            if cantidad > 1
        ]

        no_esperados = sorted(recibidos - DISPOSITIVOS_ESPERADOS)

        completo = not (faltantes or duplicados or no_esperados)
        estado = "COMPLETO" if completo else "INCOMPLETO"

        if completo:
            ciclos_completos += 1
        else:
            ciclos_incompletos += 1

        # Cada elemento faltante, duplicado o no esperado cuenta como
        # una incidencia individual.
        cantidad_incidencias = (
            len(faltantes) + len(duplicados) + len(no_esperados)
        )
        total_incidencias += cantidad_incidencias

        incidencia = {
            "id_ciclo": id_ciclo,
            "faltantes": faltantes,
            "duplicados": duplicados,
            "dispositivos_no_esperados": no_esperados,
        }

        if cantidad_incidencias > 0:
            incidencias.append(incidencia)
            ciclos_con_incidencias += 1

        total_registros += len(dispositivos)

        resultados.append(
            {
                "id_ciclo": id_ciclo,
                "estado": estado,
                "total_registros": len(dispositivos),
                "dispositivos_unicos": len(recibidos),
                "dispositivos_esperados": len(DISPOSITIVOS_ESPERADOS),
                "faltantes": faltantes,
                "duplicados": duplicados,
                "dispositivos_no_esperados": no_esperados,
            }
        )

    return {
        "total_registros": total_registros,
        "total_dispositivos_esperados": len(DISPOSITIVOS_ESPERADOS),
        "total_ciclos": len(resultados),
        "ciclos_completos": ciclos_completos,
        "ciclos_incompletos": ciclos_incompletos,
        "total_incidencias": total_incidencias,
        "total_ciclos_con_incidencias": ciclos_con_incidencias,
        "ciclos": resultados,
        "incidencias": incidencias,
    }
