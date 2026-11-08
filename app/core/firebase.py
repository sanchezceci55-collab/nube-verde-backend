
import os
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Cargar variables de entorno desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("FIREBASE_DATABASE_URL")
CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS")

if not DATABASE_URL:
    raise ValueError("No se configuró FIREBASE_DATABASE_URL")

if not CREDENTIALS_PATH:
    raise ValueError("No se configuró FIREBASE_CREDENTIALS")

# Resolver la ruta de las credenciales
credentials_file = (BASE_DIR / CREDENTIALS_PATH).resolve()

if not credentials_file.exists():
    raise FileNotFoundError(
        f"No se encontró el archivo de credenciales: {credentials_file}"
    )

# Inicializar Firebase una sola vez
if not firebase_admin._apps:
    firebase_credential = credentials.Certificate(str(credentials_file))

    firebase_admin.initialize_app(
        firebase_credential,
        {
            "databaseURL": DATABASE_URL
        }
    )

# Referencia al nodo principal de lecturas
lecturas_ref = db.reference("lecturas")


def obtener_lecturas():
    """
    Recupera los registros almacenados en Firebase Realtime Database.
    """
    return lecturas_ref.get()
