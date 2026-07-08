#!/bin/bash

###############################################################################
# Script de Backup Automático de PostgreSQL
###############################################################################
#
# Descripción:
#   Script completo para backup automático de PostgreSQL con:
#   - Backup completo de base de datos
#   - Compresión gzip para ahorrar espacio
#   - Rotación automática de backups antiguos
#   - Validación de backup exitoso
#   - Logging detallado
#   - Notificaciones por email (opcional)
#
# Uso:
#   ./backup_postgres.sh [opciones]
#
# Opciones:
#   --keep-days N    Días a mantener backups (default: 7)
#   --no-compress    No comprimir backup
#   --notify EMAIL   Enviar notificación a email
#
# Ejemplo:
#   ./backup_postgres.sh --keep-days 30 --notify admin@example.com
#
# Configuración para cron (ejecutar diariamente a las 2 AM):
#   0 2 * * * /path/to/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
#
###############################################################################

set -e  # Exit on error
set -u  # Exit on undefined variable
set -o pipefail  # Exit on pipe failure

###############################################################################
# CONFIGURACIÓN
###############################################################################

# Docker
DOCKER_CONTAINER="iot_postgres"
DOCKER_COMPOSE_PATH="/e/Documentos/Marcelo/Trabajos\ Idea/Python/Idea_IoT"

# PostgreSQL
POSTGRES_USER="${POSTGRES_USER:-iot_admin}"
POSTGRES_DB="${POSTGRES_DB:-iot_monitoring}"

# Directorios
BACKUP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../backups"
LOG_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../../logs"

# Configuración de retención
KEEP_DAYS=7  # Días a mantener backups

# Flags
COMPRESS=true
NOTIFY_EMAIL=""

###############################################################################
# COLORES PARA OUTPUT
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

###############################################################################
# FUNCIONES
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

check_docker_container() {
    if ! docker ps | grep -q "$DOCKER_CONTAINER"; then
        log_error "Container $DOCKER_CONTAINER no está corriendo"
        exit 1
    fi
    log_success "Container $DOCKER_CONTAINER está corriendo"
}

create_directories() {
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    log_success "Directorios creados: $BACKUP_DIR, $LOG_DIR"
}

perform_backup() {
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_name="postgres_${POSTGRES_DB}_${timestamp}"
    local backup_file="$BACKUP_DIR/${backup_name}.sql"
    local final_file="$backup_file"

    log_info "Iniciando backup de $POSTGRES_DB..."

    # Ejecutar pg_dump dentro del container
    if docker exec -t "$DOCKER_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$backup_file"; then
        log_success "Backup SQL generado: $backup_file"
    else
        log_error "Fallo al generar backup SQL"
        return 1
    fi

    # Verificar que el backup no esté vacío
    if [ ! -s "$backup_file" ]; then
        log_error "Backup generado está vacío"
        return 1
    fi

    local file_size=$(du -h "$backup_file" | cut -f1)
    log_info "Tamaño del backup: $file_size"

    # Comprimir si está habilitado
    if [ "$COMPRESS" = true ]; then
        log_info "Comprimiendo backup con gzip..."
        gzip "$backup_file"
        final_file="${backup_file}.gz"

        if [ -f "$final_file" ]; then
            local compressed_size=$(du -h "$final_file" | cut -f1)
            log_success "Backup comprimido: $final_file (Tamaño: $compressed_size)"
        else
            log_error "Fallo al comprimir backup"
            return 1
        fi
    fi

    # Validar integridad del backup
    validate_backup "$final_file"

    echo "$final_file"
}

validate_backup() {
    local backup_file="$1"

    log_info "Validando integridad del backup..."

    # Verificar que el archivo existe y no está vacío
    if [ ! -s "$backup_file" ]; then
        log_error "Archivo de backup no existe o está vacío"
        return 1
    fi

    # Si está comprimido, verificar integridad de gzip
    if [[ "$backup_file" == *.gz ]]; then
        if gzip -t "$backup_file" 2>/dev/null; then
            log_success "Integridad de gzip verificada"
        else
            log_error "Backup comprimido está corrupto"
            return 1
        fi
    fi

    log_success "Validación de backup exitosa"
}

