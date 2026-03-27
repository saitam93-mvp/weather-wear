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
    # 1. Inyectar Metaetiquetas PWA
    inject_pwa_metadata()

    # 2. Intentar obtener ubicación
    initialize_user_location()

    # 3. Sincronizar memoria
    run_startup_sync()

    # 4. Renderizar Dashboard Principal
    render_dashboard()

if __name__ == "__main__":
    main()