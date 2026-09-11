# -*- coding: utf-8 -*-
"""
webhook_app.py
----------------
Servidor pequeño (Flask), el ÚNICO componente que necesita estar
"vivo" 24/7 (a diferencia de los scripts, que son cron jobs).

Ahora usa la tabla puente "Menú Semana" en vez de escribir directo en
Platillos — así puedes elegir varios platillos el mismo día, y repetir
el mismo platillo en varios días.

Rutas:
    GET  /menu          -> página con selección múltiple (Lunes-Viernes)
    POST /guardar-menu  -> guarda lo elegido en Menú Semana
    GET  /comido         -> marca una entrada del menú como "ya la comí"
    GET  /cambiar        -> redirige a /menu

Despliegue en Render:
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
MENU_SEMANA_DB = ids["MENU_SEMANA_DB_ID"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]


def obtener_platillos():
    resp = notion.databases.query(database_id=PLATILLOS_DB)
    platillos = []
    for page in resp["results"]:
        titulo = page["properties"]["Nombre"]["title"]
        nombre = titulo[0]["plain_text"] if titulo else None
        if nombre:
            platillos.append({"id": page["id"], "nombre": nombre})
    return platillos


def obtener_menu_actual():
    """Regresa {dia: {platillo_id, platillo_id, ...}} con lo ya elegido."""
    resp = notion.databases.query(database_id=MENU_SEMANA_DB)
    menu = {}
    for page in resp["results"]:
        dia_prop = page["properties"]["Día"]["select"]
        if not dia_prop:
            continue
        dia = dia_prop["name"]
        rel = page["properties"]["Platillo"]["relation"]
        if rel:
            menu.setdefault(dia, set()).add(rel[0]["id"])
    return menu


def limpiar_dia(dia):
    """Archiva (borra) todas las entradas actuales de ese día."""
    resp = notion.databases.query(
        database_id=MENU_SEMANA_DB,
        filter={"property": "Día", "select": {"equals": dia}},
    )
    for page in resp["results"]:
        notion.pages.update(page_id=page["id"], archived=True)


def guardar_dia(dia, platillo_ids, nombres_por_id):
    for pid in platillo_ids:
        nombre = nombres_por_id.get(pid, "")
        notion.pages.create(
            parent={"database_id": MENU_SEMANA_DB},
            properties={
                "Nombre": {"title": [{"text": {"content": f"{dia} - {nombre}"}}]},
                "Día": {"select": {"name": dia}},
                "Platillo": {"relation": [{"id": pid}]},
                "Comido": {"checkbox": False},
            },
        )


@app.route("/menu")
def pagina_menu():
    platillos = obtener_platillos()
    menu_actual = obtener_menu_actual()

    filas = ""
    for dia in DIAS:
        seleccionados = menu_actual.get(dia, set())
        opciones_html = "".join(
            f'<option value="{p["id"]}" {"selected" if p["id"] in seleccionados else ""}>{p["nombre"]}</option>'
            for p in platillos
        )
        filas += f"""
        <label style="display:block;margin:20px 0 4px;font-weight:600;">{dia}</label>
        <select name="{dia}" multiple size="5" style="width:100%;padding:8px;font-size:16px;">
            {opciones_html}
        </select>
        <div style="font-size:12px;color:#666;margin-top:2px;">
            Mantén Ctrl (o Cmd) para elegir varios, o ninguno si ese día no aplica.
        </div>
        """

    return f"""
    <html><body style="font-family:sans-serif;max-width:480px;margin:40px auto;padding:0 16px;">
        <h2>🍽️ Menú de la próxima semana</h2>
        <p style="color:#666;font-size:14px;">Puedes elegir más de uno por día (desayuno + cena),
        o repetir el mismo platillo en varios días.</p>
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
    platillos = obtener_platillos()
    nombres_por_id = {p["id"]: p["nombre"] for p in platillos}

    for dia in DIAS:
        seleccionados = request.form.getlist(dia)
        limpiar_dia(dia)
        guardar_dia(dia, seleccionados, nombres_por_id)

    return """
    <html><body style="font-family:sans-serif;text-align:center;padding:60px;">
        <h2>✅ Menú guardado</h2>
        <p>Ya puedes cerrar esta pestaña.</p>
    </body></html>
    """


@app.route("/comido")
def comido():
    entry_id = request.args.get("entry_id")
    nombre = request.args.get("nombre", "el platillo")

    notion.pages.update(
        page_id=entry_id,
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