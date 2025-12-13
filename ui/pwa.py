import streamlit as st
import json
import base64

def inject_pwa_metadata():
    """
    Inyecta las metaetiquetas y el manifiesto PWA en el header de la app.
    Usa el truco de Base64 para evitar tener que configurar un servidor de estáticos.
    """
    
    # 1. Definición del Manifiesto (Configuración de la App)
    # NOTA: Cambia 'src' por la URL de tu propio icono si lo subes a Supabase o GitHub.
    # Por ahora usaremos un icono de clima genérico de alta calidad.
    APP_ICON_URL = "https://cdn-icons-png.flaticon.com/512/4052/4052984.png"
    
    manifest = {
        "name": "WeatherWear",
        "short_name": "IsiWear",
        "description": "Tu asistente de vestuario inteligente",
        "start_url": "/",
        "display": "standalone", # Esto quita la barra del navegador
        "background_color": "#0e1117", # Color de fondo Streamlit Dark
        "theme_color": "#0e1117",      # Color de la barra de estado móvil
        "icons": [
            {
                "src": APP_ICON_URL,
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": APP_ICON_URL,
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }

    # 2. Convertir Manifiesto a Data URI (Base64)
    manifest_json = json.dumps(manifest)
    b64_manifest = base64.b64encode(manifest_json.encode()).decode()
    manifest_href = f"data:application/manifest+json;base64,{b64_manifest}"

    # 3. HTML para inyectar en el <head>
    # Incluye soporte especial para iOS (Apple no lee el manifest igual que Android)
    pwa_html = f"""
        <link rel="manifest" href="{manifest_href}" />
        <meta name="theme-color" content="#0e1117" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="apple-touch-icon" href="{APP_ICON_URL}" />
        <style>
            /* Opcional: Ajustes CSS para que se sienta más 'app' */
            header[data-testid="stHeader"] {{ visibility: hidden; }} /* Oculta el header de Streamlit */
            .main {{ padding-top: 2rem; }}
        </style>
    """

    # 4. Inyección Insegura (Necesaria para esto)
    st.markdown(pwa_html, unsafe_allow_html=True)