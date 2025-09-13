"""
Módulo para extraer texto y datos estructurados de archivos PDF
"""
import os
import re
import json
from typing import Dict, Any, List, Optional, Union
import PyPDF2
import google.generativeai as genai

from config import settings


def read_pdf_content(pdf_path: str) -> str:
    """
    Lee el contenido de texto de un archivo PDF.
    
    Args:
        pdf_path (str): Ruta al archivo PDF
        
    Returns:
        str: Contenido del PDF como texto, o cadena vacía si hay error
    """
    try:
        content = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            if reader.is_encrypted:
                try:
                    reader.decrypt('')
                except Exception as e:
                    print(f"No se pudo desencriptar {pdf_path}: {e}. Intentando leer de todas formas.")

            for page_num in range(len(reader.pages)):
                try:
                    page_text = reader.pages[page_num].extract_text()
                    if page_text:
                        content += page_text + "\n" # Añadir un salto entre páginas
                except Exception as e:
                    print(f"Error al extraer texto de la página {page_num} de {pdf_path}: {e}")
                    continue # Continuar con la siguiente página
        return content
    except Exception as e:
        print(f"Error general al leer el archivo PDF {pdf_path}: {e}")
        return ""


def sanitize_text_for_prompt(text: str) -> str:
    """
    Limpia el texto eliminando o reemplazando caracteres de control
    comunes que pueden causar problemas en prompts o JSON.
    
    Args:
        text (str): Texto a sanitizar
        
    Returns:
        str: Texto sanitizado
    """
    if text is None:
        return ""
        
    # Reemplazar múltiples espacios/saltos de línea con uno solo
    text = re.sub(r'\s+', ' ', text)
    
    # Eliminar caracteres de control comunes excepto tab, newline, carriage return
    text = "".join(char for char in text if char.isprintable() or char in ('\t', '\n', '\r'))
    
    # Específicamente, los caracteres NUL pueden ser muy problemáticos.
    text = text.replace('\x00', '') # Eliminar NUL bytes
    
    return text


def configure_gemini_api() -> bool:
    """
    Configura la API de Gemini usando la API key almacenada en variables de entorno
    
    Returns:
        bool: True si la configuración fue exitosa, False en caso contrario
    """
    try:
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            print("Error: La variable de entorno GEMINI_API_KEY no está configurada.")
            return False
            
        genai.configure(api_key=api_key)
        print("API de Gemini configurada correctamente")
        return True
    except Exception as e:
        print(f"Error al configurar la API de Gemini: {e}")
        return False


