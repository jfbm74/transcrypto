import os
import subprocess
import json
import math
import uuid
import mimetypes

def get_file_duration(file_path):
    """
    Obtiene la duración de un archivo de audio usando ffprobe
    con manejo de errores mejorado
    """
    try:
        cmd = [
            'ffprobe', 
            '-v', 'error', 
            '-show_entries', 'format=duration', 
            '-of', 'json', 
            file_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            # Si falla, intentar con una estrategia alternativa
            fallback_cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'stream=duration',
                '-select_streams', 'a:0',
                '-of', 'json',
                file_path
            ]
            fallback_result = subprocess.run(fallback_cmd, capture_output=True, text=True)
            if fallback_result.returncode != 0:
                # Si ambos intentos fallan, estimar la duración basada en el tamaño
                file_size = get_file_size(file_path)
                # Estimación aproximada: 1MB ≈ 1 minuto para audio de calidad media
                estimated_duration = (file_size / (1024 * 1024)) * 60
                return estimated_duration
            
            data = json.loads(fallback_result.stdout)
            if 'streams' in data and len(data['streams']) > 0 and 'duration' in data['streams'][0]:
                return float(data['streams'][0]['duration'])
            else:
                # Estimación basada en tamaño como último recurso
                file_size = get_file_size(file_path)
                estimated_duration = (file_size / (1024 * 1024)) * 60
                return estimated_duration
        
        data = json.loads(result.stdout)
        return float(data['format']['duration'])
    except Exception as e:
        # En caso de cualquier error, devolver una duración estimada
        file_size = get_file_size(file_path)
        estimated_duration = (file_size / (1024 * 1024)) * 60
        print(f"Error al obtener duración, usando estimación: {estimated_duration}s para {file_size} bytes")
        return estimated_duration


def get_file_size(file_path):
    """
    Obtiene el tamaño de un archivo en bytes
    """
    return os.path.getsize(file_path)

def split_audio_file(file_path, max_size_mb=24, output_folder=None):
    """
    Divide un archivo de audio en segmentos más pequeños usando ffmpeg.
    
    Args:
        file_path: Ruta al archivo de audio
        max_size_mb: Tamaño máximo deseado para cada segmento en MB
        output_folder: Carpeta donde guardar los segmentos
        
    Returns:
        Lista de rutas a los archivos de segmentos creados
    """
    if output_folder is None:
        output_folder = os.path.dirname(file_path)
    
    # Determinar extensión del archivo
    _, ext = os.path.splitext(file_path)
    
    # Obtener duración total del archivo
    duration = get_file_duration(file_path)
    file_size = get_file_size(file_path)
    
    # Calcular cuántos segmentos necesitamos
    max_size_bytes = max_size_mb * 1024 * 1024
    num_segments = math.ceil(file_size / max_size_bytes)
    
    # Calcular duración de cada segmento
    segment_duration = duration / num_segments
    
    # Crear segmentos
    segment_paths = []
    
    for i in range(num_segments):
        start_time = i * segment_duration
        segment_filename = f"segment_{uuid.uuid4().hex}{ext}"
        segment_path = os.path.join(output_folder, segment_filename)
        
        # Comando ffmpeg para extraer el segmento
        cmd = [
            'ffmpeg',
            '-y',  # Sobrescribir archivos existentes
            '-i', file_path,
            '-ss', str(start_time),
            '-t', str(segment_duration),
            '-c', 'copy',  # Copiar sin recodificar para mayor velocidad
            segment_path
        ]
        
        # Ejecutar comando
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Error al dividir el archivo: {result.stderr}")
        
        segment_paths.append(segment_path)
    
    return segment_paths

def combine_transcriptions(transcriptions):
    """
    Combina múltiples transcripciones en una sola.

    Args:
        transcriptions: Lista de textos transcritos

    Returns:
        Texto combinado
    """
    return " ".join(transcriptions)

def detect_file_type(file_path):
    """
    Detecta el tipo de archivo (audio o video) usando ffprobe.

    Args:
        file_path: Ruta al archivo a analizar

    Returns:
        Tupla (tipo, extensión) donde tipo es 'audio', 'video' o 'unknown'
    """
    try:
        # Primero intentar con la extensión
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Extensiones de video comunes
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
        # Extensiones de audio comunes
        audio_extensions = {'.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma'}

        # Verificar con ffprobe para mayor precisión
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'stream=codec_type',
            '-of', 'json',
            file_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            if 'streams' in data:
                has_video = any(s.get('codec_type') == 'video' for s in data['streams'])
                has_audio = any(s.get('codec_type') == 'audio' for s in data['streams'])

                if has_video:
                    return ('video', ext)
                elif has_audio:
                    return ('audio', ext)

        # Fallback: usar extensión
        if ext in video_extensions:
            return ('video', ext)
        elif ext in audio_extensions:
            return ('audio', ext)

        return ('unknown', ext)

    except Exception as e:
        print(f"Error al detectar tipo de archivo: {str(e)}")
        # Fallback: intentar con mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type:
            if mime_type.startswith('video/'):
                return ('video', ext)
            elif mime_type.startswith('audio/'):
                return ('audio', ext)

        return ('unknown', ext)

def convert_video_to_audio(video_path, output_folder=None, output_format='mp3'):
    """
    Convierte un archivo de video a audio (MP3) extrayendo la pista de audio.

    Args:
        video_path: Ruta al archivo de video
        output_folder: Carpeta donde guardar el archivo de audio (por defecto, la misma que el video)
        output_format: Formato de salida (por defecto 'mp3')

    Returns:
        Ruta al archivo de audio generado
    """
    if output_folder is None:
        output_folder = os.path.dirname(video_path)

    # Crear nombre de archivo de salida
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f"{base_name}_audio.{output_format}"
    output_path = os.path.join(output_folder, output_filename)

    try:
        # Comando ffmpeg para extraer audio
        cmd = [
            'ffmpeg',
            '-y',  # Sobrescribir archivo si existe
            '-i', video_path,
            '-vn',  # No video (solo audio)
            '-acodec', 'libmp3lame' if output_format == 'mp3' else 'copy',
            '-q:a', '2',  # Calidad de audio (2 es alta calidad para MP3)
            output_path
        ]

        # Ejecutar comando
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Error al convertir video a audio: {result.stderr}")

        return output_path

    except Exception as e:
        raise Exception(f"Error durante la conversión de video a audio: {str(e)}")

def convert_audio_to_mp3(audio_path, output_folder=None):
    """
    Convierte un archivo de audio a MP3 para garantizar compatibilidad con Whisper.

    Args:
        audio_path: Ruta al archivo de audio original
        output_folder: Carpeta donde guardar el MP3 (por defecto, la misma que el audio)

    Returns:
        Ruta al archivo MP3 generado
    """
    if output_folder is None:
        output_folder = os.path.dirname(audio_path)

    # Crear nombre de archivo de salida
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    output_filename = f"{base_name}_converted.mp3"
    output_path = os.path.join(output_folder, output_filename)

    try:
        # Comando ffmpeg para convertir a MP3
        cmd = [
            'ffmpeg',
            '-y',  # Sobrescribir archivo si existe
            '-i', audio_path,
            '-acodec', 'libmp3lame',
            '-q:a', '2',  # Calidad de audio alta
            '-ar', '44100',  # Sample rate estándar
            output_path
        ]

        # Ejecutar comando
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"Error al convertir audio a MP3: {result.stderr}")

        return output_path

    except Exception as e:
        raise Exception(f"Error durante la conversión de audio a MP3: {str(e)}")