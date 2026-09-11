# -*- coding: utf-8 -*-
"""
cargar_datos.py
-----------------
Carga masiva de recetas a Notion: crea Ingredientes, Platillos y conecta
automáticamente la tabla puente (Recetas x Ingrediente). También crea
las filas de Inventario en 0, para que solo tengas que actualizar la
cantidad real después, en vez de armar relaciones a mano.

Es idempotente: si corres el script dos veces, NO duplica nada — busca
por nombre antes de crear.

Uso:
    1. Edita el diccionario RECETAS más abajo con tus platillos reales.
    2. python cargar_datos.py
"""

import os
import json
from notion_client import Client
from dotenv import load_dotenv

load_dotenv()

notion = Client(auth=os.environ["NOTION_TOKEN"])

with open("db_ids.json") as f:
    ids = json.load(f)

INGREDIENTES_DB = ids["INGREDIENTES_DB_ID"]
INVENTARIO_DB = ids["INVENTARIO_DB_ID"]
PLATILLOS_DB = ids["PLATILLOS_DB_ID"]
PUENTE_DB = ids["PUENTE_DB_ID"]


# ============================================================
# 1. EDITA AQUÍ TUS RECETAS
# Formato: "Nombre del platillo": {
#     "categoria": "Desayuno" | "Comida" | "Cena" | "Snack",
#     "tiempo": minutos (int),
#     "ingredientes": [(nombre, cantidad, unidad), ...]
# }
# Unidad debe ser una de: "piezas", "gramos", "ml", "litros"
# ============================================================

