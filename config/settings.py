"""
Configuraciones globales para el proyecto ETL web MAC
"""
import os
from pathlib import Path

# Rutas de directorios
ROOT_DIR = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = ROOT_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
OUTPUT_DIR = DATA_DIR / "output"
PICKLES_DIR = DATA_DIR / "pickles"

# Asegurar que existen los directorios necesarios
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(PICKLES_DIR, exist_ok=True)

# URLs y recursos externos
BASE_URL = "https://mac.acatlan.unam.mx/escolares/temarios/1644/"

# Configuraciones del driver de Selenium
HEADLESS_MODE = True
BROWSER_TIMEOUT = 10  # Segundos

# Modelos y configuración de IA
DEFAULT_EMBEDDING_MODEL = "models/text-embedding-004"
GEN_AI_MODEL = "gemini-1.5-flash"

# Configuración de extracción de datos
MAX_RETRIES = 2  # Reintentos para extracción de datos

# Cargar variables de entorno si es necesario
try:
    from dotenv import load_dotenv
    load_dotenv()  # Cargar variables de entorno desde .env
except ImportError:
    print("dotenv no está instalado. No se cargarán variables desde .env") 