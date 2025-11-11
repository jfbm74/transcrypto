# Feature: Speaker Diarization (Identificación de Hablantes)

## Descripción General

Esta feature agrega capacidad de **diarización de hablantes** a la aplicación de transcripción, permitiendo identificar automáticamente quién habla en cada momento del audio y generar transcripciones con atribución de texto a cada participante.

## Motivación

El servicio de transcripción existente usando Whisper (OpenAI) genera transcripciones precisas, pero no identifica quién habla en cada momento. En conversaciones con múltiples participantes, esta limitación dificulta:
- Seguir el flujo de la conversación
- Identificar acuerdos y responsabilidades por persona
- Generar actas de reunión con claridad sobre quién dijo qué

## Solución Implementada

### Arquitectura: Whisper + pyannote.audio

La solución combina dos tecnologías especializadas:

1. **pyannote.audio** - Diarización (identificación de hablantes)
   - Analiza el audio y detecta segmentos temporales por hablante
   - Asigna etiquetas (SPEAKER_00, SPEAKER_01, etc.)
   - No transcribe texto, solo identifica "quién" y "cuándo"

2. **Whisper (OpenAI)** - Transcripción con timestamps
   - Transcribe el contenido hablado con alta precisión
   - Genera timestamps detallados por segmento
   - No identifica hablantes

3. **Alineación** - Integración de ambos resultados
   - Combina timestamps de Whisper con segmentos de diarización
   - Asigna cada fragmento de texto al hablante correspondiente
   - Genera transcripción formateada con identificación clara

### Pipeline de Procesamiento

```
┌────────────────┐
│  Archivo de    │
│     Audio      │
└───────┬────────┘
        │
        ├──────────────────┬──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   pyannote   │   │   Whisper    │   │  Segmentos   │
│  Diarización │   │ Transcripción│   │  Temporales  │
└───────┬──────┘   └──────┬───────┘   └──────────────┘
        │                  │
        │    Segmentos     │    Texto con
        │    por hablante  │    timestamps
        │                  │
        └────────┬─────────┘
                 ▼
        ┌────────────────┐
        │   Alineación   │
        │   Temporal     │
        └────────┬───────┘
                 ▼
        ┌────────────────┐
        │  Transcripción │
        │  con Hablantes │
        └────────────────┘
```

## Componentes Implementados

### 1. `diarization_service.py`
Servicio de diarización usando pyannote.audio.

**Clase principal:** `DiarizationService`

**Métodos clave:**
- `initialize()`: Inicializa pipeline de pyannote con modelo de Hugging Face
- `diarize_audio(audio_path)`: Ejecuta diarización, retorna segmentos por hablante
- `extract_audio_segment()`: Extrae segmento de audio entre timestamps (útil para debug)
- `is_available()`: Verifica si pyannote está configurado correctamente

**Configuración requerida:**
- Variable de entorno `HF_TOKEN` (token de Hugging Face)
- Aceptar modelo en: https://huggingface.co/pyannote/speaker-diarization-3.1

### 2. `whisper_diarization_service.py`
Servicio integrado que combina Whisper + pyannote.

**Función principal:** `transcribe_with_diarization(audio_path, language='es')`

**Retorna:**
```python
{
    'success': True,
    'transcription': str,  # Texto formateado: "SPEAKER_00: ... SPEAKER_01: ..."
    'segments': [          # Segmentos detallados
        {
            'start': 0.0,
            'end': 5.2,
            'speaker': 'SPEAKER_00',
            'text': 'Bienvenidos a la reunión...'
        },
        ...
    ],
    'speakers': ['SPEAKER_00', 'SPEAKER_01'],  # Lista de hablantes detectados
    'method': 'whisper_with_diarization'
}
```

**Funciones auxiliares:**
- `_transcribe_with_timestamps()`: Llama a Whisper con formato verbose_json
- `_align_transcription_with_diarization()`: Alinea resultados de ambos servicios
- `_find_speaker_for_segment()`: Encuentra hablante por superposición temporal
- `_format_transcription_with_speakers()`: Formatea salida legible
- `export_segments_to_json()`: Exporta segmentos a JSON para análisis

### 3. Modelo de Base de Datos

**Campos agregados a `Transcription`:**
```python
has_diarization = Boolean          # Indica si se usó diarización
speakers_count = Integer           # Número de hablantes detectados
diarization_segments = Text        # JSON con segmentos detallados
```

**Migración creada:**
`migrations/versions/23c2645ff2d8_add_speaker_diarization_fields_to_.py`

### 4. Script de Prueba

