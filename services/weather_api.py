import openmeteo_requests
import requests_cache
import pandas as pd  # <--- ESTA ERA LA LÍNEA QUE FALTABA
from retry_requests import retry
import streamlit as st
from services.location import get_current_coords 

# --- CONFIGURACIÓN DE CACHÉ ---
cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

def get_weather_forecast():
    """
    Obtiene el clima usando coordenadas dinámicas y estandariza los datos.
    """
    
    # 1. Obtener coordenadas (del usuario o default)
    loc = get_current_coords()
    lat = loc['lat']
    lon = loc['lon']
    
    # Debug en consola
    print(f"📡 API Clima consultando: {lat}, {lon}")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "past_days": 1,     # CRÍTICO para tener datos de "Ayer"
        "forecast_days": 3, 
        "timezone": "auto", # CRÍTICO para calcular hora local correctamente
        "daily": [
            "temperature_2m_max", 
            "temperature_2m_min",
            "temperature_2m_mean",
            "precipitation_sum",
            "precipitation_probability_max", 
            "windspeed_10m_max",
            "windspeed_10m_mean",
            "shortwave_radiation_sum",
            "weathercode"
        ],
        "hourly": ["relative_humidity_2m", "cloud_cover"],
    }

    try:
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        # --- CAPTURA DE ZONA HORARIA ---
        # Guardamos la diferencia horaria (segundos) que nos dice la API
        # Esto es vital para que logic/inference.py sepa qué hora es realmente ahí
        utc_offset = response.UtcOffsetSeconds()
        st.session_state["current_utc_offset"] = utc_offset
        
        # --- PROCESAMIENTO DAILY ---
        daily = response.Daily()
        
        daily_data = {
            "date": pd.date_range(
                start=pd.to_datetime(daily.Time(), unit="s", utc=True),
                end=pd.to_datetime(daily.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=daily.Interval()),
                inclusive="left"
            ).normalize()
        }
        
        # Mapeo directo a nombres cortos
        daily_data["temp_max"] = daily.Variables(0).ValuesAsNumpy()
        daily_data["temp_min"] = daily.Variables(1).ValuesAsNumpy()
        daily_data["temp_mean"] = daily.Variables(2).ValuesAsNumpy()
        daily_data["precipitation_sum"] = daily.Variables(3).ValuesAsNumpy()
        daily_data["precip_prob_max"] = daily.Variables(4).ValuesAsNumpy()
        daily_data["windspeed_max"] = daily.Variables(5).ValuesAsNumpy()
        daily_data["windspeed_mean"] = daily.Variables(6).ValuesAsNumpy()
        daily_data["solar_rad_sum"] = daily.Variables(7).ValuesAsNumpy()
        daily_data["weathercode"] = daily.Variables(8).ValuesAsNumpy()

        df_daily = pd.DataFrame(data=daily_data)

        # --- PROCESAMIENTO HOURLY ---
        hourly = response.Hourly()
        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left"
            )
        }
        
        hourly_data["relative_humidity_2m"] = hourly.Variables(0).ValuesAsNumpy()
        hourly_data["cloud_cover"] = hourly.Variables(1).ValuesAsNumpy()
        
        df_hourly = pd.DataFrame(data=hourly_data)
        
        # Agregación por día
        df_hourly_mean = df_hourly.set_index('date').resample('D').mean().reset_index()
        
        # Nombres simplificados
        df_hourly_mean = df_hourly_mean.rename(columns={
            "relative_humidity_2m": "humidity_mean",
            "cloud_cover": "cloud_cover_mean"
        })
        
        # Merge Final
        df_daily['date_match'] = df_daily['date'].dt.date
        df_hourly_mean['date_match'] = df_hourly_mean['date'].dt.date
        
        df_final = pd.merge(
            df_daily, 
            df_hourly_mean[['date_match', 'humidity_mean', 'cloud_cover_mean']], 
            on='date_match', 
            how='left'
        )
        
        df_final = df_final.drop(columns=['date_match'])

        # --- LIMPIEZA FINAL (Fix Decimales y Tipos) ---
        
        # 1. Convertir float32 a float estándar (Python nativo)
        cols_num = df_final.select_dtypes(include=['number']).columns
        df_final[cols_num] = df_final[cols_num].astype(float)

        # 2. Redondear SOLO TEMPERATURAS a 1 decimal
        temps = ["temp_max", "temp_min", "temp_mean"]
        for col in temps:
            if col in df_final.columns:
                df_final[col] = df_final[col].round(1)

        return df_final

    except Exception as e:
        print(f"Error API Clima: {e}")
        # Aquí fallaba antes porque 'pd' no existía
        return pd.DataFrame()