RECETAS = {
    "Chilaquiles": {
        "categoria": "Desayuno",
        "tiempo": 20,
        "ingredientes": [
            ("Tortilla", 15, "piezas"),
            ("Huevo", 5, "piezas"),
            ("Jitomate", 4, "piezas"),
            ("Cebolla", 1, "pieza"),
            ("Queso fresco", 120, "gramos"),
        ],
    },
    "Toast": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Pan", 5, "piezas"),
            ("Lechuga", 50, "gramos"),
            ("Frijoles refritos", 220, "gramos"),
            ("Salsa Habanero", 30, "gramos"),
            ("Aguacate", 1, "pieza"),
        ],
    },
    "Comida de mamá": {
        "categoria": "Comida",
        "tiempo": 30,
        "ingredientes": [],
    },
    "Macarrones con codo (saludable)": {
        "categoria": "Comida",
        "tiempo": 25,
        "ingredientes": [
            ("Pasta de macarrones", 250, "gramos"),
            ("Yogur griego", 120, "gramos"),
            ("Queso cottage", 120, "gramos"),
            ("Aguacate", 1, "pieza"),
            ("Cilantro", 25, "gramos"),
            ("Ajo", 2, "diente"),
            ("Cebolla", 70, "gramos"),
            ("Aceite de oliva", 35, "ml"),
        ],
    },
    "Sopa fría": {
        "categoria": "Comida",
        "tiempo": 15,
        "ingredientes": [
            ("Pasta de macarrones", 250, "gramos"),
            ("Crema agria", 70, "gramos"),
            ("Mayonesa", 50, "gramos"),
            ("Jamón", 120, "gramos"),
        ],
    },
    "Pasta fusilli al chipotle": {
        "categoria": "Comida",
        "tiempo": 30,
        "ingredientes": [
            ("Chile chipotle", 40, "gramos"),
            ("Crema agria", 90, "gramos"),
            ("Yogur griego", 90, "gramos"),
            ("Carne molida de res", 350, "gramos"),
            ("Zanahoria", 120, "gramos"),
            ("Papa", 250, "gramos"),
            ("Pimienta negra", 10, "gramos"),
        ],
    },
    "Noche libre": {
        "categoria": "Cena",
        "tiempo": 15,
        "ingredientes": [],
    },
    "Huevo sobre pan": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Huevos", 5, "piezas"),
            ("Aguacate", 1, "pieza"),
            ("Aceite", 20, "ml"),
            ("Queso panela", 90, "gramos"),
            ("Pan", 5, "piezas"),
        ],
    },
    "Hot cakes de avena": {
        "categoria": "Desayuno",
        "tiempo": 15,
        "ingredientes": [
            ("Avena", 140, "gramos"),
            ("Leche", 220, "ml"),
            ("Huevos", 2, "piezas"),
            ("Plátanos", 2, "piezas"),
            ("Mantequilla", 20, "gramos"),
            ("Mermelada", 40, "gramos"),
        ],
    },
    "Ensalada de quinua con pollo": {
        "categoria": "Comida",
        "tiempo": 25,
        "ingredientes": [
            ("Pechuga de pollo", 350, "gramos"),
            ("Quinua", 220, "gramos"),
            ("Lechuga", 70, "gramos"),
            ("Aceite de oliva", 30, "ml"),
            ("Sal", 10, "gramos"),
            ("Pimienta negra", 10, "gramos"),
            ("Ajo en polvo", 10, "gramos"),
        ],
    },
    "Espagueti de mamá": {
        "categoria": "Comida",
        "tiempo": 25,
        "ingredientes": [
            ("Milanesa de pollo", 350, "gramos"),
        ],
    },
    "Milanesa de pollo en plato": {
        "categoria": "Comida",
        "tiempo": 25,
        "ingredientes": [
            ("Milanesa de pollo", 350, "gramos"),
            ("Jitomate", 2, "pieza"),
            ("Aguacate", 1, "pieza"),
            ("Aceite", 30, "ml"),
            ("Lechuga", 70, "gramos"),
            ("Mayonesa", 30, "gramos"),
            ("Pepino", 120, "gramos"),
            ("Frijoles refritos", 180, "gramos"),
        ],
    },
    "Pozole de mamá": {
        "categoria": "Comida",
        "tiempo": 40,
        "ingredientes": [
            ("Tostada", 5, "piezas"),
            ("Limón", 2, "pieza"),
            ("Chile en polvo", 20, "gramos"),
            ("Lechuga", 70, "gramos"),
            ("Rábano", 90, "gramos"),
        ],
    },
    "Arroz con huevo": {
        "categoria": "Desayuno",
        "tiempo": 15,
        "ingredientes": [
            ("Huevos", 5, "piezas"),
            ("Arroz de mamá", 220, "gramos"),
            ("Limón", 1, "piezas"),
            ("Salsa macha", 30, "gramos"),
            ("Salsa habanero", 30, "gramos"),
            ("Tortilla", 5, "piezas"),
        ],
    },
    "Mole de mamá": {
        "categoria": "Comida",
        "tiempo": 20,
        "ingredientes": [
            ("Tortilla", 7, "piezas"),
        ],
    },
    "Sopa de fideo de mamá": {
        "categoria": "Comida",
        "tiempo": 20,
        "ingredientes": [
            ("Tortilla", 5, "piezas"),
        ],
    },
    "Torta de milanesa de pollo": {
        "categoria": "Desayuno",
        "tiempo": 15,
        "ingredientes": [
            ("Torta", 3, "piezas"),
            ("Frijoles refritos", 120, "gramos"),
            ("Aguacate", 1, "pieza"),
            ("Queso Oaxaca", 120, "gramos"),
            ("Jitomate", 2, "pieza"),
            ("Mayonesa", 35, "gramos"),
            ("Chile chipotle", 40, "gramos"),
        ],
    },
    "Avena con fruta": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Avena", 120, "gramos"),
            ("Yogur", 220, "gramos"),
            ("Plátanos", 2, "pieza"),
            ("Fresas", 120, "gramos"),
            ("Kiwi", 2, "pieza"),
            ("Leche", 220, "ml"),
            ("Manzanas", 2, "pieza"),
            ("Nueces", 40, "gramos"),
            ("Chía", 20, "gramos"),
            ("Arándanos", 35, "gramos"),
        ],
    },
    "Torta de jamón": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Torta", 3, "piezas"),
            ("Jamón", 6, "rebanadas"),
            ("Frijoles refritos", 120, "gramos"),
            ("Aguacate", 1, "pieza"),
            ("Queso Oaxaca", 90, "gramos"),
            ("Jitomate", 2, "pieza"),
            ("Mayonesa", 35, "gramos"),
            ("Chile chipotle", 40, "gramos"),
        ],
    },
    "Huevos revueltos con jamón": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Huevos", 5, "piezas"),
            ("Aceite", 20, "ml"),
            ("Jamón", 5, "rebanadas"),
            ("Sal", 7, "gramos"),
            ("Tortilla", 5, "piezas"),
            ("Cebolla", 50, "gramos"),
            ("Frijoles refritos", 140, "gramos"),
        ],
    },
    "Cereal con leche": {
        "categoria": "Desayuno",
        "tiempo": 5,
        "ingredientes": [
            ("Cereal", 120, "gramos"),
            ("Leche", 350, "ml"),
            ("Plátanos", 1, "pieza"),
        ],
    },
    "Wrap de atún": {
        "categoria": "Comida",
        "tiempo": 10,
        "ingredientes": [
            ("Atún en lata", 2, "latas"),
            ("Tortilla de harina", 3, "piezas"),
            ("Lechuga", 70, "gramos"),
            ("Jitomate", 2, "pieza"),
            ("Mayonesa", 35, "gramos"),
        ],
    },
    "Arroz frito económico": {
        "categoria": "Comida",
        "tiempo": 15,
        "ingredientes": [
            ("Arroz cocido", 350, "gramos"),
            ("Huevo", 3, "piezas"),
            ("Verduras congeladas", 120, "gramos"),
            ("Salsa de soya", 35, "ml"),
            ("Aceite", 20, "ml"),
        ],
    },
    "Pasta con atún": {
        "categoria": "Comida",
        "tiempo": 15,
        "ingredientes": [
            ("Pasta", 250, "gramos"),
            ("Atún en lata", 2, "latas"),
            ("Crema agria", 70, "gramos"),
            ("Cebolla", 50, "gramos"),
        ],
    },
    "Quesadillas con frijol": {
        "categoria": "Cena",
        "tiempo": 10,
        "ingredientes": [
            ("Tortilla", 7, "piezas"),
            ("Queso Oaxaca", 140, "gramos"),
            ("Frijoles refritos", 120, "gramos"),
        ],
    },
    "Smoothie verde energético": {
        "categoria": "Desayuno",
        "tiempo": 5,
        "ingredientes": [
            ("Espinaca", 90, "gramos"),
            ("Plátanos", 2, "pieza"),
            ("Leche", 450, "ml"),
            ("Avena", 70, "gramos"),
        ],
    },
    "Tacos de papa con chorizo": {
        "categoria": "Comida",
        "tiempo": 25,
        "ingredientes": [
            ("Papa", 450, "gramos"),
            ("Chorizo", 120, "gramos"),
            ("Tortilla", 9, "piezas"),
            ("Aceite", 35, "ml"),
            ("Lechuga", 70, "gramos"),
            ("Queso fresco", 70, "gramos"),
        ],
    },
    "Sándwich de huevo y aguacate": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Pan", 5, "piezas"),
            ("Huevo", 3, "piezas"),
            ("Aguacate", 1, "pieza"),
            ("Jitomate", 2, "pieza"),
            ("Sal", 5, "gramos"),
        ],
    },
    "Quesadillas de pollo deshebrado": {
        "categoria": "Cena",
        "tiempo": 15,
        "ingredientes": [
            ("Tortilla", 7, "piezas"),
            ("Pechuga de pollo", 250, "gramos"),
            ("Queso Oaxaca", 140, "gramos"),
            ("Cebolla", 50, "gramos"),
        ],
    },
    "Huevos a la mexicana": {
        "categoria": "Desayuno",
        "tiempo": 10,
        "ingredientes": [
            ("Huevo", 5, "piezas"),
            ("Jitomate", 2, "pieza"),
            ("Cebolla", 70, "gramos"),
            ("Chile serrano", 2, "piezas"),
            ("Aceite", 20, "ml"),
            ("Tortilla", 5, "piezas"),
        ],
    },
    "Ensalada rápida de garbanzo": {
        "categoria": "Comida",
        "tiempo": 10,
        "ingredientes": [
            ("Garbanzos en lata", 350, "gramos"),
            ("Jitomate", 2, "pieza"),
            ("Cebolla", 50, "gramos"),
            ("Pepino", 120, "gramos"),
            ("Aceite de oliva", 30, "ml"),
            ("Limón", 2, "pieza"),
        ],
    },
    "Hot cakes de plátano": {
        "categoria": "Desayuno",
        "tiempo": 15,
        "ingredientes": [
            ("Plátanos", 2, "pieza"),
            ("Huevo", 2, "piezas"),
            ("Avena", 120, "gramos"),
            ("Leche", 120, "ml"),
            ("Mantequilla", 20, "gramos"),
        ],
    },
    "Tostadas de frijol con queso": {
        "categoria": "Cena",
        "tiempo": 10,
        "ingredientes": [
            ("Tostada", 7, "piezas"),
            ("Frijoles refritos", 180, "gramos"),
            ("Queso fresco", 90, "gramos"),
            ("Lechuga", 70, "gramos"),
            ("Crema agria", 50, "gramos"),
        ],
    },
}

