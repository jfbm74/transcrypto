# ZentraText de Audio

Aplicación web Flask para transcripción de audio a texto con IA, que permite convertir archivos de audio a texto y generar documentos estructurados como actas de reunión y documentos de requerimientos de software.

## ✨ Características Principales

- **🔐 Autenticación completa**: Registro, inicio de sesión y gestión de perfiles
- **🎵 Transcripción multi-formato**: Soporte para MP3, WAV, M4A, OGG, MP4
- **🤖 Doble proveedor de IA**: 
  - OpenAI Whisper + GPT-4 (principal)
  - Google AI Gemini (alternativo/respaldo)
- **📝 Generación de documentos**:
  - Actas de reunión con identificación de participantes
  - Documentos de requerimientos de software
- **📊 Historial de transcripciones** por usuario
- **💰 Modelo freemium**: 10 transcripciones gratuitas por usuario
- **📁 Archivos grandes**: División automática para archivos >25MB
- **🏗️ Arquitectura modular** con Blueprints de Flask

## Estructura del Proyecto

La aplicación está organizada de forma modular para facilitar su mantenimiento y extensión:

- `app.py`: Punto de entrada principal de la aplicación
- `config.py`: Configuración de la aplicación
- `modules/`: Módulos de la aplicación
  - `auth/`: Módulo de autenticación
  - `transcription/`: Módulo de transcripción
  - `subscription/`: Módulo para futuras suscripciones
- `templates/`: Plantillas HTML
- `static/`: Archivos estáticos (CSS, JS, imágenes)
- `uploads/`: Carpeta para archivos de audio subidos
- `transcripciones/`: Carpeta para guardar las transcripciones

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.8+
- Cuenta OpenAI con API Key (opcional: Google AI API Key)

### Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd transcripto
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   
   Crear archivo `.env` en la raíz del proyecto:
   ```env
   SECRET_KEY=tu_clave_secreta_muy_segura
   OPENAI_API_KEY=tu_clave_api_openai
   GOOGLE_AI_API_KEY=tu_clave_api_google_ai  # Opcional
   ```

5. **Inicializar base de datos**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Ejecutar aplicación**
   ```bash
   python app.py
   ```

La aplicación estará disponible en `http://localhost:5000`

## 📖 Uso

1. **Registro/Inicio de sesión**
   - Crear cuenta nueva o acceder con credenciales existentes

2. **Configuración de API**
   - Acceder a "Configuración API" desde el menú
   - Configurar clave OpenAI (obligatorio) y/o Google AI (opcional)

3. **Transcripción de audio**
   - Subir archivo de audio (formatos soportados: MP3, WAV, M4A, OGG, MP4)
   - El sistema maneja automáticamente archivos grandes (>25MB)
   - Esperar a que complete la transcripción

4. **Generación de documentos**
   - Ver transcripción en texto plano
   - Generar acta de reunión estructurada
   - Crear documento de requerimientos de software
   - Descargar documentos generados

5. **Historial**
   - Acceder al historial de transcripciones desde el menú superior
   - Revisar transcripciones anteriores y documentos generados

## 🛠️ Tecnologías Utilizadas

- **Backend**: Flask, SQLAlchemy, Flask-Login, Flask-Migrate
- **Base de datos**: SQLite
- **IA**: OpenAI Whisper & GPT-4, Google AI Gemini
- **Procesamiento de audio**: PyDub
- **Frontend**: HTML5, Bootstrap 5, JavaScript
- **Despliegue**: Gunicorn, SystemD

## 🔄 Roadmap y Futuras Mejoras

- [ ] Sistema de suscripción Premium
- [ ] Soporte multiidioma (detección automática)
- [ ] Panel de administración avanzado
- [ ] Exportación a PDF, DOCX, y otros formatos
- [ ] API REST para integraciones
- [ ] Procesamiento en lotes
- [ ] Análisis de sentimientos en transcripciones
- [ ] Integración con servicios de almacenamiento en la nube

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.