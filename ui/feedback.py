import streamlit as st
import pandas as pd
from logic.training import train_model
from services.db import save_feedback_history # <--- IMPORTANTE: Importamos el servicio
from config import settings
import datetime

def render_feedback_section(yesterday_row):
    """
    Muestra un expansor o formulario para que el usuario corrija 
    la predicción de AYER.
    """
    st.divider()
    st.subheader("🧠 Entrena a tu Asistente")
    
    # Asumimos que yesterday_row tiene una columna 'date' o calculamos la fecha de ayer
    # Si yesterday_row viene de un DF filtrado, asegúrate de tener acceso a la fecha.
    # Por seguridad, calculamos la fecha de ayer aquí si no viene explícita:
    yesterday_date = datetime.date.today() - datetime.timedelta(days=1)
    
    with st.expander("¿Qué debiste usar ayer realmente?", expanded=False):
        st.write(f"Datos del {yesterday_date}: Max {yesterday_row['temp_max']}°C / Min {yesterday_row['temp_min']}°C")
        
        # Formulario para capturar el dato real
        with st.form("feedback_form"):
            selected_level = st.selectbox(
                "Selecciona el nivel que fue MÁS adecuado:",
                options=list(settings.CLOTHING_LEVELS.keys()),
                format_func=lambda x: settings.CLOTHING_LEVELS[x]
            )
            
            submit_btn = st.form_submit_button("Corregir y Aprender")
            
            if submit_btn:
                # --- PASO 1: PERSISTENCIA (Supabase) ---
                # Guardamos primero en la nube. Si esto falla, avisamos.
                saved_cloud = save_feedback_history(
                    date_ref=yesterday_date,
                    t_max=yesterday_row['temp_max'],
                    t_min=yesterday_row['temp_min'],
                    level=selected_level
                )

                if saved_cloud:
                    st.toast("✅ Dato guardado en la nube (Supabase)", icon="☁️")
                else:
                    st.error("⚠️ No se pudo guardar en la base de datos, pero entrenaremos localmente.")

                # --- PASO 2: APRENDIZAJE LOCAL (KNN) ---
                # Construir el dato de entrenamiento para el modelo en memoria
                training_data = pd.DataFrame([{
                    "temp_max": yesterday_row['temp_max'],
                    "temp_min": yesterday_row['temp_min'],
                    "clothing_level": selected_level
                }])
                
                try:
                    train_model(training_data)
                    st.success("¡Gracias! He actualizado mi modelo con tu preferencia.")
                    
                    # Opcional: sleep breve o rerun para limpiar el form visualmente
                    # time.sleep(1)
                    # st.rerun()
                except Exception as e:
                    st.error(f"Error al entrenar modelo local: {e}")