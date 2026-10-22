# Unimarket (tienda_flask) — Re-arquitectura del módulo Carrito de Compras

Unimarket es una tienda en línea sencilla hecha con Flask y MySQL: los usuarios se
registran, publican productos, navegan el catálogo y arman un carrito de compras
("pedido") que pueden editar y pagar. También incluye un asistente llamado LUNA.

**Módulo MVP de la re-arquitectura: Carrito de Compras** (`/pedido`, `/pedidos_lista`,
`/actualizar_pedido/<id>`, `/eliminar_pedido/<id>`, `/pagar` y la nueva `/mis_ordenes`).
El resto de la aplicación (login, registro, catálogo, LUNA) se conserva y es
dependencia del MVP. Atributos de calidad priorizados: **Usabilidad, Eficiencia de
ejecución e Idoneidad funcional**.

## Problemas arquitectónicos identificados (Entregable 1)

| # | Problema | Estado en esta versión |
|---|----------|------------------------|
| 1 | Monolito sin separación de capas (rutas, reglas y SQL mezclados en `app.py`) | Resuelto: rutas → servicio → repositorios (`src/carrito/`) |
| 2 | Control de acceso roto (IDOR) en `/eliminar_pedido` y `/actualizar_pedido` | Resuelto: el SQL filtra por `usuario_id` de la sesión |
| 3 | Sin pool de conexiones, sin `try/finally` ni transacciones | Resuelto: pool + `conexion()` + `transaccion()` en `src/db_config.py` |
| 4 | Checkout sin modelo de órdenes ni límite transaccional | Resuelto: tablas `ordenes`/`detalle_orden` y pago atómico |
| 5 | Código y esquema de BD inconsistentes; clave secreta escrita en el código | Resuelto: `db/schema.sql` completo; clave por variable de entorno |

Detalle de cada decisión: [`docs/adr/`](docs/adr/). Arquitectura completa:
**[`docs/arquitectura.md`](docs/arquitectura.md)**.

## Estructura

```
src/            app.py (entrada, login, catálogo, LUNA) · db_config.py (pool y transacción)
  carrito/      routes.py · carrito_service.py · pedidos_repository.py · ordenes_repository.py
templates/      HTML (Jinja2)          static/   CSS, JavaScript e imágenes
db/             schema.sql (esquema completo) · dump_original_entregable1.sql
docs/           arquitectura.md · diagramas/ (C4, fuentes .mmd y exportados) · adr/ · tareas_semana15.md
tests/          pruebas unitarias (sin MySQL) y prueba de carga del pool
```

## Cómo ejecutarlo

1. Crear y activar un entorno virtual e instalar dependencias:
   ```
   python -m venv venv
   venv\Scripts\activate          # Windows   (Linux/Mac: source venv/bin/activate)
   pip install -r requirements.txt
   ```
2. Crear las tablas en MySQL (si ya tenías la base `tienda_flask`, este script solo
   agrega tablas que falten; `CREATE TABLE IF NOT EXISTS` no modifica tablas existentes):
   ```
   mysql -u root -p < db/schema.sql
   ```
   Si `detalle_orden` ya existía y no tiene la columna `producto_id`, agrégala una
   sola vez con `ALTER TABLE detalle_orden ADD COLUMN producto_id INT DEFAULT NULL;`.
3. Copiar `.env.example` a `.env` y completar los datos de MySQL y `FLASK_SECRET_KEY`.
4. Ejecutar desde la **raíz** del proyecto:
   ```
   python -m src.app
   ```
   Abrir http://127.0.0.1:5000. En producción: `gunicorn src.app:app` (ver `Procfile.txt`).

## Pruebas

```
python -m unittest discover -s tests -t . -v      # no necesitan MySQL
python -m tests.prueba_carga_pool                 # necesita MySQL: 50 usuarios simultáneos
```

## Notas y limitaciones

- "Pagar" no se conecta a una pasarela real: es una limitación funcional del MVP
  (el modal de tarjeta solo valida el formato). Lo arquitectónico que sí se resolvió es
  el modelo de Orden y la transacción que lo registra.
- "Disponible" significa que el producto sigue publicado en `productos`; el esquema
  no tiene inventario (stock), así que no se valida cantidad en existencia.
- `pedidos` guarda el *nombre* del producto (diseño original). Si dos productos
  comparten nombre, el carrito usa el menor precio.
- Los tipos de datos de `productos` en `db/schema.sql` son una suposición: el dump
  original no incluía esa tabla.
