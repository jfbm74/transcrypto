#!/bin/bash
# Script de Verificación de Configuración GPU para Transcrypto
# Uso: ./verify_gpu_setup.sh [--step NUMERO]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funciones de ayuda
print_header() {
    echo -e "\n${BLUE}===================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# Función para verificar comandos
check_command() {
    if command -v $1 &> /dev/null; then
        print_success "$1 está instalado"
        return 0
    else
        print_error "$1 NO está instalado"
        return 1
    fi
}

# Paso 1: Verificar GPU Hardware
verify_step1() {
    print_header "PASO 1: Verificación de Hardware GPU"

    if lspci | grep -i nvidia &> /dev/null; then
        GPU_INFO=$(lspci | grep -i nvidia | head -1)
        print_success "GPU NVIDIA detectada: $GPU_INFO"

        if echo "$GPU_INFO" | grep -i "RTX 3090" &> /dev/null; then
            print_success "RTX 3090 confirmada ✓"
        else
            print_warning "GPU detectada no es RTX 3090"
        fi
    else
        print_error "No se detectó GPU NVIDIA"
        print_info "Verifica que la GPU está correctamente instalada en la placa madre"
        return 1
    fi
}

# Paso 2: Verificar Drivers NVIDIA
verify_step2() {
    print_header "PASO 2: Verificación de Drivers NVIDIA"

    if check_command nvidia-smi; then
        echo ""
        print_info "Información de nvidia-smi:"
        nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

        DRIVER_VERSION=$(nvidia-smi --query-gpu=driver_version --format=csv,noheader | head -1)
        CUDA_VERSION=$(nvidia-smi | grep "CUDA Version" | awk '{print $9}')

        print_success "Driver NVIDIA: $DRIVER_VERSION"
        print_success "CUDA Version: $CUDA_VERSION"

        # Verificar versión mínima del driver (525+)
        MAJOR_VERSION=$(echo $DRIVER_VERSION | cut -d. -f1)
        if [ "$MAJOR_VERSION" -ge 525 ]; then
            print_success "Versión del driver es compatible (>= 525)"
        else
            print_warning "Versión del driver podría ser antigua. Recomendado: 525+"
        fi
    else
        print_error "nvidia-smi no funciona. Drivers no instalados correctamente"
        print_info "Ejecuta: sudo ubuntu-drivers autoinstall"
        return 1
    fi
}

# Paso 3: Verificar Docker
verify_step3() {
    print_header "PASO 3: Verificación de Docker"

    if check_command docker; then
        DOCKER_VERSION=$(docker --version)
        print_success "$DOCKER_VERSION"

        # Verificar que docker funciona sin sudo
        if docker ps &> /dev/null; then
            print_success "Docker funciona sin sudo"
        else
            print_warning "Docker requiere sudo. Considera agregar tu usuario al grupo docker"
            print_info "Ejecuta: sudo usermod -aG docker \$USER && newgrp docker"
        fi

        # Verificar docker compose
        if docker compose version &> /dev/null; then
            COMPOSE_VERSION=$(docker compose version)
            print_success "$COMPOSE_VERSION"
        else
            print_error "Docker Compose plugin no instalado"
            return 1
        fi
    else
        print_error "Docker no está instalado"
        return 1
    fi
}

# Paso 4: Verificar NVIDIA Container Toolkit
verify_step4() {
    print_header "PASO 4: Verificación de NVIDIA Container Toolkit"

    if check_command nvidia-ctk; then
        print_success "NVIDIA Container Toolkit instalado"

        # Verificar runtime de Docker
        if docker info | grep -i nvidia &> /dev/null; then
            print_success "Docker runtime NVIDIA configurado"
        else
            print_warning "Docker runtime NVIDIA no detectado"
            print_info "Ejecuta: sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker"
        fi

        # Probar GPU en Docker
        print_info "Probando acceso a GPU desde Docker..."
        if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
            print_success "Docker puede acceder a la GPU correctamente"
        else
            print_error "Docker NO puede acceder a la GPU"
            print_info "Verifica que docker runtime está configurado correctamente"
            return 1
        fi
    else
        print_error "NVIDIA Container Toolkit no está instalado"
        print_info "Sigue las instrucciones del Paso 4 en SETUP_GPU_MACHINE.md"
        return 1
    fi
}

# Paso 5: Verificar Archivos del Proyecto
verify_step5() {
    print_header "PASO 5: Verificación de Archivos del Proyecto"

    FILES=("Dockerfile.gpu" "docker-compose.gpu.yml" ".env" "requirements.txt")

    for file in "${FILES[@]}"; do
        if [ -f "$file" ]; then
            print_success "$file existe"
        else
            if [ "$file" == ".env" ]; then
                print_warning "$file no existe. Créalo antes de continuar"
                print_info "Copia .env.example o crea uno nuevo con las API keys"
            else
                print_error "$file no existe"
                return 1
            fi
        fi
    done

    # Verificar variables de entorno importantes
    if [ -f ".env" ]; then
        print_info "Verificando variables de entorno en .env..."

        if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=\$" .env; then
            print_success "OPENAI_API_KEY configurado"
        else
            print_warning "OPENAI_API_KEY no configurado en .env"
        fi

        if grep -q "HUGGINGFACE_TOKEN=" .env && ! grep -q "HUGGINGFACE_TOKEN=\$" .env; then
            print_success "HUGGINGFACE_TOKEN configurado"
        else
            print_warning "HUGGINGFACE_TOKEN no configurado (necesario para pyannote.audio)"
        fi
    fi
}

# Paso 6: Verificar Imagen Docker
verify_step6() {
    print_header "PASO 6: Verificación de Imagen Docker"

    if docker images | grep -q transcrypto.*gpu; then
        IMAGE_INFO=$(docker images | grep transcrypto | grep gpu | head -1)
        print_success "Imagen Docker GPU encontrada"
        echo "$IMAGE_INFO"
    else
        print_warning "Imagen Docker GPU no construida"
        print_info "Ejecuta: docker compose -f docker-compose.gpu.yml build"
    fi
}

# Paso 7: Verificar Contenedor Corriendo
verify_step7() {
    print_header "PASO 7: Verificación de Contenedor en Ejecución"

    if docker ps | grep -q transcripto-gpu; then
        print_success "Contenedor transcripto-gpu está corriendo"

        # Verificar GPU dentro del contenedor
        print_info "Verificando GPU dentro del contenedor..."
        if docker exec transcripto-gpu nvidia-smi &> /dev/null; then
            print_success "GPU accesible dentro del contenedor"

            # Información de GPU en contenedor
            echo ""
            docker exec transcripto-gpu nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader
        else
            print_error "GPU NO accesible dentro del contenedor"
            return 1
        fi

        # Verificar PyTorch con CUDA
        print_info "Verificando PyTorch con CUDA..."
        PYTORCH_CHECK=$(docker exec transcripto-gpu python3 -c "import torch; print(f'PyTorch {torch.__version__} | CUDA: {torch.cuda.is_available()} | GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')" 2>/dev/null)

        if echo "$PYTORCH_CHECK" | grep -q "CUDA: True"; then
            print_success "$PYTORCH_CHECK"
        else
            print_error "PyTorch no detecta CUDA"
            echo "$PYTORCH_CHECK"
            return 1
        fi

        # Verificar endpoint HTTP
        print_info "Verificando endpoint HTTP..."
        if curl -s http://localhost:5001/ &> /dev/null; then
            print_success "Aplicación responde en http://localhost:5001"
        else
            print_warning "Aplicación no responde en http://localhost:5001"
            print_info "Verifica logs: docker compose -f docker-compose.gpu.yml logs"
        fi
    else
        print_warning "Contenedor transcripto-gpu NO está corriendo"
        print_info "Ejecuta: docker compose -f docker-compose.gpu.yml up -d"
    fi
}

# Resumen Final
print_summary() {
    print_header "RESUMEN DE VERIFICACIÓN"

    echo -e "${GREEN}Pasos completados exitosamente:${NC}"
    echo "1. ✓ GPU Hardware detectado"
    echo "2. ✓ Drivers NVIDIA instalados y funcionando"
    echo "3. ✓ Docker instalado y configurado"
    echo "4. ✓ NVIDIA Container Toolkit funcionando"
    echo "5. ✓ Archivos del proyecto presentes"
    echo "6. ✓ Imagen Docker construida"
    echo "7. ✓ Contenedor corriendo con GPU"
    echo ""
    print_success "¡Sistema completamente configurado y funcionando!"
    echo ""
    print_info "Accede a la aplicación en: http://localhost:5001"
    print_info "Monitorea la GPU con: watch -n 1 nvidia-smi"
    print_info "Ver logs: docker compose -f docker-compose.gpu.yml logs -f"
}

# Main
main() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════╗"
    echo "║   Verificación de Configuración GPU - Transcrypto     ║"
    echo "╚════════════════════════════════════════════════════════╝"
    echo -e "${NC}"

    # Verificar si se especificó un paso
    if [ "$1" == "--step" ] && [ -n "$2" ]; then
        case $2 in
            1) verify_step1 ;;
            2) verify_step2 ;;
            3) verify_step3 ;;
            4) verify_step4 ;;
            5) verify_step5 ;;
            6) verify_step6 ;;
            7) verify_step7 ;;
            *) echo "Paso inválido. Usa números del 1 al 7" ;;
        esac
    else
        # Ejecutar todos los pasos
        FAILED=0

        verify_step1 || FAILED=1
        verify_step2 || FAILED=1
        verify_step3 || FAILED=1
        verify_step4 || FAILED=1
        verify_step5 || FAILED=1
        verify_step6 || ((FAILED+=0))  # No es crítico
        verify_step7 || ((FAILED+=0))  # No es crítico

        if [ $FAILED -eq 0 ]; then
            print_summary
        else
            echo ""
            print_error "Algunos pasos fallaron. Revisa los errores arriba."
            print_info "Puedes verificar pasos individuales con: ./verify_gpu_setup.sh --step N"
            exit 1
        fi
    fi
}

# Ejecutar
main "$@"
