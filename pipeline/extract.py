"""
Script para la fase de extracción del ETL
"""
import os
import sys
import argparse
from typing import List, Dict, Any, Optional

# Agregar la ruta del proyecto al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.extractors.web_scraper import get_driver, download_pdfs_by_semester
from src.extractors.pdf_extractor import process_all_pdfs
from src.loaders.file_handler import save_extracted_data


def extract_data(
    download_pdfs: bool = True,
    extract_pdf_content: bool = True,
    pdf_dir: Optional[str] = None,
    output_filename: str = "resultados_extraccion"
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Ejecuta el proceso completo de extracción:
    1. Descarga PDFs del sitio web (opcional)
    2. Extrae información de los PDFs descargados (opcional)
    
    Args:
        download_pdfs (bool): Si es True, descarga los PDFs del sitio web
        extract_pdf_content (bool): Si es True, extrae información de los PDFs
        pdf_dir (Optional[str]): Directorio donde se encuentran los PDFs o donde se descargarán
        output_filename (str): Nombre base para los archivos de salida
        
    Returns:
        Dict[str, Any]: Resultados del proceso de extracción
    """
    results = {
        "pdfs_downloaded": None,
        "data_extracted": None,
        "saved_files": None
    }
    
    # Usar el directorio de PDFs especificado o el predeterminado
    if pdf_dir is None:
        pdf_dir = settings.PDF_DIR
    
    # 1. Descargar PDFs si se solicita
    if download_pdfs:
        print("=" * 50)
        print("Iniciando descarga de PDFs...")
        pdfs_info = download_pdfs_by_semester(save_dir=pdf_dir)
        results["pdfs_downloaded"] = pdfs_info
        print(f"Descarga de PDFs completada. {sum(len(files) for files in pdfs_info.values())} archivos descargados.")
        print("=" * 50)
    
    # 2. Extraer datos de los PDFs si se solicita
    if extract_pdf_content:
        print("=" * 50)
        print("Iniciando extracción de datos de los PDFs...")
        extracted_data = process_all_pdfs(pdf_dir=pdf_dir)
        results["data_extracted"] = extracted_data
        
        # Guardar los resultados en diferentes formatos
        saved_files = save_extracted_data(extracted_data, base_filename=output_filename)
        results["saved_files"] = saved_files
        
        print(f"Extracción de datos completada. {len(extracted_data)} registros procesados.")
        print("=" * 50)
    
    return results


def main():
    """Función principal para ejecutar el script desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Ejecutar la fase de extracción del ETL')
    
    parser.add_argument('--skip-download', action='store_true',
                      help='Omitir la descarga de PDFs y usar los existentes')
    
    parser.add_argument('--skip-extraction', action='store_true',
                      help='Omitir la extracción de datos de los PDFs')
    
    parser.add_argument('--pdf-dir', type=str, default=None,
                      help=f'Directorio donde se encuentran o se guardarán los PDFs (default: {settings.PDF_DIR})')
    
    parser.add_argument('--output-name', type=str, default="resultados_extraccion",
                      help='Nombre base para los archivos de salida (default: resultados_extraccion)')
    
    args = parser.parse_args()
    
    # Ejecutar la extracción con los argumentos especificados
    results = extract_data(
        download_pdfs=not args.skip_download,
        extract_pdf_content=not args.skip_extraction,
        pdf_dir=args.pdf_dir,
        output_filename=args.output_name
    )
    
    # Mostrar resumen de resultados
    if results["pdfs_downloaded"]:
        total_pdfs = sum(len(files) for files in results["pdfs_downloaded"].values())
        print(f"Total PDFs descargados: {total_pdfs}")
        
    if results["data_extracted"]:
        print(f"Total registros extraídos: {len(results['data_extracted'])}")
        
    if results["saved_files"]:
        print("Archivos guardados:")
        for fmt, path in results["saved_files"].items():
            print(f"  - {fmt.upper()}: {path}")
    
    print("Proceso de extracción completado exitosamente.")


if __name__ == "__main__":
    main() 