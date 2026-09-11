# Cocina Depa — Inventario en Notion con Python

## Setup (una sola vez)

1. Sigue los 4 pasos manuales en Notion (integración + página vacía compartida).
2. Instala dependencias:
   ```bash
   pip install -r requirements.txt
   ```
3. Copia `.env.example` a `.env` y llena `NOTION_TOKEN` y `NOTION_PARENT_PAGE_ID`.
4. Corre el script que crea las 4 bases de datos:
   ```bash
   python setup_notion.py
   ```
   Esto genera un archivo `db_ids.json` — no lo borres, `inventory_ops.py` lo necesita.

## Uso diario

Primero, dentro de Notion (a mano, es rápido):
- Llena la tabla **Ingredientes** con lo que normalmente compran.
- Llena **Inventario** relacionando cada fila a su ingrediente, con cantidad actual y mínima.
- Llena **Platillos** con tus recetas.
- Llena **Recetas x Ingrediente**: por cada platillo, una fila por cada ingrediente que lleva, con la cantidad que se necesita.

Después, desde la terminal:

```bash
# Ver qué hay en inventario y qué falta comprar
python inventory_ops.py ver

# Cuando cocinen algo, descuenta automáticamente el inventario
python inventory_ops.py cocinar "Chilaquiles"
```

## Siguiente nivel (opcional)

- **Botón en Notion**: puedes agregar un botón en cada página de Platillos que
  llame a un webhook tuyo (hosteado gratis en Render/Railway) y corra `cocinar()`
  sin necesidad de abrir la terminal — así tu novia también lo puede usar sin
  tocar código.
- **Bot de WhatsApp/Telegram**: mismo `cocinar()` pero disparado por un mensaje
  de texto, para que sea aún más fácil para los dos.

Avísame si quieres que armemos cualquiera de las dos.