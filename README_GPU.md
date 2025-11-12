# Transcrypto con GPU - Guía Rápida

Esta es una guía rápida para ejecutar Transcrypto con aceleración GPU. Para instrucciones detalladas paso a paso, consulta [SETUP_GPU_MACHINE.md](./SETUP_GPU_MACHINE.md).

## Requisitos

- **GPU**: NVIDIA RTX 3090 (24GB) o similar
- **Driver NVIDIA**: 525+
- **CUDA**: 11.8+
- **SO**: Ubuntu 22.04 LTS recomendado
- **Docker**: 20.10+ con Compose V2
- **NVIDIA Container Toolkit**

## Inicio Rápido

### 1. Verificar Requisitos Previos

```bash
# Verificar GPU
nvidia-smi

# Verificar Docker con GPU
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### 2. Configurar Variables de Entorno

```bash
# Copiar template
cp .env.example .env

# Editar y agregar tus API keys
nano .env
```

**Variables requeridas:**
- `OPENAI_API_KEY`: Para transcripción con Whisper
- `HF_TOKEN`: Para speaker diarization con pyannote.audio ([obtener aquí](https://huggingface.co/settings/tokens))

### 3. Construir y Ejecutar

```bash
# Construir imagen
docker compose -f docker-compose.gpu.yml build

# Inicializar base de datos (solo primera vez)
docker compose -f docker-compose.gpu.yml run --rm transcripto-gpu flask db upgrade

# Iniciar aplicación
docker compose -f docker-compose.gpu.yml up -d

# Ver logs
docker compose -f docker-compose.gpu.yml logs -f
```

### 4. Verificar Instalación

```bash
# Ejecutar script de verificación automática
./verify_gpu_setup.sh

# O verificar manualmente:
# - GPU en contenedor
docker exec transcripto-gpu nvidia-smi

# - PyTorch con CUDA
docker exec transcripto-gpu python3 -c "import torch; print('CUDA:', torch.cuda.is_available())"

# - Aplicación web
curl http://localhost:5001
```

## Acceso

- **URL**: http://localhost:5001
- **Usuario Admin**: admin / adminpassword (cambiar en producción)

## Comandos Útiles

```bash
# Iniciar
docker compose -f docker-compose.gpu.yml up -d

# Detener
docker compose -f docker-compose.gpu.yml down

# Reiniciar
docker compose -f docker-compose.gpu.yml restart

# Ver logs
docker compose -f docker-compose.gpu.yml logs -f

# Reconstruir (después de cambios)
docker compose -f docker-compose.gpu.yml up -d --build

# Shell en contenedor
docker exec -it transcripto-gpu bash

# Monitorear GPU
watch -n 1 nvidia-smi
```

## Arquitectura

```
┌─────────────────────────────────────────┐
│         Transcrypto Container           │
│  ┌───────────────────────────────────┐  │
│  │   Flask App (Gunicorn)            │  │
│  │   - Whisper (OpenAI)              │  │
│  │   - GPT-4/Gemini (Doc generation) │  │
│  └───────────────────────────────────┘  │
│  ┌───────────────────────────────────┐  │
│  │   PyTorch + CUDA 11.8             │  │
│  │   - pyannote.audio                │  │
│  │   - Speaker Diarization           │  │
│  └───────────────────────────────────┘  │
│                  ↓                      │
└──────────────────┼──────────────────────┘
                   ↓
        ┌──────────────────────┐
        │   NVIDIA RTX 3090    │
        │   24GB VRAM          │
        │   CUDA Cores: 10496  │
        └──────────────────────┘
```

## Características GPU

- **Transcripción**: OpenAI Whisper API (cloud)
- **Diarización**: pyannote.audio 3.3.2 (local GPU)
- **Conversión Audio**: FFmpeg (CPU)
- **Generación Documentos**: GPT-4 o Gemini (cloud)

## Optimizaciones GPU

### Workers de Gunicorn

El `docker-compose.gpu.yml` usa **2 workers** por defecto. Considera:
- **1 worker**: Máximo uso de VRAM por proceso (recomendado para modelos grandes)
- **2 workers**: Balance entre throughput y memoria
- **3+ workers**: Solo si VRAM lo permite (puede causar OOM)

### Memoria Compartida

Si ves errores de memoria compartida, aumenta `shm_size` en `docker-compose.gpu.yml`:

```yaml
shm_size: '4gb'  # Valor por defecto: 2gb
```

### Limitar Memoria GPU

Edita `docker-compose.gpu.yml`:

```yaml
environment:
  - PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

