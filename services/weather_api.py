import requests
import pandas as pd
import streamlit as st
from services.location import get_current_coords

# El caché guarda la respuesta por 3600 segundos (1 hora).
# show_spinner=False evita que salga un doble spinner en la UI.
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_open_meteo_data(lat, lon):
    """Función interna cacheada que hace la petición real a la API."""
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
        'snowfall': daily['snowfall_sum'] 
    }
    
    weather_df = pd.DataFrame(weather_data)
    weather_df['date'] = pd.to_datetime(weather_df['date'])
    
    return weather_df


def get_weather_forecast():
    """Función expuesta que obtiene las coordenadas y llama a la función cacheada."""
    loc = get_current_coords()
    # Pasa las coordenadas a la función cacheada. Si cambian, Streamlit hace una nueva petición.
    return _fetch_open_meteo_data(loc['lat'], loc['lon'])