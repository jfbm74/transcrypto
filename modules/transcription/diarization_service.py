"""
Servicio de diarización de hablantes usando pyannote.audio

Este módulo proporciona funcionalidad para identificar diferentes hablantes
en un archivo de audio y segmentar la transcripción por hablante.
"""

import os
import torch
from flask import current_app
from typing import List, Dict, Tuple
from pydub import AudioSegment


class DiarizationService:
    """Servicio para identificación y segmentación de hablantes"""

    def __init__(self):
        self.pipeline = None
        self._initialized = False

    def initialize(self):
        """
        Inicializa el pipeline de diarización de pyannote.audio

        Requiere un token de Hugging Face para descargar los modelos.
        El token debe estar configurado en HF_TOKEN en las variables de entorno.
        """
        if self._initialized:
            return True

        try:
            from pyannote.audio import Pipeline

            hf_token = current_app.config.get('HF_TOKEN')
            if not hf_token:
                current_app.logger.warning(
                    "HF_TOKEN no configurado. La diarización no estará disponible. "
                    "Obtén un token en: https://huggingface.co/settings/tokens"
                )
                return False

            # Usar el modelo community (gratuito) de pyannote
            # Alternativa premium: "pyannote/speaker-diarization-precision-2"
            model_name = "pyannote/speaker-diarization-3.1"

            current_app.logger.info(f"Inicializando pipeline de diarización: {model_name}")

            # Determinar dispositivo (GPU si está disponible)
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            current_app.logger.info(f"Usando dispositivo: {device}")

            self.pipeline = Pipeline.from_pretrained(
                model_name,
                use_auth_token=hf_token
            )

            # Mover el pipeline al dispositivo apropiado
            if device.type == "cuda":
                self.pipeline.to(device)

            self._initialized = True
            current_app.logger.info("Pipeline de diarización inicializado correctamente")
            return True

        except ImportError:
            current_app.logger.error(
                "pyannote.audio no está instalado. "
                "Instala con: pip install pyannote.audio"
            )
            return False
        except Exception as e:
            current_app.logger.error(f"Error al inicializar pipeline de diarización: {str(e)}")
            return False

    def diarize_audio(self, audio_path: str) -> List[Dict]:
        """
        Realiza diarización en un archivo de audio

        Args:
            audio_path: Ruta al archivo de audio

        Returns:
            Lista de segmentos con formato:
            [
                {
                    'start': 0.0,        # tiempo de inicio en segundos
                    'end': 5.2,          # tiempo de fin en segundos
                    'speaker': 'SPEAKER_00'  # identificador del hablante
                },
                ...
            ]
        """
        if not self._initialized:
            current_app.logger.info("Inicializando servicio de diarización...")
            if not self.initialize():
                raise RuntimeError("No se pudo inicializar el servicio de diarización")

        try:
            current_app.logger.info(f"Iniciando diarización de: {audio_path}")

            # Obtener duración del archivo
            import os
            file_size_mb = os.path.getsize(audio_path) / (1024 * 1024)
            current_app.logger.info(f"Tamaño del archivo: {file_size_mb:.2f} MB")
            current_app.logger.info("Ejecutando pipeline de diarización... (esto puede tomar varios minutos)")

            # Ejecutar el pipeline de diarización
            diarization = self.pipeline(audio_path)

            current_app.logger.info("Pipeline de diarización completado")

            # Convertir el resultado a una lista de segmentos
            segments = []

            # pyannote 4.0+ retorna un objeto DiarizeOutput con atributo speaker_diarization
            if hasattr(diarization, 'speaker_diarization'):
                # Versión nueva de pyannote (4.0+)
                current_app.logger.info("Usando API de pyannote 4.0+")
                for turn, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
                    segments.append({
                        'start': turn.start,
                        'end': turn.end,
                        'speaker': speaker
                    })
            elif hasattr(diarization, 'itertracks'):
                # Versión antigua de pyannote (< 4.0)
                current_app.logger.info("Usando API de pyannote < 4.0")
                for turn, _, speaker in diarization.itertracks(yield_label=True):
                    segments.append({
                        'start': turn.start,
                        'end': turn.end,
                        'speaker': speaker
                    })
            else:
                raise RuntimeError("Formato de diarización no reconocido")

            current_app.logger.info(
                f"Diarización completada. "
                f"Detectados {len(set(s['speaker'] for s in segments))} hablantes en "
                f"{len(segments)} segmentos"
            )

            return segments

        except Exception as e:
            current_app.logger.error(f"Error durante la diarización: {str(e)}")
            raise

    def extract_audio_segment(
        self,
        audio_path: str,
        start_time: float,
        end_time: float,
        output_path: str = None
    ) -> str:
        """
        Extrae un segmento de audio entre dos tiempos

        Args:
            audio_path: Ruta al archivo de audio original
            start_time: Tiempo de inicio en segundos
            end_time: Tiempo de fin en segundos
            output_path: Ruta opcional para guardar el segmento (si no se provee, usa temp)

        Returns:
            Ruta al archivo del segmento extraído
        """
        try:
            # Cargar el audio
            audio = AudioSegment.from_file(audio_path)

            # Convertir tiempos a milisegundos
            start_ms = int(start_time * 1000)
            end_ms = int(end_time * 1000)

            # Extraer el segmento
            segment = audio[start_ms:end_ms]

            # Determinar ruta de salida
            if output_path is None:
                temp_folder = os.path.join(current_app.config["UPLOAD_FOLDER"], "temp_segments")
                os.makedirs(temp_folder, exist_ok=True)
                output_path = os.path.join(
                    temp_folder,
                    f"segment_{start_time}_{end_time}.mp3"
                )

            # Guardar el segmento
            segment.export(output_path, format="mp3")

            return output_path

        except Exception as e:
            current_app.logger.error(f"Error al extraer segmento de audio: {str(e)}")
            raise

    def is_available(self) -> bool:
        """Verifica si el servicio de diarización está disponible"""
        try:
            import pyannote.audio
            return current_app.config.get('HF_TOKEN') is not None
        except ImportError:
            return False


# Instancia global del servicio
_diarization_service = None


def get_diarization_service() -> DiarizationService:
    """Obtiene la instancia singleton del servicio de diarización"""
    global _diarization_service
    if _diarization_service is None:
        _diarization_service = DiarizationService()
    return _diarization_service
