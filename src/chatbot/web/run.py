"""
Script para ejecutar la aplicación web del chatbot MAC-GPT.
"""
import os
import sys

# Asegurarnos de que podemos importar desde la raíz del proyecto
root_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(root_path)

from dotenv import load_dotenv
from src.chatbot.web.app import app

# Cargar variables de entorno
load_dotenv()

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    print(f"Iniciando servidor web de MAC-GPT en el puerto {port}")
    print("Para acceder a la interfaz, abre en tu navegador: http://localhost:{port}")
    print("Presiona Ctrl+C para detener el servidor.")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nServidor detenido por el usuario.") 