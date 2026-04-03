# services/weather_api.py

import requests
import pandas as pd
from services.location import get_current_coords

def get_weather_forecast():
    """Consulta la API de Open-Meteo y devuelve un DataFrame con el pronóstico diario."""
    loc = get_current_coords()
    lat, lon = loc['lat'], loc['lon']
    
    # URL ACTUALIZADA para incluir datos diarios de precipitación (mm y %)
    # daily = variables diarias: temperatura máx/mín, suma de precipitación, probabilidad máx de precipitación
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max&timezone=auto"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() # Lanza una excepción para estados de error HTTP
        json_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Open-Meteo: {e}")
        # Devolvemos un DataFrame vacío para que la app no se rompa
        return pd.DataFrame() 
        
    daily = json_data['daily']
    
    # Creamos un diccionario con los datos parseados
    weather_data = {
        'date': daily['time'],
        'temp_max': daily['temperature_2m_max'],
        'temp_min': daily['temperature_2m_min'],
        'precipitation': daily['precipitation_sum'], # Mapeamos 'precipitation_sum' a 'precipitation'
        'precipitation_probability': daily['precipitation_probability_max'] # Mapeamos 'precipitation_probability_max' a 'precipitation_probability'
    }
    
    # Creamos el DataFrame
    weather_df = pd.DataFrame(weather_data)
    
    # Convertimos la columna 'date' a objetos datetime para trabajar mejor
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    
    return weather_df