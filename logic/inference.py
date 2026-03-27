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

    # 1. CÁLCULO DE HORA LOCAL REAL
    offset_sec = st.session_state.get("current_utc_offset", -14400)
    
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc + timedelta(seconds=offset_sec)
    current_hour = now_local.hour
    
    print(f"🕒 Hora local calculada: {now_local.strftime('%H:%M')} (Offset: {offset_sec/3600}h)")

    # 2. DETERMINAR MODO TEMPORAL
    is_morning_mode = current_hour < 14 
    
    if is_morning_mode:
        target_row = weather_df.iloc[1] # Hoy
        ref_row = weather_df.iloc[0]    # Ayer
        time_label = "hoy"
        ref_label = "ayer"
        mode_text = "Para hoy"
    else:
        target_row = weather_df.iloc[2] # Mañana
        ref_row = weather_df.iloc[1]    # Hoy
        time_label = "mañana"
        ref_label = "hoy"
        mode_text = "Para mañana"

    # 3. REGLA DE LLUVIA
    rain_prob = target_row.get('precip_prob_max', 0)
    rain_mm = target_row.get('precipitation_sum', 0)
    
    is_raining = (rain_prob >= settings.RAIN_PROB_THRESHOLD) or \
                 (rain_mm >= settings.RAIN_AMOUNT_THRESHOLD)

    if is_raining:
        suggested_level = 3
        reasoning = f"⚠️ Alerta de lluvia ({round(rain_prob, 1)}% / {round(rain_mm, 1)}mm). Mejor prevenir."
    else:
        # 4. INFERENCIA CON MODELO KNN
        knn = load_model()
        if knn:
            X_in = prepare_features(target_row.to_frame().T, is_training=False)
            suggested_level = int(knn.predict(X_in)[0])
            reasoning = "Según tu historial de preferencias."
        else:
            suggested_level = 2 
            reasoning = "Usando configuración estándar (Aún no tengo datos tuyos)."

    # 5. CONTEXTO RELATIVO
    temp_diff = target_row['temp_max'] - ref_row['temp_max']
    
    if abs(temp_diff) < 2:
        context_text = f"Similar a {ref_label}"
    elif temp_diff > 0:
        context_text = f"{abs(round(temp_diff, 1))}°C más calor que {ref_label}"
    else:
        context_text = f"{abs(round(temp_diff, 1))}°C más frío que {ref_label}"

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

def get_weekly_recommendations(weather_df):
    """
    Evalúa los próximos 7 días y retorna una lista con las recomendaciones de IA.
    """
    if weather_df.empty or len(weather_df) < 2:
        return []

    knn = load_model()
    weekly_data = []
    
    # Tomamos desde Hoy (índice 1) hasta 7 días adelante
    dias_a_extraer = weather_df.iloc[1:8]
    dias_espanol = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    for idx, row in dias_a_extraer.iterrows():
        # Regla de lluvia individual para cada día
        rain_prob = row.get('precip_prob_max', 0)
        rain_mm = row.get('precipitation_sum', 0)
        
        is_raining = (rain_prob >= settings.RAIN_PROB_THRESHOLD) or \
                     (rain_mm >= settings.RAIN_AMOUNT_THRESHOLD)

        if is_raining:
            level = 3
        else:
            if knn:
                X_in = prepare_features(row.to_frame().T, is_training=False)
                level = int(knn.predict(X_in)[0])
            else:
                level = 2

        # Formateo de fechas
        fecha = pd.to_datetime(row['date'])
        nombre_dia = dias_espanol[fecha.weekday()]

        if idx == 1:
            nombre_dia = "Hoy"
        elif idx == 2:
            nombre_dia = "Mañana"

        weekly_data.append({
            "dia": nombre_dia,
            "fecha": fecha.strftime("%d/%m"),
            "temp_max": round(row['temp_max']),
            "temp_min": round(row['temp_min']),
            "level": level,
            "level_text": settings.CLOTHING_LEVELS.get(level, f"Nivel {level}")
        })

    return weekly_data