import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation, get_weekly_recommendations 
from ui.feedback import render_feedback_section
from services.location import get_current_coords

def geocode_city(city_name):
    """Busca las coordenadas de una ciudad usando la API gratuita de Open-Meteo."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5&language=es&format=json"
        res = requests.get(url).json()
        return res.get("results", [])
    except Exception:
        return []

def render_dashboard():
    # --- DETALLE DE ANIVERSARIO (EL CAMBIO DE LOOK COMPLETO) ---
    zona_stgo = ZoneInfo("America/Santiago")
    hoy = datetime.now(zona_stgo)
    
    # Para probar hoy, está en 27
    es_aniversario = hoy.day == 12
    
    if es_aniversario:
        st.markdown("""
        <style>
            .stApp { background: linear-gradient(135deg, #300A17 0%, #0F0307 100%) !important; }
            h1 { text-shadow: 0 0 10px #ff4b4b, 0 0 20px #ff4b4b; }
            div[data-testid="stMetric"] {
                background-color: rgba(255, 75, 75, 0.1) !important;
                border: 1px solid rgba(255, 75, 75, 0.3) !important;
                border-radius: 10px;
                padding: 10px;
            }
        </style>
        """, unsafe_allow_html=True)

        st.balloons()
        st.title("IsiWear 💖")
        st.markdown("<h3 style='text-align: center; color: #ffb3d9;'>¡Feliz cumple mes, my love! 🥰</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8; color: white;'>Hoy la app se viste de gala. Que tengas un día hermoso, te amo muchísimo.</p>", unsafe_allow_html=True)
        st.divider()
    else:
        st.title("IsiWear 🧣")

    # --- 1. INDICADOR Y SELECTOR DE UBICACIÓN ---
    loc = get_current_coords()
    
    if loc.get("source") == "manual":
        source_icon = "📍"
        loc_label = loc.get("name", "Ubicación Seleccionada")
    elif loc.get("source") == "gps":
        source_icon = "🛰️" 
        loc_label = "Ubicación Actual"
    else:
        source_icon = "🏢"
        loc_label = "Santiago (Default)"
        
    st.caption(f"{source_icon} **{loc_label}**: {loc['lat']:.4f}, {loc['lon']:.4f}")

    with st.expander("🔎 Cambiar de ciudad"):
        if loc.get("source") == "manual":
            if st.button("🛰️ Volver a mi ubicación automática"):
                del st.session_state["manual_loc"]
                st.rerun()
                
        search_query = st.text_input("Escribe una ciudad (ej. Villa O'Higgins, Tokio):")
        if search_query:
            with st.spinner("Buscando en el mapa..."):
                results = geocode_city(search_query)
                if results:
                    for r in results:
                        city_text = f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}".strip(", ")
                        if st.button(f"📍 {city_text}", key=r['id']):
                            st.session_state["manual_loc"] = {
                                "lat": r["latitude"],
                                "lon": r["longitude"],
                                "source": "manual",
                                "name": r["name"]
                            }
                            st.rerun() 
                else:
                    st.warning("No encontramos esa ciudad. Intenta con otro nombre.")

    # --- 2. Obtener Datos ---
    with st.spinner("Consultando satélites..."):
        weather_df = get_weather_forecast()
    
    if weather_df.empty:
        st.error("No pudimos conectar con el servicio de clima. Revisa tu conexión.")
        return

    # --- 3. Obtener Recomendación Principal ---
    rec = get_recommendation(weather_df)
    
    if not rec:
        st.error("Error calculando la recomendación.")
        return

    # --- 4. UI: Header con Contexto Temporal ---
    mode_color = "blue" if rec['mode'] == "Mañana" else "orange"
    st.markdown(f":{mode_color}[**MODO {rec['mode'].upper()}**]")
    
    # --- 5. UI: La Recomendación Principal ---
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

    # --- 6. UI: Razón de la decisión ---
    if "Alerta" in rec['reasoning']:
        st.warning(rec['reasoning'])
    else:
        st.caption(f"💡 Razón: {rec['reasoning']}")

    # --- 7. UI: PRONÓSTICO SEMANAL COMPACTO ---
    st.divider()
    st.subheader("📅 Próximos 7 días")
    
    weekly_forecast = get_weekly_recommendations(weather_df)
    
    html_cards = ""
    for day in weekly_forecast:
        if day['rain_prob'] > 0 or day['rain_mm'] > 0:
            rain_text = f"☔ {day['rain_prob']}% ({day['rain_mm']}mm)"
        else:
            rain_text = "☀️ Despejado"
            
        if ':' in day['level_text'] and '(' in day['level_text']:
            level_desc = day['level_text'].split(':')[1].split('(')[0].strip()
        else:
            level_desc = day['level_text']
            
        html_cards += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background-color: rgba(150, 150, 150, 0.1); padding: 12px 15px; 
                    border-radius: 10px; margin-bottom: 10px;">
            <div style="flex: 1.2; line-height: 1.4;">
                <strong style="font-size: 15px;">{day['dia']}</strong><br>
                <span style="font-size: 13px; opacity: 0.7;">{day['fecha']}</span>
            </div>
            <div style="flex: 1.5; text-align: center; line-height: 1.4;">
                <span style="font-size: 15px;">🌡️ {day['temp_max']}° / {day['temp_min']}°</span><br>
                <span style="font-size: 13px; opacity: 0.7;">{rain_text}</span>
            </div>
            <div style="flex: 1.3; text-align: right; line-height: 1.4;">
                <strong style="font-size: 14px; color: #ff4b4b;">🧣 Nivel {day['level']}</strong><br>
                <span style="font-size: 11px; opacity: 0.7;">{level_desc}</span>
            </div>
        </div>
        """
        
    st.markdown(html_cards, unsafe_allow_html=True)

    # --- 8. UI: Sección de Feedback ---
    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)