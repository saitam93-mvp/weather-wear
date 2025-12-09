def save_daily_feedback(date_str, temp_max, temp_min, real_level):
    """Guarda el feedback del usuario (La verdad absoluta)."""
    # 1. Debug: Imprimir en la consola de la terminal
    print(f"--> INTENTANDO GUARDAR: {date_str}, Nivel: {real_level}")
    
    supabase = init_supabase()
    if not supabase: 
        print("--> ERROR: No hay conexión a Supabase")
        return False

    data = {
        "date": str(date_str),
        "temp_max": float(temp_max),
        "temp_min": float(temp_min),
        "clothing_level": int(real_level),
        # "created_at": "now()"  <-- COMENTA ESTO. Deja que Supabase ponga la fecha por defecto.
    }

    try:
        # 2. Ejecutar y capturar respuesta
        response = supabase.table("user_feedback").insert(data).execute()
        
        # 3. Debug: Ver qué respondió Supabase
        print(f"--> RESPUESTA SUPABASE: {response}")
        
        return True
    except Exception as e:
        # 4. Debug: Imprimir el error real
        print(f"--> EXCEPCIÓN AL GUARDAR: {e}")
        st.error(f"Error técnico: {e}")
        return False