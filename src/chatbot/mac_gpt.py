"""
Chatbot MAC-GPT - Asistente virtual para la Licenciatura en Matemáticas Aplicadas y Computación.

Este módulo implementa un chatbot RAG (Retrieval-Augmented Generation) que utiliza
la API de Google Generative AI (Gemini) para responder preguntas sobre la 
Licenciatura en Matemáticas Aplicadas y Computación de la FES Acatlán, UNAM.
"""

import os
import pickle
import re
import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Any, Tuple

# Attempt to import google.generativeai and scipy
try:
    import google.generativeai as genai
except ImportError:
    print("WARNING: google.generativeai library not found. Please install it: pip install google-generativeai")
    genai = None

try:
    from scipy.spatial.distance import cosine as scipy_cosine_distance
    from numpy.linalg import norm as np_linalg_norm
except ImportError:
    print("WARNING: scipy library not found. Please install it: pip install scipy")
    scipy_cosine_distance = None
    np_linalg_norm = None

# --- Global Variables & Configuration ---
GOOGLE_API_KEY_CONFIGURED = False
REPRESENTATIVE_TOPIC_EMBEDDINGS: Dict[str, np.ndarray] = {}
EMBEDDING_MODEL_NAME = "models/text-embedding-004"
GENERATIVE_MODEL_NAME = "gemini-1.5-flash-latest" 

DEFAULT_TEXT_COLUMN_NAME = "texto_original" 
FALLBACK_TEXT_COLUMN_INDEX = 0 

THEME_FILES = [
    'acerca_de.pkl',
    'convocatorias_eventos_avisos.pkl',
    'olap_plan_de_estudios.pkl',
    'perfiles.pkl',
    'profesores.pkl'
]
DEFAULT_PICKLE_DIR = "data/pickles/"

# --- Descripciones Textuales de los Temas ---
DESCRIPCIONES_TEMAS = {
    'acerca_de.pkl': "Información general sobre la Licenciatura en Matemáticas Aplicadas y Computación (MAC) de la FES Acatlán: ¿Qué es la carrera?, misión, visión, objetivos, detalles de contacto general y diversos recursos disponibles para la comunidad estudiantil y aspirantes.",
    'convocatorias_eventos_avisos.pkl': "Anuncios, noticias, comunicados importantes, convocatorias (como becas, procesos de inscripción, servicio social), detalles sobre eventos académicos (tales como seminarios, conferencias, talleres, cursos) y fechas relevantes para la comunidad de la Licenciatura MAC.",
    'olap_plan_de_estudios.pkl': "Estructura curricular y académica detallada de la Licenciatura MAC: descripción del plan de estudios, listado de asignaturas o materias por semestre, sus claves, créditos, contenidos temáticos, objetivos de aprendizaje, seriación, y la descripción de las áreas de especialización, líneas terminales u optativas disponibles.",
    'perfiles.pkl': "Perfiles relacionados con la Licenciatura MAC: describe el perfil de ingreso esperado de los aspirantes, incluyendo conocimientos y habilidades previas recomendadas, así como el perfil de egreso que tendrán los licenciados al finalizar, detallando capacidades, conocimientos y aptitudes profesionales, incluyendo posibles énfasis.",
    'profesores.pkl': "Información sobre el personal docente, catedráticos y académicos de la Licenciatura MAC: nombres de los profesores, sus áreas de conocimiento, especialización o interés, materias que imparten, datos de contacto como correo electrónico, y potencialmente un resumen de su currículum vitae, publicaciones o trayectoria."
}

