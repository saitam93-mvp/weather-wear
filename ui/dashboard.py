import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from zoneinfo import ZoneInfo
import streamlit.components.v1 as components

from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation, get_weekly_recommendations 
from ui.feedback import render_feedback_section
from services.location import get_current_coords


# --- FUNCIONES AUXILIARES ---

def geocode_city(city_name):
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=5&language=es&format=json"
        res = requests.get(url).json()
        return res.get("results", [])
    except Exception: return []

def format_precipitation(row):
    snow = row.get('snowfall', 0)
    rain_prob = row.get('precipitation_probability', 0)
    rain_mm = row.get('precipitation', 0)
    temp_max = row.get('temp_max', 20)
    
    if pd.isna(snow): snow = 0
    if pd.isna(rain_prob): rain_prob = 0
    if pd.isna(rain_mm): rain_mm = 0
    
    is_snowing = snow > 0 or (rain_mm > 0 and temp_max <= 3)
    
    if is_snowing:
        display_snow = snow if snow > 0 else rain_mm
        return f"❄️ {int(rain_prob)}% ({round(display_snow, 1)} cm)", "<br><span style='color: #81d4fa; font-size: 11px; font-weight: bold;'>+ ❄️ Nieve</span>"
    elif rain_prob > 0 or rain_mm > 0:
        return f"☔ {int(rain_prob)}% ({round(rain_mm, 1)} mm)", "<br><span style='color: #ffeb3b; font-size: 11px; font-weight: bold;'>+ ☔ Impermeable</span>"
    else:
        return "☀️ Sin precipitación", ""

def render_wear_card(rec, target_row, ref_row):
    es_modo_manana = "mañana" in rec['mode'].lower()
    t_obj = "Mañana" if es_modo_manana else "Hoy"
    t_ref = "Hoy" if es_modo_manana else "Ayer"

    # Escala Térmica de Colores
    if rec['level'] == 0:
        color_acc = "#ff4b4b" 
    elif rec['level'] == 1:
        color_acc = "#ffeb3b" 
    elif rec['level'] == 2:
        color_acc = "#03a9f4" 
    else:
        color_acc = "#1e88e5" 

    t_precip_text, _ = format_precipitation(target_row)
    r_precip_text, _ = format_precipitation(ref_row)

    html = f"""
<style>
.wear-card {{ background-color: #262730; border-radius: 15px; padding: 25px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-left: 5px solid {color_acc}; margin-bottom: 20px; color: #ffffff; }}
.wear-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
.wear-mode {{ color: #888; font-size: 14px; text-transform: uppercase; font-weight: bold; }}
.wear-title {{ font-size: 32px; font-weight: 800; margin: 0; color: #ffffff; }}
.wear-delta {{ font-size: 14px; color: #aaa; margin-top: -5px; }}
.wear-desc {{ font-size: 18px; color: #ffffff; font-weight: bold; margin-bottom: 15px; }}
.wear-metrics {{ display: flex; justify-content: space-between; background-color: #1a1b21; padding: 15px; border-radius: 10px; }}
.metric-block {{ flex: 1; text-align: center; }}
.metric-title {{ color: #ccc; font-size: 12px; margin-bottom: 5px; }}
.metric-value {{ font-size: 20px; font-weight: bold; margin-bottom: 5px; color: #ffffff; }}
.metric-rain {{ font-size: 14px; color: #b3e5fc; margin: 0; }}
</style>
<div class="wear-card">
<div class="wear-header">
<div>
<p class="wear-mode">MODO {rec['mode'].upper()}</p>
<h1 class="wear-title">Nivel {rec['level']}</h1>
<p class="wear-delta">{rec['context']}</p>
</div>
</div>
<div class="wear-desc">{rec['level_text']}</div>
<div class="wear-metrics">
<div class="metric-block" style="border-right: 1px solid #444;">
<p class="metric-title">Referencia ({t_ref})</p>
<p class="metric-value">🌡️ {ref_row['temp_max']}° / {ref_row['temp_min']}°</p>
<p class="metric-rain">{r_precip_text}</p>
</div>
<div class="metric-block">
<p class="metric-title">Pronóstico ({t_obj})</p>
<p class="metric-value">🌡️ {target_row['temp_max']}° / {target_row['temp_min']}°</p>
<p class="metric-rain">{t_precip_text}</p>
</div>
</div>
</div>
"""
    st.markdown(html, unsafe_allow_html=True)


# --- CALLBACKS PARA EL MANEJO DE ESTADO DEL BUSCADOR ---

