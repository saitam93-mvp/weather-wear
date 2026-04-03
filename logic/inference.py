import pandas as pd
from datetime import datetime

# Ajusta esta importación según dónde tengas tu diccionario de configuración.
# Si lo tienes en el mismo archivo, puedes dejar el diccionario aquí directamente.
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
# IMPORTA AQUÍ TU MODELO KNN O LAS FUNCIONES DE LA BASE DE DATOS
# =====================================================================


def get_recommendation(weather_df):
    """Genera la recomendación principal para hoy o mañana."""
    if weather_df.empty:
        return None

    # 1. Determinar modo (después de las 18:00 muestra el clima de mañana)
    hora_actual = datetime.now().hour
    es_modo_manana = hora_actual >= 18
    
    # Índices del DataFrame: 0 = Ayer, 1 = Hoy, 2 = Mañana
    target_idx = 2 if es_modo_manana else 1
    ref_idx = 1 if es_modo_manana else 0
    
    # Validación por si el DataFrame viene más corto
    if target_idx >= len(weather_df):
        target_idx = len(weather_df) - 1
        
    target_row = weather_df.iloc[target_idx]
    ref_row = weather_df.iloc[ref_idx]

    mode = "Mañana" if es_modo_manana else "Hoy"
    
    temp_max = round(target_row['temp_max'], 1)
    temp_min = round(target_row['temp_min'], 1)
    ref_temp_max = round(ref_row['temp_max'], 1)

    # =====================================================================
    # 2. PREDICCIÓN DE LA IA (KNN)
    # Reemplaza este bloque de if/else con la llamada real a tu modelo.
    # Ejemplo: level = tu_modelo_knn.predict([[temp_max, temp_min]])[0]
    # =====================================================================
    if temp_max >= 25:
        level = 0
    elif temp_max >= 20:
        level = 1
    elif temp_max >= 15:
        level = 2
    else:
        level = 3
    # =====================================================================

    # 3. Lógica de Contexto (Delta de temperatura)
    delta_temp = temp_max - ref_temp_max
    if abs(delta_temp) <= 2:
        context = "Similar a hoy" if mode == "Mañana" else "Similar a ayer"
    elif delta_temp > 2:
        context = f"{abs(delta_temp):.1f}°C más cálido que {'hoy' if mode == 'Mañana' else 'ayer'}"
    else:
        context = f"{abs(delta_temp):.1f}°C más frío que {'hoy' if mode == 'Mañana' else 'ayer'}"

    # 4. LÓGICA DE LLUVIA (Independiente del nivel de ropa)
    rain_prob = target_row.get('precipitation_probability', 0)
    rain_mm = target_row.get('precipitation', 0)
    
    if pd.isna(rain_prob): rain_prob = 0
    if pd.isna(rain_mm): rain_mm = 0

    reasoning = "Según tu historial de preferencias."
    
    # Si hay lluvia, no tocamos la variable 'level'. Solo cambiamos la advertencia.
    if rain_prob > 0 or rain_mm > 0:
        reasoning = f"⚠️ Alerta de lluvia ({int(rain_prob)}% / {round(rain_mm, 1)} mm). Mantén el nivel de ropa recomendado, pero es imprescindible sumar un impermeable o paraguas."

    return {
        "mode": mode,
        "level": level,
        "level_text": CLOTHING_LEVELS.get(level, f"Nivel {level}"),
        "context": context,
        "temp_max": temp_max,
        "temp_min": temp_min,
        "reasoning": reasoning
    }


def get_weekly_recommendations(weather_df):
    """Genera las recomendaciones para los próximos 7 días."""
    weekly_data = []
    
    if weather_df.empty:
        return weekly_data

    # Ignoramos el índice 0 (Ayer) para el pronóstico hacia adelante
    forecast_df = weather_df.iloc[1:8] 
    
    for idx, row in forecast_df.iterrows():
        fecha = row['date']
        
        # Asignar nombre del día
        if idx == 1:
            nombre_dia = "Hoy"
        elif idx == 2:
            nombre_dia = "Mañana"
        else:
            dias_es = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            nombre_dia = dias_es[fecha.weekday()]

        temp_max = round(row['temp_max'], 1)
        temp_min = round(row['temp_min'], 1)

        # =====================================================================
        # PREDICCIÓN KNN PARA LA SEMANA
        # Reemplaza también este bloque con la llamada a tu modelo.
        # =====================================================================
        if temp_max >= 25:
            level = 0
        elif temp_max >= 20:
            level = 1
        elif temp_max >= 15:
            level = 2
        else:
            level = 3
        # =====================================================================

        rain_prob = row.get('precipitation_probability', 0)
        rain_mm = row.get('precipitation', 0)
        
        if pd.isna(rain_prob): rain_prob = 0
        if pd.isna(rain_mm): rain_mm = 0

        weekly_data.append({
            "dia": nombre_dia,
            "fecha": fecha.strftime("%d/%m"),
            "temp_max": temp_max,
            "temp_min": temp_min,
            "rain_prob": int(rain_prob),
            "rain_mm": round(rain_mm, 1),
            "level": level,
            "level_text": CLOTHING_LEVELS.get(level, f"Nivel {level}")
        })

    return weekly_data