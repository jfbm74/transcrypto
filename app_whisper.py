import os
import time
import datetime
from faster_whisper import WhisperModel  # Cambiamos a faster-whisper
from openai import OpenAI
from flask import current_app
from werkzeug.utils import secure_filename

# Variable para almacenar el modelo de Whisper local
whisper_model = None

# Cliente de OpenAI
openai_client = None

def initialize_whisper_model():
    """Inicializa el modelo de Whisper local usando faster-whisper"""
    global whisper_model
    if whisper_model is None:
        # Puedes cambiar el modelo según tus necesidades: "tiny", "base", "small", "medium", "large"
        # Parámetro device: 'cuda' para GPU, 'cpu' para CPU
        device = "cpu"  # Usar CPU por defecto, cambia a "cuda" si tienes GPU compatible
        compute_type = "float32"  # Usar float32 para CPU, "float16" para GPU
        
        whisper_model = WhisperModel("medium", device=device, compute_type=compute_type)
        current_app.logger.info("Modelo Whisper (faster-whisper) inicializado correctamente")
    return whisper_model

def initialize_openai_client():
    """Inicializa el cliente de OpenAI con la clave API configurada"""
    global openai_client
    api_key = current_app.config['OPENAI_API_KEY']
    
    if openai_client is None and api_key:
        openai_client = OpenAI(api_key=api_key)
        current_app.logger.info("Cliente OpenAI inicializado correctamente")
    
    return openai_client

def transcribe_audio_locally(file_path):
    """Transcribe un archivo de audio usando faster-whisper instalado localmente"""
    model = initialize_whisper_model()
    if not model:
        raise ValueError("No se pudo inicializar el modelo Whisper local")
    
    # Realizar la transcripción con faster-whisper
    # La API es un poco diferente: primero devuelve segmentos, luego hay que unirlos
    segments, info = model.transcribe(file_path, language="es", task="transcribe")
    
    # Unir todos los segmentos en un texto completo
    transcription = ""
    for segment in segments:
        transcription += segment.text + " "
    
    return transcription.strip()

def transcribe_audio_api(file_path):
    """Transcribe un archivo de audio usando la API de OpenAI"""
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

def transcribe_audio(file_path):
    """Transcribe un archivo de audio, intentando primero localmente y luego con la API si falla"""
    try:
        # Intentar transcribir localmente primero
        return transcribe_audio_locally(file_path)
    except Exception as e:
        current_app.logger.warning(f"Transcripción local falló: {str(e)}. Intentando con API...")
        # Si falla, intentar con la API de OpenAI
        return transcribe_audio_api(file_path)

def generate_meeting_minutes(transcription):
    """Genera un acta de reunión basada en la transcripción usando GPT-4"""
    try:
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
        current_app.logger.error(f"Error al generar el acta: {str(e)}")
        return {"success": False, "error": str(e)}

def save_uploaded_file(file, user_id):
    """Guarda un archivo subido y devuelve información sobre el mismo"""
    # Crear un nombre de archivo seguro con timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    original_filename = file.filename
    filename = secure_filename(original_filename)
    safe_filename = f"{timestamp}_{user_id}_{filename}"
    
    # Ruta completa donde se guardará el archivo
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], safe_filename)
    
    # Guardar el archivo
    file.save(filepath)
    
    return {
        "original_filename": original_filename,
        "safe_filename": safe_filename,
        "filepath": filepath
    }

def save_transcription(transcription_text, original_filename, user_id):
    """Guarda la transcripción en un archivo y devuelve información"""
    # Crear un nombre de archivo para la transcripción
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.splitext(original_filename)[0]
    transcript_filename = f"{timestamp}_{user_id}_{base_filename}_transcripcion.txt"
    
    # Ruta completa donde se guardará la transcripción
    transcript_path = os.path.join(current_app.config["TRANSCRIPT_FOLDER"], transcript_filename)
    
    # Guardar la transcripción
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(transcription_text)
    
    return {
        "transcript_filename": transcript_filename,
        "transcript_path": transcript_path
    }

def process_audio_file(file, user_id):
    """Procesa un archivo de audio: guarda, transcribe y almacena la transcripción"""
    # Guardar el archivo
    file_info = save_uploaded_file(file, user_id)
    
    # Transcribir el audio
    start_time = time.time()
    transcription_text = transcribe_audio(file_info["filepath"])
    processing_time = time.time() - start_time
    
    # Guardar la transcripción
    transcription_info = save_transcription(
        transcription_text, 
        file_info["original_filename"],
        user_id
    )
    
    # Devolver toda la información
    return {
        "original_filename": file_info["original_filename"],
        "file_path": file_info["filepath"],
        "transcript_path": transcription_info["transcript_path"],
        "transcript_filename": transcription_info["transcript_filename"],
        "transcription_text": transcription_text,
        "processing_time": round(processing_time, 2)
    }