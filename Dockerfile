# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.11-slim as builder

# Instalar dependencias del sistema para compilación
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar requirements.txt primero para aprovechar cache de Docker
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --user -r requirements.txt

# Imagen de producción
FROM python:3.11-slim

# Instalar ffmpeg para procesamiento de audio
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no privilegiado
RUN useradd --create-home --shell /bin/bash app

# Crear directorio de trabajo
WORKDIR /app

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /home/app/.local

# Asegurar que el PATH incluya las dependencias locales
ENV PATH=/home/app/.local/bin:$PATH

# Copiar código de la aplicación
COPY --chown=app:app . .

# Crear directorios necesarios
RUN mkdir -p uploads transcripciones static/css static/img && \
    chown -R app:app uploads transcripciones static

# Cambiar al usuario no privilegiado
USER app

# Variables de entorno
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Exponer puerto
EXPOSE 5000

# Comando de inicio usando Gunicorn para producción
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "--timeout", "3600", "wsgi:app"]