# --- Prompt de Sistema para el LLM ---
SISTEMA_PROMPT_MAC = """Eres MAC-GPT, un asistente virtual experto y amigable, dedicado a proporcionar información precisa y útil sobre la Licenciatura en Matemáticas Aplicadas y Computación (MAC) de la FES Acatlán, UNAM.

**Instrucción Fundamental:**
Tu única fuente de información para responder es el 'BASE DE CONOCIMIENTOS' que se te entregará junto con la 'PREGUNTA DEL USUARIO'. NO debes usar conocimiento externo ni hacer suposiciones más allá de este contexto. No menciones "Información proporcionada", si necesitas hacerlo menciona "base de conocimientos" o "fuente de información". Tu objetivo es ayudar al usuario a encontrar respuestas precisas y relevantes.

**Directrices de Respuesta:**

1.  **Fidelidad al Contexto:** Basa TODAS tus respuestas exclusivamente en los fragmentos de texto del 'BASE DE CONOCIMIENTOS'.
2.  **No Invenciones:** Nunca inventes información, detalles, fechas, nombres, procedimientos, requisitos, URLs, o cualquier dato que no esté explícitamente presente en el contexto.
3.  **Información Insuficiente:** Si el 'BASE DE CONOCIMIENTOS' no contiene la respuesta a la 'PREGUNTA DEL USUARIO', o si la información es parcial, debes indicarlo claramente. Por ejemplo: "La información sobre [aspecto de la pregunta] no está disponible en mi base de conocimientos actual." o "No cuento con detalles específicos sobre [aspecto de la pregunta] en mi base de conocimientos."
4.  **Guía Específica para "Áreas de Especialización":**
    Si la 'PREGUNTA DEL USUARIO' se refiere a 'áreas de especialización', 'líneas terminales', 'orientaciones', o temas similares del plan de estudios, y el contexto proviene del archivo `olap_plan_de_estudios.pkl`:
    * Presta especial atención a los registros donde se mencione un campo como `etapa_formacion` igual a "Terminal" (o un valor similar que indique etapa terminal, como "Optativa de Elección", "Area de Profundización").
    * Los nombres de estas áreas de especialización suelen estar en un campo como `campo_conocimiento` (o un nombre similar como 'nombre_del_area', 'linea_especializacion', 'asignatura', 'nombre_materia') asociado a esa etapa 'Terminal'.
    * Enumera las áreas de especialización que identifiques bajo estas condiciones. Si el contexto no es claro o no sigue esta estructura, basa tu respuesta en la información textual disponible sobre especializaciones en el contexto.
5.  **Formato de Respuesta:** Sé conciso y claro. Si la pregunta se puede responder con una lista, considera usarla (viñetas - o numeración).
6.  **Tono:** Mantén un tono profesional, servicial y neutral.
7.  **Preguntas Fuera de Alcance:** Si la pregunta no se relaciona con la carrera MAC, indica amablemente: "Como MAC-GPT, mi especialidad es la Licenciatura en Matemáticas Aplicadas y Computación. ¿Tienes alguna consulta sobre este programa?"

**Estructura para tu Respuesta (sigue este formato):**

PREGUNTA DEL USUARIO:
{pregunta_del_usuario}

BASE DE CONOCIMIENTOS {archivo_seleccionado}):
{contexto_concatenado_o_numerado}

RESPUESTA DE MAC-GPT:
[Tu respuesta aquí, basada estrictamente en el contexto anterior]
"""

# --- Variable global para la instancia del modelo LLM ---
LLM_INSTANCE = None

