"""
Servicio integrado de transcripción con diarización de hablantes

Combina Whisper (OpenAI) para transcripción con pyannote.audio para
identificación de hablantes, generando transcripciones con atribución
de texto a cada hablante.
"""

import os
import json
from typing import List, Dict, Tuple, Optional
from flask import current_app
from openai import OpenAI
from modules.transcription.diarization_service import get_diarization_service
from modules.utils.audio_processing import detect_file_type, convert_video_to_audio


def transcribe_with_diarization(
    audio_path: str,
    language: str = "es"
) -> Dict:
    """
    Transcribe un archivo de audio con identificación de hablantes

    Args:
        audio_path: Ruta al archivo de audio o video
        language: Código de idioma para Whisper (default: "es")

    Returns:
        Dict con estructura:
        {
            'success': bool,
            'transcription': str,  # Transcripción completa formateada
            'segments': [
                {
                    'start': float,
                    'end': float,
                    'speaker': str,
                    'text': str
                },
                ...
            ],
            'speakers': ['SPEAKER_00', 'SPEAKER_01', ...],
            'method': 'whisper_with_diarization'
        }
    """
    temp_audio_path = None

    try:
        current_app.logger.info(f"Iniciando transcripción con diarización: {audio_path}")

        # Paso 0: Detectar tipo de archivo y convertir video a audio si es necesario
        file_type, file_ext = detect_file_type(audio_path)
        current_app.logger.info(f"Tipo de archivo detectado: {file_type} ({file_ext})")

        actual_audio_path = audio_path
        if file_type == 'video':
            current_app.logger.info(f"Convirtiendo video a audio para diarización: {audio_path}")
            try:
                # Convertir video a audio en la misma carpeta
                output_folder = os.path.dirname(audio_path)
                temp_audio_path = convert_video_to_audio(
                    audio_path,
                    output_folder=output_folder,
                    output_format='mp3'
                )
                actual_audio_path = temp_audio_path
                current_app.logger.info(f"Video convertido exitosamente a: {actual_audio_path}")
            except Exception as e:
                current_app.logger.error(f"Error al convertir video a audio: {str(e)}")
                return {
                    'success': False,
                    'error': f"No se pudo convertir el video a audio: {str(e)}",
                    'method': 'error'
                }

        # Paso 1: Verificar disponibilidad de diarización
        diarization_service = get_diarization_service()
        if not diarization_service.is_available():
            current_app.logger.warning(
                "Servicio de diarización no disponible. "
                "Cayendo a transcripción simple sin identificación de hablantes."
            )
            # Fallback a transcripción normal
            from modules.transcription.services import transcribe_audio
            simple_transcription = transcribe_audio(actual_audio_path)

            # Limpiar archivo temporal si fue creado
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    current_app.logger.info(f"Archivo temporal eliminado: {temp_audio_path}")
                except Exception as e:
                    current_app.logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

            return {
                'success': True,
                'transcription': simple_transcription,
                'segments': [],
                'speakers': [],
                'method': 'whisper_only',
                'warning': 'Diarización no disponible. Configure HF_TOKEN para habilitar.'
            }

        # Paso 2: Realizar diarización (identificar segmentos por hablante)
        try:
            diarization_segments = diarization_service.diarize_audio(actual_audio_path)
        except Exception as diar_error:
            current_app.logger.error(f"Error en diarización: {str(diar_error)}")
            current_app.logger.warning("Cayendo a transcripción simple sin diarización")

            # Fallback a transcripción normal
            from modules.transcription.services import transcribe_audio
            simple_transcription = transcribe_audio(actual_audio_path)

            # Limpiar archivo temporal si fue creado
            if temp_audio_path and os.path.exists(temp_audio_path):
                try:
                    os.remove(temp_audio_path)
                    current_app.logger.info(f"Archivo temporal eliminado: {temp_audio_path}")
                except Exception as e:
                    current_app.logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

            return {
                'success': True,
                'transcription': simple_transcription,
                'segments': [],
                'speakers': [],
                'method': 'whisper_only',
                'warning': f'Error en diarización ({str(diar_error)}). Se procesó sin identificación de hablantes.'
            }

        # Paso 3: Transcribir con Whisper usando timestamps
        whisper_segments = _transcribe_with_timestamps(actual_audio_path, language)

        # Paso 4: Alinear transcripción de Whisper con segmentos de diarización
        aligned_segments = _align_transcription_with_diarization(
            whisper_segments,
            diarization_segments
        )

        # Paso 5: Formatear resultado final
        speakers = sorted(set(seg['speaker'] for seg in aligned_segments))
        formatted_transcription = _format_transcription_with_speakers(aligned_segments)

        current_app.logger.info(
            f"Transcripción con diarización completada. "
            f"Detectados {len(speakers)} hablantes en {len(aligned_segments)} segmentos"
        )

        # Limpiar archivo temporal si fue creado
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                current_app.logger.info(f"Archivo temporal eliminado: {temp_audio_path}")
            except Exception as e:
                current_app.logger.warning(f"No se pudo eliminar archivo temporal: {str(e)}")

        return {
            'success': True,
            'transcription': formatted_transcription,
            'segments': aligned_segments,
            'speakers': speakers,
            'method': 'whisper_with_diarization'
        }

    except Exception as e:
        current_app.logger.error(f"Error en transcripción con diarización: {str(e)}")

        # Limpiar archivo temporal si fue creado
        if temp_audio_path and os.path.exists(temp_audio_path):
            try:
                os.remove(temp_audio_path)
                current_app.logger.info(f"Archivo temporal eliminado tras error: {temp_audio_path}")
            except Exception as cleanup_error:
                current_app.logger.warning(f"No se pudo eliminar archivo temporal tras error: {str(cleanup_error)}")

        return {
            'success': False,
            'error': str(e),
            'method': 'error'
        }


