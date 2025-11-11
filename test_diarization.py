#!/usr/bin/env python
"""
Script de prueba para evaluación de diarización de hablantes

Este script permite probar la funcionalidad de diarización con un archivo de audio
y ver los resultados sin necesidad de usar la interfaz web completa.

Uso:
    python test_diarization.py <ruta_al_archivo_audio>

Ejemplo:
    python test_diarization.py uploads/test_conversation.mp3
"""

import sys
import os
import json
from app import create_app
from modules.transcription.whisper_diarization_service import (
    transcribe_with_diarization,
    export_segments_to_json
)


def test_diarization(audio_file_path: str):
    """
    Prueba la funcionalidad de diarización con un archivo de audio

    Args:
        audio_file_path: Ruta al archivo de audio a procesar
    """
    # Verificar que el archivo existe
    if not os.path.exists(audio_file_path):
        print(f"❌ Error: El archivo '{audio_file_path}' no existe")
        return False

    print(f"\n{'='*80}")
    print(f"PRUEBA DE DIARIZACIÓN DE HABLANTES")
    print(f"{'='*80}")
    print(f"\nArchivo: {audio_file_path}")
    print(f"Tamaño: {os.path.getsize(audio_file_path) / 1024 / 1024:.2f} MB\n")

    # Crear contexto de aplicación
    app = create_app()

    with app.app_context():
        print("🔄 Iniciando transcripción con diarización...")
        print("-" * 80)

        try:
            # Ejecutar transcripción con diarización
            result = transcribe_with_diarization(audio_file_path)

            if not result['success']:
                print(f"\n❌ Error en la transcripción: {result.get('error', 'Error desconocido')}")
                return False

            # Mostrar resultados
            print(f"\n✅ Transcripción completada exitosamente")
            print(f"Método usado: {result['method']}")

            if result.get('warning'):
                print(f"⚠️  Advertencia: {result['warning']}")

            if result['speakers']:
                print(f"\n👥 Hablantes detectados: {len(result['speakers'])}")
                for speaker in result['speakers']:
                    speaker_segments = [s for s in result['segments'] if s['speaker'] == speaker]
                    total_time = sum(s['end'] - s['start'] for s in speaker_segments)
                    print(f"   - {speaker}: {len(speaker_segments)} segmentos, {total_time:.1f} segundos")

            print(f"\n📝 TRANSCRIPCIÓN CON IDENTIFICACIÓN DE HABLANTES:")
            print("=" * 80)
            print(result['transcription'])
            print("=" * 80)

            # Exportar segmentos detallados a JSON
            if result['segments']:
                output_json = audio_file_path.replace(
                    os.path.splitext(audio_file_path)[1],
                    '_diarization_segments.json'
                )
                export_segments_to_json(result['segments'], output_json)
                print(f"\n💾 Segmentos detallados exportados a: {output_json}")

            # Mostrar estadísticas por segmento
            if result['segments']:
                print(f"\n📊 ESTADÍSTICAS DE SEGMENTOS:")
                print(f"   Total de segmentos: {len(result['segments'])}")

                # Mostrar primeros 5 segmentos como ejemplo
                print(f"\n   Primeros segmentos (ejemplo):")
                for i, seg in enumerate(result['segments'][:5], 1):
                    duration = seg['end'] - seg['start']
                    print(f"   {i}. [{seg['start']:.1f}s - {seg['end']:.1f}s] "
                          f"{seg['speaker']}: {seg['text'][:60]}...")

            return True

        except Exception as e:
            print(f"\n❌ Error durante la prueba: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def check_requirements():
    """Verifica que las dependencias necesarias estén instaladas"""
    print("\n🔍 Verificando dependencias...")

    missing = []

    # Verificar pyannote.audio
    try:
        import pyannote.audio
        print("   ✅ pyannote.audio instalado")
    except ImportError:
        print("   ❌ pyannote.audio NO instalado")
        missing.append("pyannote.audio")

    # Verificar torch
    try:
        import torch
        gpu_available = torch.cuda.is_available()
        device = "GPU (CUDA)" if gpu_available else "CPU"
        print(f"   ✅ PyTorch instalado (usando {device})")
    except ImportError:
        print("   ❌ PyTorch NO instalado")
        missing.append("torch")

    # Verificar pydub
    try:
        import pydub
        print("   ✅ pydub instalado")
    except ImportError:
        print("   ❌ pydub NO instalado")
        missing.append("pydub")

    # Verificar OpenAI
    try:
        import openai
        print("   ✅ openai instalado")
    except ImportError:
        print("   ❌ openai NO instalado")
        missing.append("openai")

    # Verificar variables de entorno
    print("\n🔑 Verificando configuración:")

    if os.getenv('OPENAI_API_KEY'):
        print("   ✅ OPENAI_API_KEY configurada")
    else:
        print("   ❌ OPENAI_API_KEY NO configurada")
        missing.append("OPENAI_API_KEY (variable de entorno)")

    if os.getenv('HF_TOKEN'):
        print("   ✅ HF_TOKEN configurada")
    else:
        print("   ⚠️  HF_TOKEN NO configurada (requerida para diarización)")
        print("      Obtén un token en: https://huggingface.co/settings/tokens")
        print("      Y acepta el modelo en: https://huggingface.co/pyannote/speaker-diarization-3.1")
        missing.append("HF_TOKEN (variable de entorno)")

    if missing:
        print(f"\n⚠️  Dependencias faltantes: {', '.join(missing)}")
        print("\nPara instalar dependencias faltantes:")
        print("   pip install -r requirements.txt")
        return False

    print("\n✅ Todas las dependencias están instaladas correctamente\n")
    return True


def main():
    """Función principal del script de prueba"""
    print("\n" + "="*80)
    print("TEST DE DIARIZACIÓN - Whisper + pyannote.audio")
    print("="*80)

    # Verificar requisitos primero
    if not check_requirements():
        print("\n⚠️  Algunas dependencias faltan. El test podría no funcionar correctamente.")
        response = input("\n¿Deseas continuar de todas formas? (s/n): ")
        if response.lower() != 's':
            print("Test cancelado.")
            return 1

    # Verificar argumentos
    if len(sys.argv) < 2:
        print("\n❌ Error: Debes proporcionar la ruta al archivo de audio")
        print("\nUso:")
        print(f"   python {sys.argv[0]} <ruta_al_archivo_audio>")
        print("\nEjemplo:")
        print(f"   python {sys.argv[0]} uploads/conversation.mp3")
        return 1

    audio_file = sys.argv[1]

    # Ejecutar prueba
    success = test_diarization(audio_file)

    print("\n" + "="*80)
    if success:
        print("✅ PRUEBA COMPLETADA EXITOSAMENTE")
    else:
        print("❌ PRUEBA FALLIDA")
    print("="*80 + "\n")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
