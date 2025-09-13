"""
Módulo para manejo de archivos y persistencia de datos
"""
import os
import json
import pickle
from typing import Dict, List, Any, Optional, Union
import pandas as pd

from config import settings


def save_dataframe_to_pickle(df: pd.DataFrame, filename: str, directory: Optional[str] = None) -> str:
    """
    Guarda un DataFrame en formato pickle
    
    Args:
        df (pd.DataFrame): DataFrame a guardar
        filename (str): Nombre del archivo (sin extensión)
        directory (Optional[str]): Directorio donde guardar, si es None se usa settings.PICKLES_DIR
        
    Returns:
        str: Ruta completa al archivo guardado
    """
    if directory is None:
        directory = settings.PICKLES_DIR
    
    # Crear directorio si no existe
    os.makedirs(directory, exist_ok=True)
    
    # Asegurar que el nombre del archivo tiene extensión .pkl
    if not filename.lower().endswith('.pkl'):
        filename += '.pkl'
        
    # Ruta completa al archivo
    full_path = os.path.join(directory, filename)
    
    try:
        df.to_pickle(full_path)
        print(f"DataFrame guardado exitosamente en {full_path}")
        return full_path
    except Exception as e:
        print(f"Error al guardar DataFrame como pickle: {e}")
        raise


def load_dataframe_from_pickle(filepath: str) -> pd.DataFrame:
    """
    Carga un DataFrame desde un archivo pickle
    
    Args:
        filepath (str): Ruta completa al archivo pickle
        
    Returns:
        pd.DataFrame: DataFrame cargado desde el archivo
    """
    try:
        df = pd.read_pickle(filepath)
        print(f"DataFrame cargado exitosamente desde {filepath}")
        return df
    except Exception as e:
        print(f"Error al cargar DataFrame desde pickle {filepath}: {e}")
        raise


def save_to_json(data: Union[Dict, List], filename: str, directory: Optional[str] = None) -> str:
    """
    Guarda datos en formato JSON
    
    Args:
        data (Union[Dict, List]): Datos a guardar en formato JSON
        filename (str): Nombre del archivo (sin extensión)
        directory (Optional[str]): Directorio donde guardar, si es None se usa settings.OUTPUT_DIR
        
    Returns:
        str: Ruta completa al archivo guardado
    """
    if directory is None:
        directory = settings.OUTPUT_DIR
    
    # Crear directorio si no existe
    os.makedirs(directory, exist_ok=True)
    
    # Asegurar que el nombre del archivo tiene extensión .json
    if not filename.lower().endswith('.json'):
        filename += '.json'
        
    # Ruta completa al archivo
    full_path = os.path.join(directory, filename)
    
    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Datos guardados exitosamente en {full_path}")
        return full_path
    except Exception as e:
        print(f"Error al guardar datos como JSON: {e}")
        raise


def load_from_json(filepath: str) -> Union[Dict, List]:
    """
    Carga datos desde un archivo JSON
    
    Args:
        filepath (str): Ruta completa al archivo JSON
        
    Returns:
        Union[Dict, List]: Datos cargados desde el archivo
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Datos cargados exitosamente desde {filepath}")
        return data
    except Exception as e:
        print(f"Error al cargar datos desde JSON {filepath}: {e}")
        raise


def save_dataframe_to_csv(df: pd.DataFrame, filename: str, directory: Optional[str] = None, **kwargs) -> str:
    """
    Guarda un DataFrame en formato CSV
    
    Args:
        df (pd.DataFrame): DataFrame a guardar
        filename (str): Nombre del archivo (sin extensión)
        directory (Optional[str]): Directorio donde guardar, si es None se usa settings.OUTPUT_DIR
        **kwargs: Argumentos adicionales para pandas.DataFrame.to_csv()
        
    Returns:
        str: Ruta completa al archivo guardado
    """
    if directory is None:
        directory = settings.OUTPUT_DIR
    
    # Crear directorio si no existe
    os.makedirs(directory, exist_ok=True)
    
    # Asegurar que el nombre del archivo tiene extensión .csv
    if not filename.lower().endswith('.csv'):
        filename += '.csv'
        
    # Ruta completa al archivo
    full_path = os.path.join(directory, filename)
    
    try:
        # Establecer valores predeterminados para to_csv si no se proporcionan
        default_kwargs = {
            'index': False,
            'encoding': 'utf-8'
        }
        
        # Actualizar con los kwargs proporcionados
        for k, v in kwargs.items():
            default_kwargs[k] = v
            
        df.to_csv(full_path, **default_kwargs)
        print(f"DataFrame guardado exitosamente en {full_path}")
        return full_path
    except Exception as e:
        print(f"Error al guardar DataFrame como CSV: {e}")
        raise


def load_dataframe_from_csv(filepath: str, **kwargs) -> pd.DataFrame:
    """
    Carga un DataFrame desde un archivo CSV
    
    Args:
        filepath (str): Ruta completa al archivo CSV
        **kwargs: Argumentos adicionales para pandas.read_csv()
        
    Returns:
        pd.DataFrame: DataFrame cargado desde el archivo
    """
    try:
        # Establecer valores predeterminados para read_csv si no se proporcionan
        default_kwargs = {
            'encoding': 'utf-8'
        }
        
        # Actualizar con los kwargs proporcionados
        for k, v in kwargs.items():
            default_kwargs[k] = v
            
        df = pd.read_csv(filepath, **default_kwargs)
        print(f"DataFrame cargado exitosamente desde {filepath}")
        return df
    except Exception as e:
        print(f"Error al cargar DataFrame desde CSV {filepath}: {e}")
        raise


def save_extracted_data(data: List[Dict[str, Any]], base_filename: str = "resultados_extraccion") -> Dict[str, str]:
    """
    Guarda los datos extraídos en varios formatos (JSON, CSV y Pickle)
    
    Args:
        data (List[Dict[str, Any]]): Datos extraídos a guardar
        base_filename (str): Nombre base para los archivos (sin extensión)
        
    Returns:
        Dict[str, str]: Diccionario con las rutas a los archivos guardados por formato
    """
    try:
        # Convertir a DataFrame
        df = pd.DataFrame(data)
        
        # Resultados de las operaciones de guardado
        saved_paths = {}
        
        # Guardar como JSON
        json_path = save_to_json(data, base_filename)
        saved_paths['json'] = json_path
        
        # Guardar como CSV
        csv_path = save_dataframe_to_csv(df, base_filename)
        saved_paths['csv'] = csv_path
        
        # Guardar como Pickle
        pickle_path = save_dataframe_to_pickle(df, base_filename)
        saved_paths['pickle'] = pickle_path
        
        print(f"\n--- Guardando Resultados ({len(data)} registros) ---")
        for fmt, path in saved_paths.items():
            print(f"Resultados guardados en {path}")
        
        return saved_paths
    except Exception as e:
        print(f"Error al guardar datos extraídos: {e}")
        raise 