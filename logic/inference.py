import pandas as pd
from datetime import datetime, timezone, timedelta
import streamlit as st
from config import settings
from logic.preprocessing import prepare_features
from logic.training import load_model

def get_recommendation(weather_df):
    """
    Toma el DataFrame del clima (Ayer, Hoy, Mañana) y decide qué recomendar
    basado en la hora local real del usuario y reglas de negocio.
    """
    if weather_df.empty:
        return None

    # --- 1. CÁLCULO DE HORA LOCAL REAL (CRÍTICO) ---
    # Recuperamos el offset que nos dio Open-Meteo al consultar la API.
    # Si no existe (ej. error API), usamos -14400 segundos (-4 horas, Chile) como fallback seguro.
    offset_sec = st.session_state.get("current_utc_offset", -14400)
    
    # Calculamos la hora en la ubicación del usuario
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc + timedelta(seconds=offset_sec)
    current_hour = now_local.hour
    
    # Debug para consola (para que veas que funciona la hora dinámica)
    print(f"🕒 Hora local calculada: {now_local.strftime('%H:%M')} (Offset: {offset_sec/3600}h)")

    # --- 2. DETERMINAR MODO TEMPORAL ---
    # Hasta las 13:59 es modo "Hoy" (Mañana). Desde las 14:00 es modo "Mañana" (Tarde/Noche).
    is_morning_mode = current_hour < 14 
    
    # Índices del DataFrame asumiendo que API trae: [0: Ayer, 1: Hoy, 2: Mañana, ...]
    if is_morning_mode:
        # Modo Mañana: ¿Qué me pongo HOY? (Comparado con AYER)
        target_row = weather_df.iloc[1] # Hoy
        ref_row = weather_df.iloc[0]    # Ayer
        time_label = "hoy"
        ref_label = "ayer"
        mode_text = "Mañana"
    else:
        # Modo Tarde: ¿Qué preparo para MAÑANA? (Comparado con HOY)
        target_row = weather_df.iloc[2] # Mañana
        ref_row = weather_df.iloc[1]    # Hoy
        time_label = "mañana"
        ref_label = "hoy"
        mode_text = "Tarde"

    # --- 3. REGLA DE LLUVIA (VETO DURO) ---
    # Si la probabilidad es alta O la cantidad es significativa, ignoramos el modelo KNN
    rain_prob = target_row.get('precip_prob_max', 0)
    rain_mm = target_row.get('precipitation_sum', 0)
    
    is_raining = (rain_prob >= settings.RAIN_PROB_THRESHOLD) or \
                 (rain_mm >= settings.RAIN_AMOUNT_THRESHOLD)

    if is_raining:
        # Lluvia fuerza nivel 3 (Abrigo/Impermeable) como mínimo
        suggested_level = 3
        reasoning = f"⚠️ Alerta de lluvia ({rain_prob}% / {rain_mm}mm). Mejor prevenir."
    else:
        # --- 4. INFERENCIA CON MODELO KNN (IA) ---
        knn = load_model()
        if knn:
            # Preparamos los datos de una sola fila para predicción
            # is_training=False usa el scaler guardado, no crea uno nuevo
            X_in = prepare_features(target_row.to_frame().T, is_training=False)
            suggested_level = int(knn.predict(X_in)[0])
            reasoning = "Según tu historial de preferencias."
        else:
            # Fallback por si borraron el modelo o es usuario nuevo
            suggested_level = 2 
            reasoning = "Usando configuración estándar (Aún no tengo datos tuyos)."

    # --- 5. CONTEXTO RELATIVO (EL DELTA) ---
    # Calculamos cuánto cambia la temperatura máxima respecto a la referencia
    temp_diff = target_row['temp_max'] - ref_row['temp_max']
    
    if abs(temp_diff) < 2:
        context_text = f"Similar a {ref_label}"
    elif temp_diff > 0:
        context_text = f"{abs(round(temp_diff, 1))}°C más calor que {ref_label}"
    else:
        context_text = f"{abs(round(temp_diff, 1))}°C más frío que {ref_label}"

    # Retornamos un diccionario rico en información para la UI
    return {
        "level": suggested_level,
        "level_text": settings.CLOTHING_LEVELS.get(suggested_level, "Desconocido"),
        "temp_max": target_row['temp_max'],
        "temp_min": target_row['temp_min'],
        "context": context_text,
        "reasoning": reasoning,
        "target_date": target_row['date'],
        "mode": mode_text
    }