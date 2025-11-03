#!/bin/bash

# Script de limpieza automática de archivos media para transcrypto
# Elimina archivos más antiguos que 60 minutos de los directorios de uploads y transcripciones

# Rutas de los volúmenes de Docker
UPLOADS_DIR="/var/lib/docker/volumes/transcrypto_uploads_data/_data"
TRANSCRIPTIONS_DIR="/var/lib/docker/volumes/transcrypto_transcriptions_data/_data"

# Tiempo de retención en minutos
RETENTION_MINUTES=60

# Archivo de log
LOG_FILE="/var/log/transcrypto_cleanup.log"

# Función para registrar mensajes
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_message "Iniciando limpieza de archivos antiguos..."

# Limpiar archivos en el directorio de uploads
if [ -d "$UPLOADS_DIR" ]; then
    DELETED_UPLOADS=$(find "$UPLOADS_DIR" -type f -mmin +$RETENTION_MINUTES -print -delete 2>&1 | wc -l)
    log_message "Archivos eliminados en uploads: $DELETED_UPLOADS"
else
    log_message "ADVERTENCIA: Directorio $UPLOADS_DIR no existe"
fi

# Limpiar archivos en el directorio de transcripciones
if [ -d "$TRANSCRIPTIONS_DIR" ]; then
    DELETED_TRANSCRIPTIONS=$(find "$TRANSCRIPTIONS_DIR" -type f -mmin +$RETENTION_MINUTES -print -delete 2>&1 | wc -l)
    log_message "Archivos eliminados en transcripciones: $DELETED_TRANSCRIPTIONS"
else
    log_message "ADVERTENCIA: Directorio $TRANSCRIPTIONS_DIR no existe"
fi

log_message "Limpieza completada."
log_message "---"
