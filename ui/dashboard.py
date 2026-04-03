# ui/dashboard.py - Código completo y corregido

import streamlit as st
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation, get_weekly_recommendations 
from ui.feedback import render_feedback_section
from services.location import get_current_coords

# --- FUNCIONES AUXILIARES ---

def geocode_city(city_name):
    """Busca las coordenadas de una ciudad usando la API gratuita de Open-Meteo."""
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5&language=es&format=json"
        res = requests.get(url).json()
        return res.get("results", [])
    except Exception:
        return []

def render_wear_card(rec, target_row, ref_row):
    """Genera una tarjeta HTML/CSS rica para la recomendación principal."""
    es_modo_manana = "mañana" in rec['mode'].lower()
    t_obj = "Mañana" if es_modo_manana else "Hoy"
    t_ref = "Hoy" if es_modo_manana else "Ayer"

    # Determinar un color de acento según el nivel
    color_acc = "#ff4b4b" # Rojo por defecto
    if rec['level'] == 0: color_acc = "#4caf50" # Verde
    if rec['level'] == 1: color_acc = "#ffeb3b" # Amarillo
    if rec['level'] == 2: color_acc = "#ff9800" # Naranja

    # Extracción de lluvia del DataFrame. Ahora vendrá de weather_api.py
    # target_row proviene de weather_df, que ahora tiene las columnas correctas.
    rain_prob = target_row['precipitation_probability'] if 'precipitation_probability' in target_row else 0
    rain_mm = target_row['precipitation'] if 'precipitation' in target_row else 0
    
    # Preparamos el texto de lluvia para el pronóstico
    if rain_prob > 0 or rain_mm > 0:
        rain_text = f"☔ {int(rain_prob)}% ({round(rain_mm, 1)} mm)"
    else:
        rain_text = "☀️ Sin lluvia"

    # IMPORTANTE: Este HTML no debe tener espacios a la izquierda para evitar que Streamlit lo lea como código
    html = f"""
<style>
.wear-card {{ background-color: #262730; border-radius: 15px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-left: 5px solid {color_acc}; margin-bottom: 20px; }}
.wear-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
.wear-mode {{ color: #888; font-size: 14px; text-transform: uppercase; font-weight: bold; }}
.wear-title {{ font-size: 32px; font-weight: 800; margin: 0; }}
.wear-delta {{ font-size: 14px; color: #aaa; margin-top: -5px; }}
.wear-desc {{ font-size: 18px; color: white; font-weight: bold; margin-bottom: 15px; }}
.wear-metrics {{ display: flex; justify-content: space-between; background-color: #1a1b21; padding: 15px; border-radius: 10px; }}
.metric-block {{ flex: 1; text-align: center; }}
.metric-title {{ color: #ccc; font-size: 12px; margin-bottom: 5px; }}
.metric-value {{ font-size: 20px; font-weight: bold; margin-bottom: 5px; }}
.metric-rain {{ font-size: 14px; color: #4fc3f7; margin: 0; }}
</style>
<div class="wear-card">
    <div class="wear-header">
        <div>
            <p class="wear-mode">MODO {rec['mode'].upper()}</p>
            <h1 class="wear-title">Nivel {rec['level']}</h1>
            <p class="wear-delta">{rec['context']}</p>
        </div>
        <div style="font-size: 50px;">🧣</div>
    </div>
    <div class="wear-desc">{rec['level_text']}</div>
    
    <div class="wear-metrics">
        <div class="metric-block" style="border-right: 1px solid #444;">
            <p class="metric-title">Pronóstico ({t_obj})</p>
            <p class="metric-value">🌡️ {rec['temp_max']}° / {rec['temp_min']}°</p>
            <p class="metric-rain">{rain_text}</p> # ¡Aquí se está mostrando la lluvia!
        </div>
        <div class="metric-block">
            <p class="metric-title">Referencia ({t_ref})</p>
            <p class="metric-value">🌡️ {ref_row['temp_max']}° / {ref_row['temp_min']}°</p>
        </div>
    </div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)

# --- FUNCIÓN PRINCIPAL DEL DASHBOARD ---

def render_dashboard():
    # --- DETALLE DE ANIVERSARIO ---
    zona_stgo = ZoneInfo("America/Santiago")
    hoy = datetime.now(zona_stgo)
    es_aniversario = hoy.day == 12
    
    if es_aniversario:
        st.markdown("""
        <style>
            .stApp { background: linear-gradient(135deg, #300A17 0%, #0F0307 100%) !important; }
            h1 { text-shadow: 0 0 10px #ff4b4b, 0 0 20px #ff4b4b; }
        </style>
        """, unsafe_allow_html=True)

        st.balloons()
        st.title("IsiWear 💖") # Título especial de aniversario queda igual
        st.markdown("<h3 style='text-align: center; color: #ffb3d9;'>¡Feliz día 12, mi amor! 🥰</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8; color: white;'>Hoy la app se viste de gala. Que tengas un día hermoso, te amo muchísimo.</p>", unsafe_allow_html=True)
        st.divider()
    else:
        # Título normal con la bufanda a la derecha. Este es el cambio solicitado.
        # Ponemos el icono directamente en st.title para que esté a la derecha del nombre.
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

    with st.expander("🔎 Cambiar de ciudad", expanded=False):
        if loc.get("source") == "manual":
            if st.button("🛰️ Volver a mi ubicación automática"):
                del st.session_state["manual_loc"]
                st.rerun()
                
        search_query = st.text_input("Escribe una ciudad (ej. Puerto Montt):")
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

    # --- 2. Obtener Datos (Services) ---
    with st.spinner("Consultando satélites..."):
        weather_df = get_weather_forecast()
    
    if weather_df.empty:
        st.error("No pudimos conectar con el servicio de clima. Revisa tu conexión.")
        return

    # --- 3. Obtener Recomendación (Logic) ---
    rec = get_recommendation(weather_df)
    
    if not rec:
        st.error("Error calculando la recomendación.")
        return

    # --- 4 & 5. UI: TARJETA DE RECOMENDACIÓN PRINCIPAL ---
    es_modo_manana = "mañana" in rec['mode'].lower()
    
    # Índice 0 = Ayer, 1 = Hoy, 2 = Mañana
    target_idx = 2 if es_modo_manana else 1
    ref_idx = 1 if es_modo_manana else 0
    
    target_row = weather_df.iloc[target_idx]
    ref_row = weather_df.iloc[ref_idx] 
    
    # Llamamos a la función para renderizar la tarjeta. Ahora tendrá los datos de lluvia.
    render_wear_card(rec, target_row, ref_row)

    # --- 6. UI: Razón de la decisión ---
    # Esto incluye el banner de alerta amarilla si se detecta lluvia
    if "Alerta" in rec['reasoning']:
        st.warning(rec['reasoning'])
    else:
        st.caption(f"💡 Razón: {rec['reasoning']}")

    # --- 7. UI: PRONÓSTICO SEMANAL ---
    st.divider()
    st.subheader("📅 Próximos 7 días")
    
    # Esta función en logic/inference.py ya debe tener la lógica para rain_prob y rain_mm
    weekly_forecast = get_weekly_recommendations(weather_df)
    
    # Construimos una lista de tarjetas compactas usando HTML/CSS para forzar la vista horizontal en móviles.
    html_cards = ""
    for day in weekly_forecast:
        # Preparamos el texto de lluvia para el pronóstico semanal
        if day['rain_prob'] > 0 or day['rain_mm'] > 0:
            rain_text = f"☔ {day['rain_prob']}% ({day['rain_mm']} mm)"
        else:
            rain_text = "☀️ Sin lluvia"
            
        if ':' in day['level_text'] and '(' in day['level_text']:
            level_desc = day['level_text'].split(':')[1].split('(')[0].strip()
        else:
            level_desc = day['level_text']

        html_cards += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px;
                    border-left: 3px solid rgba(255, 75, 75, 0.5);">
            <div style="flex: 1.2;">
                <strong style="font-size: 16px;">{day['dia']}</strong><br>
                <span style="font-size: 12px; color: #aaa;">{day['fecha']}</span>
            </div>
            <div style="flex: 1.8; text-align: center;">
                🌡️ {day['temp_max']}° / {day['temp_min']}°<br>
                <span style="font-size: 12px; color: #aaa;">{rain_text}</span>
            </div>
            <div style="flex: 2; text-align: right;">
                🧣 <strong>Nivel {day['level']}</strong><br>
                <span style="font-size: 11px; color: #ccc;">{level_desc}</span>
            </div>
        </div>
        """
        
    st.markdown(html_cards, unsafe_allow_html=True)

    # --- 8. UI: Sección de Feedback ---
    st.divider()
    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)