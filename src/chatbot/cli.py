"""
Interfaz de línea de comandos para interactuar con MAC-GPT.
"""

import os
import sys
import dotenv
from src.chatbot import ask_mac_gpt, configure_google_api

def main():
    # Cargar variables de entorno desde .env si existe
    dotenv.load_dotenv()
    
    # Verificar si se proporcionó una clave de API en variables de entorno
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: No se encontró la clave de API para Google Generative AI.")
        print("Configure su clave de API en una variable de entorno GEMINI_API_KEY o GOOGLE_API_KEY,")
        print("o proporcione la clave directamente como argumento de línea de comandos.")
        return 1
    
    # Inicializar el API
    if not configure_google_api(api_key):
        print("ERROR: No se pudo configurar la API de Google.")
        return 1
    
    # Modo interactivo
    print("=== MAC-GPT - Asistente Virtual de la Licenciatura en Matemáticas Aplicadas y Computación ===")
    print("Escribe 'salir', 'exit' o 'q' para terminar la sesión.")
    
    while True:
        try:
            # Solicitar pregunta al usuario
            prompt = input("\n>>> ")
            
            # Verificar si el usuario quiere salir
            if prompt.lower() in ["salir", "exit", "q"]:
                print("¡Hasta luego!")
                break
            
            if prompt.strip():
                # Enviar la pregunta al chatbot
                respuesta = ask_mac_gpt(prompt)
                print("\n" + respuesta)
            
        except KeyboardInterrupt:
            print("\n¡Hasta luego!")
            break
        except Exception as e:
            print(f"\nERROR: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 