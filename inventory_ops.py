"""
inventory_ops.py
-----------------
Operaciones del día a día una vez que ya corriste setup_notion.py.

Uso:
    python inventory_ops.py ver               # muestra qué falta comprar
    python inventory_ops.py cocinar "Chilaquiles"   # descuenta inventario
"""

import os
import sys
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
notion = Client(auth=NOTION_TOKEN)

with open("db_ids.json") as f:
    ids = json.load(f)

INVENTARIO_DB = ids["INVENTARIO_DB_ID"]
PLATILLOS_DB = ids["PLATILLOS_DB_ID"]
PUENTE_DB = ids["PUENTE_DB_ID"]


def _titulo(page, campo):
    val = page["properties"][campo]
    if val["type"] == "title":
        arr = val["title"]
    else:
        arr = val["rich_text"]
    return arr[0]["plain_text"] if arr else ""


def ver_inventario():
    """Imprime todo el inventario y resalta lo que hay que comprar."""
    resultados = notion.databases.query(database_id=INVENTARIO_DB)["results"]
    faltantes = []

    print("\n📦 INVENTARIO ACTUAL\n" + "-" * 40)
    for page in resultados:
        nombre = _titulo(page, "Nombre")
        cantidad = page["properties"]["Cantidad actual"]["number"]
        estado = page["properties"]["Estado"]["formula"]["string"]
        print(f"{nombre:30s} {cantidad:>6} {estado}")
        if "Comprar" in (estado or ""):
            faltantes.append(nombre)

    if faltantes:
        print("\n🛒 Lista de compra sugerida:")
        for f in faltantes:
            print(f"  - {f}")
    else:
        print("\n✅ No falta nada por ahora.")


def _buscar_platillo(nombre_platillo):
    resp = notion.databases.query(
        database_id=PLATILLOS_DB,
        filter={"property": "Nombre", "title": {"equals": nombre_platillo}},
    )
    if not resp["results"]:
        raise ValueError(f"No encontré el platillo '{nombre_platillo}' en Notion.")
    return resp["results"][0]


def _ingredientes_del_platillo(platillo_id):
    """Regresa [(inventario_page_id, cantidad_requerida, nombre), ...]."""
    resp = notion.databases.query(
        database_id=PUENTE_DB,
        filter={"property": "Platillo", "relation": {"contains": platillo_id}},
    )
    items = []
    for row in resp["results"]:
        cantidad = row["properties"]["Cantidad requerida"]["number"]
        ingrediente_ids = [
            r["id"] for r in row["properties"]["Ingrediente"]["relation"]
        ]
        for ing_id in ingrediente_ids:
            items.append((ing_id, cantidad))
    return items


def _pagina_inventario_por_ingrediente(ingrediente_id):
    resp = notion.databases.query(
        database_id=INVENTARIO_DB,
        filter={"property": "Ingrediente", "relation": {"contains": ingrediente_id}},
    )
    if not resp["results"]:
        return None
    return resp["results"][0]


def cocinar(nombre_platillo):
    """Descuenta del inventario los ingredientes usados por un platillo."""
    platillo = _buscar_platillo(nombre_platillo)
    items = _ingredientes_del_platillo(platillo["id"])

    if not items:
        print(f"'{nombre_platillo}' no tiene ingredientes cargados en la tabla puente.")
        return

    print(f"\n🍳 Cocinando: {nombre_platillo}\n" + "-" * 40)
    for ingrediente_id, cantidad_necesaria in items:
        inv_page = _pagina_inventario_por_ingrediente(ingrediente_id)
        if inv_page is None:
            print(f"  ⚠️  Ingrediente sin registro en Inventario, se ignora.")
            continue

        actual = inv_page["properties"]["Cantidad actual"]["number"] or 0
        nuevo = max(actual - cantidad_necesaria, 0)

        notion.pages.update(
            page_id=inv_page["id"],
            properties={"Cantidad actual": {"number": nuevo}},
        )
        nombre_inv = _titulo(inv_page, "Nombre")
        print(f"  {nombre_inv:25s} {actual} → {nuevo}")

    print("\n✅ Inventario actualizado.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    comando = sys.argv[1]

    if comando == "ver":
        ver_inventario()
    elif comando == "cocinar":
        if len(sys.argv) < 3:
            print('Uso: python inventory_ops.py cocinar "Nombre del platillo"')
            sys.exit(1)
        cocinar(sys.argv[2])
    else:
        print(f"Comando desconocido: {comando}")
        print(__doc__)