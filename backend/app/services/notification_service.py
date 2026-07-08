"""
Servicio de notificaciones para alertas.

Soporta múltiples canales:
- Email (SMTP)
- Telegram (Bot API)
- Webhook (HTTP POST)

Actualiza el campo notification_sent en AlertHistory con el resultado
de cada intento de notificación.
"""

import logging
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.alert import AlertHistory

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Servicio para enviar notificaciones de alertas por múltiples canales.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio de notificaciones.

        Args:
            db: Sesión de base de datos SQLAlchemy
        """
        self.db = db

    def send_alert_notifications(self, alert: AlertHistory) -> Dict[str, str]:
        """
        Envía notificaciones para un AlertHistory por todos los canales configurados.

        Args:
            alert: AlertHistory que contiene la alerta a notificar

        Returns:
            Dict con resultado de cada canal: {"email": "success", "telegram": "failed", ...}
        """
        if not alert.alert_rule:
            logger.error(f"AlertHistory {alert.id} no tiene alert_rule asociado")
            return {}

        channels = alert.alert_rule.notification_channels
        if not channels:
            logger.warning(f"AlertHistory {alert.id} no tiene canales de notificación configurados")
            return {}

        results: Dict[str, str] = {}

        # Preparar datos del mensaje
        message_data = self._prepare_message_data(alert)

        # Enviar por cada canal
        for channel in channels:
            try:
                if channel == "email":
                    recipients = self._get_recipient_emails(alert)
                    result = self._send_email(message_data, recipients)
                    results["email"] = result

                elif channel == "telegram":
                    result = self._send_telegram(message_data)
                    results["telegram"] = result

                elif channel == "webhook":
                    webhook_url = alert.alert_rule.webhook_url
                    if webhook_url:
                        result = self._send_webhook(webhook_url, message_data)
                        results["webhook"] = result
                    else:
                        results["webhook"] = "failed - no URL configured"
                        logger.warning(f"Webhook channel configured but no URL for alert {alert.id}")

                else:
                    logger.warning(f"Canal de notificación desconocido: {channel}")
                    results[channel] = "failed - unknown channel"

            except Exception as e:
                logger.error(f"Error enviando notificación por {channel}: {str(e)}", exc_info=True)
                results[channel] = f"failed - {str(e)}"

        # Actualizar AlertHistory con resultados
        alert.notification_sent = results
        self.db.commit()

        logger.info(f"Notificaciones enviadas para alert {alert.id}: {results}")
        return results

    def _prepare_message_data(self, alert: AlertHistory) -> Dict[str, Any]:
        """
        Prepara los datos del mensaje a partir de un AlertHistory.

        Args:
            alert: AlertHistory a notificar

        Returns:
            Dict con datos estructurados para el mensaje
        """
        device = alert.device
        rule = alert.alert_rule

        data = {
            "alert_id": alert.id,
            "rule_name": rule.name,
            "device_name": device.name if device else "Unknown",
            "device_eui": device.device_eui if device else "Unknown",
            "message": alert.message,
            "value_observed": alert.value_observed,
            "triggered_at": alert.triggered_at.isoformat(),
            "check_type": rule.check_type,
            "variable_key": rule.variable_key,
        }

        return data

    def _get_recipient_emails(self, alert: AlertHistory) -> List[str]:
        """
        Resuelve los destinatarios del email de alerta.

        Reciben la alerta los usuarios activos (no archivados, no guest) que
        tienen acceso a la location del device: super_admins siempre, y
        service_admins/technicians cuya allowed_location_ids incluye la location.

        Fallback: si nadie matchea, se usa el email del remitente SMTP para
        no perder la notificación.

        Args:
            alert: AlertHistory a notificar

        Returns:
            Lista de emails destinatarios
        """
        from app.models.user import User

        location_id = None
        device = alert.device
        if device is not None and device.asset is not None:
            location_id = device.asset.location_id

        users = (
            self.db.query(User)
            .filter(
                User.is_active.is_(True),
                User.archived.is_(False),
                User.role != "guest",
            )
            .all()
        )

        recipients = []
        for user in users:
            if user.is_super_admin:
                recipients.append(user.email)
            elif (
                location_id is not None
                and user.allowed_location_ids
                and location_id in user.allowed_location_ids
            ):
                recipients.append(user.email)

        if not recipients and settings.smtp_user:
            recipients = [settings.smtp_from_email or settings.smtp_user]

        return recipients

    def _send_email(self, message_data: Dict[str, Any], recipients: List[str]) -> str:
        """
        Envía notificación por email usando SMTP.

        Args:
            message_data: Datos del mensaje preparados
            recipients: Emails destinatarios (de _get_recipient_emails)

        Returns:
            "success" si se envió correctamente, "failed - <reason>" si falló
        """
        # Verificar configuración SMTP
        if not settings.smtp_host or not settings.smtp_user:
            logger.warning("Email notifications not configured (missing SMTP settings)")
            return "skipped - not configured"

        if not recipients:
            logger.warning("Email notification sin destinatarios resueltos")
            return "skipped - no recipients"

        try:
            # Crear mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"⚠️ Alerta: {message_data['rule_name']}"
            msg["From"] = settings.smtp_user
            msg["To"] = ", ".join(recipients)

            # Cuerpo HTML
            html_body = f"""
            <html>
                <body>
                    <h2 style="color: #ff6b6b;">⚠️ Alerta del Sistema de Monitoreo IoT</h2>
                    <p><strong>Regla:</strong> {message_data['rule_name']}</p>
                    <p><strong>Dispositivo:</strong> {message_data['device_name']} ({message_data['device_eui']})</p>
                    <p><strong>Tipo de chequeo:</strong> {message_data['check_type']}</p>
                    <p><strong>Variable:</strong> {message_data['variable_key']}</p>
                    <p><strong>Valor observado:</strong> {message_data['value_observed']}</p>
                    <hr>
                    <p>{message_data['message']}</p>
                    <hr>
                    <p style="color: #666; font-size: 12px;">
                        Disparada: {message_data['triggered_at']}<br>
                        Alert ID: {message_data['alert_id']}
                    </p>
                </body>
            </html>
            """

            # Cuerpo texto plano (fallback)
            text_body = f"""
            ⚠️ Alerta del Sistema de Monitoreo IoT

            Regla: {message_data['rule_name']}
            Dispositivo: {message_data['device_name']} ({message_data['device_eui']})
            Tipo: {message_data['check_type']}
            Variable: {message_data['variable_key']}
            Valor: {message_data['value_observed']}

            {message_data['message']}

            ---
            Disparada: {message_data['triggered_at']}
            Alert ID: {message_data['alert_id']}
            """

            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))

            # Enviar email
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
                if settings.smtp_tls:
                    server.starttls()
                if settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)
                server.send_message(msg)

            logger.info(f"Email sent successfully for alert {message_data['alert_id']}")
            return "success"

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}", exc_info=True)
            return f"failed - {str(e)}"

    def _send_telegram(self, message_data: Dict[str, Any]) -> str:
        """
        Envía notificación por Telegram Bot API.

        Args:
            message_data: Datos del mensaje preparados

        Returns:
            "success" si se envió correctamente, "failed - <reason>" si falló
        """
        # Verificar configuración Telegram
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.warning("Telegram notifications not configured (missing bot token or chat ID)")
            return "skipped - not configured"

        try:
            # Preparar mensaje en formato Markdown
            message_text = f"""
