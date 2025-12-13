import os

# Configuración
OUTPUT_FILE = "proyecto_completo.txt"
# Carpetas y archivos a ignorar (ajusta según necesites)
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', '.streamlit', '.idea', '.vscode'}
IGNORE_FILES = {'bundle_code.py', 'poetry.lock', 'package-lock.json', '.DS_Store', OUTPUT_FILE}
EXTENSIONS = {'.py', '.md', '.txt', '.env.example', '.toml', '.yml', '.yaml', 'Dockerfile'}

def main():
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as outfile:
        outfile.write(f"# CONTEXTO DEL PROYECTO WEATHERWEAR\n")
        outfile.write(f"# Generado automáticamente\n\n")

        # Recorrer el directorio actual
        for root, dirs, files in os.walk("."):
            # Filtrar carpetas ignoradas
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for file in files:
                if file in IGNORE_FILES:
                    continue
                
                # Filtrar por extensión (opcional, pero recomendado para no subir binarios)
                _, ext = os.path.splitext(file)
                if ext not in EXTENSIONS and file != 'Dockerfile':
                    continue

                file_path = os.path.join(root, file)
                
                # Escribir cabecera y contenido
                outfile.write(f"\n{'='*50}\n")
                outfile.write(f"FILE: {file_path}\n")
                outfile.write(f"{'='*50}\n")
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        outfile.write(infile.read())
                except Exception as e:
                    outfile.write(f"[Error leyendo archivo: {e}]\n")

    print(f"✅ Éxito! Todo el código ha sido guardado en: {OUTPUT_FILE}")
    print("Ahora sube ese archivo al chat.")

if __name__ == "__main__":
    main()