def set_manual_location(r):
    """Callback: Guarda la nueva ubicación y limpia la caja de texto antes de recargar."""
    st.session_state["manual_loc"] = {
        "lat": r["latitude"], "lon": r["longitude"],
        "source": "manual", "name": r["name"]
    }
    st.session_state["city_search"] = ""

def reset_to_auto_location():
    """Callback: Borra la ubicación manual y limpia la caja de texto antes de recargar."""
    if "manual_loc" in st.session_state:
        del st.session_state["manual_loc"]
    st.session_state["city_search"] = ""


# --- FUNCIÓN PRINCIPAL DEL DASHBOARD ---

def render_dashboard():
    # --- INYECCIÓN PWA ---
    pwa_code = """
    <script>
        const parent = window.parent.document;
        if (!parent.querySelector('link[rel="manifest"]')) {
            const manifest = parent.createElement('link');
            manifest.rel = 'manifest';
            manifest.href = '/static/manifest.json';
            parent.head.appendChild(manifest);
        }
        if ('serviceWorker' in window.parent.navigator) {
            window.parent.navigator.serviceWorker.register('/static/sw.js')
            .then(function(reg) { console.log('PWA Lista'); })
            .catch(function(err) { console.log('Error PWA', err); });
        }
    </script>
    """
    components.html(pwa_code, height=0, width=0)
    # ---------------------

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
        st.title("IsiWear 💖")
        st.markdown("<h3 style='text-align: center; color: #ffb3d9;'>¡Feliz día 12, mi amor! 🥰</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; opacity: 0.8; color: white;'>Hoy la app se viste de gala. Que tengas un día hermoso, te amo muchísimo.</p>", unsafe_allow_html=True)
        st.divider()
    else:
        st.title("IsiWear 🧣") 

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
            st.button("🛰️ Volver a mi ubicación automática", on_click=reset_to_auto_location)
                
        search_query = st.text_input("Escribe una ciudad:", key="city_search")
        if search_query:
            with st.spinner("Buscando en el mapa..."):
                results = geocode_city(search_query)
                if results:
                    for r in results:
                        city_text = f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}".strip(", ")
                        st.button(f"📍 {city_text}", key=r['id'], on_click=set_manual_location, args=(r,))
                else:
                    st.warning("No encontramos esa ciudad.")

    with st.spinner("Consultando satélites..."):
        weather_df = get_weather_forecast()
    
    if weather_df.empty:
        st.error("No pudimos conectar con el servicio de clima.")
        return

    rec = get_recommendation(weather_df)
    if not rec:
        st.error("Error calculando la recomendación.")
        return

    es_modo_manana = "mañana" in rec['mode'].lower()
    target_idx = 2 if es_modo_manana else 1
    ref_idx = 1 if es_modo_manana else 0
    target_row = weather_df.iloc[target_idx]
    ref_row = weather_df.iloc[ref_idx] 
    
    render_wear_card(rec, target_row, ref_row)

    if "Alerta" in rec['reasoning']:
        st.warning(rec['reasoning'])
    else:
        st.caption(f"💡 Razón: {rec['reasoning']}")

    st.divider()
    st.subheader("📅 Próximos 7 días")
    
    weekly_forecast = get_weekly_recommendations(weather_df)
    
    html_cards = ""
    for i, day in enumerate(weekly_forecast):
        try: df_row = weather_df.iloc[i + 1] 
        except: df_row = {}
            
        precip_text, precip_alert = format_precipitation(df_row)
        
        if ':' in day['level_text'] and '(' in day['level_text']:
            level_desc = day['level_text'].split(':')[1].split('(')[0].strip()
        else:
            level_desc = day['level_text']

        html_cards += f"""
        <div style="display: flex; justify-content: space-between; align-items: center; 
                    background-color: #262730; padding: 15px; border-radius: 10px; margin-bottom: 10px;
                    border-left: 3px solid rgba(255, 75, 75, 0.5); color: #ffffff;">
            <div style="flex: 1.2;">
                <strong style="font-size: 16px; color: #ffffff;">{day['dia']}</strong><br>
                <span style="font-size: 12px; color: #aaa;">{day['fecha']}</span>
            </div>
            <div style="flex: 1.8; text-align: center; color: #ffffff;">
                🌡️ {day['temp_max']}° / {day['temp_min']}°<br>
                <span style="font-size: 12px; color: #b3e5fc;">{precip_text}</span>
            </div>
            <div style="flex: 2; text-align: right; line-height: 1.4; color: #ffffff;">
                🧣 <strong>Nivel {day['level']}</strong><br>
                <span style="font-size: 11px; color: #ccc;">{level_desc}</span>{precip_alert}
            </div>
        </div>
        """
        
    st.markdown(html_cards, unsafe_allow_html=True)

    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)