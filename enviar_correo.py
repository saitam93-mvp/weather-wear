import sys
from datetime import datetime
from zoneinfo import ZoneInfo
import os
import smtplib
from email.message import EmailMessage
from threading import current_thread

try:
    from streamlit.runtime.scriptrunner.script_run_context import add_script_run_ctx
except ModuleNotFoundError:
    from streamlit.runtime.scriptrunner_utils.script_run_context import add_script_run_ctx

add_script_run_ctx(current_thread())
import streamlit as st

# --- GUARDIA DE ZONA HORARIA ---
zona_stgo = ZoneInfo("America/Santiago")
hora_stgo = datetime.now(zona_stgo)

# PARA PROBAR AHORA MISMO, ESTAS LÍNEAS ESTÁN COMENTADAS. 
# CUANDO TERMINES DE PROBAR, QUÍTALE EL "#" A LAS 3 LÍNEAS DE ABAJO PARA QUE VUELVA A FUNCIONAR EL GUARDIA:
# if hora_stgo.hour != 6:
#     print(f"Zzz... Son las {hora_stgo.strftime('%H:%M')} en Santiago. El correo solo sale a las 6 AM. Abortando.")
#     sys.exit(0) 

print("Procediendo a preparar el correo...")

# Forzamos contexto para Streamlit
st.session_state["current_utc_offset"] = -10800 
st.session_state["user_location"] = {"lat": -33.426334, "lon": -70.589805, "source": "bot"}

from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation
from logic.training import sync_model_with_db

def ejecutar_bot():
    print("🤖 Iniciando bot de IsiWear...")
    sync_model_with_db()

    weather_df = get_weather_forecast()
    if weather_df.empty:
        print("❌ Error: No se pudo conectar a Open-Meteo.")
        return

    rec = get_recommendation(weather_df)
    if not rec:
        print("❌ Error: No se pudo generar la recomendación.")
        return

    remitente = os.getenv("EMAIL_USER")
    password = os.getenv("EMAIL_PASS")
    destinatario = os.getenv("EMAIL_TO")

    if not all([remitente, password, destinatario]):
        print("❌ Error: Faltan credenciales de correo en el entorno.")
        return

    msg = EmailMessage()
    
    # --- DETALLE DE ANIVERSARIO 
    es_aniversario = hora_stgo.day == 12
    
    msg['Subject'] = '❤️ ¡Feliz cumplemes! + Tu recomendación IsiWear' if es_aniversario else '🧣 Tu recomendación de vestuario para hoy'
    msg['From'] = remitente
    msg['To'] = destinatario

    saludo_html = '<h2 style="color: #e83e8c;">¡Buenos días mi amor! Feliz 12 ❤️🥰</h2>' if es_aniversario else '<h2 style="color: #ff4b4b;">¡Buenos días, Isi! 🌤️</h2>'
    mensaje_extra = '<div style="background-color: #ffe6f2; border-left: 5px solid #d81b60; padding: 15px; border-radius: 5px; margin-bottom: 15px;"><strong style="color: #d81b60;">¡Feliz cumplemes! Que tengas un día hermoso, te amo muchísimo. 💕</strong></div>' if es_aniversario else ''

    cuerpo_html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; color: #333;">
            {saludo_html}
            {mensaje_extra}
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

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(remitente, password)
            smtp.send_message(msg)
            print("✅ ¡Correo enviado exitosamente a Isi!")
    except Exception as e:
        print(f"❌ Falló el envío del correo: {e}")

if __name__ == "__main__":
    ejecutar_bot()