def configure_google_api(api_key: Optional[str] = None) -> bool:
    """
    Configura la API de Google con la clave proporcionada.
    
    Args:
        api_key: Clave de API de Google (opcional). Si no se proporciona, intenta
                obtenerla de las variables de entorno GEMINI_API_KEY o GOOGLE_API_KEY.
    
    Returns:
        bool: True si la configuración fue exitosa, False en caso contrario.
    """
    global GOOGLE_API_KEY_CONFIGURED, LLM_INSTANCE
    if GOOGLE_API_KEY_CONFIGURED: return True
    if not genai:
        print("ERROR: google.generativeai library is not available.")
        return False
    actual_api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not actual_api_key or actual_api_key == "YOUR_GOOGLE_API_KEY_HERE":
        print("ERROR: API key not provided, not in GEMINI_API_KEY/GOOGLE_API_KEY env var, or is a placeholder.")
        return False
    try:
        genai.configure(api_key=actual_api_key)
        print(f"Attempting to access embedding model: {EMBEDDING_MODEL_NAME}")
        genai.get_model(EMBEDDING_MODEL_NAME) 
        print(f"Embedding model {EMBEDDING_MODEL_NAME} accessible.")
        print(f"Attempting to initialize generative model: {GENERATIVE_MODEL_NAME}")
        LLM_INSTANCE = genai.GenerativeModel(GENERATIVE_MODEL_NAME)
        print(f"Generative model {GENERATIVE_MODEL_NAME} initialized successfully.")
        GOOGLE_API_KEY_CONFIGURED = True
        print("Google API configured successfully for all required models.")
        return True
    except Exception as e:
        print(f"ERROR: Configuring Google API, accessing models, or initializing generative model: {e}")
        GOOGLE_API_KEY_CONFIGURED, LLM_INSTANCE = False, None
        return False

def get_embedding_google(text: str, task_type: str, model_name: str = EMBEDDING_MODEL_NAME) -> Optional[np.ndarray]:
    """
    Genera un embedding con la API de Google.
    
    Args:
        text: Texto para generar el embedding.
        task_type: Tipo de tarea ('RETRIEVAL_QUERY' o 'RETRIEVAL_DOCUMENT').
        model_name: Nombre del modelo de embedding a utilizar.
        
    Returns:
        np.ndarray: El vector de embedding o None si hubo un error.
    """
    if not GOOGLE_API_KEY_CONFIGURED or not genai: print("API not configured for get_embedding_google"); return None
    if not text or not text.strip(): print("Empty text for get_embedding_google"); return None
    try:
        response = genai.embed_content(model=model_name, content=text, task_type=task_type)
        return np.array(response['embedding'])
    except Exception as e:
        print(f"ERROR generating embedding for text '{text[:50]}...': {e}"); return None

def similitud_coseno_scipy(vec1: Any, vec2: Any) -> Optional[float]:
    """
    Calcula la similitud del coseno entre dos vectores.
    
    Args:
        vec1: Primer vector (numpy array o lista).
        vec2: Segundo vector (numpy array o lista).
        
    Returns:
        float: Valor de similitud entre 0 y 1, o None si hubo un error.
    """
    if scipy_cosine_distance is None or np_linalg_norm is None: return None
    if not isinstance(vec1, (np.ndarray, list)) or not isinstance(vec2, (np.ndarray, list)): return None
    try:
        vec1_np = np.array(vec1, dtype=float)
        vec2_np = np.array(vec2, dtype=float)
    except ValueError: return None # Non-numeric data
    if vec1_np.shape != vec2_np.shape or vec1_np.size == 0: return None
    norm1, norm2 = np_linalg_norm(vec1_np), np_linalg_norm(vec2_np)
    if norm1 == 0 and norm2 == 0: return 1.0
    if norm1 == 0 or norm2 == 0: return 0.0
    try: return float(1 - scipy_cosine_distance(vec1_np, vec2_np))
    except Exception: return None

