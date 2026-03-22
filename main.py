import streamlit as st

# --- 1. CONFIGURACIÓN PRIMERO (CRÍTICO: Debe ser la primera instrucción) ---
st.set_page_config(
    page_title="IsiWear",
    page_icon="🧣",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# --- 2. IMPORTACIONES DEL NEGOCIO ---
from logic.training import sync_model_with_db
from ui.dashboard import render_dashboard
from services.location import initialize_user_location
from ui.pwa import inject_pwa_metadata

def check_password():
    """Verifica si Isi tiene el enlace mágico o ingresa la clave correcta."""
    
    # 1. Revisar si la clave mágica está escondida en la URL
    if st.query_params.get("pwd") == st.secrets["APP_PASSWORD"]:
        return True

    # 2. Revisar la memoria a corto plazo
    if st.session_state.get("password_correct", False):
        return True

    # 3. Si no hay link especial ni sesión, pedimos la clave manual
    st.title("IsiWear 🧣")
    st.write("Por favor, ingresa tu contraseña para entrar:")
    
    clave = st.text_input("Contraseña", type="password")
    
    if st.button("Entrar"):
        if clave == st.secrets["APP_PASSWORD"]:
            # Guardamos en la sesión actual
            st.session_state["password_correct"] = True
            
            # ¡LA MAGIA! Inyectamos la clave en la URL automáticamente
            st.query_params["pwd"] = clave
            
            st.rerun()
        else:
            st.error("Contraseña incorrecta. Intenta de nuevo.")
            
    return False

def run_startup_sync():
    """Ejecuta la sincronización con Supabase SOLO una vez por sesión."""
    if "data_synced" not in st.session_state:
        with st.spinner("🧠 Sincronizando memoria con la nube..."):
            try:
                success = sync_model_with_db()
                if success:
                    st.toast("Modelo actualizado con tu historial.", icon="✅")
                else:
                    st.toast("Conectado a la nube (Historial vacío).", icon="☁️")
            except Exception as e:
                st.error(f"⚠️ Advertencia: No se pudo sincronizar el historial. ({e})")
        
        st.session_state["data_synced"] = True

def main():
    # 1. Chequeo de seguridad primero (Bloquea el resto si no hay clave)
    if not check_password():
        return  

    # 2. Inyectar Metaetiquetas PWA
    inject_pwa_metadata()

    # 3. Intentar obtener ubicación
    initialize_user_location()

    # 4. Sincronizar memoria
    run_startup_sync()

    # 5. Renderizar Dashboard Principal
    render_dashboard()

if __name__ == "__main__":
    main()