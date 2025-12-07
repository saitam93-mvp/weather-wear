import os
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# --- SUPABASE CONFIG ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# --- LOCATION CONFIG ---
# Default: Santiago de Chile
LATITUDE = float(os.getenv("LATITUDE", "-33.426334"))
LONGITUDE = float(os.getenv("LONGITUDE", "-70.589805"))
TIMEZONE = os.getenv("TIMEZONE", "auto")

# --- APP CONSTANTS ---
# Definición de Niveles de Ropa (0 a 4)
CLOTHING_LEVELS = {
    0: "Nivel 0: Muy Ligero (Shorts/Polera)",
    1: "Nivel 1: Ligero (Pantalón/Manga larga fina)",
    2: "Nivel 2: Intermedio (Polerón/Chaqueta ligera)",
    3: "Nivel 3: Abrigo (Chaqueta gruesa/Impermeable)",
    4: "Nivel 4: Extremo (Parka térmica/Bufanda/Guantes)"
}

# Reglas de Negocio (Hard Rules)
RAIN_PROB_THRESHOLD = 40.0  # % probabilidad
RAIN_AMOUNT_THRESHOLD = 1.0 # mm lluvia