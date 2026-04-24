import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class EmailService:
    @staticmethod
    def send_reset_password_email(to_email: str, token: str):
        if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
            logger.error("Configurações de e-mail não preenchidas no .env")
            return False

        subject = "Redefinição de Senha — Cabeleleila Leila"
        reset_link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: auto; background: #ffffff; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
                    <h2 style="color: #6a11cb; text-align: center;">Cabeleleila Leila</h2>
                    <p>Olá,</p>
                    <p>Você solicitou a redefinição de sua senha. Clique no botão abaixo para prosseguir:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%); color: #ffffff; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">Redefinir Minha Senha</a>
                    </div>
                    <p style="color: #666; font-size: 12px;">Se você não solicitou esta alteração, ignore este e-mail.</p>
                    <p style="color: #666; font-size: 12px;">O link expirará em 15 minutos.</p>
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                    <p style="text-align: center; font-size: 12px; color: #999;">&copy; 2024 Cabeleleila Leila — Todos os direitos reservados.</p>
                </div>
            </body>
        </html>
        """

        msg = MIMEMultipart()
        msg["From"] = settings.MAIL_FROM
        msg["To"] = to_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT) as server:
                server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.send_message(msg)
            logger.info(f"E-mail de reset enviado para {to_email}")
            return True
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail para {to_email}: {e}")
            return False