**Archivo:** `test_diarization.py`

**Uso:**
```bash
python test_diarization.py uploads/conversation.mp3
```

**Características:**
- Verifica dependencias instaladas
- Ejecuta diarización completa
- Muestra estadísticas de hablantes
- Exporta segmentos a JSON
- Muestra transcripción formateada

## Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nuevas dependencias agregadas:**
- `pyannote.audio==3.3.2` - Pipeline de diarización
- `torch>=2.0.0` - Framework de ML (requerido por pyannote)
- `torchaudio>=2.0.0` - Procesamiento de audio para PyTorch

**Nota sobre instalación:**
- PyTorch puede ser grande (~2GB). Para CPU-only, usar:
  ```bash
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
  ```
- Para GPU (CUDA 11.8):
  ```bash
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
  ```

### 2. Configurar Token de Hugging Face

1. Crear cuenta en https://huggingface.co
2. Generar token en https://huggingface.co/settings/tokens
3. Aceptar licencia del modelo: https://huggingface.co/pyannote/speaker-diarization-3.1
4. Agregar token al `.env`:

```bash
HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
```

### 3. Aplicar Migración de Base de Datos

```bash
flask db upgrade
```

## Uso

### Modo Programático

```python
from modules.transcription.whisper_diarization_service import transcribe_with_diarization

# Transcribir con diarización
result = transcribe_with_diarization('path/to/audio.mp3', language='es')

if result['success']:
    print(f"Detectados {len(result['speakers'])} hablantes")
    print(result['transcription'])

    # Acceder a segmentos individuales
    for seg in result['segments']:
        print(f"[{seg['start']:.1f}s] {seg['speaker']}: {seg['text']}")
```

### Script de Prueba

```bash
# Verificar configuración y probar con un archivo
python test_diarization.py uploads/meeting.mp3

# Salida esperada:
# - Verificación de dependencias
# - Número de hablantes detectados
# - Transcripción formateada
# - Archivo JSON con segmentos detallados
```

### Integración con Rutas Existentes

Para integrar en la ruta de transcripción existente (`modules/transcription/routes.py`):

```python
from modules.transcription.whisper_diarization_service import transcribe_with_diarization
import json

# Opción 1: Reemplazar transcripción normal
result = transcribe_with_diarization(file_path)
if result['success']:
    transcription_text = result['transcription']

    # Guardar metadata de diarización
    new_transcription.has_diarization = True
    new_transcription.speakers_count = len(result['speakers'])
    new_transcription.diarization_segments = json.dumps(result['segments'])

# Opción 2: Hacer diarización opcional (checkbox en UI)
if request.form.get('enable_diarization'):
    result = transcribe_with_diarization(file_path)
else:
    # Transcripción simple existente
    transcription_text = transcribe_audio(file_path)
```

## Formato de Salida

### Transcripción Simple (sin diarización)
```
Bienvenidos a la reunión de planificación del proyecto. Hoy vamos a revisar
el estado actual y definir los próximos pasos. ¿Hay alguna pregunta antes
de comenzar? Sí, tengo una duda sobre el presupuesto...
```

### Transcripción con Diarización
```
SPEAKER_00: Bienvenidos a la reunión de planificación del proyecto. Hoy vamos
a revisar el estado actual y definir los próximos pasos. ¿Hay alguna pregunta
antes de comenzar?

SPEAKER_01: Sí, tengo una duda sobre el presupuesto asignado para la fase dos.

SPEAKER_00: Claro, el presupuesto actual es de cincuenta mil dólares. ¿Es
suficiente para tu equipo?

SPEAKER_01: Creo que necesitaríamos diez mil adicionales para el módulo de
reportes avanzados.

SPEAKER_00: Entendido. Lo revisaremos con finanzas la próxima semana.
```

### JSON de Segmentos Detallados
```json
[
  {
    "start": 0.0,
    "end": 8.5,
    "speaker": "SPEAKER_00",
    "text": "Bienvenidos a la reunión de planificación del proyecto."
  },
  {
    "start": 8.5,
    "end": 12.3,
    "speaker": "SPEAKER_00",
    "text": "Hoy vamos a revisar el estado actual y definir los próximos pasos."
  },
  {
    "start": 13.1,
    "end": 16.2,
    "speaker": "SPEAKER_01",
    "text": "Sí, tengo una duda sobre el presupuesto asignado para la fase dos."
  }
]
```

## Consideraciones Técnicas

### Rendimiento

