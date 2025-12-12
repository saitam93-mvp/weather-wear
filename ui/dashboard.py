import streamlit as st
import datetime
from streamlit_js_eval import get_geolocation # <--- IMPORTANTE
from services.weather_api import get_weather_forecast
from logic.inference import get_clothing_recommendation
from ui.feedback import render_feedback_section

def render_dashboard():
    st.title("IsiWear 🧣")
    
    # --- 1. GEOLOCALIZACIÓN ---
    # Por defecto usaremos None (lo que forzará el default del config)
    user_lat = None
    user_lon = None
    
    col_geo, col_info = st.columns([1, 3])
    
    with col_geo:
        # Botón para pedir ubicación
        if st.checkbox("📍 Usar mi ubicación"):
            loc = get_geolocation()
            if loc:
                user_lat = loc['coords']['latitude']
                user_lon = loc['coords']['longitude']
                st.success(f"Ubicación detectada.")
            else:
                st.warning("Esperando permiso del navegador...")

    # --- 2. OBTENER DATOS ---
    # Pasamos las coordenadas dinámicas (si existen) a la API
    with st.spinner("Consultando satélites..."):
        # Si user_lat es None, la función usará el default de settings
        df_forecast = get_weather_forecast(lat=user_lat, lon=user_lon)
    
    if df_forecast.empty:
        st.error("No se pudo conectar con el servicio meteorológico.")
        return

    # --- 3. LÓGICA DE NEGOCIO (Igual que antes) ---
    now = datetime.datetime.now()
    current_hour = now.hour
    today = now.date()
    
    df_forecast['date_only'] = df_forecast['date'].dt.date
    
    # Filtros de seguridad por si las fechas no coinciden exacto por timezone
    try:
        row_today = df_forecast[df_forecast['date_only'] == today].iloc[0]
        tomorrow = today + datetime.timedelta(days=1)
        row_tomorrow = df_forecast[df_forecast['date_only'] == tomorrow].iloc[0]
    except IndexError:
        st.warning("Los datos del clima no están sincronizados con tu fecha local.")
        return

    # CASO A vs CASO B
    if current_hour < 14:
        mode_label = "🌞 MODO MAÑANA (Outfit de Hoy)"
        target_row = row_today
        yesterday = today - datetime.timedelta(days=1)
        row_compare = df_forecast[df_forecast['date_only'] == yesterday]
        
        comparison_text = ""
        if not row_compare.empty:
            diff = row_today['temp_max'] - row_compare.iloc[0]['temp_max']
            comparison_text = f"({abs(diff):.1f}°C {'más calor' if diff > 0 else 'más frío'} que ayer)"
    else:
        mode_label = "🌙 MODO TARDE (Prepárate para Mañana)"
        target_row = row_tomorrow
        diff = row_tomorrow['temp_max'] - row_today['temp_max']
        comparison_text = f"({abs(diff):.1f}°C {'más calor' if diff > 0 else 'más frío'} que hoy)"

    # Inferencia
    recommendation = get_clothing_recommendation(target_row)
    
    st.caption(mode_label)
    
    # KPIs Visuales
    col_main, col_data = st.columns([2, 1])
    
    with col_main:
        st.metric(
            label="Nivel Recomendado", 
            value=f"Nivel {recommendation['level']}",
            delta=comparison_text,
            delta_color="off"
        )
        st.info(f"💡 **Tip:** {recommendation['description']}")
    
    with col_data:
        st.markdown("### Pronóstico")
        st.write(f"🌡️ **Max:** {target_row['temp_max']}°C")
        st.write(f"❄️ **Min:** {target_row['temp_min']}°C")
        
        if target_row['precipitation_sum'] > 0.1:
            st.write(f"🌧️ **Lluvia:** {target_row['precipitation_sum']} mm")
            st.warning("¡Lleva paraguas!")

    # Feedback Section
    yesterday_date = today - datetime.timedelta(days=1)
    row_yesterday = df_forecast[df_forecast['date_only'] == yesterday_date]
    
    if not row_yesterday.empty:
        render_feedback_section(row_yesterday.iloc[0])