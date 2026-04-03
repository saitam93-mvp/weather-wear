import requests
import pandas as pd
from services.location import get_current_coords

def get_weather_forecast():
    loc = get_current_coords()
    lat, lon = loc['lat'], loc['lon']
    
    # Agregamos snowfall_sum a la petición
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,snowfall_sum&timezone=auto"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status() 
        json_data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error al conectar con Open-Meteo: {e}")
        return pd.DataFrame() 
        
    daily = json_data['daily']
    
    weather_data = {
        'date': daily['time'],
        'temp_max': daily['temperature_2m_max'],
        'temp_min': daily['temperature_2m_min'],
        'precipitation': daily['precipitation_sum'],
        'precipitation_probability': daily['precipitation_probability_max'],
        'snowfall': daily['snowfall_sum'] # NUEVO: Guardamos la nieve (en cm)
    }
    
    weather_df = pd.DataFrame(weather_data)
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    
    return weather_df