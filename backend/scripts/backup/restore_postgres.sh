#!/bin/bash

###############################################################################
# Script de Restauración de PostgreSQL desde Backup
###############################################################################
#
# Descripción:
#   Script para restaurar base de datos PostgreSQL desde backup.
#   Soporta backups comprimidos (.gz) y sin comprimir (.sql).
#
# Uso:
#   ./restore_postgres.sh <archivo_backup> [opciones]
#
# Opciones:
#   --force          No pedir confirmación
#   --drop-first     Eliminar BD existente antes de restaurar
#
# Ejemplo:
#   ./restore_postgres.sh ../backups/postgres_iot_monitoring_20231215_140530.sql.gz
#   ./restore_postgres.sh ../backups/postgres_iot_monitoring_20231215_140530.sql.gz --drop-first
#
# IMPORTANTE:
#   - Este script SOBRESCRIBE la base de datos existente
#   - Asegúrate de tener un backup reciente antes de ejecutar
#   - El container de PostgreSQL debe estar corriendo
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

# PostgreSQL
POSTGRES_USER="${POSTGRES_USER:-iot_admin}"
POSTGRES_DB="${POSTGRES_DB:-iot_monitoring}"

# Flags
FORCE=false
DROP_FIRST=false

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

validate_backup_file() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        log_error "Archivo de backup no existe: $backup_file"
        exit 1
    fi

    if [ ! -s "$backup_file" ]; then
        log_error "Archivo de backup está vacío: $backup_file"
        exit 1
    fi

    # Verificar integridad si está comprimido
    if [[ "$backup_file" == *.gz ]]; then
        if ! gzip -t "$backup_file" 2>/dev/null; then
            log_error "Backup comprimido está corrupto"
            exit 1
        fi
        log_success "Integridad de backup comprimido verificada"
    fi

    log_success "Backup file validado: $backup_file"
}

confirm_restore() {
    if [ "$FORCE" = true ]; then
        return 0
    fi

    log_warning "═════════════════════════════════════════════════════════════"
    log_warning "  ADVERTENCIA: Esta operación SOBRESCRIBIRÁ la base de datos"
    log_warning "═════════════════════════════════════════════════════════════"
    log_warning "Base de datos: $POSTGRES_DB"
    log_warning "Container: $DOCKER_CONTAINER"
    log_warning "Backup: $1"
    log_warning ""

    read -p "¿Estás seguro que deseas continuar? (escribir 'yes' para confirmar): " confirmation

    if [ "$confirmation" != "yes" ]; then
        log_info "Restauración cancelada por el usuario"
        exit 0
    fi
}

create_backup_before_restore() {
    log_info "Creando backup de seguridad antes de restaurar..."

    local timestamp=$(date +%Y%m%d_%H%M%S)
    local safety_backup="/tmp/postgres_safety_backup_${timestamp}.sql.gz"

    if docker exec -t "$DOCKER_CONTAINER" pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" | gzip > "$safety_backup"; then
        log_success "Backup de seguridad creado: $safety_backup"
        echo "$safety_backup"
    else
        log_warning "No se pudo crear backup de seguridad (la BD puede no existir)"
        echo ""
    fi
}

drop_database() {
    log_warning "Eliminando base de datos existente..."

    # Terminar conexiones activas
    docker exec -t "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "
        SELECT pg_terminate_backend(pg_stat_activity.pid)
        FROM pg_stat_activity
        WHERE pg_stat_activity.datname = '$POSTGRES_DB'
          AND pid <> pg_backend_pid();
    " > /dev/null 2>&1 || true

    # Drop database
    docker exec -t "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "
        DROP DATABASE IF EXISTS $POSTGRES_DB;
    " > /dev/null 2>&1

    # Recrear database
    docker exec -t "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d postgres -c "
        CREATE DATABASE $POSTGRES_DB OWNER $POSTGRES_USER;
    " > /dev/null 2>&1

    log_success "Base de datos recreada"
}

