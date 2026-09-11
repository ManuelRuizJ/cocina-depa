# -*- coding: utf-8 -*-
"""
menu_semanal.py
-----------------
Manda un correo el sábado con un link a la página de selección
(/menu en el webhook), donde eliges por dropdown el platillo de
Lunes a Viernes para la semana siguiente. Sábado y domingo no
aplican porque no comen en el depa esos días.
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.environ["WEBHOOK_URL"]


def enviar_correo(asunto, cuerpo_html):
    msg = MIMEText(cuerpo_html, "html")
    msg["Subject"] = asunto
    msg["From"] = os.environ["EMAIL_FROM"]
    msg["To"] = os.environ["EMAIL_TO"]

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.environ["EMAIL_FROM"], os.environ["EMAIL_APP_PASSWORD"])
        server.sendmail(
            os.environ["EMAIL_FROM"],
            os.environ["EMAIL_TO"].split(","),
            msg.as_string(),
        )


def main():
    html = f"""
    <h2>🍽️ Es hora de armar el menú</h2>
    <p>Elige qué van a comer de lunes a viernes la próxima semana:</p>
    <a href="{WEBHOOK_URL}/menu" style="display:inline-block;margin-top:12px;
        padding:12px 24px;background:#2563eb;color:white;text-decoration:none;
        border-radius:6px;font-size:16px;">Armar menú de la semana</a>
    """
    enviar_correo("🍽️ Arma el menú de la próxima semana", html)
    print("Correo enviado.")


if __name__ == "__main__":
    main()