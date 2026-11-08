
from math import isclose

# El simulador trabaja con ciclos de 60 segundos.
INTERVALO_ESPERADO_SEGUNDOS = 60

# El consumo_kwh se almacena redondeado a 5 decimales.
TOLERANCIA_CONSUMO = 0.0000051

TOLERANCIA_INTERVALO = 1.0


def validar_reglas_negocio(lectura):
    errores = []

    estado = lectura.estado
    potencia = lectura.potencia_estimada_w
    consumo = lectura.consumo_kwh

    # Calcular duración real entre timestamps.
    duracion = (
        lectura.timestamp_fin - lectura.timestamp_inicio
    ).total_seconds()

    # Regla 1: estados apagado y falla deben tener valores en cero.
    if estado in ("apagado", "falla"):
        if potencia != 0:
            errores.append(
                "La potencia debe ser cero cuando el estado es apagado o falla"
            )

        if consumo != 0:
            errores.append(
                "El consumo debe ser cero cuando el estado es apagado o falla"
            )

    # Regla 2: un equipo encendido debe registrar valores positivos.
    elif estado == "encendido":
        if potencia <= 0:
            errores.append(
                "La potencia debe ser mayor que cero cuando está encendido"
            )

        if consumo <= 0:
            errores.append(
                "El consumo debe ser mayor que cero cuando está encendido"
            )

    # Regla 3: verificar intervalo esperado de 60 segundos.
    if not isclose(
        duracion,
        INTERVALO_ESPERADO_SEGUNDOS,
        abs_tol=TOLERANCIA_INTERVALO
    ):
        errores.append(
            f"El intervalo debe ser de {INTERVALO_ESPERADO_SEGUNDOS} segundos; "
            f"se encontraron {duracion} segundos"
        )

    # Regla 4: comprobar correspondencia entre potencia y consumo.
    if duracion > 0:
        consumo_esperado = (
            potencia * duracion / 3_600_000
        )

        if not isclose(
            consumo,
            consumo_esperado,
            rel_tol=0,
            abs_tol=TOLERANCIA_CONSUMO
        ):
            errores.append(
                f"El consumo registrado ({consumo}) no coincide "
                f"con el calculado ({consumo_esperado:.8f} kWh)"
            )

    return errores