def _transcribe_with_timestamps(audio_path: str, language: str) -> List[Dict]:
    """
    Transcribe audio usando Whisper con timestamps detallados

    Returns:
        Lista de segmentos de Whisper con formato:
        [{'start': float, 'end': float, 'text': str}, ...]
    """
    try:
        api_key = current_app.config['OPENAI_API_KEY']
        if not api_key:
            raise ValueError("OPENAI_API_KEY no configurada")

        client = OpenAI(api_key=api_key)

        # Verificar que el archivo existe y tiene extensión válida
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Archivo de audio no encontrado: {audio_path}")

        file_ext = os.path.splitext(audio_path)[1].lower()
        valid_extensions = ['.flac', '.m4a', '.mp3', '.mp4', '.mpeg', '.mpga', '.oga', '.ogg', '.wav', '.webm']

        if file_ext not in valid_extensions:
            raise ValueError(
                f"Formato de archivo no soportado: {file_ext}. "
                f"Formatos válidos: {', '.join(valid_extensions)}"
            )

        current_app.logger.info(f"Transcribiendo con Whisper: {audio_path} (formato: {file_ext})")

        # Transcribir con formato verbose_json para obtener timestamps
        with open(audio_path, "rb") as audio_file:
            # Nota: timestamp_granularity solo está disponible en versiones recientes de openai
            # Si falla, intentar sin ese parámetro
            try:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularity=["segment"]
                )
            except TypeError:
                # Fallback para versiones antiguas de openai
                current_app.logger.warning(
                    "timestamp_granularity no soportado, usando verbose_json sin granularidad"
                )
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )

        # Extraer segmentos con timestamps
        segments = []
        if hasattr(response, 'segments') and response.segments:
            for segment in response.segments:
                # Los segmentos son objetos, no diccionarios
                segments.append({
                    'start': segment.start if hasattr(segment, 'start') else segment.get('start', 0),
                    'end': segment.end if hasattr(segment, 'end') else segment.get('end', 0),
                    'text': (segment.text if hasattr(segment, 'text') else segment.get('text', '')).strip()
                })
        else:
            # Fallback si no hay segmentos (modelo retornó solo texto)
            current_app.logger.warning(
                "Whisper no retornó segmentos con timestamps. "
                "Usando transcripción completa sin segmentación."
            )
            segments.append({
                'start': 0.0,
                'end': 0.0,
                'text': response.text
            })

        return segments

    except Exception as e:
        error_msg = str(e)
        current_app.logger.error(f"Error en transcripción de Whisper: {error_msg}")
        current_app.logger.error(f"Archivo de audio: {audio_path}")
        current_app.logger.error(f"Tamaño del archivo: {os.path.getsize(audio_path) if os.path.exists(audio_path) else 'N/A'} bytes")

        # Si el error es de formato inválido, dar más contexto
        if "Invalid file format" in error_msg or "format" in error_msg.lower():
            file_ext = os.path.splitext(audio_path)[1].lower()
            current_app.logger.error(
                f"Error de formato detectado. Extensión del archivo: {file_ext}. "
                f"Verifique que el archivo no está corrupto y es un archivo de audio/video válido."
            )

        raise


