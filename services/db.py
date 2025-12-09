import streamlit as st
from supabase import create_client, Client
from config import settings
import datetime

# Singleton de conexión (aprovechando el caché de Streamlit)
@st.cache_resource
def get_db_client() -> Client:
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def save_feedback_history(date_ref, t_max, t_min, level):
    """
    Guarda o actualiza el registro de feedback en Supabase.
    date_ref: puede ser string 'YYYY-MM-DD' o objeto date.
    """
    supabase = get_db_client()
    
    data = {
        "date": str(date_ref), # Aseguramos formato string
        "temp_max": t_max,
        "temp_min": t_min,
        "clothing_level": level
    }

    try:
        # Usamos upsert para que si corrige el mismo día dos veces, se actualice
        response = supabase.table("training_history").upsert(data).execute()
        return True
    except Exception as e:
        print(f"Error guardando en Supabase: {e}")
        return False