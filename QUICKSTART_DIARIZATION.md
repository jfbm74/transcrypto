# Guía Rápida: Evaluación de Diarización de Hablantes

Esta guía te ayudará a probar la funcionalidad de diarización de hablantes (Whisper + pyannote.audio) en pocos pasos.

## 🎯 ¿Qué es esto?

La diarización identifica automáticamente **quién habla** en cada momento de un audio, generando transcripciones como:

```
SPEAKER_00: Bienvenidos a la reunión de hoy.
SPEAKER_01: Gracias, tengo una pregunta sobre el proyecto.
SPEAKER_00: Claro, adelante.
```

En lugar de una transcripción continua sin identificar hablantes.

## 📋 Requisitos Previos

1. **Python 3.10+** ya instalado
2. **FFmpeg** ya instalado
3. **Entorno virtual** activado
4. **OpenAI API Key** configurada

## 🚀 Instalación Rápida

### Paso 1: Instalar Dependencias

```bash
# Activar entorno virtual
source venv/bin/activate

# Instalar nuevas dependencias
pip install pyannote.audio torch torchaudio

# O instalar todo desde requirements.txt
pip install -r requirements.txt
```

**Nota**: La instalación de PyTorch puede tomar varios minutos (~2GB de descarga).

### Paso 2: Configurar Token de Hugging Face

1. **Crear cuenta** en https://huggingface.co (gratis)

2. **Generar token**:
   - Ve a: https://huggingface.co/settings/tokens
   - Click en "New token"
   - Tipo: "Read"
   - Copia el token generado

3. **Aceptar licencia del modelo**:
   - Ve a: https://huggingface.co/pyannote/speaker-diarization-3.1
   - Click en "Agree and access repository"

4. **Agregar token al `.env`**:
   ```bash
   # Editar archivo .env
   nano .env

   # Agregar esta línea:
   HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
   ```

### Paso 3: Aplicar Migración de Base de Datos

```bash
flask db upgrade
```

## 🧪 Prueba Rápida

### Opción 1: Usar Script de Prueba

```bash
# Probar con un archivo de audio existente
python test_diarization.py uploads/tu_archivo.mp3

# El script mostrará:
# - Verificación de dependencias
# - Número de hablantes detectados
# - Transcripción formateada
# - Exportará JSON con segmentos detallados
```

### Opción 2: Usar Python Interactivo

```python
from app import create_app
from modules.transcription.whisper_diarization_service import transcribe_with_diarization

app = create_app()
with app.app_context():
    result = transcribe_with_diarization('uploads/conversation.mp3')

    if result['success']:
        print(f"Hablantes detectados: {len(result['speakers'])}")
        print("\nTranscripción:")
        print(result['transcription'])
```

## 📊 Interpretación de Resultados

### Salida del Script de Prueba

```
================================================================================
PRUEBA DE DIARIZACIÓN DE HABLANTES
================================================================================

Archivo: uploads/meeting.mp3
Tamaño: 5.23 MB

✅ Transcripción completada exitosamente
Método usado: whisper_with_diarization

👥 Hablantes detectados: 3
   - SPEAKER_00: 12 segmentos, 45.3 segundos
   - SPEAKER_01: 8 segmentos, 32.1 segundos
   - SPEAKER_02: 5 segmentos, 18.7 segundos

📝 TRANSCRIPCIÓN CON IDENTIFICACIÓN DE HABLANTES:
================================================================================
SPEAKER_00: Bienvenidos a todos a la reunión de planificación...
SPEAKER_01: Gracias por la introducción, tengo algunas preguntas...
[...]
```

### Archivo JSON de Segmentos

Se genera automáticamente: `uploads/tu_archivo_diarization_segments.json`

```json
[
  {
    "start": 0.0,
    "end": 5.2,
    "speaker": "SPEAKER_00",
    "text": "Bienvenidos a todos a la reunión de planificación."
  },
  ...
]
```

## ⚙️ Configuración Opcional

### Usar CPU en lugar de GPU

Si no tienes GPU o prefieres CPU:

```bash
# Desinstalar versión con CUDA
pip uninstall torch torchaudio

# Instalar versión CPU-only (más pequeña)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### Cambiar Modelo de Diarización

En `modules/transcription/diarization_service.py`, línea 41:

```python
# Modelo community (gratuito, buena calidad)
model_name = "pyannote/speaker-diarization-3.1"

