# ============================================================
# Sistema de Monitoreo IoT
# Dockerfile - Backend FastAPI
# ============================================================
# Imagen base: Python 3.11 slim (ligera y segura)
# ============================================================

FROM python:3.11-slim

# ============================================================
# Metadata
# ============================================================
LABEL maintainer="IoT Development Team"
LABEL description="Backend FastAPI para Sistema de Monitoreo IoT"
LABEL version="1.0.0"

# ============================================================
# Variables de Entorno
# ============================================================
# Evitar crear archivos .pyc
ENV PYTHONDONTWRITEBYTECODE=1
# Mostrar logs de Python en tiempo real
ENV PYTHONUNBUFFERED=1
# Directorio de trabajo
ENV APP_HOME=/app

# ============================================================
# Instalación de Dependencias del Sistema
# ============================================================
RUN apt-get update && apt-get install -y \
    # Cliente PostgreSQL (para healthchecks)
    postgresql-client \
    # Build tools (para compilar algunas librerías Python)
    gcc \
    # Limpieza de cache para reducir tamaño de imagen
    && rm -rf /var/lib/apt/lists/*

# ============================================================
# Configuración del Directorio de Trabajo
# ============================================================
WORKDIR $APP_HOME

# ============================================================
# Instalación de Dependencias Python
# ============================================================
# Copiar solo requirements.txt primero (para aprovechar cache de Docker)
COPY requirements.txt .

# Actualizar pip y instalar dependencias
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ============================================================
# Copiar Código de la Aplicación
# ============================================================
# En desarrollo, esto se sobreescribe con volúmenes en docker-compose
COPY ./app $APP_HOME/app
COPY ./alembic $APP_HOME/alembic
COPY ./alembic.ini $APP_HOME/alembic.ini
COPY ./scripts $APP_HOME/scripts
COPY ./tests $APP_HOME/tests

# ============================================================
# Crear Usuario No-Root (Seguridad)
# ============================================================
# En producción es importante no correr como root
RUN addgroup --system appuser && \
    adduser --system --ingroup appuser appuser && \
    chown -R appuser:appuser $APP_HOME

# Cambiar a usuario no-root
USER appuser

# ============================================================
# Exponer Puerto
# ============================================================
EXPOSE 8000

# ============================================================
# Health Check
# ============================================================
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health', timeout=5)"

# ============================================================
# Comando por Defecto
# ============================================================
# Este comando se puede sobreescribir en docker-compose.yml
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
