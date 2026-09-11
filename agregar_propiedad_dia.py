# -*- coding: utf-8 -*-
"""
agregar_propiedad_dia.py
--------------------------
Migración de una sola vez: agrega la propiedad "Día asignado" a Platillos,
necesaria para que el webhook pueda marcar qué platillo se eligió para
cada día de la semana.

Uso:
    python agregar_propiedad_dia.py
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()
notion = Client(auth=os.environ["NOTION_TOKEN"])

with open("db_ids.json") as f:
    ids = json.load(f)

notion.databases.update(
    database_id=ids["PLATILLOS_DB_ID"],
    properties={
        "Comido": {"checkbox": {}},
        "Día asignado": {
            "select": {
                "options": [
                    {"name": "Lunes", "color": "blue"},
                    {"name": "Martes", "color": "green"},
                    {"name": "Miércoles", "color": "yellow"},
                    {"name": "Jueves", "color": "orange"},
                    {"name": "Viernes", "color": "red"},
                    {"name": "Sábado", "color": "purple"},
                    {"name": "Domingo", "color": "pink"},
                ]
            }
        }
    },
)

print("✅ Propiedades 'Día asignado' y 'Comido' agregadas a Platillos.")