import streamlit as st

# --- 1. CONFIGURACIÓN PRIMERO (CRÍTICO: Debe ser la primera instrucción Streamlit) ---
st.set_page_config(
    page_title="IsiWear",
    page_icon="🧣",
    layout="centered",
    initial_sidebar_state="collapsed",
    # Ocultamos el menú de hamburguesa estándar para que parezca más App
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# --- 2. IMPORTACIONES DEL NEGOCIO ---
# Importamos después de la config para evitar conflictos de inicialización
from logic.training import sync_model_with_db
from ui.dashboard import render_dashboard
from services.location import initialize_user_location
from ui.pwa import inject_pwa_metadata # <--- NUEVO: Módulo PWA

def run_startup_sync():
    """
    Ejecuta la sincronización con Supabase SOLO una vez por sesión.
    Esto recupera la 'memoria' del asistente si la app se reinició en el servidor.
    """
    if "data_synced" not in st.session_state:
        # Mostramos un spinner visual mientras descarga los datos
        with st.spinner("🧠 Sincronizando memoria con la nube..."):
            try:
                # Llamamos a la lógica de entrenamiento/descarga
                success = sync_model_with_db()
                
                if success:
                    st.toast("Modelo actualizado con tu historial.", icon="✅")
                else:
                    # Conectó bien, pero no había datos previos (usuario nuevo)
                    st.toast("Conectado a la nube (Historial vacío).", icon="☁️")
                    
            except Exception as e:
                # Si falla la red, no rompemos la app, solo avisamos
                st.error(f"⚠️ Advertencia: No se pudo sincronizar el historial. ({e})")
        
        # Marcamos la flag en sesión para no volver a ejecutar esto en cada click
        st.session_state["data_synced"] = True

def main():
    # 1. Inyectar Metaetiquetas PWA
    # Esto debe ir antes de cualquier elemento visual grande para configurar el navegador
    inject_pwa_metadata()

    # 2. Intentar obtener ubicación (No bloqueante, escucha activa)
    initialize_user_location()

    # 3. Sincronizar memoria (Solo la primera vez)
    run_startup_sync()

    # 4. Renderizar Dashboard Principal
    render_dashboard()

if __name__ == "__main__":
    main()