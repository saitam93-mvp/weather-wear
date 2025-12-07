import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
import joblib
import os
from logic.preprocessing import prepare_features

MODEL_PATH = os.path.join("models", "knn_model.pkl")

def train_model(data):
    """
    Entrena el modelo KNN con nuevos datos y lo guarda en disco.
    
    Args:
        data: DataFrame con columnas ['temp_max', 'temp_min', 'clothing_level']
    """
    # 1. Preprocesar Features (Scaling)
    # Importante: Al entrenar, regeneramos el scaler con los nuevos rangos de datos
    X = prepare_features(data, is_training=True)
    y = data['clothing_level']

    # 2. Configurar KNN
    # n_neighbors=3 es un buen balance para empezar con pocos datos
    n_neighbors = min(3, len(data)) 
    knn = KNeighborsClassifier(n_neighbors=n_neighbors)
    
    # 3. Entrenar
    knn.fit(X, y)

    # 4. Guardar
    joblib.dump(knn, MODEL_PATH)
    print(f"Modelo re-entrenado y guardado en {MODEL_PATH} con {len(data)} muestras.")

def load_model():
    """Carga el modelo desde disco."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None