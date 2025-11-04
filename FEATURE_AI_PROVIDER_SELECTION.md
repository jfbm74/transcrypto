# Selección de Proveedor de IA

## Descripción General

Esta funcionalidad permite a los usuarios seleccionar su proveedor de IA preferido (OpenAI o Google AI) para la generación de documentos (actas de reunión y documentos de requerimientos).

## Motivación

Los usuarios pueden tener créditos disponibles en diferentes proveedores de IA. Esta funcionalidad les permite aprovechar los créditos que tengan disponibles en lugar de estar limitados a un solo proveedor.

## Características Implementadas

### 1. Campo de Preferencia en el Modelo de Usuario

- Se agregó el campo `ai_provider` al modelo `User` en `modules/auth/models.py`
- Valores posibles: `'openai'` o `'google'`
- Valor predeterminado: `'openai'`

### 2. Interfaz de Usuario en el Perfil

- Se agregó un formulario en la página de perfil (`templates/auth/profile.html`)
- Permite seleccionar entre:
  - **OpenAI (GPT-4)**: Usa el modelo GPT-4 de OpenAI
  - **Google AI (Gemini)**: Usa el modelo Gemini 2.5 Pro de Google

### 3. API para Actualizar Preferencias

- Nueva ruta: `POST /auth/update-ai-provider`
- Permite actualizar la preferencia del usuario
- Retorna confirmación de éxito o error

### 4. Lógica de Generación de Documentos

Las funciones `generate_meeting_minutes()` y `generate_requirements()` fueron actualizadas para:

1. **Usar el proveedor preferido del usuario** como primera opción
2. **Fallback automático**: Si el proveedor preferido no está disponible (sin API key), intenta con el proveedor alternativo
3. **Logging detallado**: Registra qué proveedor se está usando y por qué

## Migración de Base de Datos

Se creó la migración `a1b2c3d4e5f6_add_ai_provider_to_user.py` que:

- Agrega la columna `ai_provider` a la tabla `user`
- Establece `'openai'` como valor predeterminado para usuarios existentes

Para aplicar la migración:

```bash
flask db upgrade
```

## Uso

### Para Usuarios

1. Ir a **Perfil** en la aplicación
2. En la sección **"Preferencias de IA"**, seleccionar el proveedor deseado:
   - OpenAI (GPT-4)
   - Google AI (Gemini)
3. Hacer clic en **"Guardar preferencias"**
4. Las próximas generaciones de documentos usarán el proveedor seleccionado

### Para Desarrolladores

```python
# Las funciones ahora aceptan el parámetro user_provider
from modules.transcription.services import generate_meeting_minutes, generate_requirements

# Generar acta con el proveedor del usuario
result = generate_meeting_minutes(transcription, user_provider='openai')

# Generar requerimientos con Google AI
result = generate_requirements(transcription, user_provider='google')
```

## Comportamiento de Fallback

Si el usuario selecciona un proveedor que no está configurado (sin API key):

1. El sistema intenta usar el proveedor alternativo automáticamente
2. Se registra un warning en los logs
3. El usuario recibe el documento generado sin interrupciones

Ejemplo de log:
```
WARNING: Google AI no disponible, usando OpenAI como fallback
```

## Configuración Requerida

Para que ambos proveedores funcionen, asegúrate de tener las API keys en el archivo `.env`:

```bash
# Para OpenAI
OPENAI_API_KEY=sk-...

# Para Google AI
GOOGLE_AI_API_KEY=AI...
```

## Archivos Modificados

### Modelos
- `modules/auth/models.py`: Agregado campo `ai_provider`

### Rutas
- `modules/auth/routes.py`: Nueva ruta `update_ai_provider()`
- `modules/transcription/routes.py`: Actualizado para pasar el proveedor del usuario

### Servicios
- `modules/transcription/services.py`:
  - `generate_meeting_minutes()` ahora acepta `user_provider`
  - `generate_requirements()` ahora acepta `user_provider`

### Templates
- `templates/auth/profile.html`:
  - Formulario de selección de proveedor
  - JavaScript para enviar preferencias

### Migraciones
- `migrations/versions/a1b2c3d4e5f6_add_ai_provider_to_user.py`: Nueva migración

## Beneficios

1. **Flexibilidad**: Los usuarios pueden cambiar de proveedor según disponibilidad de créditos
2. **Resiliencia**: Fallback automático si un proveedor no está disponible
3. **Control**: Los usuarios tienen control sobre qué modelo de IA usar
4. **Escalabilidad**: Fácil agregar nuevos proveedores en el futuro

## Próximos Pasos (Futuro)

- Agregar estadísticas de uso por proveedor en el perfil
- Permitir configurar el proveedor por tipo de documento
- Agregar más proveedores de IA (Anthropic Claude, etc.)
- Mostrar estimación de costos por proveedor