**Procesamiento:**
- Diarización es más lenta que transcripción simple (2-3x)
- Archivo de 10 minutos: ~2-3 minutos en CPU, ~1 minuto en GPU
- Modelos de pyannote requieren ~1.5GB de RAM adicional

**Recomendaciones:**
- Para producción, considerar usar GPU (reduce tiempo 50-70%)
- Implementar procesamiento asíncrono (Celery) para archivos largos
- Cachear resultados de diarización si se retranscriben archivos

### Precisión

**Factores que afectan la diarización:**
- ✅ Buena calidad de audio
- ✅ Hablantes con voces distintivas
- ✅ Conversación clara sin mucho solapamiento
- ❌ Audio con mucho ruido de fondo
- ❌ Hablantes con voces muy similares
- ❌ Mucho solapamiento de voces

**Mejoras posibles:**
- Ajustar hiperparámetros de pyannote (umbral de detección, clustering)
- Usar modelo premium: `pyannote/speaker-diarization-precision-2`
- Pre-procesar audio (reducción de ruido, normalización)

### Alternativas Consideradas

| Opción | Pros | Cons | Decisión |
|--------|------|------|----------|
| **Whisper + pyannote** | Open source, control total, sin costos por uso | Requiere configuración, más lento | ✅ **Implementado** |
| **AssemblyAI** | API simple, muy preciso | Costo por hora (~$0.65/h), dependencia externa | ⏸️ Considerar para futuro |
| **Deepgram** | Rápido, API simple | Costo por hora (~$0.50/h), lock-in | ⏸️ Considerar para futuro |
| **Amazon Transcribe** | Integración AWS, escalable | Más complejo, costo variable | ❌ Complejidad alta |
| **Whisper local con timestamps** | Sin diarización, solo segmentación | No identifica hablantes | ❌ Insuficiente |

### Seguridad y Privacidad

**Ventajas de la solución open source:**
- ✅ Procesamiento local, audio no sale del servidor
- ✅ Sin dependencias de APIs externas para diarización
- ✅ Control total sobre datos sensibles

**Consideraciones:**
- Token HF solo se usa para descargar modelos (una vez)
- Modelos se cachean localmente
- Procesamiento completamente offline después de descarga inicial

## Casos de Uso

### 1. Actas de Reunión
- Identificar quién propuso cada idea
- Rastrear compromisos por persona
- Clarificar quién aprobó decisiones

### 2. Entrevistas
- Separar respuestas del entrevistado vs preguntas del entrevistador
- Facilitar análisis cualitativo
- Generar transcripciones estructuradas

### 3. Conferencias
- Identificar diferentes panelistas
- Separar preguntas de audiencia vs respuestas
- Facilitar edición y segmentación

### 4. Documentación de Requisitos
- Identificar stakeholders que mencionan cada requisito
- Rastrear origen de cada necesidad
- Validar quién aprobó requisitos críticos

## Trabajo Futuro

### Mejoras Planificadas

1. **UI para Diarización**
   - [ ] Checkbox en formulario de upload: "Identificar hablantes"
   - [ ] Mostrar número de hablantes detectados en resultados
   - [ ] Permitir renombrar SPEAKER_00 → "Juan Pérez" en UI

2. **Edición de Hablantes**
   - [ ] Interfaz para corregir asignaciones incorrectas
   - [ ] Fusionar hablantes detectados erróneamente como diferentes
   - [ ] Dividir segmentos mal atribuidos

3. **Optimizaciones**
   - [ ] Procesamiento asíncrono con Celery
   - [ ] Caché de resultados de diarización
   - [ ] Procesamiento incremental para archivos largos

4. **Integración con Documentos**
   - [ ] Generar actas con nombres de hablantes desde metadatos
   - [ ] Incluir participantes identificados en header del documento
   - [ ] Resaltar acuerdos por hablante en documento final

5. **Análisis Avanzado**
   - [ ] Estadísticas de participación (tiempo de habla por persona)
   - [ ] Visualización de timeline de conversación
   - [ ] Detección de interrupciones y solapamientos

## Referencias

- **pyannote.audio**: https://github.com/pyannote/pyannote-audio
- **Modelo usado**: https://huggingface.co/pyannote/speaker-diarization-3.1
- **Documentación pyannote**: https://pyannote.github.io/pyannote-audio/
- **Whisper API**: https://platform.openai.com/docs/guides/speech-to-text
- **Paper pyannote**: https://arxiv.org/abs/2104.04045

## Autor

Implementado por: Claude (Anthropic)
Fecha: 2025-11-10
Versión: 1.0
Branch: `feature/speaker-diarization`
