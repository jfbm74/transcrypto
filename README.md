# App de Transcripción de Audio

Esta aplicación permite transcribir archivos de audio a texto utilizando la API de OpenAI (Whisper) y generar actas de reunión a partir de las transcripciones utilizando GPT-4.

## Características

- Autenticación de usuarios (registro, inicio de sesión, perfil)
- Transcripción de archivos de audio (MP3, WAV, M4A, OGG, MP4)
- Generación de actas de reunión a partir de transcripciones
- Historial de transcripciones por usuario
- Límite de 10 transcripciones gratuitas por usuario
- Estructura modular para fácil mantenimiento y extensión

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

## Instalación

1. Clonar el repositorio
2. Crear un entorno virtual:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```
3. Instalar las dependencias:
   ```
   pip install -r requirements.txt
   ```
4. Configurar las variables de entorno en el archivo `.env`:
   ```
   SECRET_KEY=tu_clave_secreta
   DATABASE_URI=sqlite:///instance/app.db
   OPENAI_API_KEY=tu_clave_api_openai
   ```
5. Inicializar la base de datos:
   ```
   flask db init
   flask db migrate -m "Initial migration."
   flask db upgrade
   ```
6. Ejecutar la aplicación:
   ```
   python app.py
   ```

## Uso

1. Registrarse o iniciar sesión en la aplicación
2. Configurar la clave de API de OpenAI en la sección "Configuración API"
3. Subir un archivo de audio para transcribirlo
4. Ver la transcripción y descargarla o generar un acta de reunión
5. Acceder al historial de transcripciones desde el menú superior

## Futuras Mejoras

- Sistema de suscripción para permitir más transcripciones
- Soporte para más idiomas
- Mejoras en la generación de actas de reunión
- Panel de administración para gestionar usuarios y transcripciones
- Exportación de transcripciones en diferentes formatos (PDF, DOCX, etc.)

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo LICENSE para más detalles.