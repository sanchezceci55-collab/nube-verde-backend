
from collections import defaultdict
from datetime import timezone


def obtener_intervalo(timestamp):
    """
    Normaliza timestamp_inicio al inicio del minuto en UTC.
    Ejemplo: 18:33:25.014876 -> 18:33:00Z
    """
    timestamp_utc = timestamp.astimezone(timezone.utc)

    return timestamp_utc.replace(
        second=0,
        microsecond=0
    )


def crear_acumulador():
    return {
        "equipos": {},
        "potencia_por_intervalo": defaultdict(float),
        "consumo_total_kwh": 0.0,
        "cantidad_lecturas": 0
    }


def agregar_lectura(acumulador, lectura, intervalo):
    """
    Acumula una lectura sin duplicar las unidades físicas.
    """
    dispositivo = lectura.id_dispositivo

    # Guardar una sola cantidad por dispositivo.
    # Se utiliza el máximo observado para evitar sumar
    # repetidamente el mismo grupo en diferentes ciclos.
    acumulador["equipos"][dispositivo] = max(
        acumulador["equipos"].get(dispositivo, 0),
        lectura.cantidad_equipos
    )

    acumulador["potencia_por_intervalo"][intervalo] += (
        lectura.potencia_estimada_w
    )

    acumulador["consumo_total_kwh"] += lectura.consumo_kwh
    acumulador["cantidad_lecturas"] += 1


def finalizar_resumen(acumulador):
    """
    Calcula los indicadores finales de una agrupación.
    """
    potencias = list(
        acumulador["potencia_por_intervalo"].values()
    )

    potencia_maxima = max(potencias, default=0.0)

    potencia_promedio = (
        sum(potencias) / len(potencias)
        if potencias else 0.0
    )

    return {
        "total_equipos": sum(acumulador["equipos"].values()),
        "dispositivos_unicos": len(acumulador["equipos"]),
        "cantidad_lecturas": acumulador["cantidad_lecturas"],
        "consumo_total_kwh": round(
            acumulador["consumo_total_kwh"], 6
        ),
        "potencia_maxima_intervalo_w": round(
            potencia_maxima, 2
        ),
        "potencia_promedio_intervalo_w": round(
            potencia_promedio, 2
        ),
        "cantidad_intervalos": len(potencias)
    }


def procesar_lecturas(lecturas):
    """
    Procesa lecturas previamente validadas.

    Genera:
    - Resumen por zona.
    - Resumen por tipo de equipo.
    - Resumen por intervalo temporal.
    """

    zonas = defaultdict(crear_acumulador)
    tipos = defaultdict(crear_acumulador)
    intervalos = defaultdict(
        lambda: {
            "potencia_total_w": 0.0,
            "consumo_total_kwh": 0.0,
            "cantidad_lecturas": 0,
            "dispositivos": set(),
            "zonas": defaultdict(
                lambda: {
                    "potencia_total_w": 0.0,
                    "consumo_total_kwh": 0.0,
                    "cantidad_lecturas": 0
                }
            )
        }
    )

    for lectura in lecturas:

        intervalo = obtener_intervalo(
            lectura.timestamp_inicio
        )

        # Resumen por zona
        agregar_lectura(
            zonas[lectura.zona],
            lectura,
            intervalo
        )

        # Resumen por tipo de equipo
        agregar_lectura(
            tipos[lectura.tipo],
            lectura,
            intervalo
        )

        # Resumen por intervalo
        datos_intervalo = intervalos[intervalo]

        datos_intervalo["potencia_total_w"] += (
            lectura.potencia_estimada_w
        )

        datos_intervalo["consumo_total_kwh"] += (
            lectura.consumo_kwh
        )

        datos_intervalo["cantidad_lecturas"] += 1
        datos_intervalo["dispositivos"].add(
            lectura.id_dispositivo
        )

        # Desglose por zona dentro del intervalo
        datos_zona = datos_intervalo["zonas"][lectura.zona]

        datos_zona["potencia_total_w"] += (
            lectura.potencia_estimada_w
        )

        datos_zona["consumo_total_kwh"] += (
            lectura.consumo_kwh
        )

        datos_zona["cantidad_lecturas"] += 1

    # Construir resultados por zona
    resumen_zonas = {
        nombre: finalizar_resumen(datos)
        for nombre, datos in zonas.items()
    }

    # Construir resultados por tipo
    resumen_tipos = {
        nombre: finalizar_resumen(datos)
        for nombre, datos in tipos.items()
    }

    # Construir resultados por intervalo
    resumen_intervalos = {}

    for intervalo, datos in sorted(intervalos.items()):

        resumen_intervalos[intervalo.isoformat()] = {
            "potencia_total_w": round(
                datos["potencia_total_w"], 2
            ),
            "consumo_total_kwh": round(
                datos["consumo_total_kwh"], 6
            ),
            "cantidad_lecturas": datos["cantidad_lecturas"],
            "dispositivos_unicos": len(
                datos["dispositivos"]
            ),
            "zonas": {
                nombre: {
                    "potencia_total_w": round(
                        valores["potencia_total_w"], 2
                    ),
                    "consumo_total_kwh": round(
                        valores["consumo_total_kwh"], 6
                    ),
                    "cantidad_lecturas": valores[
                        "cantidad_lecturas"
                    ]
                }
                for nombre, valores in datos["zonas"].items()
            }
        }

    return {
        "total_lecturas_procesadas": len(lecturas),
        "total_intervalos": len(resumen_intervalos),
        "resumen_zonas": resumen_zonas,
        "resumen_tipos": resumen_tipos,
        "resumen_intervalos": resumen_intervalos
    }
