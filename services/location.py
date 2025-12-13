import streamlit as st
from streamlit_js_eval import get_geolocation
import time

# Coordenadas por defecto (Santiago) - Plan B
DEFAULT_LAT = -33.426334
DEFAULT_LON = -70.589805
DEFAULT_TZ = "America/Santiago"

def initialize_user_location():
    """
    Intenta obtener la ubicación real del usuario.
    Retorna un diccionario con 'lat', 'lon', 'timezone'.
    Gestiona el estado de sesión para no preguntar en cada rerun.
    """
    
    # 1. Si ya tenemos la ubicación en memoria, no hacemos nada más.
    if "user_location" in st.session_state:
        return st.session_state["user_location"]

    # 2. UI: Mostrar mensaje mientras buscamos (Placeholder)
    loc_placeholder = st.empty()
    loc_placeholder.info("📍 Detectando tu ubicación para el clima exacto...")

    try:
        # 3. Llamada a JavaScript (Esto pausa la ejecución hasta que el navegador responde)
        # get_geolocation devuelve un diccionario si el usuario acepta
        loc_data = get_geolocation()
        
        # 4. Obtener la Zona Horaria del navegador usando JS puro (hack limpio)
        # Streamlit-js-eval no trae timezone directo, así que inyectamos un script pequeño
        # Nota: Por ahora, asumiremos la timezone basada en coordenadas o usaremos una librería,
        # pero para simplificar, usaremos 'timezonefinder' si quieres precisión total,
        # o dejaremos que el usuario defina su zona si falla. 
        # PERO, para MVP robusto, intentaremos inferir.
        
        if loc_data and 'coords' in loc_data:
            latitude = loc_data['coords']['latitude']
            longitude = loc_data['coords']['longitude']
            
            # Guardamos en sesión
            st.session_state["user_location"] = {
                "lat": latitude,
                "lon": longitude,
                "timezone": "auto" # Open-Meteo detecta timezone por lat/lon automáticamente
            }
            loc_placeholder.success("✅ Ubicación encontrada.")
            time.sleep(1) # Breve pausa para que el usuario vea el check
            loc_placeholder.empty()
            st.rerun() # Recargamos para que toda la app use los nuevos datos
            
        else:
            # Si el usuario deniega o hay error, usamos default silenciosamente
            print("⚠️ No se pudo obtener ubicación o usuario denegó.")
            set_default_location()
            loc_placeholder.empty()

    except Exception as e:
        print(f"Error en geolocalización: {e}")
        set_default_location()
        loc_placeholder.empty()

    return st.session_state["user_location"]

def set_default_location():
    """Fuerza los valores por defecto del .env"""
    st.session_state["user_location"] = {
        "lat": DEFAULT_LAT,
        "lon": DEFAULT_LON,
        "timezone": DEFAULT_TZ
    }

def get_current_coords():
    """Getter limpio para usar en el resto de la app"""
    if "user_location" not in st.session_state:
        set_default_location()
    return st.session_state["user_location"]