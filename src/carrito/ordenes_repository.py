"""
Repositorio de órdenes (nuevo): guarda y consulta el historial de compras.
Resuelve el Problema 4 del Entregable 1 (no existía modelo de Orden).
"""

from src.db_config import conexion


def insertar_orden(cur, usuario_id, total):
    """Se llama dentro de la transacción del pago. Devuelve el id de la orden."""
    cur.execute("INSERT INTO ordenes (usuario_id, total) VALUES (%s, %s)", (usuario_id, total))
    return cur.lastrowid


def insertar_detalle(cur, orden_id, producto_id, producto, cantidad, precio, subtotal):
    cur.execute(
        """
        INSERT INTO detalle_orden
            (orden_id, producto_id, producto, cantidad, precio, subtotal)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (orden_id, producto_id, producto, cantidad, precio, subtotal),
    )


def listar_ordenes_usuario(usuario_id):
    """Historial del usuario con sus productos, en una sola consulta."""
    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT o.id AS orden_id, o.total, o.fecha,
                   d.producto, d.cantidad, d.precio, d.subtotal
            FROM ordenes o
            JOIN detalle_orden d ON d.orden_id = o.id
            WHERE o.usuario_id = %s
            ORDER BY o.fecha DESC, o.id DESC, d.id
            """,
            (usuario_id,),
        )
        filas = cursor.fetchall()
        cursor.close()

    ordenes = []
    por_id = {}
    for f in filas:
        if f["orden_id"] not in por_id:
            por_id[f["orden_id"]] = {"id": f["orden_id"], "total": f["total"], "fecha": f["fecha"], "detalle": []}
            ordenes.append(por_id[f["orden_id"]])
        por_id[f["orden_id"]]["detalle"].append(
            {"producto": f["producto"], "cantidad": f["cantidad"], "precio": f["precio"], "subtotal": f["subtotal"]}
        )
    return ordenes
