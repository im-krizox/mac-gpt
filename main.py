"""
Script principal para orquestar el proceso ETL completo:
1. Extracción (E): Descarga PDFs y extrae su contenido
2. Transformación (T): Procesa los datos y enriquece con embeddings
3. Carga (L): Guarda los datos en formato adecuado para su consumo
4. Chatbot: Interfaz de preguntas y respuestas usando la información procesada
"""
import os
import sys
import argparse
from typing import Dict, Any

# Asegurar que se pueden importar los módulos del proyecto
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import settings
from pipeline.extract import extract_data
from pipeline.transform import transform_data
# Importamos el módulo del chatbot
from src.chatbot.cli import main as run_chatbot
# Importamos para la interfaz web
try:
    from src.chatbot.web.app import app as web_app
    web_interface_available = True
except ImportError:
    web_interface_available = False


def run_etl_pipeline(
    download_pdfs: bool = True,
    extract_pdf_content: bool = True,
    add_embeddings: bool = True,
    pdf_dir: str = None,
    output_name: str = "plan_estudios_mac"
) -> Dict[str, Any]:
    """
    Ejecuta el proceso ETL completo
    
    Args:
        download_pdfs (bool): Si es True, descarga los PDFs del sitio web
        extract_pdf_content (bool): Si es True, extrae información de los PDFs
        add_embeddings (bool): Si es True, agrega embeddings a los datos
        pdf_dir (str): Directorio donde se encuentran/guardarán los PDFs
        output_name (str): Nombre base para los archivos de salida
        
    Returns:
        Dict[str, Any]: Resultados del proceso ETL
    """
    results = {
        "extract": None,
        "transform": None
    }
    
    # Fase de extracción
    print("\n" + "=" * 70)
    print("FASE DE EXTRACCIÓN".center(70))
    print("=" * 70)
    
    extract_results = extract_data(
        download_pdfs=download_pdfs,
        extract_pdf_content=extract_pdf_content,
        pdf_dir=pdf_dir,
        output_filename=output_name
    )
    results["extract"] = extract_results
    
    # Si no hay datos extraídos y no se realizó la extracción, terminar aquí
    if not extract_results.get("data_extracted") and extract_pdf_content:
        print("No se obtuvieron datos en la fase de extracción. ETL finalizado.")
        return results
    
    # Fase de transformación
    print("\n" + "=" * 70)
    print("FASE DE TRANSFORMACIÓN".center(70))
    print("=" * 70)
    
    # Determinar el archivo de entrada para la transformación
    if extract_results.get("saved_files") and extract_results["saved_files"].get("pickle"):
        input_file = extract_results["saved_files"]["pickle"]
    elif extract_pdf_content:
        print("No se encontró un archivo pickle para transformar. Fase de transformación omitida.")
        return results
    else:
        # Si no se realizó extracción, buscar el archivo pickle por defecto
        default_pickle = os.path.join(settings.PICKLES_DIR, f"{output_name}.pkl")
        if os.path.exists(default_pickle):
            input_file = default_pickle
        else:
            print(f"No se encontró el archivo {default_pickle}. Fase de transformación omitida.")
            return results
    
    transform_results = transform_data(
        input_file=input_file,
        add_embeddings=add_embeddings,
        output_filename=f"{output_name}_processed"
    )
    results["transform"] = transform_results
    
    # Resumen final
    print("\n" + "=" * 70)
    print("RESUMEN DEL PROCESO ETL".center(70))
    print("=" * 70)
    
    if download_pdfs and extract_results.get("pdfs_downloaded"):
        total_pdfs = sum(len(files) for files in extract_results["pdfs_downloaded"].values())
        print(f"PDFs descargados: {total_pdfs}")
    
    if extract_pdf_content and extract_results.get("data_extracted"):
        print(f"Registros extraídos: {len(extract_results['data_extracted'])}")
    
    if transform_results and transform_results.get("data_transformed"):
        print(f"Registros transformados: {transform_results['data_transformed']['records']}")
        if "embeddings" in transform_results["data_transformed"]["columns"]:
            print("Se agregaron embeddings a los datos")
    
    print("\nArchivos generados:")
    if extract_results.get("saved_files"):
        for fmt, path in extract_results["saved_files"].items():
            print(f"  - Extracción ({fmt}): {path}")
    
    if transform_results and transform_results.get("saved_files"):
        for fmt, path in transform_results["saved_files"].items():
            print(f"  - Transformación ({fmt}): {path}")
    
    print("\n¡Proceso ETL completado exitosamente!")
    return results


def run_web_interface(port=5000, debug=False):
    """
    Ejecuta la interfaz web del chatbot
    
    Args:
        port (int): Puerto en el que se ejecutará el servidor
        debug (bool): Modo de depuración
    """
    if not web_interface_available:
        print("ERROR: No se pudo iniciar la interfaz web. Asegúrate de tener Flask instalado.")
        print("  pip install flask")
        return 1
    
    try:
        print("\n" + "=" * 70)
        print("INICIANDO INTERFAZ WEB DE MAC-GPT".center(70))
        print("=" * 70)
        print(f"\nServidor web iniciado en el puerto {port}")
        print(f"Accede a la interfaz en: http://localhost:{port}")
        print("Presiona Ctrl+C para detener el servidor.")
        
        web_app.run(host='0.0.0.0', port=port, debug=debug)
        return 0
    except KeyboardInterrupt:
        print("\nServidor web detenido por el usuario.")
        return 0
    except Exception as e:
        print(f"\nERROR: No se pudo iniciar el servidor web: {e}")
        return 1


def main():
    """Función principal para ejecutar el script desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Ejecutar el proceso ETL completo o el chatbot')
    
    parser.add_argument('--skip-download', action='store_true',
                       help='Omitir la descarga de PDFs y usar los existentes')
    
    parser.add_argument('--skip-extraction', action='store_true',
                       help='Omitir la extracción de datos de los PDFs')
    
    parser.add_argument('--skip-embeddings', action='store_true',
                       help='No generar embeddings para los datos')
    
    parser.add_argument('--pdf-dir', type=str, default=None,
                       help=f'Directorio donde se encuentran o guardarán los PDFs (default: {settings.PDF_DIR})')
    
    parser.add_argument('--output-name', type=str, default="plan_estudios_mac",
                       help='Nombre base para los archivos de salida (default: plan_estudios_mac)')
    
    parser.add_argument('--chatbot', action='store_true',
                       help='Ejecutar el chatbot en lugar del proceso ETL')
    
    parser.add_argument('--web', action='store_true',
                       help='Ejecutar la interfaz web del chatbot')
    
    parser.add_argument('--port', type=int, default=5000,
                       help='Puerto para el servidor web (default: 5000)')
    
    parser.add_argument('--debug', action='store_true',
                       help='Ejecutar el servidor web en modo de depuración')
    
    args = parser.parse_args()
    
    if args.web:
        # Ejecutar la interfaz web
        return run_web_interface(port=args.port, debug=args.debug)
    elif args.chatbot:
        # Ejecutar el chatbot en línea de comandos
        print("\n" + "=" * 70)
        print("INICIANDO CHATBOT MAC-GPT (CLI)".center(70))
        print("=" * 70)
        return run_chatbot()
    else:
        # Ejecutar el pipeline ETL con los argumentos especificados
        run_etl_pipeline(
            download_pdfs=not args.skip_download,
            extract_pdf_content=not args.skip_extraction,
            add_embeddings=not args.skip_embeddings,
            pdf_dir=args.pdf_dir,
            output_name=args.output_name
        )
    return 0


if __name__ == "__main__":
    sys.exit(main()) 