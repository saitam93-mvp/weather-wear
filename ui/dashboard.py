import streamlit as st
from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation
from ui.feedback import render_feedback_section
from services.location import get_current_coords # <--- NUEVO IMPORT

def render_dashboard():
    st.title("IsiWear 🧣")
    
    # --- 1. INDICADOR DE UBICACIÓN (NUEVO) ---
    # Recuperamos el estado actual de la localización para mostrarlo al usuario
    loc = get_current_coords()
    
    # Lógica visual: Icono distinto si es GPS real o Default
    if loc.get("source") == "gps":
        source_icon = "🛰️" 
        loc_label = "Ubicación Actual"
    else:
        source_icon = "🏢"
        loc_label = "Santiago (Default)"
        
    # Mostramos las coordenadas con 4 decimales
    st.caption(f"{source_icon} **{loc_label}**: {loc['lat']:.4f}, {loc['lon']:.4f}")
    # -----------------------------------------

    # 2. Obtener Datos (Services)
    with st.spinner("Consultando satélites..."):
        weather_df = get_weather_forecast()
    
    if weather_df.empty:
        st.error("No pudimos conectar con el servicio de clima. Revisa tu conexión.")
        return

    # 3. Obtener Recomendación (Logic)
    rec = get_recommendation(weather_df)
    
    if not rec:
        st.error("Error calculando la recomendación.")
        return

    # 4. UI: Header con Contexto Temporal
    # Usamos colores semánticos: Mañana (Azul/Día) vs Tarde (Naranja/Atardecer)
    mode_color = "blue" if rec['mode'] == "Mañana" else "orange"
    st.markdown(f":{mode_color}[**MODO {rec['mode'].upper()}**]")
    
    # 5. UI: La Recomendación Principal (Big Number)
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric(
            label="Nivel Recomendado",
            value=f"Nivel {rec['level']}",
            delta=rec['context'], # Ej: "3°C más frío que ayer"
            delta_color="off"     # Gris neutro, ya que es informativo
        )
        st.info(f"**{rec['level_text']}**")

    with col2:
        st.write("Pronóstico:")
        st.write(f"🌡️ Max: {rec['temp_max']}°C")
        st.write(f"❄️ Min: {rec['temp_min']}°C")

    # 6. UI: Razón de la decisión
    if "Alerta" in rec['reasoning']:
        st.warning(rec['reasoning']) # Amarillo si es por lluvia
    else:
        st.caption(f"💡 Razón: {rec['reasoning']}")

    # 7. UI: Sección de Feedback (Pasamos los datos de AYER - fila 0)
    # Solo mostramos feedback si estamos en modo mañana o si el usuario quiere
    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)