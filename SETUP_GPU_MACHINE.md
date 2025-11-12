# Guía de Configuración: Máquina con GPU para Transcrypto

Esta guía te ayudará a configurar una máquina con GPU NVIDIA RTX 3090 (24GB) para ejecutar Transcrypto en Docker con aceleración GPU.

## Especificaciones de la Máquina

- **GPU**: NVIDIA RTX 3090 (24GB VRAM)
- **Arquitectura**: Ampere (Compute Capability 8.6)
- **CUDA**: 11.8 o superior
- **Sistema Operativo Recomendado**: Ubuntu 22.04 LTS

---

## Paso 1: Preparar el Sistema Operativo

### 1.1 Instalar Ubuntu 22.04 LTS

```bash
# Actualizar el sistema
sudo apt-get update && sudo apt-get upgrade -y

# Instalar herramientas básicas
sudo apt-get install -y \
    build-essential \
    curl \
    wget \
    git \
    vim \
    htop \
    net-tools
```

### 1.2 Verificar que la GPU es detectada

```bash
# Verificar que el sistema detecta la GPU
lspci | grep -i nvidia
# Deberías ver: NVIDIA Corporation GA102 [GeForce RTX 3090]
```

---

## Paso 2: Instalar Drivers NVIDIA

### 2.1 Método Recomendado (Ubuntu)

```bash
# Agregar repositorio de drivers NVIDIA
sudo add-apt-repository ppa:graphics-drivers/ppa
sudo apt-get update

# Ver drivers disponibles
ubuntu-drivers devices

# Instalar el driver recomendado (versión 525 o superior)
sudo ubuntu-drivers autoinstall

# O instalar una versión específica (ejemplo: 535)
sudo apt-get install -y nvidia-driver-535

# Reiniciar el sistema
sudo reboot
```

### 2.2 Verificar Instalación

```bash
# Después del reinicio, verificar que el driver está funcionando
nvidia-smi

# Deberías ver información de tu RTX 3090:
# - Versión del driver
# - CUDA Version
# - Memoria GPU (24GB)
# - Temperatura, utilización, etc.
```

**Salida esperada de nvidia-smi:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 535.xx.xx    Driver Version: 535.xx.xx    CUDA Version: 12.2    |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  NVIDIA GeForce ...  Off  | 00000000:01:00.0 Off |                  N/A |
| 30%   35C    P8    25W / 350W |      0MiB / 24576MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

---

## Paso 3: Instalar Docker

### 3.1 Desinstalar versiones antiguas (si existen)

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
```

### 3.2 Instalar Docker Engine

```bash
# Agregar repositorio de Docker
sudo apt-get install -y \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

sudo mkdir -m 0755 -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instalar Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Verificar instalación
sudo docker --version
docker compose version
```

### 3.3 Configurar Docker (opcional pero recomendado)

```bash
# Agregar tu usuario al grupo docker (evita usar sudo)
sudo usermod -aG docker $USER

# Aplicar cambios (o reinicia sesión)
newgrp docker

# Verificar que funciona sin sudo
docker ps
```

---

## Paso 4: Instalar NVIDIA Container Toolkit

El NVIDIA Container Toolkit permite que Docker acceda a la GPU.

### 4.1 Agregar Repositorio

```bash
# Configurar repositorio
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
```

### 4.2 Instalar NVIDIA Container Toolkit

```bash
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit

# Configurar Docker runtime
sudo nvidia-ctk runtime configure --runtime=docker

# Reiniciar Docker
sudo systemctl restart docker
```

### 4.3 Verificar que Docker puede acceder a la GPU

```bash
# Probar con un contenedor de prueba
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# Deberías ver la misma información de nvidia-smi dentro del contenedor
```

---

## Paso 5: Configurar Transcrypto

### 5.1 Clonar/Copiar el Repositorio

```bash
# Si es una máquina nueva, clonar el repositorio
cd /home/juan/projects/zentratek
git clone <url-del-repo> transcrypto
cd transcrypto

# Si ya existe, asegurarte de estar en la última versión
git pull origin main
```

### 5.2 Configurar Variables de Entorno

```bash
# Crear archivo .env
cp .env.example .env  # Si existe un ejemplo

# O crear uno nuevo
nano .env
```

**Contenido del archivo `.env`:**
```bash
# Flask
SECRET_KEY=tu-clave-secreta-muy-larga-y-aleatoria-aqui

