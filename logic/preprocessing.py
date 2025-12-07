import pandas as pd
import joblib
import os
from sklearn.preprocessing import MinMaxScaler

# Rutas de persistencia
MODEL_DIR = "models"
SCALER_PATH = os.path.join(MODEL_DIR, "scaler.pkl")

def get_scaler():
    """Carga el scaler existente o retorna None si no existe."""
    if os.path.exists(SCALER_PATH):
        return joblib.load(SCALER_PATH)
    return None

def save_scaler(scaler):
    """Guarda el scaler entrenado."""
    if not os.path.exists(MODEL_DIR):
        os.makedirs(MODEL_DIR)
    joblib.dump(scaler, SCALER_PATH)

def prepare_features(df_or_dict, is_training=False):
    """
    Convierte datos crudos (temp_max, temp_min) en vector normalizado para el modelo.
    
    Args:
        df_or_dict: DataFrame o Diccionario con 'temp_max', 'temp_min'.
        is_training: Si es True, entrena (fit) el scaler. Si es False, solo transforma.
    
    Returns:
        X_scaled: Datos listos para el KNN.
    """
    # Asegurar formato DataFrame
    if isinstance(df_or_dict, dict):
        df = pd.DataFrame([df_or_dict])
    else:
        df = df_or_dict.copy()

    # Seleccionar features relevantes para sensación térmica
    features = df[['temp_max', 'temp_min']]

    if is_training:
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(features)
        save_scaler(scaler)
    else:
        scaler = get_scaler()
        if not scaler:
            raise FileNotFoundError("Scaler no encontrado. Entrena el modelo primero.")
        X_scaled = scaler.transform(features)
        
    return X_scaled