def extract_syllabus_info(pdf_content_raw: str, filename_full_path: str) -> Dict[str, Any]:
    """
    Extrae información estructurada del contenido de un temario usando el modelo Gemini.
    
    Args:
        pdf_content_raw (str): Contenido del PDF como texto
        filename_full_path (str): Ruta completa al archivo PDF
        
    Returns:
        Dict[str, Any]: Diccionario con la información extraída del temario
    """
    model = genai.GenerativeModel(
        model_name=settings.GEN_AI_MODEL
    )

    # Extraer el nombre base del archivo y la clave
    base_filename = os.path.basename(filename_full_path)
    clave_from_filename, _ = os.path.splitext(base_filename)

    # Sanitizar el contenido del PDF antes de pasarlo al prompt
    pdf_content_sanitized = sanitize_text_for_prompt(pdf_content_raw)

    # Usar el nombre de archivo base (sin ruta) en el prompt para 'archivo_origen' y 'clave'
    prompt = f"""
    Analiza el siguiente contenido de un temario de materia extraído de un PDF.

    Tu objetivo es extraer únicamente la información clave y devolverla como un objeto JSON **estrictamente limitado** a los campos especificados más abajo. **No incluyas claves adicionales bajo ninguna circunstancia.**

    El temario sigue una estructura donde se presentan datos generales al inicio (nombre de la materia, semestre, etc.), seguido de tablas con detalles como horas, créditos. Usualmente sigue un índice temático, el contenido detallado por unidad y referencias y/o sugerencias al final.

    Reglas:
    - Ignora diferencias entre **mayúsculas y minúsculas**, así como entre palabras con o sin **acentos ortográficos**. Por ejemplo, trata "CLAVE", "clave", "Clavé" y "clavé" como equivalentes.
    - **No infieras ni crees campos adicionales** fuera de los enumerados.
    - **Sanitiza el texto extraído**: Antes de incluir texto en los valores del JSON, escapa adecuadamente caracteres especiales (saltos de línea, tabulaciones, comillas) o reemplaza caracteres de control no imprimibles para asegurar que el JSON resultante sea válido. Si un campo contiene listas (ej. indice_tematico, referencias), asegúrate que sean listas JSON válidas de strings.
    - Devuelve la información como un objeto JSON **válido** con exactamente las siguientes claves:

    Lógica especial:
    - La clave `"clave"` **siempre** debe ser: `{clave_from_filename}`.
    - La clave `"archivo_origen"` **siempre** debe ser: `{base_filename}`.
    - Si algún otro campo o sección no se encuentra de forma clara y explícita en el PDF, utiliza el valor JSON `null` para esa clave. No omitas la clave.

    Campos a extraer:
    - `"nombre_materia"`: Nombre de la materia, generalmente al inicio del documento.
    - `"clave"`: (Siempre `{clave_from_filename}`)
    - `"semestre_num"`: Número del semestre (ej. 8, 1). Debe ser un número o `null`.
    - `"semestre_txt"`: Nombre textual del semestre (ej. OCTAVO).
    - `"modalidad"`: Modalidad de la materia (ej. Curso, Seminario).
    - `"caracter"`: Carácter (ej. Obligatoria, Optativa).
    - `"tipo"`: Tipo (ej. Teórica, Teórico-Práctica).
    - `"horas_al_semestre"`: Número total de horas al semestre. Debe ser un número o `null`.
    - `"horas_semana"`: Número de horas a la semana. Debe ser un número o `null`.
    - `"horas_teoricas"`: Número de horas teóricas. Debe ser un número o `null`.
    - `"horas_practicas"`: Número de horas prácticas. Debe ser un número o `null`.
    - `"creditos"`: Número de créditos. Debe ser un número o `null`.
    - `"etapa_formacion"`
    - `"campo_conocimiento"`
    - `"antecedente"`: Materias antecedentes, o "Ninguna" si así se especifica o no se encuentra.
    - `"subsecuente"`: Materias subsecuentes, o "Ninguna" si así se especifica o no se encuentra.
    - `"objetivo_general"`
    - `"indice_tematico"`: Lista de strings tipo `["1- Tema Alfa", "2- Tema Beta"]` extraída de la sección "Índice Temático" o similar. Si no se encuentra, `null`.
    - `"contenido"`: Contenido completo de la sección "CONTENIDO" o "Temario detallado". Puede ser un string largo. Si no se encuentra, `null`.
    - `"referencias_basicas"`: Lista de strings con referencias básicas. Busca la sección "Referencias básicas" o similar. Si no se encuentra, `null`.
    - `"referencias_complementarias"`: Lista de strings con referencias complementarias. Busca la sección "Referencias complementarias" o similar. Si no se encuentra, `null`.
    - `"sugerencias_didacticas"`: Texto extraído de la sección 'Sugerencias didácticas' o un encabezado muy similar. Si no se encuentra, `null`.
    - `"sugerencias_evaluacion"`: Texto extraído de la sección 'Sugerencias de evaluación del aprendizaje', 'Sugerencias de evaluación' o un encabezado muy similar. Si no se encuentra, `null`.
    - `"archivo_origen"`: (Siempre `{base_filename}`)

    Contenido del PDF a analizar:
    ```text
    {pdf_content_sanitized}
    ```
    """
    
    retry_count = 0
    max_retries = settings.MAX_RETRIES
    extracted_data = None
    last_error = None

    while retry_count <= max_retries:
        try:
            response = model.generate_content(prompt)
            json_string = response.text.strip()
            
            # Intentar encontrar el JSON dentro del texto, puede estar envuelto en ```json ... ```
            match = re.search(r"```json\s*(\{.*?\})\s*```", json_string, re.DOTALL)
            if match:
                json_string_cleaned = match.group(1)
            elif json_string.startswith('{') and json_string.endswith('}'):
                json_string_cleaned = json_string
            else:
                start_index = json_string.find('{')
                end_index = json_string.rfind('}')
                if start_index != -1 and end_index != -1 and start_index < end_index:
                    json_string_cleaned = json_string[start_index : end_index + 1]
                else:
                    raise ValueError("La respuesta del modelo no contiene un objeto JSON válido reconocible.")
            
            extracted_data = json.loads(json_string_cleaned)
            break # Éxito, salir del bucle de reintentos

        except Exception as e:
            last_error = e
            print(f"Intento {retry_count + 1}/{max_retries + 1} fallido para {base_filename}: {e}")
            retry_count += 1
            if retry_count > max_retries:
                print(f"Todos los intentos fallaron para {base_filename}.")
    
    # Definir todos los campos esperados para asegurar que el diccionario de retorno los tenga
    expected_fields = [
        "nombre_materia", "clave", "semestre_num", "semestre_txt", "modalidad",
        "caracter", "tipo", "horas_al_semestre", "horas_semana", "horas_teoricas",
        "horas_practicas", "creditos", "etapa_formacion", "campo_conocimiento",
        "antecedente", "subsecuente", "objetivo_general", "indice_tematico",
        "contenido", "referencias_basicas", "referencias_complementarias",
        "sugerencias_didacticas", "sugerencias_evaluacion", "archivo_origen", "error"
    ]

    if extracted_data is None:
        # Falló la extracción con IA, devolver un diccionario con valores por defecto y el error
        result = {field: None for field in expected_fields}
        result["nombre_materia"] = f"Error al extraer de {base_filename}"
        result["clave"] = clave_from_filename
        result["archivo_origen"] = base_filename
        result["error"] = str(last_error)
        return result

    # Post-procesamiento y asegurar que todos los campos estén presentes
    final_result = {}
    # Forzar 'clave' y 'archivo_origen' según lo definido
    final_result["clave"] = clave_from_filename
    final_result["archivo_origen"] = base_filename

    # Procesar 'nombre_materia'
    nombre_materia_extraido = extracted_data.get("nombre_materia")
    if nombre_materia_extraido and isinstance(nombre_materia_extraido, str):
        final_result["nombre_materia"] = nombre_materia_extraido.strip()
    else:
        final_result["nombre_materia"] = None 

    # Asignar los demás campos extraídos o None si faltan
    for field in expected_fields:
        if field not in final_result: # No sobrescribir campos ya procesados
            final_result[field] = extracted_data.get(field) # Usa .get() para evitar KeyError

    # Asegurar que los campos numéricos sean números o None
    numeric_fields = ["semestre_num", "horas_al_semestre", "horas_semana", "horas_teoricas", "horas_practicas", "creditos"]
    for nf in numeric_fields:
        val = final_result.get(nf)
        if val is not None:
            try:
                final_result[nf] = int(val) # O float(val) si pueden tener decimales
            except (ValueError, TypeError):
                print(f"Advertencia: El campo '{nf}' para '{base_filename}' no es un número válido ('{val}'). Se establecerá a None.")
                final_result[nf] = None
    
    # Asegurar que los campos de lista sean listas o None
    list_fields = ["indice_tematico", "referencias_basicas", "referencias_complementarias"]
    for lf in list_fields:
        val = final_result.get(lf)
        if val is not None and not isinstance(val, list):
            print(f"Advertencia: El campo '{lf}' para '{base_filename}' no es una lista válida ('{val}'). Se establecerá a None.")
            final_result[lf] = None
        elif isinstance(val, list): # Asegurar que los elementos de la lista sean strings
            final_result[lf] = [str(item) if item is not None else "" for item in val]

    if last_error: # Si hubo un error en el último intento pero se recuperó algo
        final_result["error"] = f"Extracción parcial, error final: {str(last_error)}"
    else:
        final_result["error"] = None # Sin error

    # Verificar que todos los campos esperados estén, aunque sea con valor None
    for ef in expected_fields:
        if ef not in final_result:
            final_result[ef] = None
            
    return final_result


