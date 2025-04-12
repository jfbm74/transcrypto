import os
import time
import datetime
from openai import OpenAI
from flask import current_app
from werkzeug.utils import secure_filename
from modules.utils.audio_processing import split_audio_file, combine_transcriptions, get_file_size
from modules.transcription.google_ai_service import generate_meeting_minutes_with_google

# Cliente de OpenAI
client = None

def initialize_openai_client():
    """Inicializa el cliente de OpenAI con la clave API configurada"""
    global client
    api_key = current_app.config['OPENAI_API_KEY']
    
    if client is None and api_key:
        client = OpenAI(api_key=api_key)
        current_app.logger.info("Cliente OpenAI inicializado correctamente")
    
    return client

def transcribe_audio(file_path):
    """Transcribe un archivo de audio usando la API de OpenAI"""
    client = initialize_openai_client()
    if not client:
        raise ValueError("No se ha configurado la clave de API de OpenAI")
    
    # Verificar el tamaño del archivo
    file_size_bytes = get_file_size(file_path)
    max_size_bytes = 25 * 1024 * 1024  # 25 MB en bytes
    
    if file_size_bytes > max_size_bytes:
        current_app.logger.info(f"Archivo grande ({file_size_bytes/1024/1024:.2f} MB) detectado, dividiendo en segmentos...")
        
        # Crear carpeta temporal para segmentos
        temp_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp_segments")
        os.makedirs(temp_folder, exist_ok=True)
        
        try:
            # Dividir el archivo en segmentos de máximo 20 MB para tener margen
            segment_paths = split_audio_file(file_path, max_size_mb=20, output_folder=temp_folder)
            current_app.logger.info(f"Archivo dividido en {len(segment_paths)} segmentos")
            
            # Transcribir cada segmento
            segment_transcriptions = []
            for i, segment_path in enumerate(segment_paths):
                current_app.logger.info(f"Transcribiendo segmento {i+1}/{len(segment_paths)}")
                
                with open(segment_path, "rb") as audio_file:
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="es"
                    )
                segment_transcriptions.append(transcription.text)
                
                # Eliminar el archivo del segmento después de procesarlo
                os.remove(segment_path)
            
            # Combinar todas las transcripciones
            full_transcription = combine_transcriptions(segment_transcriptions)
            return full_transcription
        
        finally:
            # Limpiar cualquier archivo temporal restante y eliminar carpeta temporal
            if os.path.exists(temp_folder):
                for file in os.listdir(temp_folder):
                    try:
                        os.remove(os.path.join(temp_folder, file))
                    except:
                        pass
                try:
                    os.rmdir(temp_folder)
                except:
                    pass
    
    # Proceso normal para archivos pequeños
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="es"
        )
    
    return transcription.text

def generate_meeting_minutes(transcription):
    """Genera un acta de reunión basada en la transcripción"""
    try:
        # Intentar con Google AI primero si está configurado
        if current_app.config.get('GOOGLE_AI_API_KEY'):
            current_app.logger.info("Generando acta con Google AI (Gemini)")
            return generate_meeting_minutes_with_google(transcription)
        
        # Si no está configurado Google AI, usar OpenAI como fallback
        current_app.logger.info("Generando acta con OpenAI (GPT)")
        client = initialize_openai_client()
        if not client:
            return {"success": False, "error": "No se pudo inicializar el cliente de OpenAI", "provider": "OpenAI"}
        
        # Crear el prompt para la API
        system_message = "Eres un asistente especializado en crear actas de reunión."
        user_message = f"""
        Por favor, convierte la siguiente transcripción en un acta de reunión formal. 

        Formato esperado:
        1. Título "ACTA DE REUNIÓN"
        2. Fecha y hora (extráelas del contenido si es posible, si no están, usa "No especificado")
        3. Asistentes (usa roles o nombres si están presentes en la conversación, sino "No especificado")
        4. Orden del día (temas principales agrupados temáticamente)
        5. Desarrollo (resumen por temas tratados, sin omitir detalles relevantes)
        6. Acuerdos y compromisos (extrae **todos los compromisos concretos**, responsables y fechas si se mencionan)
        7. Conclusión (resumen de lo acordado con énfasis en próximos pasos)

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
        current_app.logger.info("Acta generada exitosamente con OpenAI (GPT)")
        return {"success": True, "acta": acta_text, "provider": "OpenAI (GPT-4)"}
    
    except Exception as e:
        current_app.logger.error(f"Error al generar el acta: {str(e)}")
        return {"success": False, "error": str(e), "provider": "Error en generación"}

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
    # Asegurarse de que el nombre base no contenga caracteres problemáticos
    base_filename = "".join(c for c in base_filename if c.isalnum() or c in "._- ")
    transcript_filename = f"{timestamp}_{user_id}_{base_filename}_transcripcion.txt"
    
    # Ruta completa donde se guardará la transcripción
    transcript_path = os.path.join(current_app.config["TRANSCRIPT_FOLDER"], transcript_filename)
    
    # Crear la carpeta si no existe (por si acaso)
    os.makedirs(os.path.dirname(transcript_path), exist_ok=True)
    
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