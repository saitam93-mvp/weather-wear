import pandas as pd
from datetime import datetime
from config import settings
from logic.preprocessing import prepare_features
from logic.training import load_model

def get_recommendation(weather_df):
    """
    Toma el DataFrame del clima (Ayer, Hoy, Mañana) y decide qué recomendar
    basado en la hora actual y reglas de negocio.
    """
    if weather_df.empty:
        return None

    # 1. Determinar el Modo Temporal (Mañana vs Tarde/Noche)
    current_hour = datetime.now().hour
    is_morning_mode = current_hour < 14  # Hasta las 13:59 es modo "Hoy"
    
    # Índices del DataFrame (0: Ayer, 1: Hoy, 2: Mañana)
    if is_morning_mode:
        # Modo Mañana: ¿Qué me pongo HOY? (Comparado con AYER)
        target_row = weather_df.iloc[1] # Hoy
        ref_row = weather_df.iloc[0]    # Ayer
        time_label = "hoy"
        ref_label = "ayer"
    else:
        # Modo Tarde: ¿Qué preparo para MAÑANA? (Comparado con HOY)
        target_row = weather_df.iloc[2] # Mañana
        ref_row = weather_df.iloc[1]    # Hoy
        time_label = "mañana"
        ref_label = "hoy"

    # 2. Verificar Regla de Lluvia (Hard Rule)
    # Si la probabilidad es alta O la cantidad es significativa, ignoramos el modelo KNN
    rain_prob = target_row.get('rain_prob', 0)
    rain_mm = target_row.get('rain_mm', 0)
    
    is_raining = (rain_prob >= settings.RAIN_PROB_THRESHOLD) or \
                 (rain_mm >= settings.RAIN_AMOUNT_THRESHOLD)

    if is_raining:
        # Lluvia fuerza nivel 3 (Abrigo/Impermeable) como mínimo
        suggested_level = 3
        reasoning = f"⚠️ Alerta de lluvia ({rain_prob}% / {rain_mm}mm). Mejor prevenir."
    else:
        # 3. Inferencia con Modelo KNN (Preferencia Personal)
        knn = load_model()
        if knn:
            # Preparamos los datos de una sola fila para predicción
            X_in = prepare_features(target_row.to_frame().T, is_training=False)
            suggested_level = int(knn.predict(X_in)[0])
            reasoning = "Según tu historial de preferencias."
        else:
            # Fallback por si borraron el modelo
            suggested_level = 2 
            reasoning = "Modelo no encontrado. Usando default."

    # 4. Contexto Relativo (El "Delta")
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
        "mode": "Mañana" if is_morning_mode else "Tarde"
    }