def cargar_y_precalcular_embeddings_temas() -> bool:
    """
    Genera y almacena en caché embeddings representativos para cada tema basado en su descripción predefinida.
    
    Returns:
        bool: True si la carga y precálculo fue exitoso, False en caso contrario.
    """
    global REPRESENTATIVE_TOPIC_EMBEDDINGS
    if not GOOGLE_API_KEY_CONFIGURED:
        print("ERROR: Google API not configured. Cannot generate theme description embeddings.")
        return False
    if not genai:
        print("ERROR: google.generativeai library not available for theme description embeddings.")
        return False

    print(f"Generating and caching representative embeddings for {len(DESCRIPCIONES_TEMAS)} themes...")
    loaded_count = 0
    for theme_file, description in DESCRIPCIONES_TEMAS.items():
        if theme_file in REPRESENTATIVE_TOPIC_EMBEDDINGS:
            print(f"  INFO: Representative embedding for {theme_file} already cached. Skipping generation.")
            loaded_count +=1
            continue
        
        print(f"  Generating embedding for description of: {theme_file}")
        # These descriptions act as the "document" representing the theme
        theme_desc_embedding = get_embedding_google(description, task_type="RETRIEVAL_DOCUMENT")
        
        if theme_desc_embedding is not None:
            REPRESENTATIVE_TOPIC_EMBEDDINGS[theme_file] = theme_desc_embedding
            print(f"    Successfully generated and cached representative embedding for {theme_file}.")
            loaded_count += 1
        else:
            print(f"    ERROR: Failed to generate embedding for description of {theme_file}. Skipping theme.")
            
    if loaded_count > 0:
        print(f"Representative theme description embeddings generated/cached for {loaded_count}/{len(DESCRIPCIONES_TEMAS)} themes.")
        return True
    print("ERROR: No representative theme description embeddings were successfully generated or cached.")
    return False

