# Integración con Confluence

## Descripción General

Esta funcionalidad permite a los usuarios publicar documentos generados (actas de reunión y documentos de requerimientos) directamente en su workspace de Confluence Cloud, eliminando la necesidad de copiar y pegar manualmente.

## Motivación

Los equipos que utilizan Confluence como repositorio central de documentación necesitan una forma eficiente de transferir las transcripciones y documentos generados sin trabajo manual repetitivo.

## Características Implementadas

### 1. Configuración de Credenciales (Perfil de Usuario)

**Ubicación**: `/auth/profile` - Sección "Integración con Confluence"

Los usuarios pueden configurar:
- **Email de Atlassian**: Email de la cuenta de Atlassian
- **API Token**: Token generado desde https://id.atlassian.com/manage-profile/security/api-tokens
- **URL de Confluence**: URL completa del workspace (ej: https://zentratek.atlassian.net/wiki)
- **Espacio por defecto** (opcional): Clave del espacio preferido para publicar

**Seguridad**:
- El API Token se almacena **encriptado** en la base de datos usando `cryptography.fernet`
- Nunca se expone el token en respuestas HTTP o logs
- Cada usuario tiene su propia encriptación

**Funciones**:
- ✅ Botón "Probar Conexión" para validar credenciales
- ✅ Indicador visual de estado de configuración
- ✅ Enlaces directos a documentación de Atlassian

### 2. Publicación de Documentos

**Ubicación**: Página de resultados de transcripción, modal de documentos generados

**Flujo de trabajo**:
1. Usuario transcribe audio y genera documento (acta o requerimientos)
2. Aparece botón "Publicar en Confluence" (solo si está configurado)
3. Se abre modal con opciones:
   - **Título de la página**: Pre-rellenado basándose en el archivo
   - **Espacio**: Selector dinámico de espacios disponibles
   - **Página padre** (opcional): Selector de páginas para crear jerarquía
4. Al confirmar:
   - Convierte el contenido a **Confluence Storage Format** (HTML)
   - Si la página existe, la **actualiza** (nueva versión)
   - Si no existe, la **crea**
   - Agrega labels automáticas (transcripcion, tipo de documento, fecha)
5. Muestra resultado con enlace directo a la página en Confluence

### 3. Seguimiento de Publicaciones

**Modelo Transcription** incluye campos:
- `confluence_page_id`: ID de la página en Confluence
- `confluence_page_url`: URL directa a la página
- `confluence_published_at`: Timestamp de publicación

Esto permite:
- Ver qué documentos han sido publicados
- Acceso rápido a páginas publicadas desde el historial
- Auditoría de publicaciones

## Arquitectura Técnica

### Backend

**`modules/transcription/confluence_service.py`** - Servicio completo de API:

```python
class ConfluenceService:
    - __init__(email, api_token, base_url)
    - test_connection()
    - get_spaces()
    - get_pages_in_space(space_key)
    - convert_to_storage_format(text)
    - search_page_by_title(space_key, title)
    - create_page(space_key, title, content, parent_id)
    - update_page(page_id, title, content, current_version)
    - publish_or_update_page(...)  # Smart wrapper
    - add_labels(page_id, labels)
```

**Endpoints** (`modules/transcription/routes.py`):
- `GET /transcription/confluence/spaces` - Lista espacios disponibles
- `GET /transcription/confluence/pages?space_key=X` - Lista páginas de un espacio
- `POST /transcription/confluence/publish` - Publica documento

**Rutas de configuración** (`modules/auth/routes.py`):
- `POST /auth/update-confluence-config` - Guarda credenciales
- `POST /auth/test-confluence-connection` - Prueba conexión

### Frontend

**Templates**:
- `templates/auth/profile.html` - Formulario de configuración
- `templates/result.html` - Modal y botón de publicación

**JavaScript**:
- Carga dinámica de espacios y páginas
- Validación de formularios
- Manejo de estados de carga
- Feedback visual de éxito/error

### Base de Datos

**Migración**: `migrations/versions/c4d5e6f7g8h9_add_confluence_integration.py`

**Tabla `user`**:
```sql
confluence_email VARCHAR(120)
confluence_api_token_encrypted TEXT
confluence_url VARCHAR(255)
confluence_default_space VARCHAR(100)
```

**Tabla `transcription`**:
```sql
confluence_page_id VARCHAR(50)
confluence_page_url VARCHAR(500)
confluence_published_at DATETIME
```

## Confluence Storage Format

El servicio convierte texto plano a HTML compatible con Confluence:

- **Párrafos**: Envueltos en `<p>` tags
- **Títulos**: Detectados por ":" al final → `<h2>`
- **Listas**: Líneas con "- " o "* " → `<li>`
- **Saltos de línea**: Convertidos a `<br/>`
- **Caracteres especiales**: Escapados correctamente

Ejemplo:
```
Orden del día:
- Revisión de proyecto
- Próximos pasos
```

Se convierte a:
```html
<h2>Orden del día</h2>
<li>Revisión de proyecto</li>
<li>Próximos pasos</li>
```

## Comportamiento de Actualización

Cuando se publica un documento con un título que **ya existe** en el espacio:

1. **Busca la página** por título exacto
2. **Obtiene la versión actual** de la página
3. **Crea una nueva versión** (incrementa número de versión)
4. **Preserva el historial** - Confluence mantiene todas las versiones anteriores
5. **Notifica al usuario** que la página fue actualizada

Esto permite:
- ✅ Iteración sobre documentos sin duplicados
- ✅ Historial completo de cambios en Confluence
- ✅ Rollback si es necesario (desde Confluence UI)

## Seguridad

### Encriptación de Tokens

**Implementación**:
```python
from cryptography.fernet import Fernet

# Clave de encriptación (debe estar en .env)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
cipher_suite = Fernet(ENCRYPTION_KEY)

# En el modelo User
def set_confluence_token(self, token):
    encrypted = cipher_suite.encrypt(token.encode())
    self.confluence_api_token_encrypted = encrypted.decode()

def get_confluence_token(self):
    decrypted = cipher_suite.decrypt(self.confluence_api_token_encrypted.encode())
    return decrypted.decode()
```

### Best Practices

- ✅ Tokens nunca se envían al frontend
- ✅ Tokens nunca aparecen en logs
- ✅ Conexión a Confluence sobre HTTPS
- ✅ Autenticación básica con email + token (estándar de Atlassian)
- ✅ Validación de permisos (solo el dueño puede publicar sus transcripciones)

## Configuración Requerida

### Variables de Entorno

Agregar a `.env`:
```bash
# Clave de encriptación para tokens de Confluence (generar con Fernet.generate_key())
ENCRYPTION_KEY=your-encryption-key-here
```

**Generar clave**:
```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### Dependencias

Agregar a `requirements.txt`:
```
cryptography==42.0.5
```

Instalar:
```bash
pip install cryptography==42.0.5
```

### Migración de Base de Datos

```bash
flask db upgrade
```

## Uso para Usuarios Finales

### Configuración Inicial

1. **Ir a Perfil** desde el menú de navegación
2. **Generar API Token** en Atlassian:
   - Visitar: https://id.atlassian.com/manage-profile/security/api-tokens
   - Clic en "Create API token"
   - Dar nombre descriptivo (ej: "ZentraText Integration")
   - Copiar el token generado
3. **Completar formulario** en ZentraText:
   - Email: tu-email@ejemplo.com
   - API Token: (pegar token copiado)
   - URL: https://tu-empresa.atlassian.net/wiki
   - Espacio por defecto: TEAM (opcional)
4. **Probar conexión** - Click en "Probar Conexión"
5. **Guardar configuración**

### Publicar un Documento

1. **Transcribir audio** y generar documento (acta o requerimientos)
2. **Click en "Publicar en Confluence"** (botón amarillo en modal)
3. **Configurar publicación**:
   - Revisar/editar título de página
   - Seleccionar espacio de destino
   - (Opcional) Seleccionar página padre para jerarquía
4. **Click en "Publicar"**
5. **Ver resultado** con enlace directo a Confluence

### Gestionar Páginas Publicadas

- El historial de transcripciones mostrará iconos/enlaces para páginas ya publicadas
- Puedes republicar con el mismo título para actualizar la página
- El historial de versiones está disponible en Confluence

## Limitaciones Conocidas

1. **Solo Confluence Cloud**: No soporta Confluence Server/Data Center (requiere API diferente)
2. **Formato básico**: La conversión a Storage Format es básica, no soporta tablas complejas o imágenes
3. **Sin preview**: No hay vista previa del formato antes de publicar
4. **Permisos**: El usuario debe tener permisos de escritura en el espacio de Confluence

## Próximos Pasos (Futuras Mejoras)

- [ ] Preview de cómo se verá la página antes de publicar
- [ ] Soporte para formato Markdown avanzado
- [ ] Publicación de imágenes/diagramas
- [ ] Batch publishing (múltiples documentos a la vez)
- [ ] Templates personalizados de Confluence
- [ ] Soporte para Confluence Server/Data Center
- [ ] Sincronización bidireccional (editar en Confluence → actualizar en ZentraText)
- [ ] Notificaciones a usuarios de Confluence cuando se publica
- [ ] Integración con Jira (crear tickets desde requerimientos)

## Troubleshooting

### "Error al conectar a Confluence"
- ✅ Verifica que la URL es correcta (incluye /wiki al final)
- ✅ Verifica que el API token no haya expirado
- ✅ Revoca y genera un nuevo token si es necesario

### "Credenciales inválidas"
- ✅ Verifica que el email coincide con tu cuenta de Atlassian
- ✅ Verifica que copiaste el token completo (sin espacios)

### "No se encuentran espacios"
- ✅ Verifica que tienes acceso a al menos un espacio en Confluence
- ✅ Algunos espacios pueden estar privados o restringidos

### "Error al crear página"
- ✅ Verifica que tienes permisos de escritura en el espacio
- ✅ Verifica que el título de la página no contiene caracteres especiales problemáticos

## Archivos Relacionados

**Backend**:
- `modules/auth/models.py` - Modelo User con campos Confluence
- `modules/auth/routes.py` - Endpoints de configuración
- `modules/transcription/models.py` - Modelo Transcription con tracking
- `modules/transcription/routes.py` - Endpoints de publicación
- `modules/transcription/confluence_service.py` - Servicio de API

**Frontend**:
- `templates/auth/profile.html` - Formulario de configuración
- `templates/result.html` - Modal de publicación

**Base de Datos**:
- `migrations/versions/c4d5e6f7g8h9_add_confluence_integration.py`

**Dependencias**:
- `requirements.txt` - cryptography==42.0.5

## Referencias

- [Confluence Cloud REST API Documentation](https://developer.atlassian.com/cloud/confluence/rest/v1/intro/)
- [Confluence Storage Format](https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html)
- [Atlassian API Tokens](https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/)
- [Cryptography Library Documentation](https://cryptography.io/en/latest/)
