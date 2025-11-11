from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
import os
import json
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
    allowed_extensions = {'mp3', 'wav', 'm4a', 'ogg', 'mp4', 'avi', 'mov', 'mkv', 'flv', 'wmv', 'webm'}
    if not '.' in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
        flash("Formato de archivo no soportado. Por favor, sube un archivo de audio (MP3, WAV, M4A, OGG) o video (MP4, AVI, MOV, MKV, FLV, WMV, WEBM).")
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

    # Verificar si el usuario habilitó la diarización
    enable_diarization = request.form.get('enable_diarization') == 'on'

    current_app.logger.info(f"Procesando archivo con diarización: {enable_diarization}")

    # Procesar el archivo
    try:
        # Si la diarización está habilitada, usar el servicio de diarización
        if enable_diarization:
            from modules.transcription.whisper_diarization_service import transcribe_with_diarization
            from modules.transcription.services import save_uploaded_file, save_transcription
            import time

            # Guardar el archivo
            file_info = save_uploaded_file(file, current_user.id)

            # Procesar con diarización
            start_time = time.time()
            diarization_result = transcribe_with_diarization(file_info["filepath"])
            processing_time = time.time() - start_time

            if not diarization_result['success']:
                # Si falla la diarización, informar al usuario
                flash(f"Error en diarización: {diarization_result.get('error', 'Error desconocido')}. Intenta sin diarización.")
                return redirect(url_for("index"))

            # Guardar la transcripción
            transcription_info = save_transcription(
                diarization_result['transcription'],
                file_info["original_filename"],
                current_user.id
            )

            # Preparar resultado
            result = {
                "original_filename": file_info["original_filename"],
                "file_path": file_info["filepath"],
                "transcript_path": transcription_info["transcript_path"],
                "transcription_text": diarization_result['transcription'],
                "processing_time": round(processing_time, 2),
                "has_diarization": True,
                "speakers": diarization_result.get('speakers', []),
                "segments": diarization_result.get('segments', [])
            }
        else:
            # Procesamiento normal sin diarización
            result = process_audio_file(file, current_user.id)
            result["has_diarization"] = False
            result["speakers"] = []
            result["segments"] = []

        # Guardar la transcripción en la base de datos
        transcription = Transcription(
            user_id=current_user.id,
            original_filename=result["original_filename"],
            file_path=result["file_path"],
            transcript_path=result["transcript_path"],
            transcript_text=result["transcription_text"],
            processing_time=result["processing_time"],
            has_diarization=result["has_diarization"],
            speakers_count=len(result["speakers"]) if result["has_diarization"] else None,
            diarization_segments=json.dumps(result["segments"]) if result["has_diarization"] else None
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
            transcription_id=transcription.id,
            has_diarization=result["has_diarization"],
            speakers=result["speakers"],
            speakers_count=len(result["speakers"]) if result["has_diarization"] else 0
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
        
        # Obtener el proveedor preferido del usuario
        user_provider = current_user.ai_provider if hasattr(current_user, 'ai_provider') and current_user.ai_provider else 'openai'

        # Llamar a la función correspondiente según el tipo de documento
        if document_type == 'requirements':
            result = generate_requirements(transcription, user_provider)
        else:  # Por defecto, generar acta
            result = generate_meeting_minutes(transcription, user_provider)
        
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

@transcription_bp.route('/confluence/spaces', methods=["GET"])
@login_required
def get_confluence_spaces():
    """Obtiene la lista de espacios de Confluence del usuario"""
    try:
        from modules.transcription.confluence_service import ConfluenceService

        # Verificar que el usuario tenga Confluence configurado
        current_app.logger.info(f"Usuario {current_user.id} solicitando espacios de Confluence")
        if not current_user.has_confluence_configured():
            current_app.logger.warning(f"Usuario {current_user.id} no tiene Confluence configurado")
            return jsonify({"success": False, "error": "Confluence no está configurado"})

        current_app.logger.info(f"Confluence configurado para usuario {current_user.id}: email={current_user.confluence_email}, url={current_user.confluence_url}")

        # Crear servicio de Confluence
        confluence = ConfluenceService(
            current_user.confluence_email,
            current_user.get_confluence_token(),
            current_user.confluence_url
        )

        # Obtener espacios
        result = confluence.get_spaces()

        # Agregar espacio por defecto si está configurado
        if result['success']:
            result['default_space'] = current_user.confluence_default_space

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error al obtener espacios de Confluence: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({"success": False, "error": str(e)})

@transcription_bp.route('/confluence/pages', methods=["GET"])
@login_required
def get_confluence_pages():
    """Obtiene las páginas de un espacio de Confluence"""
    try:
        from modules.transcription.confluence_service import ConfluenceService

        space_key = request.args.get('space_key')
        if not space_key:
            return jsonify({"success": False, "error": "Falta el parámetro space_key"})

        # Verificar que el usuario tenga Confluence configurado
        if not current_user.has_confluence_configured():
            return jsonify({"success": False, "error": "Confluence no está configurado"})

        # Crear servicio de Confluence
        confluence = ConfluenceService(
            current_user.confluence_email,
            current_user.get_confluence_token(),
            current_user.confluence_url
        )

        # Obtener páginas del espacio
        result = confluence.get_pages_in_space(space_key)

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error al obtener páginas de Confluence: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@transcription_bp.route('/confluence/publish', methods=["POST"])
@login_required
def publish_to_confluence():
    """Publica un documento en Confluence"""
    try:
        from modules.transcription.confluence_service import ConfluenceService
        from datetime import datetime

        data = request.get_json()
        transcription_id = data.get("transcription_id")
        page_title = data.get("page_title")
        space_key = data.get("space_key")
        parent_page_id = data.get("parent_page_id")
        content = data.get("content")
        document_type = data.get("document_type", "acta")

        # Validar datos requeridos
        if not all([transcription_id, page_title, space_key, content]):
            return jsonify({"success": False, "error": "Faltan datos requeridos"})

        # Verificar que el usuario tenga Confluence configurado
        if not current_user.has_confluence_configured():
            return jsonify({"success": False, "error": "Confluence no está configurado"})

        # Verificar que la transcripción pertenece al usuario
        transcription = Transcription.query.filter_by(
            id=transcription_id,
            user_id=current_user.id
        ).first()

        if not transcription:
            return jsonify({"success": False, "error": "Transcripción no encontrada"})

        # Crear servicio de Confluence
        confluence = ConfluenceService(
            current_user.confluence_email,
            current_user.get_confluence_token(),
            current_user.confluence_url
        )

        # Preparar etiquetas/labels
        labels = ["transcripcion", document_type, datetime.now().strftime("%Y-%m")]

        # Publicar o actualizar página
        result = confluence.publish_or_update_page(
            space_key=space_key,
            title=page_title,
            content=content,
            parent_id=parent_page_id,
            labels=labels
        )

        # Si fue exitoso, actualizar la transcripción con la información de Confluence
        if result['success']:
            transcription.confluence_page_id = result['page_id']
            transcription.confluence_page_url = result['page_url']
            transcription.confluence_published_at = datetime.utcnow()
            db.session.commit()

            current_app.logger.info(f"Documento publicado en Confluence: {result['page_url']}")

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Error al publicar en Confluence: {str(e)}")
        return jsonify({"success": False, "error": str(e)})