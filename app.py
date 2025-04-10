from flask import Flask, render_template, request, redirect, url_for, flash
import os
import whisper

# Configurar la aplicación Flask
app = Flask(__name__)
app.secret_key = "supersecretkey"  # Para manejar mensajes flash

# Configurar carpetas para subir y guardar archivos
UPLOAD_FOLDER = "uploads"
TRANSCRIPT_FOLDER = "transcripciones"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TRANSCRIPT_FOLDER"] = TRANSCRIPT_FOLDER

# Crear carpetas si no existen
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(TRANSCRIPT_FOLDER, exist_ok=True)

# Cargar el modelo de Whisper
model = whisper.load_model("medium")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_audio():
    # Verificar si hay un archivo en la solicitud
    if "file" not in request.files:
        flash("No file part")
        return redirect(url_for("index"))

    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(url_for("index"))

    # Guardar el archivo cargado
    if file:
        filename = file.filename
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(filepath)

        # Procesar el archivo con Whisper
        result = model.transcribe(filepath, language="es")
        transcription = result["text"]

        # Guardar la transcripción
        transcript_path = os.path.join(app.config["TRANSCRIPT_FOLDER"], f"{os.path.splitext(filename)[0]}_transcripcion.txt")
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        # Pasar la transcripción a la página
        return render_template("result.html", transcription=transcription)

    flash("Failed to upload file")
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)