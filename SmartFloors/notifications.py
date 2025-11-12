# SmartFloors/notifications.py
import ssl
import smtplib
from email.message import EmailMessage

def send_email_alert(to_email: str, subject: str, message: str,
                     smtp_host: str, smtp_port: int,
                     user: str, password: str):
    """Envía alerta por correo usando SMTP SSL (sin dependencias externas)."""
    email = EmailMessage()
    email["From"] = user
    email["To"] = to_email
    email["Subject"] = subject
    email.set_content(message)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
        server.login(user, password)
        server.send_message(email)