# ============================================================
# 2. NO NECESITAS TOCAR NADA DE AQUÍ PARA ABAJO
# ============================================================

def _buscar_por_nombre(database_id, nombre, campo_titulo="Nombre"):
    resp = notion.databases.query(
        database_id=database_id,
        filter={"property": campo_titulo, "title": {"equals": nombre}},
    )
    return resp["results"][0] if resp["results"] else None


def get_or_create_ingrediente(nombre, unidad="piezas"):
    existente = _buscar_por_nombre(INGREDIENTES_DB, nombre)
    if existente:
        return existente["id"]

    nuevo = notion.pages.create(
        parent={"database_id": INGREDIENTES_DB},
        properties={
            "Nombre": {"title": [{"text": {"content": nombre}}]},
            "Unidad": {"select": {"name": unidad}},
        },
    )
    print(f"  ✅ Ingrediente creado: {nombre}")
    return nuevo["id"]


def get_or_create_inventario(nombre, ingrediente_id):
    """Crea la fila de inventario en 0 si no existe. No la pisa si ya existe."""
    existente = _buscar_por_nombre(INVENTARIO_DB, nombre)
    if existente:
        return existente["id"]

    nuevo = notion.pages.create(
        parent={"database_id": INVENTARIO_DB},
        properties={
            "Nombre": {"title": [{"text": {"content": nombre}}]},
            "Ingrediente": {"relation": [{"id": ingrediente_id}]},
            "Cantidad actual": {"number": 0},
            "Cantidad mínima": {"number": 1},
        },
    )
    print(f"  📦 Inventario creado en 0: {nombre} (ve a Notion y pon la cantidad real)")
    return nuevo["id"]


