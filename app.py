from flask import Flask, render_template, request, redirect, url_for, flash, send_file
import os
import whisper
import time
import datetime

# Configurar la aplicación Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Para manejar mensajes flash

# Configurar carpetas para subir y guardar archivos
UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripciones"
STATIC_FOLDER = "static"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRANSCRIPT_FOLDER"] = TRANSCRIPT_FOLDER

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
logo_path = os.path.join(STATIC_FOLDER, "img", "logo.svg")
if not os.path.exists(logo_path):
    with open(logo_path, "w", encoding="utf-8") as f:
        # Aquí iría el contenido SVG del logo creado anteriormente
        f.write("<!-- El contenido se generará desde el archivo logo.svg -->")

# Variable global para el modelo
model = None

# Función para cargar el modelo
def load_whisper_model():
    global model
    if model is None:
        # Puedes cambiar el tamaño del modelo según tus necesidades: tiny, base, small, medium, large
        model = whisper.load_model("medium")
        app.logger.info("Modelo Whisper cargado correctamente")
    return model

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    # Cargar el modelo si aún no está cargado
    global model
    if model is None:
        model = load_whisper_model()
    
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

    # Guardar el archivo cargado con un nombre único
    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        original_filename = file.filename
        safe_filename = f"{timestamp}_{original_filename}"
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], safe_filename)
        file.save(filepath)
        
        # Procesar el archivo con Whisper
        start_time = time.time()
        result = model.transcribe(filepath, language="es", task="transcribe")
        transcription = result["text"]
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500

if __name__ == "__main__":
    app.run(debug=True)