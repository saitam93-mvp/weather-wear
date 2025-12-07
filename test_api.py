from services.weather_api import get_weather_forecast

print("Consultando API...")
df = get_weather_forecast()
print(df)