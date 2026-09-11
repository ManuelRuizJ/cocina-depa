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

## Alertas de inventario, menú semanal y confirmación diaria

### Piezas del sistema

| Archivo | Qué hace | Dónde corre |
|---|---|---|
| `agregar_propiedad_dia.py` | Migración única: agrega "Día asignado" y "Comido" a Platillos | Tu compu, una sola vez |
| `alertas.py` | Revisa inventario, manda correo si algo falta | GitHub Actions, cron diario |
| `menu_semanal.py` | Manda correo con link a la página de selección | GitHub Actions, sábado por la noche |
| `diario.py` | Manda correo preguntando si ya comiste lo planeado | GitHub Actions, cron diario |
| `webhook_app.py` | Página de dropdowns + recibe confirmaciones | Render (servidor 24/7 gratis) |

### Cómo se siente usarlo

- **Sábado en la noche**: te llega un correo con un botón "Armar menú de la
  semana". Le das clic, abre una página con 5 dropdowns (Lunes a Viernes),
  eliges un platillo por día, das "Guardar". Sábado y domingo no aparecen
  porque no comen en el depa esos días.
- **Cada día entre semana**: te llega un correo cortito "Hoy toca: X" con dos
  botones — "Sí, lo comí" o "Cambié de plan" (este último te regresa a la
  página de dropdowns por si al final cocinaron otra cosa).
- **Cuando algo se acaba**: correo aparte con la lista de compra.

### Por qué dropdowns en una página y no en el correo

Los `<select>` y formularios no se renderizan de forma confiable dentro de
un correo (Gmail y otros los bloquean). Por eso el correo solo trae UN link
que abre una página normal — ahí los dropdowns sí funcionan al 100%.

### Setup

1. **Gmail**: activa verificación en 2 pasos y genera una
   ["contraseña de aplicación"](https://myaccount.google.com/apppasswords) —
   NO uses tu contraseña normal de Gmail, Google la bloquea para esto.

2. Corre la migración una vez:
   ```bash
   python agregar_propiedad_dia.py
   ```

3. **Despliega el webhook en Render** (gratis):
   - Sube esta carpeta a un repo de GitHub (puede ser privado).
   - En [render.com](https://render.com) → New → Web Service → conecta el repo.
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn webhook_app:app`
   - Variables de entorno en Render: `NOTION_TOKEN`.
   - Copia la URL que te da Render (algo como `https://cocina-depa-xxxx.onrender.com`).

   ⚠️ Nota: el free tier de Render "duerme" el servicio tras ~15 min sin uso,
   y tarda ~30-50 segundos en despertar cuando llega el primer clic. Para este
   caso de uso no importa — es aceptable esperar ese tiempo al elegir un platillo.

4. **Configura los Secrets en GitHub** (Settings → Secrets and variables → Actions):
   - `NOTION_TOKEN`
   - `EMAIL_FROM` (tu Gmail)
   - `EMAIL_APP_PASSWORD` (la que generaste en el paso 1)
   - `EMAIL_TO` (a quién(es) llega, separados por coma si son varios)
   - `WEBHOOK_URL` (la URL de Render del paso 3)

5. Sube `db_ids.json` al repo también (no contiene información sensible,
   solo son IDs de bases de datos).

6. Los workflows ya están en `.github/workflows/` — corren solos en su horario,
   pero también puedes dispararlos manualmente desde la pestaña "Actions" de
   GitHub con el botón "Run workflow".

### Por qué así y no "responder el correo"

Parsear respuestas de correo en texto libre es frágil (firmas, citas,
formato distinto por cliente de correo). En vez de eso, el correo trae
botones/links que al hacer clic pegan directo al webhook — mismo resultado
(decides desde el correo) pero sin adivinar qué quisiste decir.

## Siguiente nivel (opcional)

- **Botón en Notion**: puedes agregar un botón en cada página de Platillos que
  llame al mismo webhook y corra la lógica de "cocinar" sin abrir la terminal.
- **Bot de WhatsApp/Telegram**: mismo patrón de webhook, pero disparado por un
  mensaje de texto en vez de un link de correo.
- **Menú inteligente**: en vez de sugerir platillos al azar, filtrar solo los
  que sí se pueden cocinar con lo que hay en Inventario ahora mismo.

Avísame si quieres que armemos cualquiera de estas.