import streamlit as st

# --- 1. CONFIGURACIÓN PRIMERO (ANTES DE CUALQUIER OTRA IMPORTACIÓN) ---
st.set_page_config(
    page_title="WeatherWear",
    page_icon="🧣",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. AHORA SÍ IMPORTAMOS EL RESTO ---
from ui.dashboard import render_dashboard

def main():
    # Enrutamiento simple.
    render_dashboard()

if __name__ == "__main__":
    main()