def seleccionar_fuente_de_datos_mac(user_prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Identifica el archivo .pkl de tema más relevante para la pregunta del usuario
    comparando el embedding de la pregunta con los embeddings precalculados de los temas.
    
    Args:
        user_prompt: Pregunta del usuario.
        
    Returns:
        tuple: (archivo_tema_seleccionado, pregunta_original_del_usuario)
    """
    if not GOOGLE_API_KEY_CONFIGURED: print("ERROR: API not configured for theme selection."); return None, user_prompt
    if not REPRESENTATIVE_TOPIC_EMBEDDINGS: print("ERROR: Theme description embeddings not calculated."); return None, user_prompt
    if not user_prompt or not user_prompt.strip(): print("WARNING: User prompt is empty."); return None, user_prompt

    print(f"\nSelecting data source for prompt: '{user_prompt}'")
    prompt_embedding = get_embedding_google(user_prompt, task_type="RETRIEVAL_QUERY")
    if prompt_embedding is None: print("ERROR: Failed to embed user prompt."); return None, user_prompt

    selected_theme_file, max_similarity_topic = None, -2.0
    print("  Calculating similarities with theme description embeddings:")
    for theme_file, desc_embedding in REPRESENTATIVE_TOPIC_EMBEDDINGS.items():
        similarity = similitud_coseno_scipy(prompt_embedding, desc_embedding)
        if similarity is not None:
            print(f"    vs {theme_file}: {similarity:.4f}")
            if similarity > max_similarity_topic:
                max_similarity_topic, selected_theme_file = similarity, theme_file
        else:
            print(f"    WARNING: Could not calculate similarity for theme {theme_file} with prompt.")
    
    if selected_theme_file:
        print(f"  -> Selected theme file based on description: {selected_theme_file} (Similarity: {max_similarity_topic:.4f})")
    else:
        print("ERROR: Could not classify prompt using theme descriptions.")
    return selected_theme_file, user_prompt

def generar_respuesta_con_llm(
    pregunta_usuario: str,
    archivo_seleccionado: Optional[str],
    directorio_pickles: str = DEFAULT_PICKLE_DIR,
    top_n_contextos: int = 7
) -> str:
    """
    Genera una respuesta final utilizando el LLM.
    Realiza su propia recuperación de contexto desde el archivo seleccionado 
    y formatea el contexto como str(List[Dict]).
    
    Args:
        pregunta_usuario: Pregunta del usuario.
        archivo_seleccionado: Archivo .pkl seleccionado para la recuperación de contexto.
        directorio_pickles: Directorio donde se encuentran los archivos .pkl.
        top_n_contextos: Número de contextos relevantes a recuperar.
        
    Returns:
        str: Respuesta generada por el modelo.
    """
    global LLM_INSTANCE
    if not GOOGLE_API_KEY_CONFIGURED: return "Error: La API de Google no está configurada."
    if LLM_INSTANCE is None: return f"Error: El modelo generativo {GENERATIVE_MODEL_NAME} no está inicializado."
    if not pregunta_usuario: return "Error: Se requiere la pregunta del usuario."

    contexto_str = "La información sobre este tema no está disponible en mi base de conocimientos actual."
    effective_archivo_seleccionado = archivo_seleccionado if archivo_seleccionado else "N/A (Clasificación de tema fallida)"

    if archivo_seleccionado: # Only retrieve context if a theme was successfully selected
        print(f"  LLM context retrieval from: {archivo_seleccionado}")
        prompt_embedding_for_retrieval = get_embedding_google(pregunta_usuario, task_type="RETRIEVAL_QUERY")
        
        if prompt_embedding_for_retrieval is None:
            contexto_str = "Error al generar embedding de la pregunta para buscar contextos."
        else:
            try:
                file_path = os.path.join(directorio_pickles, archivo_seleccionado)
                if not os.path.exists(file_path):
                    return f"Error: El archivo de conocimiento '{archivo_seleccionado}' no fue encontrado en '{directorio_pickles}'."
                
                df = pd.DataFrame() # Initialize
                try:
                    df = pd.read_pickle(file_path)
                except (pickle.UnpicklingError, TypeError, EOFError, AttributeError) as e_pkl: # Added AttributeError
                    print(f"  INFO: LLM: Failed to load {archivo_seleccionado} as PKL ({e_pkl}), attempting CSV.")
                    try:
                        df = pd.read_csv(file_path)
                        if "embeddings" in df.columns and isinstance(df["embeddings"].iloc[0], str):
                            print(f"  INFO: Converting string embeddings in {archivo_seleccionado} (CSV) to arrays.")
                            df["embeddings"] = df["embeddings"].apply(lambda x: np.array(eval(x)) if isinstance(x, str) else x)
                    except Exception as e_csv:
                        return f"Error al cargar el archivo {archivo_seleccionado} como CSV: {e_csv}"

                if df.empty:
                    return f"Error: El archivo {archivo_seleccionado} está vacío o no se pudo cargar correctamente."
                if "embeddings" not in df.columns:
                    return f"Error: La columna 'embeddings' no se encuentra en el archivo {archivo_seleccionado}."
                
                similarities = []
                for idx, row_emb_item in enumerate(df['embeddings']):
                    # Ensure row_emb_item is a valid vector (list or ndarray) before processing
                    if isinstance(row_emb_item, (list, np.ndarray)):
                        doc_emb_np = np.array(row_emb_item)
                        if doc_emb_np.size > 0:
                            sim = similitud_coseno_scipy(prompt_embedding_for_retrieval, doc_emb_np)
                            if sim is not None: similarities.append((sim, df.index[idx]))
                    # else: print(f"    Skipping invalid embedding type at index {idx} in {archivo_seleccionado}")

                if not similarities:
                    print(f"    No valid document similarities calculated within {archivo_seleccionado}.")
                    # contexto_str remains the default "no info found"
                else:
                    similarities.sort(key=lambda x: x[0], reverse=True)
                    top_indices = [idx for _, idx in similarities[:top_n_contextos]]
                    
                    top_contexts_df = df.loc[top_indices].copy()
                    if 'embeddings' in top_contexts_df.columns:
                        top_contexts_df.drop(columns=["embeddings"], inplace=True)
                    
                    top_contexts_list_of_dicts = top_contexts_df.to_dict(orient="records")
                    
                    if top_contexts_list_of_dicts:
                        contexto_str = str(top_contexts_list_of_dicts) 
                        print(f"    Context for LLM (string of list of dicts, top {len(top_contexts_list_of_dicts)} from {archivo_seleccionado}): {contexto_str[:250]}...")
                    else:
                        print(f"    No contexts found in {archivo_seleccionado} after similarity ranking.")
                        # contexto_str remains default

            except Exception as e:
                contexto_str = f"Error al cargar o procesar el archivo {archivo_seleccionado} para el contexto del LLM: {e}"
                print(f"    ERROR in LLM context retrieval from {archivo_seleccionado}: {e}")
    
    prompt_final_llm = SISTEMA_PROMPT_MAC.format(
        pregunta_del_usuario=pregunta_usuario,
        archivo_seleccionado=effective_archivo_seleccionado,
        contexto_concatenado_o_numerado=contexto_str
    )
    
    try:
        print(f"\nEnviando solicitud al LLM ({GENERATIVE_MODEL_NAME})...")
        response = LLM_INSTANCE.generate_content(prompt_final_llm)
        if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
            return f"Respuesta bloqueada: {response.prompt_feedback.block_reason}."
        return response.text.strip() if hasattr(response, 'text') and response.text else "El modelo no generó respuesta."
    except Exception as e:
        print(f"ERROR generando respuesta con LLM: {e}")
        return f"Error al generar respuesta: {str(e)}"

def ask_mac_gpt(prompt: str, directorio_pickles: str = DEFAULT_PICKLE_DIR) -> str:
    """
    Función principal para interactuar con MAC-GPT.
    
    Args:
        prompt: Pregunta del usuario.
        directorio_pickles: Directorio donde se encuentran los archivos .pkl.
        
    Returns:
        str: Respuesta generada por el chatbot.
    """
    print("--- MAC Q&A - Full RAG Pipeline (Theme Description Based Classification) ---")
    api_key_env = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    if not api_key_env or api_key_env == "YOUR_GOOGLE_API_KEY_HERE": # Check common placeholder
        print("\nWARNING: API key not set or is placeholder (GEMINI_API_KEY/GOOGLE_API_KEY).")
        print("         Functionality will be severely limited or fail.")
        configure_google_api(api_key=None) 
    else:
        configure_google_api(api_key=api_key_env)

    print("\n--- Initializing Theme Description Embeddings ---")
    themes_loaded = cargar_y_precalcular_embeddings_temas() 

    if themes_loaded and GOOGLE_API_KEY_CONFIGURED and REPRESENTATIVE_TOPIC_EMBEDDINGS:
        print("\n--- Starting Q&A Session ---")
        
        selected_file, original_prompt = seleccionar_fuente_de_datos_mac(user_prompt=prompt)

        final_answer = "No se pudo generar una respuesta."
        if original_prompt:
            if selected_file:
                print(f"\n[Debug Info] Original Prompt: {original_prompt}")
                print(f"[Debug Info] Selected File (for LLM context retrieval): {selected_file}")
                
                print("\n--- Generating Final Answer with LLM ---")
                final_answer = generar_respuesta_con_llm(
                    pregunta_usuario=original_prompt,
                    archivo_seleccionado=selected_file,
                    directorio_pickles=directorio_pickles,
                    top_n_contextos=8
                )
            else:
                final_answer = "MAC-GPT: Lo siento, no pude identificar una categoría de conocimiento específica para tu pregunta. ¿Podrías reformularla?"
        else:
            final_answer = "MAC-GPT: Parece que no hubo una pregunta para procesar."

        print("\n================ RESPUESTA DE MAC-GPT =================")
        print(final_answer)
        print("=======================================================")

        # Extraer solo la parte de la respuesta sin los metadatos
        if "RESPUESTA DE MAC-GPT:" in final_answer:
            final_answer = final_answer.split("RESPUESTA DE MAC-GPT:")[-1].strip()
        
        return final_answer
            
    else:
        mensaje_error = "No se pudo inicializar el chatbot MAC-GPT."
        if not GOOGLE_API_KEY_CONFIGURED: 
            mensaje_error += " La clave de API no está configurada o es inválida."
        if not themes_loaded or not REPRESENTATIVE_TOPIC_EMBEDDINGS: 
            mensaje_error += " No se pudieron generar o cargar los embeddings de descripciones de temas."
        print(f"\n--- ERROR: {mensaje_error} ---")
        return mensaje_error 