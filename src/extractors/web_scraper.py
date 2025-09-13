"""
Módulo para extraer datos de páginas web utilizando Beautiful Soup y Selenium
"""
from bs4 import BeautifulSoup
import requests
import os
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

from config import settings


def get_driver() -> webdriver.Chrome:
    """
    Initialize and return a Chrome WebDriver instance with options
    
    Returns:
        WebDriver: Chrome WebDriver instance
    """
    chrome_options = Options()
    if settings.HEADLESS_MODE:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        return driver
    except Exception as e:
        print(f"Error al inicializar el WebDriver: {e}")
        raise


def get_soup(url: str) -> BeautifulSoup:
    """
    Load a URL and return BeautifulSoup object with the page content
    
    Args:
        url (str): URL to load
        
    Returns:
        BeautifulSoup: BeautifulSoup object with the page content
    """
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes
    return BeautifulSoup(response.text, 'html.parser')


def get_soup_by_driver(driver: webdriver.Chrome) -> BeautifulSoup:
    """
    Create BeautifulSoup object from the current page loaded in WebDriver
    
    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        
    Returns:
        BeautifulSoup: BeautifulSoup object with the page content
    """
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return soup


def get_element_by_xpath(driver: webdriver.Chrome, xpath: str, timeout: int = None) -> str:
    """
    Get the inner HTML content of an element located by XPath

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        xpath (str): XPath of the element to find
        timeout (int): Maximum time to wait for element in seconds

    Returns:
        str: Inner HTML content of the element

    Raises:
        TimeoutException: If element is not found within timeout
    """
    if timeout is None:
        timeout = settings.BROWSER_TIMEOUT
        
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element.get_attribute('innerHTML')
    except TimeoutException:
        print(f"Element with xpath '{xpath}' not found within {timeout} seconds")
        raise
    except Exception as e:
        print(f"Error getting element HTML: {str(e)}")
        raise


def click_element_by_xpath(driver: webdriver.Chrome, xpath: str, timeout: int = None) -> None:
    """
    Wait for an element to be present and clickable, then click it

    Args:
        driver (webdriver.Chrome): Selenium WebDriver instance
        xpath (str): XPath of the element to find and click
        timeout (int): Maximum time to wait for element in seconds

    Raises:
        TimeoutException: If element is not found within timeout
    """
    if timeout is None:
        timeout = settings.BROWSER_TIMEOUT
        
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
        print(f"Clicked successfully on element with xpath: {xpath}")
    except TimeoutException:
        print(f"Element with xpath '{xpath}' not found within {timeout} seconds")
        raise
    except Exception as e:
        print(f"Error clicking element: {str(e)}")
        raise


def download_pdfs_by_semester(save_dir: str = None) -> dict:
    """
    Descarga los PDFs de temarios organizados por semestres
    
    Args:
        save_dir (str): Directorio donde guardar los PDFs, si es None 
                        se usa el directorio configurado en settings
                      
    Returns:
        dict: Información sobre los archivos descargados organizados por semestres
    """
    if save_dir is None:
        save_dir = settings.PDF_DIR
    
    # Inicializar el driver y acceder a la URL
    driver = get_driver()
    driver.get(settings.BASE_URL)
    driver.implicitly_wait(settings.BROWSER_TIMEOUT)
    
    # Obtener nombres de semestres
    semestres_text = [s.text.strip() for s in driver.find_elements(By.CSS_SELECTOR, "a.semestre")]
    
    # Estructura para almacenar la información de archivos descargados
    downloaded_files = {}
    
    # Recorrer por nombre (no por referencia directa al elemento)
    for nombre in semestres_text:
        print(f"\n📘 Semestre: {nombre}")
        downloaded_files[nombre] = []

        # Volver a cargar la página para que el DOM esté fresco
        driver.get(settings.BASE_URL)
        driver.implicitly_wait(settings.BROWSER_TIMEOUT)

        # Buscar el semestre actual por texto
        semestres_actuales = driver.find_elements(By.CSS_SELECTOR, "a.semestre")
        for s in semestres_actuales:
            if s.text.strip() == nombre:
                s.click()
                break

        time.sleep(2)  # Esperar que cargue

        # Obtener enlaces PDF
        enlaces_pdf = driver.find_elements(By.CSS_SELECTOR, "#result a[href$='.pdf']")
        if not enlaces_pdf:
            print("⚠️  No se encontraron PDFs.")
            continue

        # Carpeta para este semestre
        semestre_path = os.path.join(save_dir, nombre)
        os.makedirs(semestre_path, exist_ok=True)

        # Descargar PDFs
        for enlace in enlaces_pdf:
            url = enlace.get_attribute("href")
            nombre_pdf = url.split("/")[-1]
            destino = os.path.join(semestre_path, nombre_pdf)
            print(f"  📥 {nombre_pdf}")
            try:
                r = requests.get(url)
                with open(destino, "wb") as f:
                    f.write(r.content)
                print(f"    ✅ Guardado: {destino}")
                
                # Guardar información del archivo descargado
                downloaded_files[nombre].append({
                    "filename": nombre_pdf,
                    "path": destino,
                    "url": url
                })
            except Exception as e:
                print(f"    ❌ Error al descargar: {e}")

    # Cerrar navegador
    driver.quit()
    print("\n✅ Todos los semestres descargados.")
    
    return downloaded_files 