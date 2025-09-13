"""
Ejemplo de cómo utilizar el chatbot MAC-GPT desde otro módulo Python.
"""

import os
import dotenv
from src.chatbot import configure_google_api, ask_mac_gpt

def main():
    """
    Ejemplo sencillo de cómo utilizar el chatbot MAC-GPT programáticamente.
    """
    # Cargar variables de entorno
    dotenv.load_dotenv()
    
    # Configurar la API de Google
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("ERROR: No se encontró la clave de API para Google Generative AI.")
        print("Configure su clave de API en una variable de entorno GEMINI_API_KEY o GOOGLE_API_KEY.")
        return 1
    
    if not configure_google_api(api_key):
        print("ERROR: No se pudo configurar la API de Google.")
        return 1
    
    # Ejemplos de preguntas y respuestas
    preguntas = [
        "¿Cuáles son las áreas de especialización de la carrera MAC?",
        "¿Quiénes son los profesores de la carrera?",
        "¿Cuál es el perfil de egreso de la carrera?"
    ]
    
    print("=== Ejemplos de uso del chatbot MAC-GPT ===\n")
    
    for i, pregunta in enumerate(preguntas, 1):
        print(f"Pregunta {i}: {pregunta}")
        respuesta = ask_mac_gpt(pregunta)
        print(f"Respuesta: {respuesta}\n")
        print("-" * 70 + "\n")
    
    print("Fin de los ejemplos.")
    return 0

if __name__ == "__main__":
    main() 