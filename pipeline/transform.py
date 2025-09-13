"""
Script para la fase de transformación del ETL
"""
import os
import sys
import argparse
from typing import Dict, List, Any, Optional, Tuple

# Agregar la ruta del proyecto al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from src.transformers.embeddings import configure_gemini_api, add_embeddings_from_dict_rows
from src.loaders.file_handler import (
    load_dataframe_from_pickle,
    load_dataframe_from_csv,
    save_dataframe_to_pickle,
    save_dataframe_to_csv
)


def load_data(input_file: str) -> Tuple[Any, str]:
    """
    Carga datos desde un archivo, determinando automáticamente su formato
    
    Args:
        input_file (str): Ruta al archivo de entrada
        
    Returns:
        Tuple[Any, str]: Datos cargados y el formato del archivo
    """
    if input_file.lower().endswith('.pkl'):
        return load_dataframe_from_pickle(input_file), 'pickle'
    elif input_file.lower().endswith('.csv'):
        return load_dataframe_from_csv(input_file), 'csv'
    else:
        raise ValueError(f"Formato de archivo no soportado: {input_file}. Use .pkl o .csv")


def transform_data(
    input_file: str,
    add_embeddings: bool = True,
    text_columns: Optional[List[str]] = None,
    output_filename: Optional[str] = None,
    output_format: str = 'both'
) -> Dict[str, Any]:
    """
    Ejecuta el proceso de transformación:
    1. Carga los datos desde el archivo especificado
    2. Aplica transformaciones (por ejemplo, generación de embeddings)
    3. Guarda los resultados en el formato especificado
    
    Args:
        input_file (str): Ruta al archivo de entrada con datos a transformar
        add_embeddings (bool): Si es True, agrega embeddings a los datos
        text_columns (Optional[List[str]]): Columnas a usar para generar embeddings
                                           Si es None, usa columnas predeterminadas
        output_filename (Optional[str]): Nombre base para el archivo de salida
                                        Si es None, usa el nombre del archivo de entrada
                                        con un sufijo '_transformed'
        output_format (str): Formato de salida ('pickle', 'csv', 'both')
        
    Returns:
        Dict[str, Any]: Resultados del proceso de transformación
    """
    results = {
        "data_loaded": None,
        "data_transformed": None,
        "saved_files": {}
    }
    
    # 1. Cargar los datos
    print("=" * 50)
    print(f"Cargando datos desde {input_file}...")
    df, input_format = load_data(input_file)
    results["data_loaded"] = {
        "file": input_file,
        "format": input_format,
        "records": len(df)
    }
    print(f"Datos cargados: {len(df)} registros")
    
    # Si no se especificaron columnas para embeddings, usar estas por defecto
    if text_columns is None:
        text_columns = [
            "nombre_materia", "semestre_txt", "modalidad", "caracter",
            "tipo", "etapa_formacion", "campo_conocimiento", "antecedente",
            "subsecuente", "objetivo_general", "indice_tematico",
            "referencias_basicas", "referencias_complementarias",
            "sugerencias_didacticas", "sugerencias_evaluacion"
        ]
        # Asegurarse de que las columnas existan en el DataFrame
        text_columns = [col for col in text_columns if col in df.columns]
        
    # 2. Transformaciones
    transformed_df = df.copy()
    
    # 2.1 Generar embeddings si se solicita
    if add_embeddings:
        print("=" * 50)
        print("Configurando API de Gemini para embeddings...")
        api_configured = configure_gemini_api()
        
        if api_configured:
            print("Generando embeddings...")
            transformed_df = add_embeddings_from_dict_rows(
                df=transformed_df,
                columns_for_dict=text_columns,
                new_embedding_column_name="embeddings",
                embedding_model_name=settings.DEFAULT_EMBEDDING_MODEL
            )
            print("Generación de embeddings completada.")
        else:
            print("No se pudo configurar la API de Gemini. No se generaron embeddings.")
    
    results["data_transformed"] = {
        "records": len(transformed_df),
        "columns": transformed_df.columns.tolist()
    }
    
    # 3. Guardar resultados
    print("=" * 50)
    print("Guardando resultados...")
    
    # Determinar nombre de archivo de salida
    if output_filename is None:
        base_name = os.path.basename(input_file)
        name_parts = os.path.splitext(base_name)
        output_filename = f"{name_parts[0]}_transformed"
    
    # Guardar en el formato especificado
    if output_format.lower() in ('pickle', 'both'):
        pickle_path = save_dataframe_to_pickle(transformed_df, output_filename)
        results["saved_files"]["pickle"] = pickle_path
    
    if output_format.lower() in ('csv', 'both'):
        csv_path = save_dataframe_to_csv(transformed_df, output_filename)
        results["saved_files"]["csv"] = csv_path
    
    print(f"Transformación completada. Resultados guardados en:")
    for fmt, path in results["saved_files"].items():
        print(f"  - {fmt.upper()}: {path}")
    print("=" * 50)
    
    return results


def main():
    """Función principal para ejecutar el script desde línea de comandos"""
    parser = argparse.ArgumentParser(description='Ejecutar la fase de transformación del ETL')
    
    parser.add_argument('--input-file', type=str, required=True,
                       help='Archivo de entrada con datos a transformar (.pkl o .csv)')
    
    parser.add_argument('--no-embeddings', action='store_true',
                       help='No generar embeddings para los datos')
    
    parser.add_argument('--text-columns', type=str, nargs='+',
                       help='Columnas a usar para generar embeddings (separadas por espacio)')
    
    parser.add_argument('--output-name', type=str, default=None,
                       help='Nombre base para el archivo de salida')
    
    parser.add_argument('--output-format', type=str, choices=['pickle', 'csv', 'both'], default='both',
                       help='Formato de salida (default: both)')
    
    args = parser.parse_args()
    
    # Ejecutar la transformación con los argumentos especificados
    results = transform_data(
        input_file=args.input_file,
        add_embeddings=not args.no_embeddings,
        text_columns=args.text_columns,
        output_filename=args.output_name,
        output_format=args.output_format
    )
    
    # Mostrar resumen de resultados
    print("\nResumen de transformación:")
    print(f"Registros de entrada: {results['data_loaded']['records']}")
    print(f"Registros transformados: {results['data_transformed']['records']}")
    
    if args.no_embeddings:
        print("No se generaron embeddings (desactivado por usuario)")
    elif "embeddings" in results["data_transformed"]["columns"]:
        print("Se generaron embeddings correctamente")
    else:
        print("No se pudieron generar embeddings")
    
    print("Archivos guardados:")
    for fmt, path in results["saved_files"].items():
        print(f"  - {fmt.upper()}: {path}")


if __name__ == "__main__":
    main() 