def _align_transcription_with_diarization(
    whisper_segments: List[Dict],
    diarization_segments: List[Dict]
) -> List[Dict]:
    """
    Alinea segmentos de transcripción de Whisper con segmentos de diarización

    Asigna cada fragmento de texto transcrito al hablante correspondiente
    basándose en la superposición temporal.

    Args:
        whisper_segments: Segmentos de Whisper con 'start', 'end', 'text'
        diarization_segments: Segmentos de diarización con 'start', 'end', 'speaker'

    Returns:
        Lista de segmentos alineados con formato:
        [{'start': float, 'end': float, 'speaker': str, 'text': str}, ...]
    """
    aligned = []

    for whisper_seg in whisper_segments:
        # Encontrar el hablante con mayor superposición temporal
        best_speaker = _find_speaker_for_segment(
            whisper_seg['start'],
            whisper_seg['end'],
            diarization_segments
        )

        aligned.append({
            'start': whisper_seg['start'],
            'end': whisper_seg['end'],
            'speaker': best_speaker,
            'text': whisper_seg['text']
        })

    return aligned


def _find_speaker_for_segment(
    start: float,
    end: float,
    diarization_segments: List[Dict]
) -> str:
    """
    Encuentra el hablante con mayor superposición temporal con un segmento

    Args:
        start: Tiempo de inicio del segmento (segundos)
        end: Tiempo de fin del segmento (segundos)
        diarization_segments: Lista de segmentos de diarización

    Returns:
        ID del hablante (ej: 'SPEAKER_00') o 'UNKNOWN' si no hay superposición
    """
    max_overlap = 0
    best_speaker = 'UNKNOWN'

    segment_duration = end - start
    segment_midpoint = (start + end) / 2

    for diar_seg in diarization_segments:
        # Calcular superposición temporal
        overlap_start = max(start, diar_seg['start'])
        overlap_end = min(end, diar_seg['end'])
        overlap_duration = max(0, overlap_end - overlap_start)

        # También considerar si el punto medio del segmento cae dentro del segmento de diarización
        midpoint_in_segment = (
            diar_seg['start'] <= segment_midpoint <= diar_seg['end']
        )

        # Dar preferencia si el punto medio está dentro del segmento
        if midpoint_in_segment:
            overlap_duration += segment_duration * 0.5

        if overlap_duration > max_overlap:
            max_overlap = overlap_duration
            best_speaker = diar_seg['speaker']

    return best_speaker


def _format_transcription_with_speakers(segments: List[Dict]) -> str:
    """
    Formatea los segmentos alineados en texto legible con identificación de hablantes

    Args:
        segments: Lista de segmentos con 'speaker' y 'text'

    Returns:
        String formateado con formato:
        SPEAKER_00: Texto del hablante...
        SPEAKER_01: Respuesta del otro hablante...
        SPEAKER_00: Continuación...
    """
    if not segments:
        return ""

    formatted_lines = []
    current_speaker = None
    current_text = []

    for segment in segments:
        speaker = segment['speaker']
        text = segment['text']

        # Si cambia el hablante, guardar el texto acumulado del hablante anterior
        if speaker != current_speaker:
            if current_speaker is not None and current_text:
                formatted_lines.append(
                    f"{current_speaker}: {' '.join(current_text)}"
                )
            current_speaker = speaker
            current_text = [text]
        else:
            # Mismo hablante, acumular texto
            current_text.append(text)

    # Agregar el último segmento
    if current_speaker is not None and current_text:
        formatted_lines.append(
            f"{current_speaker}: {' '.join(current_text)}"
        )

    return "\n\n".join(formatted_lines)


def export_segments_to_json(segments: List[Dict], output_path: str) -> None:
    """
    Exporta segmentos alineados a un archivo JSON

    Útil para análisis posterior o visualización

    Args:
        segments: Lista de segmentos con diarización y transcripción
        output_path: Ruta donde guardar el archivo JSON
    """
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(segments, f, ensure_ascii=False, indent=2)
        current_app.logger.info(f"Segmentos exportados a: {output_path}")
    except Exception as e:
        current_app.logger.error(f"Error al exportar segmentos: {str(e)}")
        raise
