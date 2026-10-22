"""
Repositorio de pedidos (el carrito).

Aquí vive el SQL que antes estaba mezclado dentro de las rutas de app.py
(Problema 1 y 3 del Entregable 1). Las rutas y el servicio ya no escriben SQL.
"""

from src.db_config import conexion

# El carrito une cada pedido con su producto para traer el precio.
# LEFT JOIN: si el producto ya no existe, la fila igual aparece (precio NULL)
# y así se puede avisar al usuario en vez de ocultarla.
# El subselect agrupa por nombre para que dos productos con el mismo nombre
# no dupliquen filas (pedidos guarda solo el nombre del producto).
_SQL_CARRITO = """
    SELECT pedidos.id, pedidos.usuario_id, pedidos.producto,
           pedidos.cantidad, pr.producto_id, pr.precio
    FROM pedidos
    LEFT JOIN (
        SELECT MIN(p.id) AS producto_id, p.nombre, p.precio
        FROM productos AS p
        JOIN (
            SELECT nombre, MIN(precio) AS precio
            FROM productos
            GROUP BY nombre
        ) AS minimo
          ON minimo.nombre = p.nombre AND minimo.precio = p.precio
        GROUP BY p.nombre, p.precio
    ) AS pr
           ON pedidos.producto = pr.nombre
    WHERE pedidos.usuario_id = %s
    ORDER BY pedidos.id DESC
"""


def listar_productos():
    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM productos")
        productos = cursor.fetchall()
        cursor.close()
    return productos


def buscar_producto_por_nombre(nombre):
    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, precio FROM productos WHERE nombre=%s LIMIT 1", (nombre,))
        producto = cursor.fetchone()
        cursor.close()
    return producto


def insertar_pedido(usuario_id, producto, cantidad):
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO pedidos (usuario_id, producto, cantidad) VALUES (%s, %s, %s)",
            (usuario_id, producto, cantidad),
        )
        conn.commit()
        cursor.close()


def listar_pedidos_usuario(usuario_id):
    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(_SQL_CARRITO, (usuario_id,))
        pedidos = cursor.fetchall()
        cursor.close()
    return pedidos


def eliminar_pedido(pedido_id, usuario_id):
    """Corrige el IDOR (Problema 2): solo borra si el pedido es del usuario."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM pedidos WHERE id=%s AND usuario_id=%s",
            (pedido_id, usuario_id),
        )
        conn.commit()
        borrado = cursor.rowcount > 0
        cursor.close()
    return borrado


def actualizar_pedido(pedido_id, usuario_id, producto, cantidad):
    """Corrige el IDOR (Problema 2): solo actualiza si el pedido es del usuario."""
    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pedidos SET producto=%s, cantidad=%s WHERE id=%s AND usuario_id=%s",
            (producto, cantidad, pedido_id, usuario_id),
        )
        conn.commit()
        # rowcount cuenta filas CAMBIADAS; si se guardó lo mismo da 0, por eso
        # se confirma que el pedido existe y es del usuario con un SELECT.
        cursor.execute(
            "SELECT id FROM pedidos WHERE id=%s AND usuario_id=%s",
            (pedido_id, usuario_id),
        )
        existe = cursor.fetchone() is not None
        cursor.close()
    return existe


# ---- Pasos del pago (se llaman dentro de una transacción: reciben el cursor) ----

def bloquear_carrito(cur, usuario_id):
    """Bloquea las filas del carrito del usuario hasta terminar el pago,
    para que un doble clic en 'Pagar' no cree dos órdenes."""
    cur.execute("SELECT id FROM pedidos WHERE usuario_id=%s FOR UPDATE", (usuario_id,))
    cur.fetchall()


def leer_carrito(cur, usuario_id):
    cur.execute(_SQL_CARRITO, (usuario_id,))
    return cur.fetchall()


def borrar_carrito(cur, usuario_id):
    cur.execute("DELETE FROM pedidos WHERE usuario_id=%s", (usuario_id,))
