# 1. Imagen base: Python 3.10 ligero
FROM python:3.10-slim

# 2. Evitar archivos .pyc y buffer en logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Directorio de trabajo en el contenedor
WORKDIR /app

# 4. Instalar dependencias del sistema MÍNIMAS
# Quitamos 'software-properties-common' que estaba fallando
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 5. Copiar requirements e instalar dependencias de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copiar el resto del código
COPY . .

# 7. Exponer el puerto de Streamlit
EXPOSE 8501

# 8. Verificación de salud (Healthcheck)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# 9. Comando de inicio
ENTRYPOINT ["streamlit", "run", "main.py", "--server.port=8501", "--server.address=0.0.0.0"]