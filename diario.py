# -*- coding: utf-8 -*-
"""
diario.py
-----------
Corre todos los días. Busca TODO lo que está en el menú de hoy en
"Menú Semana" (puede ser más de un platillo) y manda un correo con
botones "Sí, lo comí" / "Cambié de plan" para cada uno.
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

MENU_SEMANA_DB = ids["MENU_SEMANA_DB_ID"]

DIAS_ES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]


def dia_de_hoy():
    return DIAS_ES[datetime.now().weekday()]


def buscar_platillos_de_hoy():
    hoy = dia_de_hoy()
    resp = notion.databases.query(
        database_id=MENU_SEMANA_DB,
        filter={"property": "Día", "select": {"equals": hoy}},
    )
    items = []
    for page in resp["results"]:
        titulo = page["properties"]["Nombre"]["title"]
        nombre_completo = titulo[0]["plain_text"] if titulo else "platillo"
        nombre = nombre_completo.split(" - ", 1)[-1]
        items.append({"id": page["id"], "nombre": nombre})
    return items


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
    items = buscar_platillos_de_hoy()
    if not items:
        print(f"No hay nada en el menú para hoy ({dia_de_hoy()}), no se manda correo.")
        return

    bloques = ""
    for item in items:
        link_comido = f"{WEBHOOK_URL}/comido?entry_id={item['id']}&nombre={item['nombre']}"
        link_cambiar = f"{WEBHOOK_URL}/cambiar"
        bloques += f"""
        <div style="margin-bottom:16px;padding-bottom:16px;border-bottom:1px solid #eee;">
            <p style="font-size:16px;margin:0 0 8px;"><b>{item['nombre']}</b></p>
            <a href="{link_comido}" style="display:inline-block;margin-right:8px;padding:10px 18px;
                background:#16a34a;color:white;text-decoration:none;border-radius:6px;">Sí, lo comí</a>
            <a href="{link_cambiar}" style="display:inline-block;padding:10px 18px;
                background:#6b7280;color:white;text-decoration:none;border-radius:6px;">Cambié de plan</a>
        </div>
        """

    html = f"<h2>Hoy toca:</h2>{bloques}"
    enviar_correo(f"¿Qué tal lo de hoy? ({dia_de_hoy()})", html)
    print(f"Correo de confirmación enviado con {len(items)} item(s).")


if __name__ == "__main__":
    main()