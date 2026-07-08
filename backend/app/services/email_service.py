"""
Servicio de Email para el sistema.

Funcionalidades:
- Envío de emails de recuperación de contraseña
- Envío de emails de bienvenida
- Templates HTML profesionales
- Soporte para SMTP con TLS

Este servicio es específico para emails transaccionales (no alertas).
Para notificaciones de alertas, usar notification_service.py
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from datetime import datetime

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """
    Servicio para envío de emails transaccionales.
    """

    @staticmethod
    def _send_email(
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """
        Envía un email usando la configuración SMTP.

        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_body: Cuerpo HTML del email
            text_body: Cuerpo texto plano (opcional, fallback)

        Returns:
            True si se envió correctamente, False si falló
        """
        # Verificar configuración SMTP
        if not settings.smtp_enabled:
            logger.warning("SMTP está deshabilitado. Email no enviado.")
            logger.info(f"[SIMULADO] Email a {to_email}: {subject}")
            return False

        if not settings.smtp_host or not settings.smtp_user:
            logger.error("Configuración SMTP incompleta (falta host o user)")
            return False

        try:
            # Crear mensaje
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.smtp_from_name or 'IoT Monitoring'} <{settings.smtp_from_email or settings.smtp_user}>"
            msg["To"] = to_email

            # Agregar cuerpo texto plano si existe
            if text_body:
                msg.attach(MIMEText(text_body, "plain"))

            # Agregar cuerpo HTML
            msg.attach(MIMEText(html_body, "html"))

            # Conectar y enviar
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
                server.set_debuglevel(0)  # 0=no debug, 1=debug

                # Iniciar TLS si está habilitado
                if settings.smtp_tls:
                    server.starttls()

                # Login si hay credenciales
                if settings.smtp_password:
                    server.login(settings.smtp_user, settings.smtp_password)

                # Enviar email
                server.send_message(msg)

            logger.info(f"Email enviado exitosamente a {to_email}: {subject}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Error de autenticación SMTP: {str(e)}")
            logger.error("Verificar SMTP_USER y SMTP_PASSWORD en .env")
            return False

        except smtplib.SMTPException as e:
            logger.error(f"Error SMTP al enviar email: {str(e)}", exc_info=True)
            return False

        except Exception as e:
            logger.error(f"Error inesperado al enviar email: {str(e)}", exc_info=True)
            return False

    @staticmethod
    def send_password_reset_email(
        to_email: str,
        user_name: str,
        reset_token: str,
        reset_url: str
    ) -> bool:
        """
        Envía email de recuperación de contraseña.

        Args:
            to_email: Email del usuario
            user_name: Nombre del usuario
            reset_token: Token de recuperación UUID
            reset_url: URL completa para resetear (con token)

        Returns:
            True si se envió correctamente, False si falló
        """
        subject = "Recuperación de Contraseña - Sistema IoT Monitoring"

        # Template HTML profesional
        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Recuperación de Contraseña</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                        🔐 Recuperación de Contraseña
                                    </h1>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Hola <strong>{user_name}</strong>,
                                    </p>
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Recibimos una solicitud para restablecer la contraseña de tu cuenta en el
                                        <strong>Sistema de Monitoreo IoT</strong>.
                                    </p>
                                    <p style="margin: 0 0 30px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Haz clic en el botón de abajo para crear una nueva contraseña:
                                    </p>

                                    <!-- CTA Button -->
                                    <table role="presentation" style="margin: 0 auto;">
                                        <tr>
                                            <td style="background-color: #667eea; border-radius: 6px; text-align: center;">
                                                <a href="{reset_url}" target="_blank" style="display: inline-block; padding: 16px 36px; font-family: Arial, sans-serif; font-size: 16px; color: #ffffff; text-decoration: none; font-weight: 600;">
                                                    Restablecer Contraseña
                                                </a>
                                            </td>
                                        </tr>
                                    </table>

                                    <p style="margin: 30px 0 20px; font-size: 14px; line-height: 1.6; color: #666666;">
                                        O copia y pega este enlace en tu navegador:
                                    </p>
                                    <p style="margin: 0 0 30px; font-size: 12px; line-height: 1.6; color: #667eea; word-break: break-all;">
                                        {reset_url}
                                    </p>

                                    <!-- Security Info -->
                                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 30px 0;">
                                        <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #856404;">
                                            <strong>⚠️ Importante:</strong><br>
                                            • Este enlace expira en <strong>10 minutos</strong><br>
                                            • Si no solicitaste este cambio, ignora este email<br>
                                            • Tu contraseña actual sigue siendo válida
                                        </p>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 10px; font-size: 14px; color: #6c757d;">
                                        Sistema de Monitoreo IoT
                                    </p>
                                    <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                                        Este es un email automático, por favor no respondas.
                                    </p>
                                    <p style="margin: 15px 0 0; font-size: 11px; color: #adb5bd;">
                                        © {datetime.now().year} IoT Monitoring System. Todos los derechos reservados.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        # Template texto plano (fallback)
        text_body = f"""
