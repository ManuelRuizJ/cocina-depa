# -*- coding: utf-8 -*-
"""
webhook_app.py
----------------
Servidor pequeño (Flask), el ÚNICO componente que necesita estar
"vivo" 24/7 (a diferencia de los scripts, que son cron jobs).

Rutas:
    GET  /menu          -> página con 5 dropdowns (Lunes-Viernes) para armar
                            el menú de la próxima semana
    POST /guardar-menu  -> guarda lo elegido en Notion
    GET  /comido         -> marca un platillo como "ya lo comí hoy"
    GET  /cambiar        -> redirige a /menu para reasignar un día

Despliegue en Render (gratis):
    Build command:  pip install -r requirements.txt
    Start command:  gunicorn webhook_app:app
    Variables de entorno: NOTION_TOKEN
"""

import os
import json
from flask import Flask, request, redirect
from notion_client import Client

app = Flask(__name__)
notion = Client(auth=os.environ["NOTION_TOKEN"])

with open("db_ids.json") as f:
    ids = json.load(f)

PLATILLOS_DB = ids["PLATILLOS_DB_ID"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


def obtener_platillos():
    resp = notion.databases.query(database_id=PLATILLOS_DB)
    platillos = []
    for page in resp["results"]:
        titulo = page["properties"]["Nombre"]["title"]
        nombre = titulo[0]["plain_text"] if titulo else None
        dia_actual = page["properties"]["Día asignado"]["select"]
        dia_actual = dia_actual["name"] if dia_actual else None
        if nombre:
            platillos.append({"id": page["id"], "nombre": nombre, "dia": dia_actual})
    return platillos


def limpiar_asignacion_previa(dia):
    """Si algún platillo ya tenía ese día asignado, se lo quita."""
    resp = notion.databases.query(
        database_id=PLATILLOS_DB,
        filter={"property": "Día asignado", "select": {"equals": dia}},
    )
    for page in resp["results"]:
        notion.pages.update(
            page_id=page["id"],
            properties={"Día asignado": {"select": None}, "Comido": {"checkbox": False}},
        )


@app.route("/menu")
def pagina_menu():
    platillos = obtener_platillos()

    opciones_html = "".join(
        f'<option value="{p["id"]}">{p["nombre"]}</option>' for p in platillos
    )

    filas = ""
    for dia in DIAS:
        seleccionado = next((p["id"] for p in platillos if p["dia"] == dia), "")
        filas += f"""
        <label style="display:block;margin:16px 0 4px;font-weight:600;">{dia}</label>
        <select name="{dia}" style="width:100%;padding:8px;font-size:16px;">
            <option value="">-- Elegir --</option>
            {opciones_html}
        </select>
        <script>
            document.currentScript.previousElementSibling.value = "{seleccionado}";
        </script>
        """

    return f"""
    <html><body style="font-family:sans-serif;max-width:480px;margin:40px auto;padding:0 16px;">
        <h2>🍽️ Menú de la próxima semana</h2>
        <form method="POST" action="/guardar-menu">
            {filas}
            <button type="submit" style="margin-top:24px;padding:12px 24px;
                background:#2563eb;color:white;border:none;border-radius:6px;
                font-size:16px;cursor:pointer;">Guardar menú</button>
        </form>
    </body></html>
    """


@app.route("/guardar-menu", methods=["POST"])
def guardar_menu():
    for dia in DIAS:
        platillo_id = request.form.get(dia)
        if not platillo_id:
            continue
        limpiar_asignacion_previa(dia)
        notion.pages.update(
            page_id=platillo_id,
            properties={"Día asignado": {"select": {"name": dia}}, "Comido": {"checkbox": False}},
        )

    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2>✅ Menú guardado</h2>
        <p>Ya puedes cerrar esta pestaña.</p>
    </body></html>
    """


@app.route("/comido")
def comido():
    platillo_id = request.args.get("platillo_id")
    nombre = request.args.get("nombre", "el platillo")

    notion.pages.update(
        page_id=platillo_id,
        properties={"Comido": {"checkbox": True}},
    )

    return f"""
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2>✅ Anotado</h2>
        <p>Se marcó <b>{nombre}</b> como comido hoy.</p>
    </body></html>
    """


@app.route("/cambiar")
def cambiar():
    return redirect("/menu")


@app.route("/")
def home():
    return "Webhook de Cocina Depa activo ✅"


if __name__ == "__main__":
    app.run(debug=True, port=5000)