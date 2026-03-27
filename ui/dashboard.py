import streamlit as st
from services.weather_api import get_weather_forecast
# Importamos la nueva función del pronóstico semanal
from logic.inference import get_recommendation, get_weekly_recommendations 
from ui.feedback import render_feedback_section
from services.location import get_current_coords

def render_dashboard():
    st.title("IsiWear 🧣")
    
    # 1. INDICADOR DE UBICACIÓN
    loc = get_current_coords()
    
    if loc.get("source") == "gps":
        source_icon = "🛰️" 
        loc_label = "Ubicación Actual"
    else:
        source_icon = "🏢"
        loc_label = "Santiago (Default)"
        
    st.caption(f"{source_icon} **{loc_label}**: {loc['lat']:.4f}, {loc['lon']:.4f}")

    # 2. Obtener Datos
    with st.spinner("Consultando satélites..."):
        weather_df = get_weather_forecast()
    
    if weather_df.empty:
        st.error("No pudimos conectar con el servicio de clima. Revisa tu conexión.")
        return

    # 3. Obtener Recomendación Principal
    rec = get_recommendation(weather_df)
    
    if not rec:
        st.error("Error calculando la recomendación.")
        return

    # 4. UI: Header con Contexto Temporal
    mode_color = "blue" if rec['mode'] == "Mañana" else "orange"
    st.markdown(f":{mode_color}[**MODO {rec['mode'].upper()}**]")
    
    # 5. UI: La Recomendación Principal
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.metric(
            label="Nivel Recomendado",
            value=f"Nivel {rec['level']}",
            delta=rec['context'],
            delta_color="off"
        )
        st.info(f"**{rec['level_text']}**")

    with col2:
        st.write("Pronóstico:")
        st.write(f"🌡️ Max: {rec['temp_max']}°C")
        st.write(f"❄️ Min: {rec['temp_min']}°C")

    # 6. UI: Razón de la decisión
    if "Alerta" in rec['reasoning']:
        st.warning(rec['reasoning'])
    else:
        st.caption(f"💡 Razón: {rec['reasoning']}")

    # 7. UI: PRONÓSTICO SEMANAL (NUEVO)
    st.divider()
    st.subheader("📅 Próximos 7 días")
    
    weekly_forecast = get_weekly_recommendations(weather_df)
    
    for day in weekly_forecast:
        c1, c2, c3 = st.columns([1.5, 1.5, 2])
        with c1:
            st.write(f"**{day['dia']}**")
            st.caption(day['fecha'])
        with c2:
            st.write(f"🔼 {day['temp_max']}°")
            st.write(f"🔽 {day['temp_min']}°")
        with c3:
            st.write(f"🧣 **Nivel {day['level']}**")
            st.caption(day['level_text'])

    # 8. UI: Sección de Feedback
    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)