def get_or_create_platillo(nombre, categoria, tiempo):
    existente = _buscar_por_nombre(PLATILLOS_DB, nombre)
    if existente:
        return existente["id"]

    nuevo = notion.pages.create(
        parent={"database_id": PLATILLOS_DB},
        properties={
            "Nombre": {"title": [{"text": {"content": nombre}}]},
            "Categoría": {"select": {"name": categoria}},
            "Tiempo (min)": {"number": tiempo},
        },
    )
    print(f"🍽️  Platillo creado: {nombre}")
    return nuevo["id"]


def _existe_relacion_puente(platillo_id, ingrediente_id):
    resp = notion.databases.query(
        database_id=PUENTE_DB,
        filter={
            "and": [
                {"property": "Platillo", "relation": {"contains": platillo_id}},
                {"property": "Ingrediente", "relation": {"contains": ingrediente_id}},
            ]
        },
    )
    return len(resp["results"]) > 0


def conectar_puente(nombre_platillo, platillo_id, ingrediente_id, nombre_ingrediente, cantidad):
    if _existe_relacion_puente(platillo_id, ingrediente_id):
        return  # ya existe, no duplicar

    titulo = f"{nombre_platillo} - {nombre_ingrediente}"
    notion.pages.create(
        parent={"database_id": PUENTE_DB},
        properties={
            "Nombre": {"title": [{"text": {"content": titulo}}]},
            "Platillo": {"relation": [{"id": platillo_id}]},
            "Ingrediente": {"relation": [{"id": ingrediente_id}]},
            "Cantidad requerida": {"number": cantidad},
        },
    )
    print(f"  🔗 Conectado: {titulo} ({cantidad})")


def cargar_todo():
    for nombre_platillo, datos in RECETAS.items():
        print(f"\n=== {nombre_platillo} ===")
        platillo_id = get_or_create_platillo(
            nombre_platillo, datos["categoria"], datos["tiempo"]
        )

        for nombre_ing, cantidad, unidad in datos["ingredientes"]:
            ingrediente_id = get_or_create_ingrediente(nombre_ing, unidad)
            get_or_create_inventario(nombre_ing, ingrediente_id)
            conectar_puente(
                nombre_platillo, platillo_id, ingrediente_id, nombre_ing, cantidad
            )

    print("\n✅ Carga completa. Ve a Notion → Inventario y actualiza las cantidades reales.")


if __name__ == "__main__":
    cargar_todo()