def process_all_pdfs(pdf_dir: str = None) -> List[Dict[str, Any]]:
    """
    Procesa todos los PDFs en una carpeta y extrae su información
    
    Args:
        pdf_dir (str): Carpeta que contiene los PDFs o subcarpetas con PDFs.
                       Si es None, usa la carpeta de PDFs configurada en settings.
    
    Returns:
        List[Dict[str, Any]]: Lista con la información extraída de cada PDF
    """
    if pdf_dir is None:
        pdf_dir = settings.PDF_DIR
        
    if not os.path.isdir(pdf_dir):
        print(f"Error: La carpeta de PDFs '{pdf_dir}' no existe.")
        return []
        
    # Configurar API de Gemini
    api_configured = configure_gemini_api()
    if not api_configured:
        print("No se pudo configurar la API de Gemini. Abortando extracción.")
        return []
    
    # Encontrar todos los archivos PDF
    subject_files_paths = []
    for root, _, files in os.walk(pdf_dir):
        for f in files:
            if f.lower().endswith(".pdf"):
                subject_files_paths.append(os.path.join(root, f))
                
    # Extraer información de cada PDF
    all_extracted_data = []
    
    for pdf_file_path in subject_files_paths:
        base_filename_for_print = os.path.basename(pdf_file_path)
        print(f"Procesando {base_filename_for_print}...")
        raw_content = read_pdf_content(pdf_file_path)
        
        if raw_content and raw_content.strip():
            extracted_info = extract_syllabus_info(raw_content, pdf_file_path)
            all_extracted_data.append(extracted_info)
            
            if extracted_info.get("error") and "Error al extraer de" not in str(extracted_info.get("nombre_materia", "")):
                print(f"Extracción completada para {base_filename_for_print} con advertencias/errores: {extracted_info.get('error')}")
            elif "Error al extraer de" in str(extracted_info.get("nombre_materia", "")):
                print(f"Extracción fallida para {base_filename_for_print}: {extracted_info.get('error')}")
            else:
                print(f"Extracción completada exitosamente para {base_filename_for_print}")
        else:
            print(f"No se pudo leer contenido válido de {base_filename_for_print} o el archivo está vacío.")
            # Añadir un registro con error si no se pudo leer el archivo
            clave_error_lectura, _ = os.path.splitext(base_filename_for_print)
            all_extracted_data.append({
                "clave": clave_error_lectura, 
                "nombre_materia": f"Error de lectura - {base_filename_for_print}",
                "semestre_num": None, 
                "semestre_txt": None,
                "modalidad": None, 
                "caracter": None, 
                "tipo": None, 
                "horas_al_semestre": None,
                "horas_semana": None, 
                "horas_teoricas": None, 
                "horas_practicas": None, 
                "creditos": None,
                "etapa_formacion": None, 
                "campo_conocimiento": None, 
                "antecedente": "Error de lectura",
                "subsecuente": "Error de lectura", 
                "objetivo_general": "Error de lectura",
                "indice_tematico": None, 
                "contenido": "Error de lectura",
                "referencias_basicas": None, 
                "referencias_complementarias": None,
                "sugerencias_didacticas": "Error de lectura", 
                "sugerencias_evaluacion": "Error de lectura",
                "archivo_origen": base_filename_for_print, 
                "error": "No se pudo leer contenido válido del PDF"
            })
    
    return all_extracted_data 