# -*- coding: utf-8 -*-
"""
crear_menu_semana.py
-----------------------
Crea la base de datos "Menú Semana", que reemplaza el uso de
"Día asignado" dentro de Platillos. Con esta tabla puente sí puedes:
  - poner varios platillos el mismo día (desayuno + cena, etc.)
  - repetir el mismo platillo en varios días (ej. huevo toda la semana)

Corre este script UNA vez. Guarda el nuevo ID en db_ids.json (no borra
los que ya tenías, los conserva y agrega uno nuevo).

Las columnas "Día asignado" y "Comido" que le agregamos antes a Platillos
ya no se usan — las puedes dejar ahí sin problema o borrarlas a mano en
Notion si quieres limpiar.
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])
PARENT_PAGE_ID = os.environ["NOTION_PARENT_PAGE_ID"]

with open("db_ids.json") as f:
    ids = json.load(f)

nueva_db = notion.databases.create(
    parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
    title=[{"type": "text", "text": {"content": "Menú Semana"}}],
    properties={
        "Nombre": {"title": {}},
        "Día": {
            "select": {
                "options": [
                    {"name": "Lunes", "color": "blue"},
                    {"name": "Martes", "color": "green"},
                    {"name": "Miércoles", "color": "yellow"},
                    {"name": "Jueves", "color": "orange"},
                    {"name": "Viernes", "color": "red"},
                ]
            }
        },
        "Platillo": {
            "relation": {
                "database_id": ids["PLATILLOS_DB_ID"],
                "type": "single_property",
                "single_property": {},
            }
        },
        "Comido": {"checkbox": {}},
    },
)

ids["MENU_SEMANA_DB_ID"] = nueva_db["id"]
with open("db_ids.json", "w") as f:
    json.dump(ids, f, indent=2)

print(f"✅ Tabla 'Menú Semana' creada: {nueva_db['id']}")
print("(guardado en db_ids.json)")