restore_backup() {
    local backup_file="$1"

    log_info "Iniciando restauración desde backup..."

    # Preparar comando según tipo de archivo
    if [[ "$backup_file" == *.gz ]]; then
        log_info "Descomprimiendo y restaurando backup..."
        if gunzip -c "$backup_file" | docker exec -i "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"; then
            log_success "Restauración completada desde backup comprimido"
        else
            log_error "Fallo al restaurar backup comprimido"
            return 1
        fi
    else
        log_info "Restaurando backup sin comprimir..."
        if docker exec -i "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$backup_file"; then
            log_success "Restauración completada desde backup sin comprimir"
        else
            log_error "Fallo al restaurar backup"
            return 1
        fi
    fi
}

verify_restoration() {
    log_info "Verificando restauración..."

    # Contar tablas
    local table_count=$(docker exec -t "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "
        SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';
    " | tr -d ' \r\n')

    if [ "$table_count" -gt 0 ]; then
        log_success "Verificación exitosa: $table_count tablas restauradas"
    else
        log_error "Verificación falló: no se encontraron tablas"
        return 1
    fi

    # Listar tablas principales
    log_info "Tablas restauradas:"
    docker exec -t "$DOCKER_CONTAINER" psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "
        SELECT schemaname, tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        ORDER BY tablename;
    "
}

show_help() {
    cat << EOF
Uso: $0 <archivo_backup> [opciones]

Script de restauración de PostgreSQL desde backup.

Argumentos:
  archivo_backup     Ruta al archivo de backup (.sql o .sql.gz)

Opciones:
  --force            No pedir confirmación
  --drop-first       Eliminar BD existente antes de restaurar
  -h, --help         Mostrar esta ayuda

Ejemplos:
  $0 ../backups/postgres_iot_monitoring_20231215_140530.sql.gz
  $0 ../backups/postgres_iot_monitoring_20231215_140530.sql --drop-first
  $0 ../backups/postgres_iot_monitoring_20231215_140530.sql.gz --force

IMPORTANTE:
  - Este script SOBRESCRIBE la base de datos existente
  - Se recomienda crear un backup antes de restaurar
  - El container de PostgreSQL debe estar corriendo

EOF
}

###############################################################################
# PARSEAR ARGUMENTOS
###############################################################################

if [ $# -eq 0 ]; then
    log_error "Falta argumento: archivo de backup"
    show_help
    exit 1
fi

BACKUP_FILE="$1"
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --force)
            FORCE=true
            shift
            ;;
        --drop-first)
            DROP_FIRST=true
            shift
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
    log_info "  Restauración de PostgreSQL - IoT Monitoring System"
    log_info "═══════════════════════════════════════════════════════════════"
    log_info "Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
    log_info "Container: $DOCKER_CONTAINER"
    log_info "Base de datos: $POSTGRES_DB"
    log_info "Backup file: $BACKUP_FILE"
    log_info "Drop first: $([ "$DROP_FIRST" = true ] && echo "Sí" || echo "No")"
    log_info "───────────────────────────────────────────────────────────────"

    # Paso 1: Verificar container Docker
    check_docker_container

    # Paso 2: Validar archivo de backup
    validate_backup_file "$BACKUP_FILE"

    # Paso 3: Confirmar operación
    confirm_restore "$BACKUP_FILE"

    # Paso 4: Backup de seguridad (opcional)
    if [ "$DROP_FIRST" = false ]; then
        safety_backup=$(create_backup_before_restore)
        if [ -n "$safety_backup" ]; then
            log_info "Si algo sale mal, puedes restaurar desde: $safety_backup"
        fi
    fi

    # Paso 5: Drop database si se solicitó
    if [ "$DROP_FIRST" = true ]; then
        drop_database
    fi

    # Paso 6: Restaurar backup
    restore_backup "$BACKUP_FILE"
    if [ $? -eq 0 ]; then
        log_success "✓ Backup restaurado exitosamente"
    else
        log_error "✗ Restauración falló"
        exit 1
    fi

    # Paso 7: Verificar restauración
    verify_restoration

    log_info "═══════════════════════════════════════════════════════════════"
    log_success "✓ Restauración completada exitosamente"
    log_info "═══════════════════════════════════════════════════════════════"
}

# Ejecutar main
main
