import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def email_sender(subject: str, body: str, email_receiver: str):
    """
    Envía un correo electrónico usando Gmail.

    Args:
        subject (str): Asunto del correo.
        body (str): Cuerpo del correo.
        email_receiver (str): Dirección de correo del destinatario.

    Raises:
        Exception: Si ocurre un error durante el envío del correo.
    """
    email_sender = os.environ.get("AZTLAN_EMAIL")
    email_password = os.environ.get("AZTLAN_PASS")

    # Crear el mensaje
    message = MIMEMultipart()
    message["From"] = email_sender
    message["To"] = email_receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "plain"))

    # Enviar el correo
    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()  # Iniciar en modo TLS
            server.login(email_sender, email_password)
            server.sendmail(email_sender, email_receiver, message.as_string())
            print(f"Correo enviado exitosamente a {email_receiver}.")
    except Exception as e:
        print(f"Error al enviar el correo: {e}")
        raise