# OpenAI API (requerido para Whisper)
OPENAI_API_KEY=sk-...tu-api-key...

# Google AI API (opcional, para Gemini)
GOOGLE_AI_API_KEY=...tu-api-key...

# Hugging Face (requerido para pyannote.audio con GPU)
HUGGINGFACE_TOKEN=hf_...tu-token...

# Límite de transcripciones gratuitas
FREE_TRANSCRIPTIONS_LIMIT=10
```

**Importante:** Necesitas un token de Hugging Face para usar pyannote.audio:
1. Crea una cuenta en https://huggingface.co/
2. Ve a Settings > Access Tokens
3. Crea un nuevo token con permisos de lectura
4. Acepta los términos de uso de los modelos pyannote:
   - https://huggingface.co/pyannote/speaker-diarization-3.1
   - https://huggingface.co/pyannote/segmentation-3.0

### 5.3 Verificar Archivos Docker GPU

```bash
# Verificar que existen los archivos GPU
ls -la Dockerfile.gpu docker-compose.gpu.yml

# Si no existen, ya los creamos en los pasos anteriores
```

---

## Paso 6: Construir y Ejecutar el Contenedor

### 6.1 Construir la Imagen Docker

```bash
# Construir la imagen con soporte GPU (puede tardar 10-15 minutos)
docker compose -f docker-compose.gpu.yml build

# Ver el progreso de la construcción
# Esto descargará la imagen CUDA (~2GB) e instalará todas las dependencias
```

### 6.2 Inicializar la Base de Datos (primera vez)

```bash
# Crear un contenedor temporal para inicializar la BD
docker compose -f docker-compose.gpu.yml run --rm transcripto-gpu flask db upgrade

# Esto creará la base de datos SQLite y las tablas necesarias
```

### 6.3 Iniciar el Contenedor

```bash
# Iniciar en modo detached (segundo plano)
docker compose -f docker-compose.gpu.yml up -d

# Ver logs en tiempo real
docker compose -f docker-compose.gpu.yml logs -f

# Ver solo logs del inicio
docker compose -f docker-compose.gpu.yml logs --tail=100
```

### 6.4 Verificar que el Contenedor está usando la GPU

```bash
# Ejecutar nvidia-smi dentro del contenedor
docker exec transcripto-gpu nvidia-smi

# Ver procesos Python usando la GPU
docker exec transcripto-gpu nvidia-smi pmon -i 0

# Verificar variables de entorno CUDA
docker exec transcripto-gpu env | grep -i cuda
```

---

## Paso 7: Verificación y Pruebas

### 7.1 Verificar que la Aplicación está Funcionando

```bash
# Verificar que el contenedor está corriendo
docker ps | grep transcripto-gpu

# Verificar logs de inicio
docker compose -f docker-compose.gpu.yml logs | grep -i "Booting worker"

# Probar la aplicación
curl http://localhost:5001/

# Deberías ver el HTML de la página principal
```

### 7.2 Probar PyTorch con GPU

```bash
# Ejecutar test de PyTorch dentro del contenedor
docker exec transcripto-gpu python3 -c "
import torch
print('PyTorch version:', torch.__version__)
print('CUDA available:', torch.cuda.is_available())
print('CUDA version:', torch.version.cuda)
print('GPU device:', torch.cuda.get_device_name(0))
print('GPU memory:', round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 2), 'GB')
"

# Salida esperada:
# PyTorch version: 2.3.1+cu118
# CUDA available: True
# CUDA version: 11.8
# GPU device: NVIDIA GeForce RTX 3090
# GPU memory: 24.0 GB
```

### 7.3 Acceder a la Aplicación

```bash
# Desde el navegador:
http://<ip-de-tu-maquina>:5001

# Si estás en la misma máquina:
http://localhost:5001
```

---

## Paso 8: Monitoreo y Mantenimiento

### 8.1 Monitorear Uso de GPU en Tiempo Real

```bash
# Monitorear GPU cada segundo
watch -n 1 nvidia-smi

# O con más detalle
nvidia-smi dmon -i 0 -s u

# Ver temperatura y consumo
nvidia-smi --query-gpu=timestamp,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1
```

### 8.2 Logs de la Aplicación

```bash
# Ver logs en tiempo real
docker compose -f docker-compose.gpu.yml logs -f

# Ver logs de errores
docker compose -f docker-compose.gpu.yml logs | grep -i error

