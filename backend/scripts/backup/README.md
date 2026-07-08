# 🔐 Sistema de Backups Automáticos PostgreSQL

Sistema completo de backups automáticos para la base de datos PostgreSQL del sistema IoT Monitoring.

## 📋 Tabla de Contenidos

- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Uso](#uso)
- [Configuración Avanzada](#configuración-avanzada)
- [Troubleshooting](#troubleshooting)
- [Mejores Prácticas](#mejores-prácticas)

---

## ✨ Características

### Sistema de Backup (`backup_postgres.sh`)

- ✅ **Backup completo** de base de datos PostgreSQL
- ✅ **Compresión gzip** automática (ahorra ~70-80% de espacio)
- ✅ **Rotación automática** de backups antiguos
- ✅ **Validación de integridad** del backup
- ✅ **Logging detallado** con timestamps
- ✅ **Notificaciones por email** (opcional)
- ✅ **Configuración flexible** vía argumentos CLI

### Sistema de Restauración (`restore_postgres.sh`)

- ✅ **Restauración desde backups** comprimidos o sin comprimir
- ✅ **Backup de seguridad** automático antes de restaurar
- ✅ **Verificación de integridad** antes de restaurar
- ✅ **Confirmación interactiva** para prevenir errores
- ✅ **Validación post-restauración**

### Automatización (`setup_cron.sh`)

- ✅ **Configuración automática** de cron jobs
- ✅ **Frecuencias predefinidas**: daily, weekly, monthly
- ✅ **Horarios personalizables**
- ✅ **Detección y reemplazo** de cron jobs existentes

---

## 🔧 Requisitos

### Herramientas necesarias

- Docker y Docker Compose (para acceder al container PostgreSQL)
- Bash shell (Linux, macOS, Git Bash en Windows)
- `gzip` (usualmente pre-instalado)
- `cron` (para backups automáticos - solo Linux/macOS)
- `mail` o `sendmail` (opcional - para notificaciones por email)

### Permisos

- Permisos de escritura en `backend/backups/` y `backend/logs/`
- Acceso al container Docker `iot_postgres`
- Permisos para modificar crontab (para setup automático)

---

## 📥 Instalación

### 1. Hacer scripts ejecutables

```bash
cd backend/scripts/backup
chmod +x backup_postgres.sh
chmod +x restore_postgres.sh
chmod +x setup_cron.sh
```

### 2. Configurar cron job (opcional pero recomendado)

**Opción A: Configuración automática (recomendada)**

```bash
# Backup diario a las 2 AM (default)
./setup_cron.sh

# Backup diario a las 3 AM
./setup_cron.sh daily 03:00

# Backup semanal (domingos) a la 1:30 AM
./setup_cron.sh weekly 01:30

# Backup mensual (día 1) a medianoche
./setup_cron.sh monthly 00:00
```

**Opción B: Configuración manual**

```bash
# Editar crontab
crontab -e

# Agregar línea (ejemplo: diario a las 2 AM)
0 2 * * * /path/to/backend/scripts/backup/backup_postgres.sh --keep-days 7 >> /path/to/backend/logs/postgres_backup.log 2>&1
```

### 3. Verificar instalación

```bash
# Ver cron jobs actuales
crontab -l

# Ejecutar backup de prueba
./backup_postgres.sh
```

---

## 🚀 Uso

### Backup Manual

**Comando básico:**

```bash
./backup_postgres.sh
```

**Con opciones:**

```bash
# Mantener backups por 30 días
./backup_postgres.sh --keep-days 30

# Sin compresión
./backup_postgres.sh --no-compress

# Con notificación por email
./backup_postgres.sh --notify admin@example.com

# Combinado
./backup_postgres.sh --keep-days 30 --notify admin@example.com
```

**Resultado esperado:**

```
[INFO] 2025-12-08 14:30:00 - ═══════════════════════════════════════════
[INFO] 2025-12-08 14:30:00 -   Backup Automático de PostgreSQL
[INFO] 2025-12-08 14:30:00 - ═══════════════════════════════════════════
[OK]   2025-12-08 14:30:00 - Container iot_postgres está corriendo
[OK]   2025-12-08 14:30:00 - Directorios creados
[OK]   2025-12-08 14:30:15 - Backup SQL generado (15.2MB)
[OK]   2025-12-08 14:30:18 - Backup comprimido (3.1MB)
[OK]   2025-12-08 14:30:18 - Integridad de gzip verificada
[OK]   2025-12-08 14:30:18 - ✓ Backup completado exitosamente
[INFO] 2025-12-08 14:30:18 - Total: 5 backups (12.8MB)
[OK]   2025-12-08 14:30:18 - ✓ Proceso de backup completado exitosamente
```

**Archivos generados:**

- `backend/backups/postgres_iot_monitoring_20251208_143000.sql.gz`
- `backend/logs/postgres_backup.log` (si se usa redirección)

---

### Restauración desde Backup

**⚠️ ADVERTENCIA:** La restauración SOBRESCRIBE la base de datos existente.

**Comando básico (interactivo):**

```bash
./restore_postgres.sh ../backups/postgres_iot_monitoring_20251208_143000.sql.gz
```

Se pedirá confirmación:

```
[WARN] ═════════════════════════════════════════════════════════════
[WARN]   ADVERTENCIA: Esta operación SOBRESCRIBIRÁ la base de datos
[WARN] ═════════════════════════════════════════════════════════════
¿Estás seguro que deseas continuar? (escribir 'yes' para confirmar): yes
```

**Comando sin confirmación (para scripts):**

```bash
./restore_postgres.sh ../backups/postgres_iot_monitoring_20251208_143000.sql.gz --force
```

**Restauración con drop de BD (limpia todo antes):**

```bash
./restore_postgres.sh ../backups/postgres_iot_monitoring_20251208_143000.sql.gz --drop-first
```

**Resultado esperado:**

```
[INFO] ═══════════════════════════════════════════════════════════
[INFO]   Restauración de PostgreSQL - IoT Monitoring System
[INFO] ═══════════════════════════════════════════════════════════
[OK]   Container iot_postgres está corriendo
[OK]   Backup file validado
[OK]   Backup de seguridad creado: /tmp/postgres_safety_backup_20251208_143500.sql.gz
[OK]   Restauración completada desde backup comprimido
[OK]   Verificación exitosa: 12 tablas restauradas
[INFO] Tablas restauradas:
         alert_history
         alert_rules
         assets
         devices
         ...
[OK]   ✓ Restauración completada exitosamente
```

---

## ⚙️ Configuración Avanzada

### Variables de Entorno

Puedes sobrescribir configuraciones mediante variables de entorno:

```bash
# Cambiar usuario de PostgreSQL
export POSTGRES_USER="otro_usuario"

# Cambiar nombre de BD
export POSTGRES_DB="otra_bd"

# Ejecutar backup
./backup_postgres.sh
```

### Configuración de Notificaciones por Email

#### Opción 1: Usando `mail` command (Linux)

```bash
# Instalar mailutils (Ubuntu/Debian)
sudo apt-get install mailutils

# Configurar SMTP en /etc/postfix/main.cf
# Luego ejecutar:
./backup_postgres.sh --notify admin@example.com
```

#### Opción 2: Integración con SendGrid/MailGun (Producción)

Modificar `send_notification()` en `backup_postgres.sh`:

```bash
send_notification() {
    local status="$1"
    local backup_file="$2"

    if [ -z "$NOTIFY_EMAIL" ]; then
        return 0
    fi

    # Usar API de SendGrid
    curl --request POST \
      --url https://api.sendgrid.com/v3/mail/send \
      --header "Authorization: Bearer $SENDGRID_API_KEY" \
      --header 'Content-Type: application/json' \
      --data '{
        "personalizations": [{
          "to": [{"email": "'"$NOTIFY_EMAIL"'"}]
        }],
        "from": {"email": "backups@iot-monitoring.com"},
        "subject": "[IoT Monitoring] Backup PostgreSQL - '"$status"'",
        "content": [{
          "type": "text/plain",
          "value": "Backup completado.\nStatus: '"$status"'\nBackup: '"$(basename "$backup_file")"'"
        }]
      }'
}
```

### Integración con Monitoreo Externo

#### Health Check Endpoint

Crear script que verifique último backup:

```bash
#!/bin/bash
# check_last_backup.sh

BACKUP_DIR="/path/to/backups"
MAX_AGE_HOURS=26  # 26 horas (para backups diarios)

LAST_BACKUP=$(find "$BACKUP_DIR" -name "postgres_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)
LAST_BACKUP_AGE=$(( ($(date +%s) - $(stat -c %Y "$LAST_BACKUP")) / 3600 ))

if [ $LAST_BACKUP_AGE -gt $MAX_AGE_HOURS ]; then
    echo "CRITICAL: Último backup hace ${LAST_BACKUP_AGE}h (umbral: ${MAX_AGE_HOURS}h)"
    exit 2
else
    echo "OK: Último backup hace ${LAST_BACKUP_AGE}h"
    exit 0
fi
```

Integrar con Nagios/Zabbix/Prometheus.

---

## 🐛 Troubleshooting

### Problema: "Container iot_postgres no está corriendo"

**Causa:** El container de PostgreSQL no está arrancado.

**Solución:**

```bash
# Verificar estado de containers
docker-compose ps

# Iniciar container si está detenido
docker-compose up -d postgres
```

---

### Problema: "Backup generado está vacío"

**Causa:** Error de permisos o BD corrupta.

**Solución:**

```bash
# Verificar que puedes conectarte manualmente
docker exec -it iot_postgres psql -U iot_admin -d iot_monitoring

# Verificar tablas
\dt

# Si no hay tablas, restaurar desde backup previo
```

---

### Problema: "gzip: command not found"

**Causa:** `gzip` no está instalado.

**Solución:**

```bash
# Ubuntu/Debian
sudo apt-get install gzip

# Windows (Git Bash)
# gzip viene pre-instalado con Git for Windows

# Alternativa: usar backups sin comprimir
./backup_postgres.sh --no-compress
```

---

### Problema: "Permission denied" al ejecutar scripts

**Causa:** Scripts no tienen permisos de ejecución.

**Solución:**

```bash
chmod +x backup_postgres.sh
chmod +x restore_postgres.sh
chmod +x setup_cron.sh
```

---

### Problema: Cron job no se ejecuta automáticamente

**Causa:** Múltiples posibles causas.

**Solución:**

```bash
# 1. Verificar que cron está corriendo
sudo service cron status

# 2. Verificar logs de cron
grep CRON /var/log/syslog

# 3. Verificar que el script tiene permisos de ejecución
ls -l /path/to/backup_postgres.sh

# 4. Ejecutar script manualmente para ver errores
bash /path/to/backup_postgres.sh

# 5. Verificar variables de entorno en cron
# Agregar al inicio del script:
# export PATH=/usr/local/bin:/usr/bin:/bin
```

---

### Problema: Backup falla con "out of disk space"

**Causa:** No hay suficiente espacio en disco.

**Solución:**

```bash
# Verificar espacio disponible
df -h

# Reducir retención de backups
./backup_postgres.sh --keep-days 3

# Limpiar backups antiguos manualmente
rm backend/backups/postgres_*_202312*.sql.gz

# Mover backups a otro disco
mv backend/backups/* /mnt/external_drive/backups/
```

---

## 🎯 Mejores Prácticas

### Estrategia de Retención Recomendada

**Desarrollo/Testing:**

- Frecuencia: Diaria
- Retención: 7 días
- Compresión: Sí

```bash
./setup_cron.sh daily 02:00
```

**Producción:**

- Backups diarios: 30 días de retención
- Backups semanales: 90 días
- Backups mensuales: 1 año
- Compresión: Sí
- Notificaciones: Sí

**Configuración multi-tier:**

```bash
# Backup diario (mantener 30 días)
0 2 * * * /path/to/backup_postgres.sh --keep-days 30 >> /var/log/postgres_backup_daily.log 2>&1

# Backup semanal (domingos, mantener 90 días)
0 3 * * 0 /path/to/backup_postgres.sh --keep-days 90 >> /var/log/postgres_backup_weekly.log 2>&1

# Backup mensual (día 1, mantener 365 días)
0 4 1 * * /path/to/backup_postgres.sh --keep-days 365 >> /var/log/postgres_backup_monthly.log 2>&1
```

### Verificación de Backups

**Automatizar tests de restauración:**

Crear script `test_restore.sh`:

```bash
#!/bin/bash

# Obtener último backup
LAST_BACKUP=$(find backend/backups -name "postgres_*.sql.gz" -type f -printf '%T@ %p\n' | sort -n | tail -1 | cut -d' ' -f2-)

echo "Testing restore de: $LAST_BACKUP"

# Restaurar en BD de testing
export POSTGRES_DB="iot_monitoring_test"
./restore_postgres.sh "$LAST_BACKUP" --force --drop-first

# Verificar integridad
docker exec iot_postgres psql -U iot_admin -d iot_monitoring_test -c "SELECT COUNT(*) FROM devices;"

echo "✓ Test de restauración exitoso"
```

Ejecutar mensualmente en cron.

### Almacenamiento Externo

**Sincronizar con S3/Cloud Storage:**

```bash
#!/bin/bash
# sync_to_s3.sh

BACKUP_DIR="backend/backups"
S3_BUCKET="s3://my-iot-backups/postgres/"

# Sincronizar a S3 (requiere AWS CLI configurado)
aws s3 sync "$BACKUP_DIR" "$S3_BUCKET" --storage-class GLACIER

echo "✓ Backups sincronizados a S3"
```

Agregar a cron después del backup:

```bash
5 2 * * * /path/to/backup_postgres.sh && /path/to/sync_to_s3.sh
```

### Encriptación de Backups

**Encriptar backups sensibles:**

```bash
#!/bin/bash
# encrypt_backup.sh

BACKUP_FILE="$1"
ENCRYPTED_FILE="${BACKUP_FILE}.gpg"

# Encriptar con GPG (requiere clave configurada)
gpg --encrypt --recipient admin@iot-monitoring.com "$BACKUP_FILE"

# Eliminar backup sin encriptar
rm "$BACKUP_FILE"

echo "✓ Backup encriptado: $ENCRYPTED_FILE"
```

Modificar `backup_postgres.sh` para encriptar automáticamente.

---

## 📚 Referencias

- [PostgreSQL Backup Documentation](https://www.postgresql.org/docs/current/backup.html)
- [Cron Format Guide](https://crontab.guru/)
- [GPG Encryption Guide](https://gnupg.org/gph/en/manual.html)

---

## 📝 Changelog

### v1.0.0 (2025-12-08)

- ✅ Script de backup completo con compresión y rotación
- ✅ Script de restauración con validación
- ✅ Setup automático de cron jobs
- ✅ Documentación completa
- ✅ Logging detallado
- ✅ Validación de integridad

---

**Mantenido por:** IoT Monitoring System Team
**Última actualización:** 2025-12-08
