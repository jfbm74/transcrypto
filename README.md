# ZentraText

ZentraText es una aplicación web que permite transcribir archivos de audio a texto utilizando inteligencia artificial, con la funcionalidad adicional de convertir las transcripciones en actas de reunión formateadas profesionalmente mediante la API de OpenAI.

![Logo de ZentraText](static/img/logo.svg)

## Características

- 🎤 **Transcripción de audio a texto**: Utiliza el modelo Whisper de OpenAI para transcribir audio con alta precisión
- 📝 **Generación de actas de reunión**: Convierte automáticamente transcripciones en actas formales utilizando GPT
- 🌐 **Interfaz web intuitiva**: Diseño moderno y fácil de usar con drag & drop para subir archivos
- 💾 **Descarga de resultados**: Guarda transcripciones y actas en formato de texto
- 🔒 **Procesamiento local**: Los archivos de audio se procesan en tu propio servidor

## Capturas de pantalla

*(Agrega capturas de pantalla de tu aplicación aquí)*

## Instalación

### Requisitos previos

- Python 3.8 o superior
- Pip (administrador de paquetes de Python)
- Una clave de API de OpenAI (para la funcionalidad de generación de actas)

### Pasos de instalación

1. **Clona el repositorio**

```bash
git clone https://github.com/tu-usuario/zentratext.git
cd zentratext
```

2. **Crea un entorno virtual (opcional pero recomendado)**

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. **Instala las dependencias**

```bash
pip install -r requirements.txt
```

4. **Configura la clave de API de OpenAI (opcional)**

Puedes configurar tu clave API mediante variables de entorno:

```bash
# Linux/Mac
export OPENAI_API_KEY=tu_clave_api_aqui

# Windows (PowerShell)
$env:OPENAI_API_KEY="tu_clave_api_aqui"

# Windows (Command Prompt)
set OPENAI_API_KEY=tu_clave_api_aqui
```

Alternativamente, puedes introducir la clave directamente en la aplicación a través de la página de configuración.

5. **Ejecuta la aplicación**

```bash
python app.py
```

La aplicación estará disponible en `http://localhost:5000`

## Uso

### Transcripción de audio a texto

1. Accede a la página principal de la aplicación
2. Arrastra un archivo de audio o haz clic para seleccionarlo (formatos soportados: MP3, WAV, M4A, OGG, MP4)
3. Haz clic en "Transcribir ahora"
4. Espera a que se complete el procesamiento
5. La transcripción se mostrará en la página de resultados

### Generación de actas de reunión

1. Después de obtener una transcripción, haz clic en el botón "Generar Acta"
2. Si aún no has configurado tu clave API de OpenAI, la aplicación te pedirá que lo hagas
3. Espera mientras se genera el acta
4. El acta formateada aparecerá en un modal
5. Puedes copiar el texto o descargar el acta como archivo TXT

## Estructura del proyecto

```
zentratext/
├── app.py                    # Aplicación principal de Flask
├── uploads/                  # Carpeta para archivos de audio subidos
├── transcripciones/          # Carpeta para transcripciones guardadas
├── static/
│   ├── css/
│   │   └── styles.css        # Estilos CSS
│   └── img/
│       └── logo.svg          # Logo de ZentraText
└── templates/
    ├── index.html            # Página principal
    ├── result.html           # Página de resultados
    ├── api_settings.html     # Página de configuración de API
    ├── 404.html              # Página de error 404
    └── 500.html              # Página de error 500
```

## Tecnologías utilizadas

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **IA para transcripción**: Whisper de OpenAI
- **IA para generación de actas**: API de OpenAI (GPT-4/GPT-3.5)
- **Iconos**: Font Awesome
- **Fuentes**: Google Fonts (Poppins)

## Personalización

### Cambiar el modelo de Whisper

Puedes modificar el tamaño del modelo Whisper en `app.py` para equilibrar precisión y velocidad:

```python
# Tamaños disponibles: tiny, base, small, medium, large
model = whisper.load_model("medium")  # Cambia a "small" para mayor velocidad o "large" para mayor precisión
```

### Personalizar el formato de las actas

Para cambiar el formato o estructura de las actas generadas, edita el prompt en la función `generate_meeting_minutes()` en `app.py`.

## Consideraciones

- El procesamiento de archivos de audio largos puede llevar tiempo y consumir recursos significativos
- El uso de la API de OpenAI para generar actas tiene costos asociados
- La precisión de la transcripción puede variar según la calidad del audio y el acento de los hablantes

## Próximas mejoras

- [ ] Autenticación de usuarios
- [ ] Historial de transcripciones
- [ ] Exportación a formatos adicionales (PDF, DOCX)
- [ ] Detección automática de participantes
- [ ] Resumen automático de transcripciones
- [ ] Soporte para múltiples idiomas

## Licencia

[MIT License](LICENSE)

## Contribuciones

Las contribuciones son bienvenidas. Para cambios importantes, por favor abre primero un issue para discutir lo que te gustaría cambiar.

## Contacto

Si tienes preguntas o comentarios, puedes contactarme en [tu-email@ejemplo.com](mailto:tu-email@ejemplo.com)
