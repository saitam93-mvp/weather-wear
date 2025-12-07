import requests
import pandas as pd
from config import settings

def get_weather_forecast():
    """
    Obtiene:
    1. Clima observado de AYER (para comparación).
    2. Pronóstico de HOY y MAÑANA.
    
    Retorna un DataFrame limpio con fechas e índices.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    
    params = {
        "latitude": settings.LATITUDE,
        "longitude": settings.LONGITUDE,
        "daily": [
            "temperature_2m_max", 
            "temperature_2m_min", 
            "precipitation_sum", 
            "precipitation_probability_max"
        ],
        "timezone": settings.TIMEZONE,
        "past_days": 1,    # Traer ayer
        "forecast_days": 2 # Traer hoy y mañana
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        # Convertir a DataFrame para fácil manipulación
        daily_data = data.get("daily", {})
        df = pd.DataFrame(daily_data)
        
        # Renombrar columnas para consistencia interna
        df = df.rename(columns={
            "time": "date",
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "precipitation_sum": "rain_mm",
            "precipitation_probability_max": "rain_prob"
        })
        
        return df
        
    except Exception as e:
        print(f"Error fetching weather: {e}")
        return pd.DataFrame() # Retornar vacío en caso de error