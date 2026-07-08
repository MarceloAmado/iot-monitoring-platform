#!/bin/bash

################################################################################
# Script de Backup Automático de PostgreSQL
#
# Realiza backup diario de la base de datos PostgreSQL y mantiene
# rotación de 7 días.
#
# Uso:
#   bash backup_db.sh [--retention-days 7]
#
# Instalación en Crontab:
#   0 2 * * * /opt/iot-monitoring/backend/scripts/backup_db.sh >> /opt/iot-monitoring/backend/logs/backup.log 2>&1
#
# Autor: Sistema IoT
# Fecha: 2025-11-24
################################################################################

set -e

# Configuración
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_DIR/backend/backups"
LOG_DIR="$PROJECT_DIR/backend/logs"
RETENTION_DAYS=7

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging
log_info() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "[$(date +'%Y-%m-%d %H:%M:%S')] ${YELLOW}[WARN]${NC} $1"
}

# Parsear argumentos
while [[ $# -gt 0 ]]; do
    case $1 in
        --retention-days)
            RETENTION_DAYS="$2"
            shift 2
            ;;
        *)
            log_error "Argumento desconocido: $1"
            exit 1
            ;;
    esac
done

# Crear directorios si no existen
mkdir -p "$BACKUP_DIR"
mkdir -p "$LOG_DIR"

# Timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/iot_backup_$TIMESTAMP.sql.gz"

log_info "======================================"
log_info "Iniciando backup de PostgreSQL"
log_info "======================================"
log_info "Directorio de backups: $BACKUP_DIR"
log_info "Archivo de backup: $(basename $BACKUP_FILE)"
log_info "Retención: $RETENTION_DAYS días"

# Verificar que Docker Compose esté corriendo
cd "$PROJECT_DIR"

if ! docker compose ps postgres | grep -q "running"; then
    log_error "PostgreSQL no está corriendo"
    exit 1
fi

log_info "PostgreSQL está corriendo"

# Obtener credenciales del .env
if [[ ! -f .env ]]; then
    log_error "Archivo .env no encontrado"
    exit 1
fi

source .env

DB_NAME="${DB_NAME:-iot_monitoring}"
DB_USER="${DB_USER:-iot_admin}"

# Hacer backup
log_info "Realizando backup..."

if docker compose exec -T postgres pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    # Verificar que el archivo no esté vacío
    if [[ -s "$BACKUP_FILE" ]]; then
        BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        log_info "Backup completado exitosamente ($BACKUP_SIZE)"
    else
        log_error "El archivo de backup está vacío"
        rm -f "$BACKUP_FILE"
        exit 1
    fi
else
    log_error "Error al realizar backup"
    exit 1
fi

# Rotación de backups (eliminar backups antiguos)
log_info "Aplicando rotación de backups (>$RETENTION_DAYS días)..."

DELETED_COUNT=0
while IFS= read -r old_backup; do
    if [[ -n "$old_backup" ]]; then
        log_info "Eliminando: $(basename $old_backup)"
        rm -f "$old_backup"
        ((DELETED_COUNT++))
    fi
done < <(find "$BACKUP_DIR" -name "iot_backup_*.sql.gz" -mtime +$RETENTION_DAYS)

if [[ $DELETED_COUNT -gt 0 ]]; then
    log_info "Eliminados $DELETED_COUNT backups antiguos"
else
    log_info "No hay backups antiguos para eliminar"
fi

# Resumen
log_info "======================================"
log_info "Backup completado"
log_info "======================================"

TOTAL_BACKUPS=$(find "$BACKUP_DIR" -name "iot_backup_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

log_info "Total de backups: $TOTAL_BACKUPS"
log_info "Espacio usado: $TOTAL_SIZE"
log_info "Último backup: $BACKUP_FILE"

# Opcional: Notificar por email (descomentar si configuras sendmail)
# if command -v mail &> /dev/null; then
#     echo "Backup completado: $BACKUP_FILE ($BACKUP_SIZE)" | mail -s "IoT Backup OK" admin@example.com
# fi

exit 0
