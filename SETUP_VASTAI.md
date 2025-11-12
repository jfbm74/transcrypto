# Guía de Configuración: Transcrypto en Vast.ai

Guía específica para desplegar Transcrypto con GPU en Vast.ai (o proveedores cloud similares).

## ¿Qué es Vast.ai?

Vast.ai es un marketplace de GPU en la nube que permite rentar GPUs a precios competitivos. Ideal para:
- Desarrollo y testing con GPU sin inversión en hardware
- Escalado temporal de capacidad
- Pruebas con diferentes modelos de GPU

---

## Paso 1: Seleccionar Instancia en Vast.ai

### 1.1 Especificaciones Recomendadas

**GPU Mínima:**
- NVIDIA RTX 3090 (24GB VRAM)
- NVIDIA RTX 4090 (24GB VRAM)
- NVIDIA A5000 (24GB VRAM)

**Recursos:**
- RAM: 32GB+ recomendado
- Disco: 50GB+ (para modelos y datos)
- Bandwidth: 100+ Mbps

### 1.2 Template Recomendado

**Opción 1 - Template Básico (RECOMENDADO):**
```
nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
```
o
```
nvidia/cuda:12.1.0-cudnn9-runtime-ubuntu22.04
```

**Opción 2 - Si usas template con PyTorch preinstalado:**
```
vastai/pytorch_cuda-12.4.1-auto/jupyter
```
(Requiere usar `Dockerfile.gpu.cuda12`)

### 1.3 Configuración de Puertos

En la interfaz de Vast.ai, asegúrate de exponer el puerto:
- **Direct Port**: 5001 → 5001

---

## Paso 2: Conectar a la Instancia

### 2.1 Obtener Credenciales SSH

Vast.ai te proporcionará:
```bash
# Ejemplo de comando SSH
ssh -p 12345 root@ssh.vast.ai
```

### 2.2 Conectar

```bash
# Usar el comando exacto que te proporciona Vast.ai
ssh -p <PUERTO> root@ssh.vast.ai

# Aceptar la huella digital SSH cuando se solicite
```

---

## Paso 3: Verificar el Sistema

### 3.1 Verificar GPU

```bash
# Verificar que la GPU está disponible
nvidia-smi

# Deberías ver tu RTX 3090 o la GPU que rentaste
```

### 3.2 Verificar CUDA

```bash
# Ver versión de CUDA instalada
nvcc --version  # Si nvcc está instalado

# O verificar desde nvidia-smi
nvidia-smi | grep "CUDA Version"
```

**Importante:** Anota la versión de CUDA. Usaremos el Dockerfile correspondiente:
- **CUDA 11.x** → Usar `Dockerfile.gpu` y `docker-compose.gpu.yml`
- **CUDA 12.x** → Usar `Dockerfile.gpu.cuda12` y `docker-compose.gpu.cuda12.yml`

### 3.3 Verificar Docker

```bash
# Docker suele estar preinstalado en Vast.ai
docker --version
docker compose version

# Si no está instalado, instalarlo:
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
```

---

## Paso 4: Instalar NVIDIA Container Toolkit (si no está)

```bash
# Verificar si ya está instalado
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Si falla, instalar NVIDIA Container Toolkit:
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

apt-get update
apt-get install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

# Verificar nuevamente
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

---

## Paso 5: Clonar Proyecto

### 5.1 Instalar Git (si no está)

```bash
apt-get update && apt-get install -y git
```

### 5.2 Clonar Repositorio

```bash
# Navegar a directorio de trabajo
cd /workspace  # O el directorio que prefieras

# Clonar repositorio
git clone <URL_DE_TU_REPO> transcrypto
cd transcrypto

# Si es privado, configura autenticación:
git config --global user.name "Tu Nombre"
git config --global user.email "tu@email.com"
```

**Alternativa:** Subir archivos con SCP:
```bash
# Desde tu máquina local
scp -P <PUERTO> -r /ruta/local/transcrypto root@ssh.vast.ai:/workspace/
```

---

## Paso 6: Configurar Variables de Entorno

### 6.1 Crear archivo .env

```bash
cd /workspace/transcrypto

# Copiar template
cp .env.example .env

# Editar con nano o vim
nano .env
```

### 6.2 Configurar APIs

```bash
# Flask
SECRET_KEY=genera-una-clave-aleatoria-larga-aqui

# OpenAI (requerido para Whisper)
OPENAI_API_KEY=sk-tu-api-key-de-openai

# Google AI (opcional)
GOOGLE_AI_API_KEY=tu-api-key-de-google

# Hugging Face (requerido para diarización)
HF_TOKEN=hf_tu-token-de-huggingface

# Límite de transcripciones
FREE_TRANSCRIPTIONS_LIMIT=10
```

**Obtener tokens:**
- OpenAI: https://platform.openai.com/api-keys
- Google AI: https://makersuite.google.com/app/apikey
- Hugging Face: https://huggingface.co/settings/tokens
  - También acepta términos en: https://huggingface.co/pyannote/speaker-diarization-3.1

---

## Paso 7: Desplegar con Docker

### 7.1 Identificar Versión CUDA

```bash
# Verificar CUDA
nvidia-smi | grep "CUDA Version"

