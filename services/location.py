import streamlit as st
from streamlit_js_eval import get_geolocation

# --- CONFIGURACIÓN DEFAULT (Plan B) ---
DEFAULT_LAT = -33.426334 # Santiago
DEFAULT_LON = -70.589805
DEFAULT_TZ = "America/Santiago"

def initialize_user_location():
    """
    Gestiona la obtención de coordenadas de forma NO bloqueante.
    """
    # 1. Llamamos al componente SIEMPRE (para que escuche cambios o cargas)
    # key="get_loc" evita que se renderice múltiples veces innecesariamente
    loc_data = get_geolocation(component_key="get_loc")

    # 2. Lógica de Actualización
    if loc_data and 'coords' in loc_data:
        # ¡Llegaron datos reales!
        coords = loc_data['coords']
        
        # Solo actualizamos si cambiaron para evitar reruns infinitos
        current = st.session_state.get("user_location", {})
        if current.get("lat") != coords['latitude']:
            st.session_state["user_location"] = {
                "lat": coords['latitude'],
                "lon": coords['longitude'],
                "source": "gps" # Marca de agua para saber que es real
            }
            st.rerun() # Recargamos para aplicar la nueva ubicación inmediatamente

    # 3. Inicialización por defecto (Si aún no hay nada en memoria)
    if "user_location" not in st.session_state:
        st.session_state["user_location"] = {
            "lat": DEFAULT_LAT,
            "lon": DEFAULT_LON,
            "source": "default"
        }

    return st.session_state["user_location"]

def get_current_coords():
    #Si hay una ubicación manual guardada en sesión, la usamos
    if "manual_loc" in st.session_state:
        return st.session_state["manual_loc"]
    """Retorna las coordenadas actuales (sean GPS o Default)"""
    # Si por alguna razón se llama antes de init, devuelve default
    return st.session_state.get("user_location", {
        "lat": DEFAULT_LAT,
        "lon": DEFAULT_LON,
        "source": "default"
    })