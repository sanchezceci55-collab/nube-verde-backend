
from app.models.lectura import Lectura
from pydantic import ValidationError
from app.services.validacion import validar_reglas_negocio
from app.services.procesamiento import procesar_lecturas
from collections import Counter
from fastapi import FastAPI, HTTPException
from firebase_admin import exceptions

from app.core.firebase import obtener_lecturas

app = FastAPI(
    title="Nube Verde API",
    description="Backend para monitoreo de consumo energético",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "proyecto": "Nube Verde",
        "servicio": "Backend API",
        "estado": "operativo"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/lecturas")
def consultar_lecturas():
    try:
        lecturas = obtener_lecturas()

        if not lecturas:
            return {
                "total": 0,
                "lecturas": {}
            }

        return {
            "total": len(lecturas),
            "lecturas": lecturas
        }

    except exceptions.FirebaseError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar Firebase"
        ) from error



@app.get("/lecturas/validar")
def validar_lecturas():
    try:
        registros = obtener_lecturas()

        if not registros:
            return {
                "total": 0,
                "validos": 0,
                "invalidos": 0,
                "resumen_errores": {},
                "resultados": {
                    "validos": [],
                    "invalidos": []
                }
            }

        validos = []
        invalidos = []
        resumen_errores = Counter()

        for clave, datos in registros.items():
            try:
                lectura = Lectura.model_validate(datos)

                validos.append({
                    "id_firebase": clave,
                    "datos": lectura.model_dump(mode="json")
                })

            except ValidationError as error:

                detalles = error.errors(include_url=False)

                invalidos.append({
                    "id_firebase": clave,
                    "errores": detalles
                })

                # Contabilizar los errores encontrados
                for detalle in detalles:
                    campo = ".".join(
                        str(item) for item in detalle["loc"]
                    )

                    resumen_errores[
                        f"{campo}: {detalle['type']}"
                    ] += 1

        return {
            "total": len(registros),
            "validos": len(validos),
            "invalidos": len(invalidos),
            "resumen_errores": dict(resumen_errores),
            "resultados": {
                "validos": validos[:5],
                "invalidos": invalidos[:5]
            }
        }

    except exceptions.FirebaseError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar Firebase"
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error durante la validación de las lecturas"
        ) from error


@app.get("/lecturas/validar-negocio")
def validar_lecturas_negocio():
    try:
        registros = obtener_lecturas()

        if not registros:
            return {
                "total": 0,
                "estructuralmente_validos": 0,
                "estructuralmente_invalidos": 0,
                "negocio_validos": 0,
                "negocio_invalidos": 0,
                "resumen_errores": {},
                "resultados": {
                    "validos": [],
                    "invalidos": []
                }
            }

        estructuralmente_validos = 0
        estructuralmente_invalidos = 0

        validos = []
        invalidos = []
        resumen_errores = Counter()

        for clave, datos in registros.items():
            try:
                lectura = Lectura.model_validate(datos)
                estructuralmente_validos += 1

                errores = validar_reglas_negocio(lectura)

                if errores:
                    invalidos.append({
                        "id_firebase": clave,
                        "errores": errores
                    })

                    for detalle in errores:
                        resumen_errores[detalle] += 1

                else:
                    validos.append({
                        "id_firebase": clave,
                        "datos": lectura.model_dump(mode="json")
                    })

            except ValidationError:
                estructuralmente_invalidos += 1

        return {
            "total": len(registros),
            "estructuralmente_validos": estructuralmente_validos,
            "estructuralmente_invalidos": estructuralmente_invalidos,
            "negocio_validos": len(validos),
            "negocio_invalidos": len(invalidos),
            "resumen_errores": dict(resumen_errores),
            "resultados": {
                "validos": validos[:5],
                "invalidos": invalidos[:5]
            }
        }

    except exceptions.FirebaseError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar Firebase"
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error durante la validación de reglas de negocio"
        ) from error

@app.get("/lecturas/procesar")
def procesar_datos():
    try:
        registros = obtener_lecturas()

        if not registros:
            return procesar_lecturas([])

        lecturas_validas = []

        for clave, datos in registros.items():
            try:
                lectura = Lectura.model_validate(datos)

                errores = validar_reglas_negocio(lectura)

                if not errores:
                    lecturas_validas.append(lectura)

            except ValidationError:
                continue

        resultado = procesar_lecturas(lecturas_validas)

        return resultado

    except exceptions.FirebaseError as error:
        raise HTTPException(
            status_code=503,
            detail="No fue posible consultar Firebase"
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail="Error durante el procesamiento energético"
        ) from error

