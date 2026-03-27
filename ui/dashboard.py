import streamlit as st
import requests # Necesario para buscar la ciudad
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
    st.title("IsiWear 🧣")
    
    # --- 1. INDICADOR Y SELECTOR DE UBICACIÓN ---
    loc = get_current_coords()
    
    # Determinamos el icono y nombre según el origen
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

    # Buscador desplegable para cambiar ubicación
    with st.expander("🔎 Cambiar de ciudad"):
        # Botón para limpiar la búsqueda y volver al GPS original
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
                        # Armamos el texto del botón (Ej: Valdivia, Los Ríos, Chile)
                        city_text = f"{r['name']}, {r.get('admin1', '')}, {r.get('country', '')}".strip(", ")
                        if st.button(f"📍 {city_text}", key=r['id']):
                            # Guardamos la nueva ciudad en la memoria temporal
                            st.session_state["manual_loc"] = {
                                "lat": r["latitude"],
                                "lon": r["longitude"],
                                "source": "manual",
                                "name": r["name"]
                            }
                            st.rerun() # Recargamos la app con la nueva ciudad
                else:
                    st.warning("No encontramos esa ciudad. Intenta con otro nombre.")

    # --- 2. Obtener Datos (Services) ---
    with st.spinner("Consultando satélites..."):
        # Nota: Si tu función get_weather_forecast requiere que le pases lat y lon, 
        # asegúrate de ponerlos aquí: get_weather_forecast(loc['lat'], loc['lon'])
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
        # Ajustamos un poco los anchos de las columnas para que respire mejor
        c1, c2, c3 = st.columns([1.2, 1.8, 2]) 
        
        with c1:
            st.write(f"**{day['dia']}**")
            st.caption(day['fecha'])
            
        with c2:
            # Temperaturas juntas en una línea
            st.write(f"🌡️ {day['temp_max']}° / {day['temp_min']}°")
            
            # Mostramos lluvia solo si hay probabilidad o milímetros, sino un solcito
            if day['rain_prob'] > 0 or day['rain_mm'] > 0:
                st.caption(f"☔ {day['rain_prob']}% ({day['rain_mm']} mm)")
            else:
                st.caption("☀️ Sin lluvia")
                
        with c3:
            st.write(f"🧣 **Nivel {day['level']}**")
            st.caption(day['level_text'])

    # 8. UI: Sección de Feedback
    yesterday_row = weather_df.iloc[0]
    render_feedback_section(yesterday_row)