rotate_old_backups() {
    log_info "Rotando backups antiguos (manteniendo últimos $KEEP_DAYS días)..."

    local deleted_count=0
    local total_size_freed=0

    # Buscar y eliminar backups más antiguos que KEEP_DAYS
    while IFS= read -r -d '' backup_file; do
        local file_age_days=$(( ($(date +%s) - $(stat -c %Y "$backup_file")) / 86400 ))

        if [ "$file_age_days" -gt "$KEEP_DAYS" ]; then
            local file_size=$(du -b "$backup_file" | cut -f1)
            total_size_freed=$((total_size_freed + file_size))

            log_warning "Eliminando backup antiguo (${file_age_days} días): $(basename "$backup_file")"
            rm "$backup_file"
            deleted_count=$((deleted_count + 1))
        fi
    done < <(find "$BACKUP_DIR" -name "postgres_*.sql*" -print0)

    if [ $deleted_count -gt 0 ]; then
        local size_mb=$((total_size_freed / 1024 / 1024))
        log_success "Eliminados $deleted_count backups antiguos (Espacio liberado: ${size_mb}MB)"
    else
        log_info "No hay backups antiguos para eliminar"
    fi
}

list_existing_backups() {
    log_info "Backups existentes:"

    local backup_count=0
    local total_size=0

    while IFS= read -r -d '' backup_file; do
        local file_size=$(du -h "$backup_file" | cut -f1)
        local file_date=$(stat -c %y "$backup_file" | cut -d' ' -f1)
        echo "  - $(basename "$backup_file") (Tamaño: $file_size, Fecha: $file_date)"
        backup_count=$((backup_count + 1))
        total_size=$((total_size + $(du -b "$backup_file" | cut -f1)))
    done < <(find "$BACKUP_DIR" -name "postgres_*.sql*" -print0 | sort -z)

    if [ $backup_count -eq 0 ]; then
        log_warning "No hay backups existentes"
    else
        local total_mb=$((total_size / 1024 / 1024))
        log_info "Total: $backup_count backups (${total_mb}MB)"
    fi
}

send_notification() {
    local status="$1"
    local backup_file="$2"

    if [ -z "$NOTIFY_EMAIL" ]; then
        return 0
    fi

    log_info "Enviando notificación a $NOTIFY_EMAIL..."

    local subject="[IoT Monitoring] Backup PostgreSQL - $status"
    local body="Backup de PostgreSQL completado.\n\nStatus: $status\nFecha: $(date '+%Y-%m-%d %H:%M:%S')\nBackup: $(basename "$backup_file")\nTamaño: $(du -h "$backup_file" | cut -f1)"

    # Usar sendmail o mail command (requiere configuración previa)
    echo -e "$body" | mail -s "$subject" "$NOTIFY_EMAIL" 2>/dev/null || log_warning "No se pudo enviar email"
}

show_help() {
    cat << EOF
Uso: $0 [opciones]

Script de backup automático de PostgreSQL para IoT Monitoring System.

Opciones:
  --keep-days N      Días a mantener backups (default: 7)
  --no-compress      No comprimir backup con gzip
  --notify EMAIL     Enviar notificación a email
  -h, --help         Mostrar esta ayuda

Ejemplos:
  $0                                      # Backup con configuración default
  $0 --keep-days 30                       # Mantener backups por 30 días
  $0 --notify admin@example.com           # Enviar notificación
  $0 --keep-days 30 --notify admin@example.com  # Combinado

EOF
}

###############################################################################
# PARSEAR ARGUMENTOS
###############################################################################

while [[ $# -gt 0 ]]; do
    case $1 in
        --keep-days)
            KEEP_DAYS="$2"
            shift 2
            ;;
        --no-compress)
            COMPRESS=false
            shift
            ;;
        --notify)
            NOTIFY_EMAIL="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Opción desconocida: $1"
            show_help
            exit 1
            ;;
    esac
done

###############################################################################
# MAIN
###############################################################################

main() {
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "  Backup Automático de PostgreSQL - IoT Monitoring System"
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Container: $DOCKER_CONTAINER"
    log_info "Base de datos: $POSTGRES_DB"
    log_info "Directorio de backups: $BACKUP_DIR"
    log_info "Retención: $KEEP_DAYS días"
    log_info "Compresión: $([ "$COMPRESS" = true ] && echo "Habilitada" || echo "Deshabilitada")"
    log_info "───────────────────────────────────────────────────────────────"

    # Paso 1: Verificar container Docker
    check_docker_container

    # Paso 2: Crear directorios
    create_directories

    # Paso 3: Realizar backup
    backup_file=$(perform_backup)
    if [ $? -eq 0 ]; then
        log_success "✓ Backup completado exitosamente"
    else
        log_error "✗ Backup falló"
        send_notification "FAILED" ""
        exit 1
    fi

    # Paso 4: Rotar backups antiguos
    rotate_old_backups

    # Paso 5: Listar backups existentes
    list_existing_backups

    # Paso 6: Notificación (si está configurada)
    send_notification "SUCCESS" "$backup_file"

    log_info "═══════════════════════════════════════════════════════════════"
    log_success "✓ Proceso de backup completado exitosamente"
    log_info "═══════════════════════════════════════════════════════════════"
}

# Ejecutar main
main
