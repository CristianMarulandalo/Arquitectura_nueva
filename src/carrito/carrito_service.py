"""
Servicio del carrito: las reglas de negocio.

Antes estas reglas (subtotales, total, qué pasa al pagar) estaban dentro de
las rutas de app.py junto con el SQL (Problema 1 del Entregable 1). Aquí no
hay Flask ni SQL: se puede probar sin servidor web ni base de datos.
"""

import logging

from src.carrito import pedidos_repository, ordenes_repository
from src.db_config import transaccion

log = logging.getLogger(__name__)


def _validar_cantidad(cantidad):
    """Devuelve (cantidad_entera, None) o (None, mensaje_de_error)."""
    try:
        n = int(cantidad)
    except (TypeError, ValueError):
        return None, "La cantidad debe ser un número entero."
    if n < 1:
        return None, "La cantidad debe ser al menos 1."
    return n, None


def _calcular(filas):
    """Calcula subtotales y total. Un producto que ya no existe (sin precio)
    se marca como no disponible y no suma al total."""
    total = 0
    for p in filas:
        if p["precio"] is None:
            p["disponible"] = False
            p["subtotal"] = 0
        else:
            p["disponible"] = True
            p["subtotal"] = p["precio"] * p["cantidad"]
            total += p["subtotal"]
    no_disponibles = [p["producto"] for p in filas if not p["disponible"]]
    return filas, total, no_disponibles


def obtener_catalogo():
    return pedidos_repository.listar_productos()


def agregar_al_carrito(usuario_id, producto, cantidad):
    """Devuelve (ok, mensaje)."""
    n, error = _validar_cantidad(cantidad)
    if error:
        return False, error
    if not producto or pedidos_repository.buscar_producto_por_nombre(producto) is None:
        return False, "Ese producto no está disponible."
    pedidos_repository.insertar_pedido(usuario_id, producto, n)
    return True, f"Producto agregado al carrito: {producto} x{n}."


def obtener_carrito(usuario_id):
    """Devuelve (pedidos, total, nombres_de_productos_no_disponibles)."""
    return _calcular(pedidos_repository.listar_pedidos_usuario(usuario_id))


def eliminar_item(pedido_id, usuario_id):
    """Devuelve (ok, mensaje). Solo elimina pedidos del propio usuario."""
    if pedidos_repository.eliminar_pedido(pedido_id, usuario_id):
        return True, "Producto eliminado del carrito."
    return False, "No se encontró ese producto en tu carrito."


def actualizar_item(pedido_id, usuario_id, producto, cantidad):
    """Devuelve (ok, mensaje). Solo actualiza pedidos del propio usuario."""
    n, error = _validar_cantidad(cantidad)
    if error:
        return False, error
    if not producto or pedidos_repository.buscar_producto_por_nombre(producto) is None:
        return False, "Ese producto no está disponible."
    if pedidos_repository.actualizar_pedido(pedido_id, usuario_id, producto, n):
        return True, "Pedido actualizado."
    return False, "No se encontró ese producto en tu carrito."


def confirmar_compra(usuario_id):
    """Checkout con límite transaccional (Problema 4 del Entregable 1):
    leer el carrito, validar, registrar la orden y vaciar el carrito son UN
    solo bloque. Si algo falla, se revierte todo y el carrito queda igual.

    Devuelve (ok, mensaje, orden_id)."""
    try:
        with transaccion() as cur:
            pedidos_repository.bloquear_carrito(cur, usuario_id)
            pedidos, total, no_disponibles = _calcular(pedidos_repository.leer_carrito(cur, usuario_id))

            if not pedidos:
                return False, "Tu carrito está vacío, agrega productos antes de pagar.", None

            if no_disponibles:
                nombres = ", ".join(no_disponibles)
                return False, (f"Estos productos ya no están disponibles: {nombres}. "
                               "Elimínalos de tu carrito para continuar."), None

            orden_id = ordenes_repository.insertar_orden(cur, usuario_id, total)
            for p in pedidos:
                ordenes_repository.insertar_detalle(
                    cur, orden_id, p["producto_id"], p["producto"],
                    p["cantidad"], p["precio"], p["subtotal"]
                )
            pedidos_repository.borrar_carrito(cur, usuario_id)
    except Exception:
        log.exception("Falló el pago del usuario %s", usuario_id)
        return False, "No se pudo completar el pago. Tu carrito no cambió, intenta de nuevo.", None

    return True, f"Pago realizado. Tu orden #{orden_id} por $ {total} quedó registrada.", orden_id


def obtener_historial(usuario_id):
    return ordenes_repository.listar_ordenes_usuario(usuario_id)
