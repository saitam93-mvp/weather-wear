import streamlit as st
from supabase import create_client, Client
from config import settings

@st.cache_resource
def get_supabase_client() -> Client:
    """
    Singleton para la conexión a Supabase.
    Usa caché de Streamlit para no reconectar en cada rerun.
    """
    try:
        if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
            # Retornamos None si no hay credenciales configuradas (modo dev local sin DB)
            return None
            
        return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
    except Exception as e:
        st.error(f"Error conectando a Supabase: {e}")
        return None