# Screenshots

Capturas de la interfaz usadas en el README (1440x900, tema claro, datos de demo).

| Archivo | Contenido |
|---|---|
| `dashboard.png` | Dashboard con métricas y lista de dispositivos en tiempo real |
| `device-detail.png` | Detalle de dispositivo con gráficos dinámicos y timeline |
| `firmware-ota.png` | Gestión de versiones de firmware OTA |
| `locations.png` | Gestión de grupos/ubicaciones/activos |
| `alerts.png` | Reglas de alerta + estadísticas |
| `login.png` | Pantalla de login |

## Cómo regenerarlas

1. Stack Docker corriendo (`docker compose up -d`) con datos de demo:
   `docker exec -it iot_backend python scripts/seed.py` + lecturas de ejemplo.
2. Capturar con el navegador a 1440px de ancho (o con Playwright headless
   contra `http://localhost:3000`, login `admin@iot-monitoring.com`/`admin123`).
3. Evitar datos reales en las capturas.