# Si es CUDA 11.x:
export COMPOSE_FILE=docker-compose.gpu.yml

# Si es CUDA 12.x:
export COMPOSE_FILE=docker-compose.gpu.cuda12.yml
```

### 7.2 Construir Imagen

```bash
# Construir imagen (tardará 10-15 minutos)
docker compose -f $COMPOSE_FILE build

# Ver progreso
# Descarga imagen CUDA, instala PyTorch y dependencias
```

### 7.3 Inicializar Base de Datos

```bash
# Primera vez: crear base de datos
docker compose -f $COMPOSE_FILE run --rm transcripto-gpu flask db upgrade
```

### 7.4 Iniciar Aplicación

```bash
# Iniciar en modo detached
docker compose -f $COMPOSE_FILE up -d

# Ver logs en tiempo real
docker compose -f $COMPOSE_FILE logs -f

# Espera ver:
# "Booting worker with pid: ..."
# "Listening at: http://0.0.0.0:5000"
```

---

## Paso 8: Verificar Despliegue

### 8.1 Verificar Contenedor

```bash
# Ver contenedores corriendo
docker ps | grep transcripto

# Ver logs recientes
docker compose -f $COMPOSE_FILE logs --tail=50

# Verificar GPU en contenedor
docker exec transcripto-gpu nvidia-smi
```

### 8.2 Verificar PyTorch con CUDA

```bash
# Test completo
docker exec transcripto-gpu python3 -c "
import torch
print('PyTorch:', torch.__version__)
print('CUDA disponible:', torch.cuda.is_available())
print('Dispositivo:', torch.cuda.get_device_name(0))
print('VRAM:', round(torch.cuda.get_device_properties(0).total_memory/1024**3, 2), 'GB')
"

# Debería mostrar:
# PyTorch: 2.3.1+cu118 (o cu124)
# CUDA disponible: True
# Dispositivo: NVIDIA GeForce RTX 3090
# VRAM: 24.0 GB
```

### 8.3 Acceder a la Aplicación

```bash
# Desde la misma instancia (test local)
curl http://localhost:5001/

# Desde tu navegador (obtén IP pública de Vast.ai)
# Vast.ai te dará una URL tipo:
# http://<ip-publica>:5001
```

**Encontrar IP pública:**
- En el panel de Vast.ai, busca "Direct Port" o "Public IP"
- También puedes obtenerla con: `curl ifconfig.me`

---

## Paso 9: Monitoreo

### 9.1 Monitorear GPU

```bash
# Ver GPU en tiempo real
watch -n 1 nvidia-smi

# Ver procesos usando GPU
nvidia-smi pmon -i 0

# Estadísticas detalladas
nvidia-smi --query-gpu=timestamp,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv -l 1
```

### 9.2 Monitorear Aplicación

```bash
# Logs en vivo
docker compose -f $COMPOSE_FILE logs -f

# Logs de errores
docker compose -f $COMPOSE_FILE logs | grep -i error

# Estadísticas del contenedor
docker stats transcripto-gpu
```

### 9.3 Monitorear Disco

```bash
# Espacio disponible
df -h

# Espacio usado por Docker
docker system df

# Limpiar si es necesario
docker system prune -a
```

---

## Paso 10: Gestión y Mantenimiento

### 10.1 Comandos Útiles

```bash
# Reiniciar aplicación
docker compose -f $COMPOSE_FILE restart

# Detener aplicación
docker compose -f $COMPOSE_FILE down

# Reconstruir (después de cambios)
docker compose -f $COMPOSE_FILE up -d --build

# Ver base de datos
docker exec -it transcripto-gpu bash
sqlite3 /app/db/app.db
.tables
.quit

# Shell dentro del contenedor
docker exec -it transcripto-gpu bash
```

### 10.2 Actualizar Código

```bash
cd /workspace/transcrypto

# Pull cambios
git pull origin main

# Reconstruir y reiniciar
docker compose -f $COMPOSE_FILE up -d --build
```

### 10.3 Backup

```bash
# Backup de base de datos
docker cp transcripto-gpu:/app/db/app.db ./backup-$(date +%Y%m%d).db

# Backup de archivos subidos
docker run --rm -v transcrypto_uploads_data:/data -v $(pwd):/backup \
    ubuntu tar czf /backup/uploads-$(date +%Y%m%d).tar.gz /data

# Descargar a tu máquina local
scp -P <PUERTO> root@ssh.vast.ai:/workspace/transcrypto/backup-*.db ./
```

---

## Consideraciones de Costos Vast.ai

### Optimización de Costos

1. **Detener cuando no uses:**
```bash
docker compose -f $COMPOSE_FILE down
```

2. **Pausar instancia en Vast.ai:**
   - Pausa facturación cuando no procesas
   - Datos persisten en disco

3. **Monitorear uso:**
```bash
# Ver cuánto tiempo lleva corriendo
docker ps -a | grep transcripto

