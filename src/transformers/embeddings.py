"""
Módulo para la generación de embeddings utilizando modelos de Google Generative AI
"""
import os
from typing import List, Dict, Any, Optional, Callable
import pandas as pd
import google.generativeai as genai

from config import settings


# Variables globales para seguimiento del estado de la API
API_KEY_CONFIGURED = False
EMBEDDING_MODEL_NAME_CACHE = None


def configure_gemini_api(api_key: Optional[str] = None) -> bool:
    """
    Configura la API de Google Generative AI para embeddings.

    Args:
        api_key (Optional[str]): La API key para Google Generative AI.
                                 Si es None, intenta obtenerla de variables de entorno.

    Returns:
        bool: True si la API fue configurada exitosamente o ya estaba configurada, False en caso contrario.
    """
    global API_KEY_CONFIGURED
    
    if API_KEY_CONFIGURED:
        return True

    effective_api_key = api_key
    if not effective_api_key:
        effective_api_key = os.getenv("GEMINI_API_KEY")
        if not effective_api_key:
            print("Error: API Key no proporcionada y no se encontró en variables de entorno.")
            return False

    try:
        genai.configure(api_key=effective_api_key)
        API_KEY_CONFIGURED = True
        print("API de Google Generative AI configurada exitosamente.")
        return True
    except Exception as e:
        print(f"Error configurando la API de Google Generative AI: {e}")
        API_KEY_CONFIGURED = False
        return False


def _is_model_available(model_name: str = None) -> bool:
    """
    Verifica si el modelo de embeddings especificado está disponible.
    
    Args:
        model_name (str): Nombre del modelo a verificar
        
    Returns:
        bool: True si el modelo está disponible, False en caso contrario
    """
    if model_name is None:
        model_name = settings.DEFAULT_EMBEDDING_MODEL
        
    if not API_KEY_CONFIGURED:
        print("No se puede verificar disponibilidad del modelo: API no configurada.")
        return False
        
    try:
        genai.get_model(model_name)
        global EMBEDDING_MODEL_NAME_CACHE
        EMBEDDING_MODEL_NAME_CACHE = model_name
        return True
    except Exception as e:
        print(f"Error al acceder al modelo de embeddings '{model_name}': {e}")
        return False


def default_row_dict_to_string_formatter(row_dict: Dict[str, Any]) -> str:
    """
    Formateador por defecto para convertir un diccionario de fila a string.
    Formato: "key1: value1; key2: value2; ..."
    Filtra elementos donde el valor es None.

    Args:
        row_dict (Dict[str, Any]): El diccionario que representa una fila.

    Returns:
        str: Una representación en formato string del diccionario.
    """
    return "; ".join(
        [f"{str(key)}: {str(value)}" for key, value in row_dict.items() if value is not None]
    )


def get_embeddings_batch(
    texts: List[str],
    model_name: str = None,
    task_type: str = "RETRIEVAL_DOCUMENT",
    dimensionality: Optional[int] = None
) -> List[Optional[List[float]]]:
    """
    Genera embeddings para un lote de textos.
    
    Args:
        texts (List[str]): Lista de textos para generar embeddings
        model_name (str): Nombre del modelo a utilizar
        task_type (str): Tipo de tarea para el modelo de embeddings
        dimensionality (Optional[int]): Dimensionalidad deseada para modelos compatibles
        
    Returns:
        List[Optional[List[float]]]: Lista de embeddings generados
    """
    if model_name is None:
        model_name = settings.DEFAULT_EMBEDDING_MODEL
        
    if not API_KEY_CONFIGURED:
        print("Error: API de Google Generative AI no configurada para get_embeddings_batch.")
        return [None] * len(texts) if texts else []
        
    if not texts:
        return []
        
    try:
        request_args = {
            "model": model_name,
            "content": texts,
            "task_type": task_type
        }
        
        # Los modelos text-embedding-004 y más recientes soportan output_dimensionality
        if dimensionality is not None and ("embedding-004" in model_name or "embedding-gecko" in model_name):
            request_args["output_dimensionality"] = dimensionality

        response = genai.embed_content(**request_args)
        return response['embedding']
    except Exception as e:
        print(f"Error generando embeddings por lotes: {e}")
        return [None] * len(texts)


