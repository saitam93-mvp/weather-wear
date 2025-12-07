import streamlit as st
import pandas as pd
from logic.training import train_model
from config import settings

def render_feedback_section(yesterday_row):
    """
    Muestra un expansor o formulario para que el usuario corrija 
    la predicción de AYER.
    """
    st.divider()
    st.subheader("🧠 Entrena a tu Asistente")
    
    with st.expander("¿Qué debiste usar ayer realmente?", expanded=False):
        st.write(f"Datos de ayer: Max {yesterday_row['temp_max']}°C / Min {yesterday_row['temp_min']}°C")
        
        # Formulario para capturar el dato real
        with st.form("feedback_form"):
            selected_level = st.selectbox(
                "Selecciona el nivel que fue MÁS adecuado:",
                options=list(settings.CLOTHING_LEVELS.keys()),
                format_func=lambda x: settings.CLOTHING_LEVELS[x]
            )
            
            submit_btn = st.form_submit_button("Corregir y Aprender")
            
            if submit_btn:
                # 1. Construir el dato de entrenamiento
                # Usamos los valores CLIMÁTICOS de ayer + la ETIQUETA real del usuario
                training_data = pd.DataFrame([{
                    "temp_max": yesterday_row['temp_max'],
                    "temp_min": yesterday_row['temp_min'],
                    "clothing_level": selected_level
                }])
                
                # 2. Re-entrenar el modelo (Llamada a Logic)
                try:
                    train_model(training_data)
                    st.success("¡Gracias! He actualizado mi modelo con tu preferencia.")
                    
                    # Opcional: Limpiar caché para forzar recarga si fuera necesario
                    # st.cache_resource.clear() 
                except Exception as e:
                    st.error(f"Error al entrenar: {e}")