⚠️ *Alerta del Sistema de Monitoreo IoT*

*Regla:* {message_data['rule_name']}
*Dispositivo:* {message_data['device_name']} (`{message_data['device_eui']}`)
*Tipo:* {message_data['check_type']}
*Variable:* `{message_data['variable_key']}`
*Valor:* {message_data['value_observed']}

{message_data['message']}

_Disparada: {message_data['triggered_at']}_
_Alert ID: {message_data['alert_id']}_
            """.strip()

            # Llamar a Telegram API
            url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
            payload = {
                "chat_id": settings.telegram_chat_id,
                "text": message_text,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True,
            }

            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                logger.info(f"Telegram message sent successfully for alert {message_data['alert_id']}")
                return "success"
            else:
                error_msg = result.get("description", "Unknown error")
                logger.error(f"Telegram API returned error: {error_msg}")
                return f"failed - {error_msg}"

        except requests.RequestException as e:
            logger.error(f"Error sending Telegram message: {str(e)}", exc_info=True)
            return f"failed - {str(e)}"

    def _send_webhook(self, webhook_url: str, message_data: Dict[str, Any]) -> str:
        """
        Envía notificación por HTTP POST webhook.

        Args:
            webhook_url: URL del webhook
            message_data: Datos del mensaje preparados

        Returns:
            "success" si se envió correctamente, "failed - <reason>" si falló
        """
        try:
            # Preparar payload JSON
            payload = {
                "alert_id": message_data["alert_id"],
                "rule_name": message_data["rule_name"],
                "device": {
                    "name": message_data["device_name"],
                    "eui": message_data["device_eui"],
                },
                "check_type": message_data["check_type"],
                "variable_key": message_data["variable_key"],
                "value_observed": message_data["value_observed"],
                "message": message_data["message"],
                "triggered_at": message_data["triggered_at"],
                "timestamp": datetime.utcnow().isoformat(),
            }

            # Enviar POST request
            response = requests.post(
                webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            response.raise_for_status()

            logger.info(f"Webhook sent successfully for alert {message_data['alert_id']} to {webhook_url}")
            return "success"

        except requests.RequestException as e:
            logger.error(f"Error sending webhook to {webhook_url}: {str(e)}", exc_info=True)
            return f"failed - {str(e)}"


# ============================================
# Funciones helper para uso en endpoints/jobs
# ============================================

def send_alert_notification(db: Session, alert_id: int) -> Dict[str, str]:
    """
    Envía notificaciones para un alert_id específico (wrapper).

    Args:
        db: Sesión de base de datos
        alert_id: ID del AlertHistory

    Returns:
        Dict con resultado de cada canal
    """
    alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
    if not alert:
        logger.error(f"AlertHistory {alert_id} no encontrado")
        return {}

    service = NotificationService(db)
    return service.send_alert_notifications(alert)


def send_multiple_alert_notifications(db: Session, alert_ids: List[int]) -> Dict[int, Dict[str, str]]:
    """
    Envía notificaciones para múltiples alertas.

    Args:
        db: Sesión de base de datos
        alert_ids: Lista de IDs de AlertHistory

    Returns:
        Dict mapeando alert_id -> resultados de notificación
    """
    service = NotificationService(db)
    results = {}

    for alert_id in alert_ids:
        alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
        if alert:
            results[alert_id] = service.send_alert_notifications(alert)
        else:
            logger.warning(f"AlertHistory {alert_id} no encontrado, saltando")
            results[alert_id] = {"error": "not found"}

    return results
