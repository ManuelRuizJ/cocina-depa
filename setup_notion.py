"""
setup_notion.py
----------------
Crea, en la página de Notion que compartiste con tu integración,
las 4 bases de datos del sistema de cocina:

  1. Ingredientes           (catálogo maestro)
  2. Inventario              (stock actual, 1-a-1 con Ingredientes)
  3. Platillos                (recetas)
  4. Recetas x Ingrediente  (tabla puente: qué platillo usa qué
                                ingrediente y en qué cantidad)

Corre este script UNA sola vez. Al final imprime los IDs de las
4 bases — guárdalos, los vas a necesitar en inventory_ops.py.

Uso:
    pip install -r requirements.txt
    cp .env.example .env      # y llena tus valores
    python setup_notion.py
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
PARENT_PAGE_ID = os.environ["NOTION_PARENT_PAGE_ID"]

notion = Client(auth=NOTION_TOKEN)


def crear_ingredientes():
    return notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": "Ingredientes"}}],
        properties={
            "Nombre": {"title": {}},
            "Categoría": {
                "select": {
                    "options": [
                        {"name": "Verdura", "color": "green"},
                        {"name": "Proteína", "color": "red"},
                        {"name": "Lácteo", "color": "blue"},
                        {"name": "Abarrotes", "color": "yellow"},
                        {"name": "Condimento", "color": "orange"},
                    ]
                }
            },
            "Unidad": {
                "select": {
                    "options": [
                        {"name": "piezas", "color": "default"},
                        {"name": "gramos", "color": "default"},
                        {"name": "ml", "color": "default"},
                        {"name": "litros", "color": "default"},
                    ]
                }
            },
        },
    )


def crear_inventario(ingredientes_db_id):
    return notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": "Inventario"}}],
        properties={
            "Nombre": {"title": {}},
            "Ingrediente": {
                "relation": {
                    "database_id": ingredientes_db_id,
                    "type": "single_property",
                    "single_property": {},
                }
            },
            "Cantidad actual": {"number": {"format": "number"}},
            "Cantidad mínima": {"number": {"format": "number"}},
            "Estado": {
                "formula": {
                    "expression": (
                        'if(prop("Cantidad actual") <= prop("Cantidad mínima"), '
                        '"🔴 Comprar", "🟢 Disponible")'
                    )
                }
            },
        },
    )


def crear_platillos():
    return notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": "Platillos"}}],
        properties={
            "Nombre": {"title": {}},
            "Categoría": {
                "select": {
                    "options": [
                        {"name": "Desayuno", "color": "yellow"},
                        {"name": "Comida", "color": "orange"},
                        {"name": "Cena", "color": "purple"},
                        {"name": "Snack", "color": "pink"},
                    ]
                }
            },
            "Tiempo (min)": {"number": {"format": "number"}},
        },
    )


def crear_puente(platillos_db_id, ingredientes_db_id):
    return notion.databases.create(
        parent={"type": "page_id", "page_id": PARENT_PAGE_ID},
        title=[{"type": "text", "text": {"content": "Recetas x Ingrediente"}}],
        properties={
            "Nombre": {"title": {}},
            "Platillo": {
                "relation": {
                    "database_id": platillos_db_id,
                    "type": "single_property",
                    "single_property": {},
                }
            },
            "Ingrediente": {
                "relation": {
                    "database_id": ingredientes_db_id,
                    "type": "single_property",
                    "single_property": {},
                }
            },
            "Cantidad requerida": {"number": {"format": "number"}},
        },
    )


def main():
    print("Creando 'Ingredientes'...")
    db_ingredientes = crear_ingredientes()

    print("Creando 'Inventario'...")
    db_inventario = crear_inventario(db_ingredientes["id"])

    print("Creando 'Platillos'...")
    db_platillos = crear_platillos()

    print("Creando 'Recetas x Ingrediente'...")
    db_puente = crear_puente(db_platillos["id"], db_ingredientes["id"])

    ids = {
        "INGREDIENTES_DB_ID": db_ingredientes["id"],
        "INVENTARIO_DB_ID": db_inventario["id"],
        "PLATILLOS_DB_ID": db_platillos["id"],
        "PUENTE_DB_ID": db_puente["id"],
    }

    print("\n✅ Listo. Guarda estos IDs en tu .env:\n")
    for k, v in ids.items():
        print(f"{k}={v}")

    with open("db_ids.json", "w") as f:
        json.dump(ids, f, indent=2)
    print("\n(también los guardé en db_ids.json)")


if __name__ == "__main__":
    main()