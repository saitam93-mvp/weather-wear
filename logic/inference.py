import pandas as pd
from datetime import datetime

try:
    from config.settings import CLOTHING_LEVELS
except ImportError:
    CLOTHING_LEVELS = {
        0: "Muy Ligero (Shorts/Polera)",
        1: "Ligero (Pantalón/Manga larga fina)",
        2: "Intermedio (Polerón/Chaqueta ligera)",
        3: "Abrigo (Chaqueta gruesa/Impermeable)"
    }

# =====================================================================
# IMPORTA AQUÍ TU MODELO KNN 
# =====================================================================

def get_recommendation(weather_df):
    if weather_df.empty: return None

    hora_actual = datetime.now().hour
    es_modo_manana = hora_actual >= 18
    target_idx = 2 if es_modo_manana else 1
    ref_idx = 1 if es_modo_manana else 0
    if target_idx >= len(weather_df): target_idx = len(weather_df) - 1
        
    target_row = weather_df.iloc[target_idx]
    ref_row = weather_df.iloc[ref_idx]
    mode = "Mañana" if es_modo_manana else "Hoy"
    temp_max = round(target_row['temp_max'], 1)
    temp_min = round(target_row['temp_min'], 1)
    ref_temp_max = round(ref_row['temp_max'], 1)

    # =====================================================================
    # PREDICCIÓN KNN PARA HOY/MAÑANA
    # =====================================================================
    if temp_max >= 25: level = 0
    elif temp_max >= 20: level = 1
    elif temp_max >= 15: level = 2
    else: level = 3
    # =====================================================================

    delta_temp = temp_max - ref_temp_max
    if abs(delta_temp) <= 2: context = "Similar a hoy" if mode == "Mañana" else "Similar a ayer"
    elif delta_temp > 2: context = f"{abs(delta_temp):.1f}°C más cálido que {'hoy' if mode == 'Mañana' else 'ayer'}"
    else: context = f"{abs(delta_temp):.1f}°C más frío que {'hoy' if mode == 'Mañana' else 'ayer'}"

    # Lógica de precipitación y nieve (con inferencia térmica)
    rain_prob = target_row.get('precipitation_probability', 0)
    rain_mm = target_row.get('precipitation', 0)
    snow_cm = target_row.get('snowfall', 0)
    
    if pd.isna(rain_prob): rain_prob = 0
    if pd.isna(rain_mm): rain_mm = 0
    if pd.isna(snow_cm): snow_cm = 0

    reasoning = "Según tu historial de preferencias."
    
    # Inferencia térmica: si llueve pero hace menos de 3 grados máximo, es nieve/hielo
    is_snowing = snow_cm > 0 or (rain_mm > 0 and temp_max <= 3)
    
    if is_snowing:
        display_snow = snow_cm if snow_cm > 0 else rain_mm
        reasoning = f"❄️ Alerta de nieve/hielo ({int(rain_prob)}% / {round(display_snow, 1)} cm est.). ¡Abrígate muy bien y usa calzado antideslizante!"
    elif rain_prob > 0 or rain_mm > 0:
        reasoning = f"⚠️ Alerta de lluvia ({int(rain_prob)}% / {round(rain_mm, 1)} mm). Mantén el nivel de ropa recomendado, pero suma un impermeable."

    return {
        "mode": mode, "level": level, "level_text": CLOTHING_LEVELS.get(level, f"Nivel {level}"),
        "context": context, "temp_max": temp_max, "temp_min": temp_min, "reasoning": reasoning
    }

def get_weekly_recommendations(weather_df):
    weekly_data = []
    if weather_df.empty: return weekly_data
    forecast_df = weather_df.iloc[1:8] 
    
    for idx, row in forecast_df.iterrows():
        fecha = row['date']
        if idx == 1: nombre_dia = "Hoy"
        elif idx == 2: nombre_dia = "Mañana"
        else:
            dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias_es[fecha.weekday()]

        temp_max = round(row['temp_max'], 1)
        temp_min = round(row['temp_min'], 1)

        # =====================================================================
        # PREDICCIÓN KNN PARA LA SEMANA
        # =====================================================================
        if temp_max >= 25: level = 0
        elif temp_max >= 20: level = 1
        elif temp_max >= 15: level = 2
        else: level = 3
        # =====================================================================

        weekly_data.append({
            "dia": nombre_dia, "fecha": fecha.strftime("%d/%m"),
            "temp_max": temp_max, "temp_min": temp_min,
            "level": level, "level_text": CLOTHING_LEVELS.get(level, f"Nivel {level}")
        })
    return weekly_data