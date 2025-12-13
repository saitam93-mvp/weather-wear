import streamlit as st
import datetime
from logic.training import sync_model_with_db # <--- CAMBIO CLAVE
from services.db import save_feedback_history
from config import settings

def render_feedback_section(yesterday_row):
    """
    Muestra un formulario para corregir la predicción de AYER.
    """
    st.divider()
    st.subheader("🧠 Entrena a tu Asistente")
    
    # Calculamos fecha de ayer por seguridad
    yesterday_date = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.expander("¿Qué debiste usar ayer realmente?", expanded=False):
        # Mostramos datos redondeados visualmente
        st.write(
            f"Datos del {yesterday_date}: "
            f"Max **{yesterday_row['temp_max']}°C** / "
            f"Min **{yesterday_row['temp_min']}°C**"
        )
        
        with st.form("feedback_form"):
            selected_level = st.selectbox(
                "Selecciona el nivel que fue MÁS adecuado:",
                options=list(settings.CLOTHING_LEVELS.keys()),
                format_func=lambda x: settings.CLOTHING_LEVELS[x]
            )
            
            submit_btn = st.form_submit_button("Corregir y Aprender")
            
            if submit_btn:
                # 1. Guardar en la Nube (La verdad absoluta)
                saved_cloud = save_feedback_history(
                    date_ref=yesterday_date,
                    t_max=yesterday_row['temp_max'],
                    t_min=yesterday_row['temp_min'],
                    level=selected_level,
                    
                    # Datos existentes
                    precip=yesterday_row.get('precipitation_sum', 0.0),
                    w_code=yesterday_row.get('weathercode', 0),
                    
                    # Datos Nuevos
                    t_mean=yesterday_row.get('temp_mean', 0.0),
                    hum_mean=yesterday_row.get('humidity_mean', 0.0),
                    wind_max=yesterday_row.get('windspeed_max', 0.0),
                    wind_mean=yesterday_row.get('windspeed_mean', 0.0),
                    clouds=yesterday_row.get('cloud_cover_mean', 0.0),
                    rad=yesterday_row.get('solar_rad_sum', 0.0),
                    precip_prob=yesterday_row.get('precip_prob_max', 0.0)
                )

                if saved_cloud:
                    st.toast("✅ Datos guardados en la nube.", icon="☁️")
                    
                    # 2. Re-entrenamiento CORRECTO (Descargar todo + Entrenar)
                    with st.spinner("Re-calibrando neuronas con el nuevo dato..."):
                        try:
                            # Reutilizamos la lógica robusta de sincronización
                            success = sync_model_with_db() 
                            if success:
                                st.success("¡Modelo actualizado! Tu asistente es más inteligente.")
                            else:
                                st.warning("Datos guardados, pero el re-entrenamiento falló.")
                        except Exception as e:
                            st.error(f"Error en re-entrenamiento: {e}")
                else:
                    st.error("⚠️ Error conectando con Supabase. Intenta más tarde.")