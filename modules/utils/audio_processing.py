import os
import subprocess
import json
import math
import uuid

def get_file_duration(file_path):
    """
    Obtiene la duración de un archivo de audio usando ffprobe
    """
    cmd = [
        'ffprobe', 
        '-v', 'error', 
        '-show_entries', 'format=duration', 
        '-of', 'json', 
        file_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error al obtener la duración del archivo: {result.stderr}")
    
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

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
    return "\n\n".join(transcriptions)