## Troubleshooting

### GPU no detectada en contenedor

```bash
# Verificar runtime
docker info | grep -i nvidia

# Reconfigurar runtime
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### CUDA Out of Memory

```bash
# Ver uso de memoria
nvidia-smi

# Reducir workers
# Editar Dockerfile.gpu línea 71: --workers 1
docker compose -f docker-compose.gpu.yml up -d --build
```

### Error de Hugging Face

```bash
# Verificar token
docker exec transcripto-gpu env | grep HF_TOKEN

# Login manual
docker exec transcripto-gpu python3 -c "from huggingface_hub import login; login('tu-token')"
```

### Logs de errores

```bash
# Ver errores
docker compose -f docker-compose.gpu.yml logs | grep -i error

# Ver logs de Python
docker compose -f docker-compose.gpu.yml logs | grep -i traceback -A 20
```

## Monitoreo

### GPU en tiempo real

```bash
# Simple
watch -n 1 nvidia-smi

# Detallado
nvidia-smi dmon -i 0 -s u

# Con temperatura y consumo
nvidia-smi --query-gpu=timestamp,temperature.gpu,utilization.gpu,memory.used,memory.total --format=csv -l 1
```

### Aplicación

```bash
# Logs en vivo
docker compose -f docker-compose.gpu.yml logs -f

# Estadísticas del contenedor
docker stats transcripto-gpu

# Healthcheck
docker inspect transcripto-gpu | grep -i health -A 10
```

## Estructura de Archivos GPU

```
transcrypto/
├── Dockerfile.gpu              # Dockerfile con CUDA
├── docker-compose.gpu.yml      # Compose con GPU support
├── SETUP_GPU_MACHINE.md        # Guía detallada paso a paso
├── README_GPU.md               # Esta guía rápida
├── verify_gpu_setup.sh         # Script de verificación
├── .env                        # Variables de entorno
└── requirements.txt            # Dependencias Python
```

## Diferencias vs CPU

| Aspecto | CPU (Dockerfile) | GPU (Dockerfile.gpu) |
|---------|------------------|---------------------|
| Imagen base | `python:3.11-slim` | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04` |
| PyTorch | CPU only | CUDA 11.8 |
| Workers | 3 | 2 (menos para evitar OOM) |
| Diarización | No disponible | pyannote.audio |
| Memoria | ~2GB RAM | ~8GB VRAM + 4GB RAM |
| Tiempo build | ~5 min | ~15 min |

## Performance Esperado

Con RTX 3090:
- **Diarización**: ~2-3x tiempo real (30 min de audio → 60-90 seg)
- **Transcripción**: Depende de OpenAI API (cloud)
- **Memoria**: ~6-8GB VRAM en uso durante diarización
- **Temperatura**: 60-75°C bajo carga

## Producción

Para deployment en producción:

1. **SSL/HTTPS**: Usar Nginx como reverse proxy
2. **Firewall**: Configurar UFW o iptables
3. **Monitoring**: Prometheus + Grafana para GPU
4. **Backups**: Volúmenes de Docker (`db_data`, `uploads_data`)
5. **Secrets**: Usar Docker secrets o vault para API keys
6. **Auto-restart**: `restart: unless-stopped` ya configurado

## Recursos

- [Guía Completa](./SETUP_GPU_MACHINE.md) - Instalación paso a paso
- [NVIDIA Drivers](https://www.nvidia.com/Download/index.aspx)
- [Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
- [PyTorch CUDA](https://pytorch.org/get-started/locally/)
- [pyannote.audio](https://github.com/pyannote/pyannote-audio)

## Soporte

- Verificación automática: `./verify_gpu_setup.sh`
- Logs: `docker compose -f docker-compose.gpu.yml logs`
- Issues: Repositorio del proyecto

---

**¡Listo para transcribir con GPU!** 🚀
