# -*- coding: utf-8 -*-
"""
diario.py
-----------
Corre todos los días. Busca qué platillo está asignado a HOY en Notion
y manda un correo cortito con dos botones: "Sí, lo comí" o "Cambié de
plan". Si no hay nada asignado para hoy (ej. fin de semana), no manda
correo.
"""

import os
import json
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])
WEBHOOK_URL = os.environ["WEBHOOK_URL"]

with open("db_ids.json") as f:
    ids = json.load(f)

PLATILLOS_DB = ids["PLATILLOS_DB_ID"]

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def dia_de_hoy():
    return DIAS_ES[datetime.now().weekday()]


def buscar_platillo_de_hoy():
    hoy = dia_de_hoy()
    resp = notion.databases.query(
        database_id=PLATILLOS_DB,
        filter={"property": "Día asignado", "select": {"equals": hoy}},
    )
    if not resp["results"]:
        return None
    page = resp["results"][0]
    titulo = page["properties"]["Nombre"]["title"]
    nombre = titulo[0]["plain_text"] if titulo else "platillo"
    return {"id": page["id"], "nombre": nombre}


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
    platillo = buscar_platillo_de_hoy()
    if not platillo:
        print(f"No hay nada asignado para hoy ({dia_de_hoy()}), no se manda correo.")
        return

    link_comido = f"{WEBHOOK_URL}/comido?platillo_id={platillo['id']}&nombre={platillo['nombre']}"
    link_cambiar = f"{WEBHOOK_URL}/cambiar"

    html = f"""
    <h2>Hoy toca: {platillo['nombre']}</h2>
    <p>
        <a href="{link_comido}" style="display:inline-block;margin-right:8px;padding:10px 18px;
            background:#16a34a;color:white;text-decoration:none;border-radius:6px;">Sí, lo comí</a>
        <a href="{link_cambiar}" style="display:inline-block;padding:10px 18px;
            background:#6b7280;color:white;text-decoration:none;border-radius:6px;">Cambié de plan</a>
    </p>
    """
    enviar_correo(f"¿Qué tal {platillo['nombre']}?", html)
    print(f"Correo de confirmación enviado para: {platillo['nombre']}")


if __name__ == "__main__":
    main()