def add_embeddings_from_dict_rows(
    df: pd.DataFrame,
    columns_for_dict: Optional[List[str]] = None,
    new_embedding_column_name: str = "embeddings",
    embedding_model_name: str = None,
    task_type: str = "RETRIEVAL_DOCUMENT",
    output_dimensionality: Optional[int] = None,
    row_formatter: Callable[[Dict[str, Any]], str] = default_row_dict_to_string_formatter
) -> pd.DataFrame:
    """
    Agrega una nueva columna con embeddings de texto a un DataFrame de pandas.

    El texto para embeddings se crea primero formando un diccionario a partir
    de las columnas especificadas en 'columns_for_dict' para cada fila (o todas las
    columnas si es None), y luego convirtiendo este diccionario a un string usando
    el 'row_formatter'.

    Args:
        df (pd.DataFrame): El DataFrame de entrada.
        columns_for_dict (Optional[List[str]]): Lista de nombres de columnas en 'df'
            a incluir en el diccionario para cada fila. Si None o vacía,
            se usarán todas las columnas del DataFrame.
        new_embedding_column_name (str): Nombre para la nueva columna que almacenará
                                         los embeddings generados.
        embedding_model_name (str): Nombre del modelo de embeddings de Google Generative AI.
        task_type (str): Tipo de tarea para el modelo de embeddings.
        output_dimensionality (Optional[int]): Dimensionalidad de salida deseada para modelos compatibles.
                                               Si es None, se usa el valor por defecto del modelo.
        row_formatter (Callable[[Dict[str, Any]], str]): Función que toma un diccionario
            (representando una fila) y devuelve un string a ser embebido.

    Returns:
        pd.DataFrame: El DataFrame con una columna adicional conteniendo los embeddings.
    """
    if embedding_model_name is None:
        embedding_model_name = settings.DEFAULT_EMBEDDING_MODEL
        
    # Configurar API si es necesario
    if not API_KEY_CONFIGURED:
        print("API no configurada. Intentando configurar con variables de entorno.")
        if not configure_gemini_api():
            print("No se pudo configurar la API. No se pueden generar embeddings.")
            df[new_embedding_column_name] = None
            return df

    # Verificar disponibilidad del modelo
    if not _is_model_available(embedding_model_name):
        print(f"No se pudo acceder al modelo de embeddings: {embedding_model_name}. No se puede continuar.")
        df[new_embedding_column_name] = None
        return df

    # Verificar si el DataFrame está vacío
    if df.empty:
        print("El DataFrame de entrada está vacío.")
        df[new_embedding_column_name] = []
        return df

    # Determinar columnas a utilizar
    actual_columns_for_dict: List[str]
    if columns_for_dict is None or not columns_for_dict:
        actual_columns_for_dict = df.columns.tolist()
        print("No se especificaron columnas, usando todas las columnas del DataFrame.")
    else:
        # Comprobar si todas las columnas existen
        missing_cols = [col for col in columns_for_dict if col not in df.columns]
        if missing_cols:
            print(f"Error: Las siguientes columnas no están en el DataFrame: {missing_cols}")
            df[new_embedding_column_name] = None
            return df
        actual_columns_for_dict = columns_for_dict

    # Preparar los textos para embedding
    texts_for_embedding: List[str] = []
    for _, row in df.iterrows():
        row_dict_content = row[actual_columns_for_dict].to_dict()
        formatted_string = row_formatter(row_dict_content)
        texts_for_embedding.append(formatted_string)

    if not texts_for_embedding:
        print("No hay datos de texto para generar embeddings después de formatear las filas.")
        df[new_embedding_column_name] = None
        return df

    # Generar embeddings
    print(f"Generando embeddings para {len(texts_for_embedding)} filas formateadas usando {embedding_model_name}...")
    embeddings_list = get_embeddings_batch(
        texts_for_embedding,
        model_name=embedding_model_name,
        task_type=task_type,
        dimensionality=output_dimensionality
    )
    
    # Asignar embeddings al DataFrame
    df[new_embedding_column_name] = embeddings_list

    # Reportar resultados
    successful_embeddings = sum(1 for emb in embeddings_list if emb is not None)
    print(f"Se generaron exitosamente {successful_embeddings}/{len(texts_for_embedding)} embeddings.")
    if successful_embeddings < len(texts_for_embedding):
        print("Algunos embeddings no pudieron ser generados (marcados como None en la columna).")
    
    return df 