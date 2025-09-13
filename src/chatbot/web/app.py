"""
Aplicación web para el chatbot MAC-GPT.
"""
import os
import threading
from flask import Flask, render_template, request, jsonify
from src.chatbot import ask_mac_gpt, configure_google_api
from pipeline.extract import extract_data
from pipeline.transform import transform_data
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar la aplicación Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'mac-gpt-secret-key')

# Configurar la API de Google
api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
api_configured = False
if api_key:
    api_configured = configure_google_api(api_key)

@app.route('/')
def index():
    """
    Renderiza la página principal del chatbot.
    """
    return render_template('index.html', api_configured=api_configured)

@app.route('/api/chat', methods=['POST'])
def chat():
    """
    Endpoint para procesar mensajes del chat.
    """
    if not api_configured:
        return jsonify({
            'success': False,
            'message': 'La API de Google no está configurada correctamente. Por favor, comprueba tu API key.'
        }), 500

    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({
            'success': False,
            'message': 'No se proporcionó ninguna pregunta.'
        }), 400

    try:
        # Obtener respuesta del chatbot
        response = ask_mac_gpt(message)
        return jsonify({
            'success': True,
            'message': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error al procesar la pregunta: {str(e)}'
        }), 500

@app.route('/api/status', methods=['GET'])
def status():
    """
    Endpoint para verificar el estado de la API.
    """
    import glob
    data_exists = len(glob.glob('data/pickles/*.pkl')) > 0
    
    return jsonify({
        'api_configured': api_configured,
        'data_exists': data_exists,
        'status': 'ready' if (api_configured and data_exists) else 'not_configured'
    })

# Variable global para tracking del pipeline
pipeline_running = False

@app.route('/api/admin/update-data', methods=['POST'])
def update_data():
    """
    Endpoint para ejecutar el pipeline ETL manualmente.
    Solo para administradores - requiere clave especial.
    """
    global pipeline_running
    
    if pipeline_running:
        return jsonify({
            'success': False,
            'message': 'El pipeline ya está ejecutándose. Por favor espera.'
        }), 409
    
    # Verificar clave de administrador
    admin_key = request.json.get('admin_key') if request.json else None
    expected_key = os.getenv('ADMIN_KEY', 'admin123')  # Cambiar en producción
    
    if admin_key != expected_key:
        return jsonify({
            'success': False,
            'message': 'Clave de administrador incorrecta.'
        }), 403
    
    def run_pipeline():
        global pipeline_running
        try:
            pipeline_running = True
            print("🚀 Iniciando pipeline ETL...")
            
            # Ejecutar extracción
            extract_results = extract_data(
                download_pdfs=True,
                extract_pdf_content=True,
                output_filename="plan_estudios_mac"
            )
            
            # Ejecutar transformación si hay datos
            if extract_results.get("saved_files") and extract_results["saved_files"].get("pickle"):
                transform_data(
                    input_file=extract_results["saved_files"]["pickle"],
                    add_embeddings=True,
                    output_filename="plan_estudios_mac_processed"
                )
            
            print("✅ Pipeline ETL completado exitosamente")
            
        except Exception as e:
            print(f"❌ Error en pipeline ETL: {e}")
        finally:
            pipeline_running = False
    
    # Ejecutar en hilo separado para no bloquear la respuesta
    thread = threading.Thread(target=run_pipeline)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'message': 'Pipeline ETL iniciado. Los datos se actualizarán en unos minutos.'
    })

@app.route('/api/admin/pipeline-status', methods=['GET'])
def pipeline_status():
    """
    Verificar si el pipeline está ejecutándose.
    """
    return jsonify({
        'running': pipeline_running
    })

# Auto-inicialización de datos (opcional)
def auto_initialize_data():
    """
    Ejecuta el pipeline automáticamente si no hay datos.
    Solo en producción.
    """
    import glob
    
    # Solo en producción y si no hay datos
    if os.getenv('FLASK_ENV') == 'production':
        data_exists = len(glob.glob('data/pickles/*.pkl')) > 0
        
        if not data_exists:
            print("🔄 Auto-inicializando datos...")
            def run_initial_pipeline():
                try:
                    extract_results = extract_data(
                        download_pdfs=True,
                        extract_pdf_content=True,
                        output_filename="plan_estudios_mac"
                    )
                    
                    if extract_results.get("saved_files") and extract_results["saved_files"].get("pickle"):
                        transform_data(
                            input_file=extract_results["saved_files"]["pickle"],
                            add_embeddings=True,
                            output_filename="plan_estudios_mac_processed"
                        )
                    
                    print("✅ Auto-inicialización completada")
                except Exception as e:
                    print(f"❌ Error en auto-inicialización: {e}")
            
            # Ejecutar en hilo separado
            thread = threading.Thread(target=run_initial_pipeline)
            thread.daemon = True
            thread.start()

if __name__ == '__main__':
    # Auto-inicializar datos si es necesario
    auto_initialize_data()
    
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug) 