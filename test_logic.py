from services.weather_api import get_weather_forecast
from logic.inference import get_recommendation

print("1. Obteniendo datos del clima...")
df = get_weather_forecast()

print("\n2. Consultando al oráculo (Inference)...")
rec = get_recommendation(df)

print("\nResultados:")
print(f"Modo: {rec['mode']}")
print(f"Recomendación: {rec['level_text']}")
print(f"Contexto: {rec['context']}")
print(f"Razón: {rec['reasoning']}")