# Ver recursos usados
docker stats --no-stream
```

### Estimación de Costos

**RTX 3090 en Vast.ai:**
- ~$0.20 - $0.40 USD/hora (varía)
- 1 hora procesamiento → ~$0.30
- 8 horas/día → ~$2.40/día
- 30 días → ~$72/mes

**Comparativa:**
- Más barato que AWS/GCP para procesamiento intermitente
- Considerar instancia dedicada si uso es 24/7

---

## Troubleshooting Específico de Vast.ai

### Problema: Conexión SSH perdida

```bash
# Reconectar
ssh -p <PUERTO> root@ssh.vast.ai

# Verificar que contenedor sigue corriendo
docker ps | grep transcripto
```

### Problema: Puerto no accesible

```bash
# Verificar firewall de Vast.ai (en panel web)
# Asegurar que puerto 5001 está abierto

# Verificar que aplicación escucha en 0.0.0.0
docker compose -f $COMPOSE_FILE logs | grep "Listening at"
```

### Problema: "Instance will be destroyed soon"

Vast.ai puede dar avisos de 5-15 minutos antes de terminar instancia.

**Solución:**
```bash
# Backup urgente
docker cp transcripto-gpu:/app/db/app.db ./emergency-backup.db

# Descargar a tu máquina
scp -P <PUERTO> root@ssh.vast.ai:/workspace/transcrypto/emergency-backup.db ./
```

### Problema: Disco lleno

```bash
# Ver uso
df -h

# Limpiar Docker
docker system prune -a -f

# Limpiar logs antiguos
truncate -s 0 /var/log/*.log

# Limpiar caché de Hugging Face (CUIDADO: descargará modelos nuevamente)
rm -rf ~/.cache/huggingface/*
```

---

## Configuración Avanzada

### Auto-restart con Systemd

Si quieres que la aplicación inicie automáticamente al reiniciar la instancia:

```bash
# Crear servicio systemd
cat > /etc/systemd/system/transcripto.service <<EOF
[Unit]
Description=Transcripto GPU Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/workspace/transcrypto
ExecStart=/usr/bin/docker compose -f $COMPOSE_FILE up -d
ExecStop=/usr/bin/docker compose -f $COMPOSE_FILE down

[Install]
WantedBy=multi-user.target
EOF

# Habilitar servicio
systemctl daemon-reload
systemctl enable transcripto.service
systemctl start transcripto.service
```

### Configurar HTTPS con Nginx

```bash
# Instalar Nginx
apt-get install -y nginx certbot python3-certbot-nginx

# Configurar proxy
cat > /etc/nginx/sites-available/transcripto <<EOF
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://localhost:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
EOF

ln -s /etc/nginx/sites-available/transcripto /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx

# Configurar SSL (si tienes dominio)
certbot --nginx -d tu-dominio.com
```

---

## Comandos Rápidos de Referencia

```bash
# CONEXIÓN
ssh -p <PUERTO> root@ssh.vast.ai

# VERIFICACIÓN
nvidia-smi                                      # GPU status
docker ps                                       # Contenedores
docker exec transcripto-gpu nvidia-smi          # GPU en contenedor

# OPERACIÓN
docker compose -f $COMPOSE_FILE up -d           # Iniciar
docker compose -f $COMPOSE_FILE down            # Detener
docker compose -f $COMPOSE_FILE restart         # Reiniciar
docker compose -f $COMPOSE_FILE logs -f         # Ver logs

# MONITOREO
watch -n 1 nvidia-smi                           # GPU en tiempo real
docker stats transcripto-gpu                    # Recursos del contenedor
df -h                                           # Espacio en disco

# MANTENIMIENTO
docker system prune -a                          # Limpiar Docker
docker compose -f $COMPOSE_FILE up -d --build   # Reconstruir
```

---

## Checklist de Despliegue

- [ ] Instancia Vast.ai rentada (RTX 3090 24GB)
- [ ] Template seleccionado (CUDA 11.8+ o 12.x)
- [ ] Conexión SSH establecida
- [ ] GPU verificada con `nvidia-smi`
- [ ] Docker funcionando
- [ ] NVIDIA Container Toolkit instalado
- [ ] Repositorio clonado
- [ ] Archivo `.env` configurado con API keys
- [ ] Imagen Docker construida
- [ ] Base de datos inicializada
- [ ] Contenedor corriendo
- [ ] GPU accesible desde contenedor
- [ ] PyTorch detecta CUDA
- [ ] Aplicación accesible en navegador
- [ ] Logs sin errores críticos

---

## Recursos

- [Vast.ai Docs](https://vast.ai/docs/)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Docker Compose](https://docs.docker.com/compose/)
- [Guía GPU Completa](./SETUP_GPU_MACHINE.md)
- [README GPU](./README_GPU.md)

---

**¡Listo para procesar transcripciones en la nube con GPU!** ☁️🚀
