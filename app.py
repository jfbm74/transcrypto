from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import os
import time
import datetime
import requests
import json
from dotenv import load_dotenv
from openai import OpenAI  # Use OpenAI client instead of standalone whisper

# Cargar variables desde archivo .env
load_dotenv()

# Configurar la aplicación Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Para manejar mensajes flash

# Configurar carpetas para subir y guardar archivos
UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripciones"
STATIC_FOLDER = "static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRANSCRIPT_FOLDER"] = TRANSCRIPT_FOLDER

# Variable para almacenar tu token de API de OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Crear carpetas si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, "css"), exist_ok=True)
os.makedirs(os.path.join(STATIC_FOLDER, "img"), exist_ok=True)

# Crear el archivo CSS si no existe
css_path = os.path.join(STATIC_FOLDER, "css", "styles.css")
if not os.path.exists(css_path):
    with open(css_path, "w", encoding="utf-8") as f:
        # Aquí iría el CSS del archivo styles.css creado anteriormente
        f.write("/* El contenido se generará desde el archivo styles.css */")

# Crear el archivo SVG del logo si no existe
logo_path = os.path.join(STATIC_FOLDER, "img", "5_Logo_Icono.png")
if not os.path.exists(logo_path):
    with open(logo_path, "w", encoding="utf-8") as f:
        # Aquí iría el contenido SVG del logo creado anteriormente
        f.write("<!-- El contenido se generará desde el archivo 5_Logo_Icono.png -->")

# Inicializar el cliente de OpenAI
client = None

# Función para inicializar el cliente de OpenAI
def initialize_openai_client():
    global client, OPENAI_API_KEY
    if client is None and OPENAI_API_KEY:
        client = OpenAI(api_key=OPENAI_API_KEY)
        app.logger.info("Cliente OpenAI inicializado correctamente")
    return client

# Función para transcribir audio usando la API de OpenAI
def transcribe_audio(file_path):
    client = initialize_openai_client()
    if not client:
        raise ValueError("No se ha configurado la clave de API de OpenAI")
    
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es"
        )
    
    return transcription.text

# Función para generar un acta de reunión utilizando la API de ChatGPT
def generate_meeting_minutes(transcription):
    try:
        # Verificar si tenemos una clave de API válida
        if not OPENAI_API_KEY:
            return {"success": False, "error": "No se ha configurado la clave de API de OpenAI"}
        
        client = initialize_openai_client()
        if not client:
            return {"success": False, "error": "No se pudo inicializar el cliente de OpenAI"}
        
        # Crear el prompt para la API
        system_message = "Eres un asistente especializado en crear actas de reunión."
        user_message = f"""
        Por favor, convierte la siguiente transcripción en un acta de reunión formal. 
        La transcripción es de una reunión. 
        Crea un formato de acta con:
        
        1. Título "ACTA DE REUNIÓN"
        2. Fecha y hora (extráelas del contenido si es posible, si no están, usa "No especificado")
        3. Asistentes (extráelos del contenido si es posible, si no están, indica "No especificado")
        4. Orden del día (basado en los temas principales discutidos)
        5. Desarrollo (resumido por puntos principales, manteniendo la información clave)
        6. Acuerdos y compromisos (extraídos de la conversación)
        7. Conclusión
        
        Aquí está la transcripción:
        
        {transcription}
        """
        
        # Realizar la solicitud a la API usando el cliente de OpenAI
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7
        )
        
        # Obtener la respuesta
        acta_text = response.choices[0].message.content
        return {"success": True, "acta": acta_text}
    
    except Exception as e:
        app.logger.error(f"Error al generar el acta: {str(e)}")
        return {"success": False, "error": str(e)}

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api-settings")
def api_settings():
    return render_template("api_settings.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    # Verificar si hay un archivo en la solicitud
    if "file" not in request.files:
        flash("No se encontró ningún archivo en la solicitud")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No se seleccionó ningún archivo")
        return redirect(url_for("index"))

    # Verificar la extensión del archivo
    allowed_extensions = {'mp3', 'wav', 'm4a', 'ogg', 'mp4'}
    if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash("Formato de archivo no soportado. Por favor, sube un archivo MP3, WAV, M4A, OGG o MP4.")
        return redirect(url_for("index"))

    # Verificar si tenemos la clave API configurada
    if not OPENAI_API_KEY:
        flash("No se ha configurado la clave de API de OpenAI. Por favor, configúrala primero.")
        return redirect(url_for("api_settings"))

    # Guardar el archivo cargado con un nombre único
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = file.filename
        safe_filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
        file.save(filepath)
        
        # Procesar el archivo con la API de OpenAI
        start_time = time.time()
        transcription = transcribe_audio(filepath)
        processing_time = time.time() - start_time
        
        # Guardar la transcripción
        base_filename = os.path.splitext(original_filename)[0]
        transcript_filename = f"{timestamp}_{base_filename}_transcripcion.txt"
        transcript_path = os.path.join(app.config["TRANSCRIPT_FOLDER"], transcript_filename)
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcription)
        
        # Pasar la transcripción y metadatos a la página
        return render_template(
            "result.html", 
            transcription=transcription,
            filename=original_filename,
            processing_time=round(processing_time, 2),
            transcript_path=transcript_filename
        )
    
    except Exception as e:
        app.logger.error(f"Error al procesar el archivo: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}")
        return redirect(url_for("index"))

@app.route("/download/<filename>")
def download_transcript(filename):
    try:
        return send_file(os.path.join(app.config["TRANSCRIPT_FOLDER"], filename), as_attachment=True)
    except Exception as e:
        flash(f"Error al descargar el archivo: {str(e)}")
        return redirect(url_for("index"))

@app.route("/generate-acta", methods=["POST"])
def generate_acta():
    # Obtener la transcripción de la solicitud
    try:
        data = request.get_json()
        transcription = data.get("transcription", "")
        
        if not transcription:
            return jsonify({"success": False, "error": "No se proporcionó ninguna transcripción"})
        
        # Llamar a la función para generar el acta
        result = generate_meeting_minutes(transcription)
        
        # Devolver la respuesta
        return jsonify(result)
    
    except Exception as e:
        app.logger.error(f"Error al generar el acta: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route("/set-api-key", methods=["POST"])
def set_api_key():
    # Ruta para configurar la clave de API (idealmente debería tener autenticación)
    try:
        data = request.get_json()
        api_key = data.get("api_key", "")
        
        if not api_key:
            return jsonify({"success": False, "error": "No se proporcionó una clave de API válida"})
        
        # En un entorno de producción, esto debería manejarse de manera más segura
        global OPENAI_API_KEY, client
        OPENAI_API_KEY = api_key
        client = None  # Reiniciar el cliente para que se vuelva a crear con la nueva clave
        initialize_openai_client()  # Inicializar con la nueva clave
        
        return jsonify({"success": True, "message": "Clave de API configurada correctamente"})
    
    except Exception as e:
        app.logger.error(f"Error al configurar la clave de API: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)