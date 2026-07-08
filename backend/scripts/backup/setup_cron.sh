#!/bin/bash

###############################################################################
# Script de Configuración de Cron Job para Backups Automáticos
###############################################################################
#
# Descripción:
#   Configura cron job para ejecutar backups automáticos de PostgreSQL.
#   Puede configurarse para ejecutarse diariamente, semanalmente o mensualmente.
#
# Uso:
#   ./setup_cron.sh [frecuencia] [hora]
#
# Frecuencias:
#   daily      - Diariamente (default)
#   weekly     - Semanalmente (domingos)
#   monthly    - Mensualmente (día 1)
#
# Hora:
#   Formato 24h (ej: 02:00 para 2 AM)
#
# Ejemplos:
#   ./setup_cron.sh                    # Daily a las 2 AM (default)
#   ./setup_cron.sh daily 03:00        # Daily a las 3 AM
#   ./setup_cron.sh weekly 01:30       # Domingos a la 1:30 AM
#   ./setup_cron.sh monthly 00:00      # Día 1 de cada mes a medianoche
#
###############################################################################

set -e
set -u

###############################################################################
# COLORES
###############################################################################

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

###############################################################################
# FUNCIONES
###############################################################################

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    cat << EOF
Uso: $0 [frecuencia] [hora]

Configura cron job para backups automáticos de PostgreSQL.

Frecuencias:
  daily      - Diariamente (default)
  weekly     - Semanalmente (domingos)
  monthly    - Mensualmente (día 1)

Hora:
  Formato 24h (ej: 02:00 para 2 AM)

Ejemplos:
  $0                     # Daily a las 2 AM
  $0 daily 03:00         # Daily a las 3 AM
  $0 weekly 01:30        # Domingos a la 1:30 AM
  $0 monthly 00:00       # Día 1 de cada mes a medianoche

EOF
}

parse_time() {
    local time_str="$1"

    if [[ ! "$time_str" =~ ^([0-1][0-9]|2[0-3]):([0-5][0-9])$ ]]; then
        log_error "Formato de hora inválido: $time_str (usar HH:MM)"
        exit 1
    fi

    local hour=$(echo "$time_str" | cut -d: -f1)
    local minute=$(echo "$time_str" | cut -d: -f2)

    # Remover leading zeros
    hour=$((10#$hour))
    minute=$((10#$minute))

    echo "$minute $hour"
}

generate_cron_expression() {
    local frequency="$1"
    local time_parts="$2"
    local minute=$(echo "$time_parts" | cut -d' ' -f1)
    local hour=$(echo "$time_parts" | cut -d' ' -f2)

    case "$frequency" in
        daily)
            echo "$minute $hour * * *"
            ;;
        weekly)
            # Domingos (day 0)
            echo "$minute $hour * * 0"
            ;;
        monthly)
            # Día 1 de cada mes
            echo "$minute $hour 1 * *"
            ;;
        *)
            log_error "Frecuencia inválida: $frequency"
            exit 1
            ;;
    esac
}

get_script_path() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "${script_dir}/backup_postgres.sh"
}

get_log_path() {
    local script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    echo "${script_dir}/../../logs/postgres_backup.log"
}

install_cron_job() {
    local cron_expr="$1"
    local script_path="$2"
    local log_path="$3"
    local keep_days="${4:-7}"

    # Crear línea de cron
    local cron_line="$cron_expr $script_path --keep-days $keep_days >> $log_path 2>&1"

    log_info "═══════════════════════════════════════════════════════════════"
    log_info "  Configuración de Cron Job para Backups PostgreSQL"
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "Expresión cron: $cron_expr"
    log_info "Script: $script_path"
    log_info "Log: $log_path"
    log_info "Retención: $keep_days días"
    log_info "───────────────────────────────────────────────────────────────"

    # Verificar si el script existe
    if [ ! -f "$script_path" ]; then
        log_error "Script de backup no encontrado: $script_path"
        exit 1
    fi

    # Hacer script ejecutable
    chmod +x "$script_path"
    log_success "Script marcado como ejecutable"

    # Crear directorio de logs si no existe
    mkdir -p "$(dirname "$log_path")"
    log_success "Directorio de logs creado"

    # Verificar si ya existe un cron job para este script
    if crontab -l 2>/dev/null | grep -q "$script_path"; then
        log_warning "Ya existe un cron job para este script"
        log_info "Removiendo cron job anterior..."

        # Remover líneas que contengan el script_path
        crontab -l 2>/dev/null | grep -v "$script_path" | crontab - || true
        log_success "Cron job anterior removido"
    fi

    # Agregar nuevo cron job
    (crontab -l 2>/dev/null; echo "$cron_line") | crontab -
    log_success "Cron job instalado exitosamente"

    # Mostrar crontab actual
    log_info ""
    log_info "Crontab actualizado:"
    log_info "───────────────────────────────────────────────────────────────"
    crontab -l | grep "$script_path" || log_warning "No se encontró el cron job"
    log_info "═══════════════════════════════════════════════════════════════"
}

show_schedule_description() {
    local frequency="$1"
    local time="$2"

    case "$frequency" in
        daily)
            log_info "Backups se ejecutarán DIARIAMENTE a las $time"
            ;;
        weekly)
            log_info "Backups se ejecutarán SEMANALMENTE (domingos) a las $time"
            ;;
        monthly)
            log_info "Backups se ejecutarán MENSUALMENTE (día 1) a las $time"
            ;;
    esac
}

test_backup_script() {
    local script_path="$1"

    log_info ""
    log_info "¿Deseas ejecutar un backup de prueba ahora? (y/n)"
    read -r response

    if [[ "$response" =~ ^[Yy]$ ]]; then
        log_info "Ejecutando backup de prueba..."
        bash "$script_path" --keep-days 7
    else
        log_info "Puedes ejecutar un backup manualmente con:"
        log_info "  bash $script_path"
    fi
}

###############################################################################
# MAIN
###############################################################################

# Default values
FREQUENCY="daily"
TIME="02:00"
KEEP_DAYS=7

# Parse arguments
if [ $# -gt 0 ]; then
    if [[ "$1" == "-h" ]] || [[ "$1" == "--help" ]]; then
        show_help
        exit 0
    fi
    FREQUENCY="$1"
fi

if [ $# -gt 1 ]; then
    TIME="$2"
fi

if [ $# -gt 2 ]; then
    KEEP_DAYS="$3"
fi

# Validar frecuencia
if [[ ! "$FREQUENCY" =~ ^(daily|weekly|monthly)$ ]]; then
    log_error "Frecuencia inválida: $FREQUENCY"
    show_help
    exit 1
fi

# Parse time
TIME_PARTS=$(parse_time "$TIME")

# Generate cron expression
CRON_EXPR=$(generate_cron_expression "$FREQUENCY" "$TIME_PARTS")

# Get paths
SCRIPT_PATH=$(get_script_path)
LOG_PATH=$(get_log_path)

# Install cron job
install_cron_job "$CRON_EXPR" "$SCRIPT_PATH" "$LOG_PATH" "$KEEP_DAYS"

# Show schedule
show_schedule_description "$FREQUENCY" "$TIME"

# Test backup
test_backup_script "$SCRIPT_PATH"

log_success ""
log_success "✓ Configuración de cron job completada"
log_info ""
log_info "Comandos útiles:"
log_info "  - Ver cron jobs:       crontab -l"
log_info "  - Editar cron jobs:    crontab -e"
log_info "  - Remover cron jobs:   crontab -r"
log_info "  - Ver logs de backup:  tail -f $LOG_PATH"
log_info ""
