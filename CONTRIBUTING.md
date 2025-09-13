# 🤝 Guía de Contribución - MAC-GPT

¡Gracias por tu interés en contribuir a MAC-GPT! Esta guía te ayudará a participar en el desarrollo del proyecto.

## 🚀 Cómo Contribuir

### 1. 🍴 Fork y Clona el Repositorio
```bash
# Fork el repositorio desde GitHub
# Luego clona tu fork
git clone https://github.com/tu-usuario/MAC-GPT.git
cd MAC-GPT
```

### 2. 🔧 Configurar Entorno de Desarrollo
```bash
# Crear entorno virtual
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp env.example .env
# Editar .env con tus API keys
```

### 3. 🌿 Crear una Rama
```bash
git checkout -b feature/nueva-funcionalidad
# O para correcciones:
git checkout -b fix/correccion-bug
```

## 📝 Tipos de Contribuciones

### 🐛 Reportar Bugs
- Usa las [GitHub Issues](https://github.com/tu-usuario/MAC-GPT/issues)
- Incluye pasos para reproducir el error
- Especifica tu entorno (OS, Python version, etc.)

### ✨ Nuevas Características
- Abre un issue primero para discutir la idea
- Mantén los cambios enfocados y pequeños
- Incluye tests cuando sea posible

### 📚 Documentación
- Mejoras al README
- Comentarios en el código
- Ejemplos de uso

### 🧪 Tests
- Agregar tests unitarios
- Mejorar cobertura de tests
- Tests de integración

## 🔍 Estándares de Código

### 🐍 Python Style Guide
```python
# Usa PEP 8
# Nombres de funciones en snake_case
def procesar_datos():
    pass

# Nombres de clases en PascalCase
class ExtractorPDF:
    pass

# Constantes en UPPER_CASE
MAX_RETRIES = 3
```

### 📝 Documentación de Código
```python
def extraer_informacion(pdf_path: str) -> Dict[str, Any]:
    """
    Extrae información estructurada de un PDF.
    
    Args:
        pdf_path: Ruta al archivo PDF
        
    Returns:
        Dict con la información extraída
        
    Raises:
        FileNotFoundError: Si el archivo no existe
    """
    pass
```

### 🧪 Tests
```python
# tests/test_extractor.py
import unittest
from src.extractors.pdf_extractor import extraer_informacion

class TestPDFExtractor(unittest.TestCase):
    def test_extraer_informacion_valido(self):
        resultado = extraer_informacion("test.pdf")
        self.assertIsNotNone(resultado)
```

## 🔄 Proceso de Pull Request

### ✅ Antes de Enviar
- [ ] Código sigue los estándares del proyecto
- [ ] Tests pasan correctamente
- [ ] Documentación actualizada
- [ ] Commit messages descriptivos

### 📤 Enviar Pull Request
1. Push a tu rama: `git push origin feature/nueva-funcionalidad`
2. Abre un Pull Request en GitHub
3. Llena la plantilla de PR
4. Espera revisión y feedback

### 📋 Plantilla de Pull Request
```markdown
## 📝 Descripción
Breve descripción de los cambios

## 🎯 Tipo de Cambio
- [ ] Bug fix
- [ ] Nueva característica
- [ ] Mejora de documentación
- [ ] Refactoring

## ✅ Testing
- [ ] Tests existentes pasan
- [ ] Agregué nuevos tests
- [ ] Tests manuales realizados

## 📷 Screenshots (si aplica)
```

## 🏷️ Convenciones de Commits

### Formato
```
tipo(scope): descripción breve

Descripción más detallada si es necesaria
```

### Tipos
- `feat`: Nueva característica
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Formateo, espacios, etc.
- `refactor`: Refactoring de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

### Ejemplos
```bash
git commit -m "feat(chatbot): agregar soporte para múltiples idiomas"
git commit -m "fix(extractor): corregir error al procesar PDFs vacíos"
git commit -m "docs(readme): actualizar instrucciones de instalación"
```

## 🚨 Código de Conducta

### 🤗 Nuestros Valores
- **Respeto**: Trata a todos con cortesía y profesionalismo
- **Inclusión**: Todos son bienvenidos, independientemente de su experiencia
- **Colaboración**: Trabajamos juntos hacia objetivos comunes
- **Aprendizaje**: Todos estamos aquí para aprender y crecer

### 🚫 Comportamientos No Aceptados
- Lenguaje ofensivo o discriminatorio
- Ataques personales o políticos
- Acoso público o privado
- Spam o contenido no relacionado

## 🆘 ¿Necesitas Ayuda?

### 📚 Recursos
- [Documentación del Proyecto](README.md)
- [Issues Existentes](https://github.com/tu-usuario/MAC-GPT/issues)
- [Discusiones](https://github.com/tu-usuario/MAC-GPT/discussions)

### 💬 Contacto
- 📧 Email: [maintainer@example.com](mailto:maintainer@example.com)
- 💬 Discord: [Servidor del Proyecto](#)
- 🐦 Twitter: [@proyecto_mac_gpt](#)

## 🎯 Roadmap y Prioridades

### 🔥 Alta Prioridad
- Mejorar velocidad de extracción
- Agregar más tests unitarios
- Optimizar búsqueda semántica

### 📋 Media Prioridad
- Interfaz de administración
- Soporte para más formatos
- Integración con bases de datos

### 💭 Ideas Futuras
- App móvil
- Multiidioma
- Analytics avanzados

---

## 🙏 Agradecimientos

¡Gracias por contribuir al proyecto MAC-GPT! Tu tiempo y esfuerzo ayudan a mejorar la experiencia de toda la comunidad académica.

**¡Cada contribución cuenta! 🌟**
