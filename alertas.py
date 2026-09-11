# -*- coding: utf-8 -*-
"""
alertas.py
-----------
Revisa el Inventario en Notion y, si hay algo en estado "🔴 Comprar",
envía un correo con la lista. Pensado para correr diario vía GitHub Actions.

Variables de entorno necesarias (van como Secrets en GitHub Actions):
    NOTION_TOKEN
    EMAIL_FROM        - tu correo de Gmail
    EMAIL_APP_PASSWORD - contraseña de aplicación de Gmail (no tu password normal)
    EMAIL_TO           - a quién(es) enviar, separado por comas
"""

import os
import json
import smtplib
from email.mime.text import MIMEText
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])

with open("db_ids.json") as f:
    ids = json.load(f)

INVENTARIO_DB = ids["INVENTARIO_DB_ID"]


def _nombre(page):
    t = page["properties"]["Nombre"]["title"]
    return t[0]["plain_text"] if t else "(sin nombre)"


def obtener_faltantes():
    resp = notion.databases.query(database_id=INVENTARIO_DB)
    faltantes = []
    for page in resp["results"]:
        estado = page["properties"]["Estado"]["formula"]["string"] or ""
        if "Comprar" in estado:
            cantidad = page["properties"]["Cantidad actual"]["number"]
            faltantes.append((_nombre(page), cantidad))
    return faltantes


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
    faltantes = obtener_faltantes()

    if not faltantes:
        print("Todo en orden, no se manda correo.")
        return

    items_html = "".join(
        f"<li>{nombre} (quedan {cantidad})</li>" for nombre, cantidad in faltantes
    )
    cuerpo = f"""
    <h2>🛒 Lista de compra</h2>
    <p>Esto se está acabando en el depa:</p>
    <ul>{items_html}</ul>
    """

    enviar_correo("🛒 Se está acabando algo en el depa", cuerpo)
    print(f"Correo enviado con {len(faltantes)} items faltantes.")


if __name__ == "__main__":
    main()