Recuperación de Contraseña - Sistema IoT Monitoring

Hola {user_name},

Recibimos una solicitud para restablecer la contraseña de tu cuenta.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_url}

IMPORTANTE:
- Este enlace expira en 10 minutos
- Si no solicitaste este cambio, ignora este email
- Tu contraseña actual sigue siendo válida

---
Sistema de Monitoreo IoT
Este es un email automático, por favor no respondas.
        """

        return EmailService._send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    @staticmethod
    def send_welcome_email(
        to_email: str,
        user_name: str,
        temp_password: str
    ) -> bool:
        """
        Envía email de bienvenida con contraseña temporal.

        Args:
            to_email: Email del nuevo usuario
            user_name: Nombre del usuario
            temp_password: Contraseña temporal generada

        Returns:
            True si se envió correctamente, False si falló
        """
        subject = "Bienvenido al Sistema IoT Monitoring"

        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bienvenido</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                        🎉 ¡Bienvenido!
                                    </h1>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Hola <strong>{user_name}</strong>,
                                    </p>
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Tu cuenta en el <strong>Sistema de Monitoreo IoT</strong> ha sido creada exitosamente.
                                    </p>

                                    <!-- Credentials Box -->
                                    <div style="background-color: #f8f9fa; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 30px 0;">
                                        <p style="margin: 0 0 15px; font-size: 14px; color: #666666;">
                                            <strong>Email:</strong>
                                        </p>
                                        <p style="margin: 0 0 20px; font-size: 16px; color: #333333; font-family: monospace;">
                                            {to_email}
                                        </p>
                                        <p style="margin: 0 0 15px; font-size: 14px; color: #666666;">
                                            <strong>Contraseña Temporal:</strong>
                                        </p>
                                        <p style="margin: 0; font-size: 18px; color: #667eea; font-family: monospace; font-weight: 600; letter-spacing: 2px;">
                                            {temp_password}
                                        </p>
                                    </div>

                                    <!-- Security Warning -->
                                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 30px 0;">
                                        <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #856404;">
                                            <strong>🔐 Por seguridad:</strong><br>
                                            • Cambia esta contraseña temporal en tu primer login<br>
                                            • Usa una contraseña fuerte (mínimo 8 caracteres)<br>
                                            • No compartas tus credenciales con nadie
                                        </p>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 10px; font-size: 14px; color: #6c757d;">
                                        Sistema de Monitoreo IoT
                                    </p>
                                    <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                                        Este es un email automático, por favor no respondas.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        text_body = f"""
Bienvenido al Sistema IoT Monitoring

Hola {user_name},

Tu cuenta ha sido creada exitosamente.

CREDENCIALES DE ACCESO:
Email: {to_email}
Contraseña Temporal: {temp_password}

IMPORTANTE:
- Cambia esta contraseña temporal en tu primer login
- Usa una contraseña fuerte (mínimo 8 caracteres)
- No compartas tus credenciales con nadie

