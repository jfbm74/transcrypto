from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
import os
from modules.transcription.services import process_audio_file, generate_meeting_minutes, generate_requirements
from modules.transcription.models import Transcription, db
import re

transcription_bp = Blueprint('transcription', __name__, url_prefix='/transcription')

@transcription_bp.route('/upload', methods=["POST"])
@login_required
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
    if not current_app.config['OPENAI_API_KEY']:
        flash("No se ha configurado la clave de API de OpenAI. Por favor, configúrala primero.")
        return redirect(url_for("api_settings"))
    
    # Verificar si el usuario puede realizar más transcripciones gratuitas
    free_limit = current_app.config['FREE_TRANSCRIPTIONS_LIMIT']
    if not current_user.can_transcribe(free_limit):
        flash(f"Has alcanzado el límite de {free_limit} transcripciones gratuitas. Por favor, actualiza a un plan de pago.")
        return redirect(url_for("index"))

    # Procesar el archivo
    try:
        result = process_audio_file(file, current_user.id)
        
        # Guardar la transcripción en la base de datos
        transcription = Transcription(
            user_id=current_user.id,
            original_filename=result["original_filename"],
            file_path=result["file_path"],
            transcript_path=result["transcript_path"],
            transcript_text=result["transcription_text"],
            processing_time=result["processing_time"]
        )
        db.session.add(transcription)
        db.session.commit()
        
        # Mostrar los resultados
        return render_template(
            "result.html", 
            transcription=result["transcription_text"],
            filename=result["original_filename"],
            processing_time=result["processing_time"],
            transcript_path=result["transcript_path"],
            transcription_id=transcription.id  # Añadir el ID directamente
        )
    
    except Exception as e:
        current_app.logger.error(f"Error al procesar el archivo: {str(e)}")
        flash(f"Error al procesar el archivo: {str(e)}")
        return redirect(url_for("index"))

@transcription_bp.route('/download/<filename>')
@login_required
def download_transcript(filename):
    try:
        # Verificar que la transcripción pertenece al usuario actual
        transcription = Transcription.query.filter_by(
            transcript_path=filename, 
            user_id=current_user.id
        ).first()
        
        if not transcription:
            flash("No se encontró la transcripción solicitada o no tienes permisos para acceder a ella.")
            return redirect(url_for("index"))
        
        file_path = os.path.join(current_app.config["TRANSCRIPT_FOLDER"], filename)
        
        # Verificar que el archivo existe
        if not os.path.exists(file_path):
            flash("El archivo de transcripción no se encuentra en el servidor.")
            return redirect(url_for("index"))
            
        # En Python 3.11, send_file puede requerir parámetros adicionales
        return send_file(
            file_path, 
            as_attachment=True,
            download_name=f"transcripcion_{transcription.original_filename}.txt",
            mimetype="text/plain"
        )
    except Exception as e:
        flash(f"Error al descargar el archivo: {str(e)}")
        return redirect(url_for("index"))

@transcription_bp.route('/generate-document', methods=["POST"])
@login_required
def generate_document():
    # Obtener la transcripción y el tipo de documento de la solicitud
    try:
        data = request.get_json()
        transcription = data.get("transcription", "")
        document_type = data.get("document_type", "acta")  # Por defecto es acta
        
        if not transcription:
            return jsonify({"success": False, "error": "No se proporcionó ninguna transcripción", "provider": "N/A"})
        
        # Registrar información sobre disponibilidad de API
        has_openai_api = bool(current_app.config.get('OPENAI_API_KEY', ''))
        has_google_api = bool(current_app.config.get('GOOGLE_AI_API_KEY', ''))
        
        current_app.logger.info(f"Generando {document_type}. APIs disponibles: OpenAI={has_openai_api}, Google AI={has_google_api}")
        
        # Llamar a la función correspondiente según el tipo de documento
        if document_type == 'requirements':
            result = generate_requirements(transcription)
        else:  # Por defecto, generar acta
            result = generate_meeting_minutes(transcription)
        
        # Devolver la respuesta con el mismo formato que antes, pero en campo content en vez de acta
        response = {
            "success": result.get("success", False),
            "content": result.get("acta") or result.get("requirements_doc") or "",
            "provider": result.get("provider", "Desconocido"),
            "error": result.get("error", "")
        }
        
        return jsonify(response)
    
    except Exception as e:
        current_app.logger.error(f"Error al generar el documento: {str(e)}")
        return jsonify({"success": False, "error": str(e), "provider": "Error en generación"})

@transcription_bp.route('/save-acta', methods=["POST"])
@login_required
def save_acta():
    try:
        data = request.get_json()
        transcription_id = data.get("transcription_id")
        acta_text = data.get("acta_text")
        document_type = data.get("document_type", "acta")  # Incluir el tipo de documento
        
        if not transcription_id or not acta_text:
            return jsonify({"success": False, "error": "Faltan datos requeridos"})
        
        # Verificar que la transcripción pertenece al usuario actual
        transcription = Transcription.query.filter_by(
            id=transcription_id, 
            user_id=current_user.id
        ).first()
        
        if not transcription:
            return jsonify({"success": False, "error": "Transcripción no encontrada"})
        
        # Tratar de limpiar el texto si viene con HTML
        if '<br>' in acta_text:
            # Reemplazar <br> con saltos de línea
            acta_text = acta_text.replace('<br>', '\n')
            # Eliminar otras etiquetas HTML
            acta_text = re.sub(r'<[^>]*>', '', acta_text)
        
        # Guardar el acta en la base de datos y el tipo de documento
        transcription.acta_text = acta_text
        transcription.document_type = document_type  # Guardar el tipo de documento
        db.session.commit()
        
        current_app.logger.info(f"Documento tipo {document_type} guardado correctamente para transcripción ID {transcription_id}")
        
        return jsonify({"success": True, "message": "Documento guardado correctamente"})
    
    except Exception as e:
        current_app.logger.error(f"Error al guardar el documento: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@transcription_bp.route('/history')
@login_required
def history():
    # Obtener todas las transcripciones del usuario actual
    transcriptions = Transcription.query.filter_by(
        user_id=current_user.id
    ).order_by(Transcription.created_at.desc()).all()
    
    # Agregar logging para depuración
    current_app.logger.info(f"Obtenidas {len(transcriptions)} transcripciones para el usuario {current_user.id}")
    for t in transcriptions:
        current_app.logger.info(f"Transcripción ID {t.id}: acta_text: {'Disponible' if t.acta_text else 'No disponible'}")
    
    return render_template(
        'transcription/history.html', 
        title='Historial de Transcripciones',
        transcriptions=transcriptions
    )

@transcription_bp.route('/get-transcription-id', methods=["POST"])
@login_required
def get_transcription_id():
    """Obtiene el ID de una transcripción a partir de su path de archivo"""
    try:
        data = request.get_json()
        transcript_path = data.get("transcript_path", "")
        
        if not transcript_path:
            return jsonify({"success": False, "error": "No se proporcionó el path de la transcripción"})
        
        # Buscar la transcripción por su path de archivo
        transcription = Transcription.query.filter_by(
            transcript_path=transcript_path, 
            user_id=current_user.id
        ).first()
        
        if not transcription:
            return jsonify({"success": False, "error": "Transcripción no encontrada"})
        
        # Devolver el ID
        return jsonify({
            "success": True, 
            "transcription_id": transcription.id
        })
    
    except Exception as e:
        current_app.logger.error(f"Error al obtener ID de transcripción: {str(e)}")
        return jsonify({"success": False, "error": str(e)})