# Ver últimas 100 líneas
docker compose -f docker-compose.gpu.yml logs --tail=100
```

### 8.3 Gestión del Contenedor

```bash
# Detener el contenedor
docker compose -f docker-compose.gpu.yml down

# Reiniciar el contenedor
docker compose -f docker-compose.gpu.yml restart

# Reconstruir y reiniciar (después de cambios en código)
docker compose -f docker-compose.gpu.yml up -d --build

# Limpiar volúmenes (¡CUIDADO! Elimina la base de datos)
docker compose -f docker-compose.gpu.yml down -v
```

---

## Paso 9: Optimizaciones Opcionales

### 9.1 Ajustar Workers de Gunicorn

Si tienes mucha carga, edita `Dockerfile.gpu:71`:

```dockerfile
# Para RTX 3090, usar 1-2 workers para evitar fragmentación de VRAM
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--timeout", "7200", "wsgi:app"]
```

**Nota**: Con GPU, menos workers es mejor. Cada worker carga modelos en VRAM.

### 9.2 Configurar Memoria Compartida

Si tienes errores de memoria compartida, edita `docker-compose.gpu.yml`:

```yaml
shm_size: '4gb'  # Aumentar si es necesario
```

### 9.3 Limitar Uso de GPU (opcional)

Para limitar el uso de memoria GPU:

```bash
# Editar docker-compose.gpu.yml
environment:
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

---

## Paso 10: Configuración de Firewall (Producción)

### 10.1 Configurar UFW (Ubuntu Firewall)

```bash
# Habilitar firewall
sudo ufw enable

# Permitir SSH (¡IMPORTANTE! hazlo antes de habilitar)
sudo ufw allow 22/tcp

# Permitir puerto de la aplicación
sudo ufw allow 5001/tcp

# Verificar reglas
sudo ufw status verbose
```

### 10.2 Configurar Reverse Proxy (opcional)

Para producción, considera usar Nginx:

```bash
sudo apt-get install -y nginx

# Configurar Nginx como proxy inverso a localhost:5001
# Ver documentación de Nginx para SSL/HTTPS
```

---

## Troubleshooting

### Problema: "nvidia-smi: command not found"
**Solución**: Reinstalar drivers NVIDIA (Paso 2)

### Problema: "docker: Error response from daemon: could not select device driver"
**Solución**: Reinstalar NVIDIA Container Toolkit (Paso 4)

### Problema: "CUDA out of memory"
**Solución**:
- Reducir workers de Gunicorn a 1
- Aumentar timeout
- Verificar que no hay otros procesos usando la GPU

### Problema: "No space left on device"
**Solución**:
```bash
# Limpiar imágenes y contenedores no usados
docker system prune -a

# Verificar espacio en disco
df -h
```

### Problema: Error de autenticación con Hugging Face
**Solución**:
- Verificar que HUGGINGFACE_TOKEN está en `.env`
- Aceptar términos de uso de modelos pyannote
- Ejecutar dentro del contenedor:
```bash
docker exec transcripto-gpu python3 -c "from huggingface_hub import login; login('<tu-token>')"
```

---

## Comandos Rápidos de Referencia

```bash
# Iniciar aplicación
docker compose -f docker-compose.gpu.yml up -d

# Ver logs
docker compose -f docker-compose.gpu.yml logs -f

# Reiniciar
docker compose -f docker-compose.gpu.yml restart

# Detener
docker compose -f docker-compose.gpu.yml down

# Reconstruir
docker compose -f docker-compose.gpu.yml up -d --build

# Ver GPU
nvidia-smi

# GPU dentro del contenedor
docker exec transcripto-gpu nvidia-smi

# Shell dentro del contenedor
docker exec -it transcripto-gpu bash
```

---

## Recursos Adicionales

- [NVIDIA Driver Installation](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [Docker Compose GPU Support](https://docs.docker.com/compose/gpu-support/)
- [PyTorch CUDA Installation](https://pytorch.org/get-started/locally/)
- [Hugging Face Tokens](https://huggingface.co/docs/hub/security-tokens)

---

## Soporte

Si encuentras problemas específicos de Transcrypto, revisa:
- Logs: `docker compose -f docker-compose.gpu.yml logs`
- Issues: Repositorio del proyecto
- Documentación: `CLAUDE.md`, `README.md`

---

**¡Configuración completada!** Tu máquina con RTX 3090 está lista para procesar transcripciones con aceleración GPU. 🚀
