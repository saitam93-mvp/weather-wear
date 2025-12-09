import streamlit as st
from supabase import create_client, Client
from config import settings
import datetime

# Singleton de conexión
@st.cache_resource
def get_db_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def get_training_history():
    """
    Descarga TODO el historial de entrenamiento desde Supabase.
    """
    supabase = get_db_client()
    try:
        response = supabase.table("training_history").select("*").execute()
        return response.data
    except Exception as e:
        print(f"Error descargando historial: {e}")
        return []

def save_feedback_history(
    date_ref, t_max, t_min, level, 
    precip=0.0, wind_max=0.0, w_code=0, 
    t_mean=0.0, hum_mean=0.0, wind_mean=0.0, clouds=0.0, rad=0.0, precip_prob=0.0
):
    """
    Guarda el registro extendido en Supabase.
    INCLUYE: Sanitización de tipos (NumPy float32 -> Python float)
    """
    supabase = get_db_client()
    
    # --- SANITIZACIÓN DE DATOS ---
    # Convertimos explícitamente a tipos nativos de Python para evitar error JSON
    try:
        data = {
            "date": str(date_ref),
            "clothing_level": int(level),
            
            # Variables Térmicas (Convertimos a float estándar)
            "temp_max": float(t_max),
            "temp_min": float(t_min),
            "temp_mean": float(t_mean),
            
            # Variables Atmosféricas
            "precipitation_sum": float(precip),
            "precip_prob_max": float(precip_prob),
            "humidity_mean": float(hum_mean),
            "cloud_cover_mean": float(clouds),
            
            # Variables Físicas
            "windspeed_max": float(wind_max),
            "windspeed_mean": float(wind_mean),
            "solar_rad_sum": float(rad),
            "weathercode": int(w_code) # Este debe ser entero
        }

        # Usamos upsert
        response = supabase.table("training_history").upsert(data).execute()
        return True
        
    except Exception as e:
        print(f"Error guardando extended history: {e}")
        return False