---
Sistema de Monitoreo IoT
        """

        return EmailService._send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )

    @staticmethod
    def send_temp_password_email(
        to_email: str,
        user_name: str,
        temp_password: str
    ) -> bool:
        """
        Envía email con contraseña temporal tras un blanqueo por admin.

        Args:
            to_email: Email del usuario
            user_name: Nombre del usuario
            temp_password: Contraseña temporal generada

        Returns:
            True si se envió correctamente, False si falló
        """
        subject = "Contraseña Blanqueada - Sistema IoT Monitoring"

        html_body = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contraseña Blanqueada</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 0;">
                        <table role="presentation" style="width: 600px; border-collapse: collapse; background-color: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                            <!-- Header -->
                            <tr>
                                <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center;">
                                    <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 600;">
                                        🔑 Contraseña Blanqueada
                                    </h1>
                                </td>
                            </tr>

                            <!-- Body -->
                            <tr>
                                <td style="padding: 40px 30px;">
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Hola <strong>{user_name}</strong>,
                                    </p>
                                    <p style="margin: 0 0 20px; font-size: 16px; line-height: 1.6; color: #333333;">
                                        Un administrador blanqueó la contraseña de tu cuenta en el
                                        <strong>Sistema de Monitoreo IoT</strong>. Usá esta contraseña
                                        temporal para ingresar:
                                    </p>

                                    <!-- Credentials Box -->
                                    <div style="background-color: #f8f9fa; border: 2px solid #667eea; border-radius: 8px; padding: 20px; margin: 30px 0;">
                                        <p style="margin: 0 0 15px; font-size: 14px; color: #666666;">
                                            <strong>Contraseña Temporal:</strong>
                                        </p>
                                        <p style="margin: 0; font-size: 18px; color: #667eea; font-family: monospace; font-weight: 600; letter-spacing: 2px;">
                                            {temp_password}
                                        </p>
                                    </div>

                                    <!-- Security Warning -->
                                    <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 30px 0;">
                                        <p style="margin: 0; font-size: 14px; line-height: 1.6; color: #856404;">
                                            <strong>🔐 Por seguridad:</strong><br>
                                            • Cambia esta contraseña temporal apenas ingreses<br>
                                            • Usa una contraseña fuerte (mínimo 8 caracteres)<br>
                                            • Si no solicitaste este cambio, contacta al administrador
                                        </p>
                                    </div>
                                </td>
                            </tr>

                            <!-- Footer -->
                            <tr>
                                <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e9ecef;">
                                    <p style="margin: 0 0 10px; font-size: 14px; color: #6c757d;">
                                        Sistema de Monitoreo IoT
                                    </p>
                                    <p style="margin: 0; font-size: 12px; color: #adb5bd;">
                                        Este es un email automático, por favor no respondas.
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

        text_body = f"""
Contraseña Blanqueada - Sistema IoT Monitoring

Hola {user_name},

Un administrador blanqueó la contraseña de tu cuenta.

Contraseña Temporal: {temp_password}

IMPORTANTE:
- Cambia esta contraseña temporal apenas ingreses
- Usa una contraseña fuerte (mínimo 8 caracteres)
- Si no solicitaste este cambio, contacta al administrador

---
Sistema de Monitoreo IoT
        """

        return EmailService._send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            text_body=text_body
        )


# Función helper para logging cuando SMTP está deshabilitado
def log_email_simulation(to_email: str, subject: str, content: str) -> None:
    """
    Loguea un email simulado cuando SMTP está deshabilitado.

    Útil para desarrollo/testing sin configurar servidor SMTP real.
    """
    logger.info("=" * 80)
    logger.info("[EMAIL SIMULADO - SMTP DESHABILITADO]")
    logger.info(f"Para: {to_email}")
    logger.info(f"Asunto: {subject}")
    logger.info("-" * 80)
    logger.info(content)
    logger.info("=" * 80)
