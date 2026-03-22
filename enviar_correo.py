import os
import smtplib
from email.message import EmailMessage

# --- TRUCO DE CONTEXTO ACTUALIZADO ---
# Engañamos a Python para que no falle al buscar "st.session_state" por fuera de la web
from threading import current_thread
try:
    # Ruta para versiones antiguas de Streamlit
    from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
except ModuleNotFoundError:
    # Ruta para versiones nuevas de Streamlit
    from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx

add_script_run_ctx(current_thread())

import streamlit as st
st.session_state["current_utc_offset"] = -10800 # Forzamos hora de Chile
st.session_state["user_location"] = {"lat": -33.426334, "lon": -70.589805, "source": "bot"}

# --- IMPORTAMOS TU LÓGICA ---
from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation
from logic.training import sync_model_with_db

def ejecutar_bot():
    print("🤖 Iniciando bot de IsiWear...")

    # 1. Bajar la memoria de la IA desde Supabase
    sync_model_with_db()

    # 2. Consultar el clima de hoy
    weather_df = get_weather_forecast()
    if weather_df.empty:
        print("❌ Error: No se pudo conectar a Open-Meteo.")
        return

    # 3. Obtener la predicción del modelo KNN
    rec = get_recommendation(weather_df)
    if not rec:
        print("❌ Error: No se pudo generar la recomendación.")
        return

    # 4. Configuración del correo
    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatario = os.getenv("EMAIL_TO")

    if not all([remitente, password, destinatario]):
        print("❌ Error: Faltan credenciales de correo en el entorno.")
        return

    msg = EmailMessage()
    msg['Subject'] = '🧣 Tu recomendación de vestuario para hoy'
    msg['From'] = remitente
    msg['To'] = destinatario

    # Cuerpo del correo 
    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            <h2 style="color: #ff4b4b;">¡Buenos días, Isi! 🌤️</h2>
            <p>Aquí tienes el pronóstico de tu asistente para hoy:</p>
            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px;">
                <h3 style="margin-top: 0;">🧥 Nivel {rec['level']} - {rec['level_text']}</h3>
                <p><b>Contexto:</b> {rec['context']}</p>
                <p>🌡️ <b>Max:</b> {rec['temp_max']}°C &nbsp; | &nbsp; ❄️ <b>Min:</b> {rec['temp_min']}°C</p>
            </div>
            <p>💡 <i>Nota del modelo: {rec['reasoning']}</i></p>
            <br>
            <p>¡Que tengas un excelente día!</p>
        </body>
    </html>
    """
    msg.set_content("Por favor, activa el formato HTML para ver este correo.")
    msg.add_alternative(cuerpo_html, subtype='html')

    # 5. Envío
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
            print("✅ ¡Correo enviado exitosamente a Isi!")
    except Exception as e:
        print(f"❌ Falló el envío del correo: {e}")

if __name__ == "__main__":
    ejecutar_bot()