# Modelo premium (mejor calidad, requiere API key de pyannote.ai)
# model_name = "pyannote/speaker-diarization-precision-2"
```

## 🐛 Solución de Problemas

### Error: "HF_TOKEN no configurado"

**Causa**: Falta el token de Hugging Face en `.env`

**Solución**:
1. Verifica que agregaste `HF_TOKEN=...` en el archivo `.env`
2. Reinicia el servidor Flask
3. Verifica con: `echo $HF_TOKEN` (debe mostrar tu token)

### Error: "pyannote.audio not installed"

**Causa**: Falta instalar pyannote.audio

**Solución**:
```bash
pip install pyannote.audio
```

### Error: "You must accept the license"

**Causa**: No has aceptado la licencia del modelo

**Solución**:
1. Ve a: https://huggingface.co/pyannote/speaker-diarization-3.1
2. Click en "Agree and access repository"
3. Espera 1-2 minutos para que se active
4. Intenta de nuevo

### La diarización es muy lenta

**Causa**: Estás usando CPU sin GPU

**Soluciones**:
1. **Mejor**: Usar GPU si tienes disponible
2. **Alternativa**: Reducir duración del audio de prueba
3. **Paciencia**: Primera ejecución descarga modelos (~1.5GB), luego será más rápido

Tiempos esperados:
- CPU: ~2-3 minutos por cada 10 minutos de audio
- GPU: ~1 minuto por cada 10 minutos de audio

### Hablantes detectados incorrectamente

**Causas comunes**:
- Audio con mucho ruido de fondo
- Voces muy similares
- Mucho solapamiento de voces
- Audio de baja calidad

**Mejoras posibles**:
1. Pre-procesar audio (reducción de ruido)
2. Usar audio de mejor calidad
3. Ajustar hiperparámetros de pyannote (avanzado)

## 📚 Siguiente Pasos

### Integrar con la Aplicación Web

Para agregar diarización a la ruta de transcripción:

```python
# En modules/transcription/routes.py
from modules.transcription.whisper_diarization_service import transcribe_with_diarization
import json

# Reemplazar la llamada a transcribe_audio() con:
result = transcribe_with_diarization(file_path)

if result['success']:
    transcription_text = result['transcription']

    # Guardar metadata
    new_transcription.has_diarization = True
    new_transcription.speakers_count = len(result['speakers'])
    new_transcription.diarization_segments = json.dumps(result['segments'])
```

### Personalizar Nombres de Hablantes

Los identificadores `SPEAKER_00`, `SPEAKER_01` pueden ser reemplazados:

```python
# Mapeo de identificadores a nombres reales
speaker_map = {
    'SPEAKER_00': 'Juan Pérez',
    'SPEAKER_01': 'María González',
    'SPEAKER_02': 'Carlos López'
}

# Reemplazar en la transcripción
transcription = result['transcription']
for speaker_id, name in speaker_map.items():
    transcription = transcription.replace(speaker_id, name)
```

## 📖 Documentación Completa

Para más detalles, consulta: **FEATURE_SPEAKER_DIARIZATION.md**

## ❓ Preguntas Frecuentes

**P: ¿Funciona con todos los idiomas?**
R: Sí, pyannote.audio es independiente del idioma. Whisper soporta 90+ idiomas.

**P: ¿Cuántos hablantes puede detectar?**
R: No hay límite teórico. Funciona mejor con 2-10 hablantes. Más de 10 puede reducir precisión.

**P: ¿Puedo usar esto en producción?**
R: Sí, pero considera:
- Procesamiento asíncrono (Celery) para archivos largos
- GPU para mejor rendimiento
- Caché de resultados

**P: ¿Cuánto cuesta?**
R: La solución es 100% gratuita y open source. Solo necesitas cuentas gratuitas de OpenAI y Hugging Face.

**P: ¿Qué tan preciso es?**
R: Depende de la calidad del audio:
- Audio limpio, 2-3 hablantes: 90-95% precisión
- Audio con ruido, 5+ hablantes: 70-80% precisión

## 🎉 ¡Listo!

Ahora tienes diarización de hablantes funcionando. Experimenta con diferentes audios y evalúa la calidad de los resultados.

Para reportar problemas o sugerencias, consulta la documentación completa o contacta al equipo de desarrollo.
