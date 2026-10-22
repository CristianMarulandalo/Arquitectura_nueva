"""
Pruebas del servicio del carrito. No necesitan MySQL ni servidor web: los
repositorios y la transacción se reemplazan por versiones falsas.

Ejecutar desde la raíz del proyecto:
    python -m unittest discover -s tests -t . -v
(o con pytest:  pytest tests)
"""

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.carrito import carrito_service as svc


class TransaccionFalsa:
    """Imita transaccion(): anota si terminó en commit o en rollback."""

    def __init__(self):
        self.resultado = None

    @contextmanager
    def __call__(self):
        try:
            yield object()
            self.resultado = "commit"
        except Exception:
            self.resultado = "rollback"
            raise


def fila(id, producto, cantidad, precio):
    return {
        "id": id,
        "usuario_id": 1,
        "producto_id": id + 100,
        "producto": producto,
        "cantidad": cantidad,
        "precio": precio,
    }


class TestCalculoDelCarrito(unittest.TestCase):
    def test_subtotales_y_total(self):
        filas = [fila(1, "PS5", 2, 100), fila(2, "Xbox", 1, 50)]
        with patch.object(svc.pedidos_repository, "listar_pedidos_usuario", return_value=filas):
            pedidos, total, no_disp = svc.obtener_carrito(1)
        self.assertEqual([p["subtotal"] for p in pedidos], [200, 50])
        self.assertEqual(total, 250)
        self.assertEqual(no_disp, [])

    def test_producto_que_ya_no_existe_no_suma_y_se_avisa(self):
        filas = [fila(1, "PS5", 2, 100), fila(2, "Viejo", 3, None)]
        with patch.object(svc.pedidos_repository, "listar_pedidos_usuario", return_value=filas):
            pedidos, total, no_disp = svc.obtener_carrito(1)
        self.assertEqual(total, 200)
        self.assertEqual(no_disp, ["Viejo"])
        self.assertFalse(pedidos[1]["disponible"])


class TestAgregarYEditar(unittest.TestCase):
    def test_cantidades_invalidas_no_se_guardan(self):
        for mala in ["0", "-1", "abc", "", None, "2.5"]:
            with patch.object(svc.pedidos_repository, "insertar_pedido") as insertar:
                ok, mensaje = svc.agregar_al_carrito(1, "PS5", mala)
            self.assertFalse(ok, f"cantidad {mala!r} debía rechazarse")
            insertar.assert_not_called()

    def test_producto_inexistente_no_se_agrega(self):
        with patch.object(svc.pedidos_repository, "buscar_producto_por_nombre", return_value=None), \
             patch.object(svc.pedidos_repository, "insertar_pedido") as insertar:
            ok, _ = svc.agregar_al_carrito(1, "Fantasma", "1")
        self.assertFalse(ok)
        insertar.assert_not_called()

    def test_agregar_correcto(self):
        with patch.object(svc.pedidos_repository, "buscar_producto_por_nombre", return_value={"id": 1}), \
             patch.object(svc.pedidos_repository, "insertar_pedido") as insertar:
            ok, mensaje = svc.agregar_al_carrito(7, "PS5", "3")
        self.assertTrue(ok)
        insertar.assert_called_once_with(7, "PS5", 3)

    def test_eliminar_pedido_ajeno_falla(self):
        # El repositorio devuelve False cuando el pedido no es del usuario.
        with patch.object(svc.pedidos_repository, "eliminar_pedido", return_value=False) as eliminar:
            ok, _ = svc.eliminar_item(99, usuario_id=1)
        self.assertFalse(ok)
        eliminar.assert_called_once_with(99, 1)

    def test_actualizar_pasa_el_usuario_al_repositorio(self):
        with patch.object(svc.pedidos_repository, "buscar_producto_por_nombre", return_value={"id": 1}), \
             patch.object(svc.pedidos_repository, "actualizar_pedido", return_value=True) as actualizar:
            ok, _ = svc.actualizar_item(5, 1, "PS5", "2")
        self.assertTrue(ok)
        actualizar.assert_called_once_with(5, 1, "PS5", 2)


class TestConfirmarCompra(unittest.TestCase):
    def _parchear(self, filas, tx):
        """Parchea todo lo que toca confirmar_compra y devuelve los mocks."""
        p = {
            "tx": patch.object(svc, "transaccion", tx),
            "bloq": patch.object(svc.pedidos_repository, "bloquear_carrito"),
            "leer": patch.object(svc.pedidos_repository, "leer_carrito", return_value=filas),
            "borrar": patch.object(svc.pedidos_repository, "borrar_carrito"),
            "orden": patch.object(svc.ordenes_repository, "insertar_orden", return_value=42),
            "detalle": patch.object(svc.ordenes_repository, "insertar_detalle"),
        }
        return p

    def _correr(self, filas, tx=None, detalle_falla=False):
        tx = tx or TransaccionFalsa()
        p = self._parchear(filas, tx)
        mocks = {k: v.start() for k, v in p.items() if k != "tx"}
        p["tx"].start()
        if detalle_falla:
            mocks["detalle"].side_effect = RuntimeError("fallo simulado en la base de datos")
        try:
            resultado = svc.confirmar_compra(1)
        finally:
            for v in p.values():
                v.stop()
        return resultado, mocks, tx

    def test_carrito_vacio_no_crea_orden(self):
        (ok, mensaje, orden_id), m, tx = self._correr([])
        self.assertFalse(ok)
        self.assertIsNone(orden_id)
        m["orden"].assert_not_called()
        m["borrar"].assert_not_called()

    def test_producto_no_disponible_no_completa_la_compra(self):
        filas = [fila(1, "PS5", 1, 100), fila(2, "Viejo", 1, None)]
        (ok, mensaje, orden_id), m, tx = self._correr(filas)
        self.assertFalse(ok)
        self.assertIn("Viejo", mensaje)
        m["orden"].assert_not_called()
        m["borrar"].assert_not_called()

    def test_compra_correcta_registra_orden_detalle_y_vacia_carrito(self):
        filas = [fila(1, "PS5", 2, 100), fila(2, "Xbox", 1, 50)]
        (ok, mensaje, orden_id), m, tx = self._correr(filas)
        self.assertTrue(ok)
        self.assertEqual(orden_id, 42)
        m["orden"].assert_called_once_with(unittest.mock.ANY, 1, 250)
        self.assertEqual(m["detalle"].call_count, 2)
        m["detalle"].assert_any_call(unittest.mock.ANY, 42, 101, "PS5", 2, 100, 200)
        m["detalle"].assert_any_call(unittest.mock.ANY, 42, 102, "Xbox", 1, 50, 50)
        m["borrar"].assert_called_once()
        self.assertEqual(tx.resultado, "commit")

    def test_si_algo_falla_se_revierte_y_el_carrito_no_se_borra(self):
        filas = [fila(1, "PS5", 2, 100)]
        (ok, mensaje, orden_id), m, tx = self._correr(filas, detalle_falla=True)
        self.assertFalse(ok)
        self.assertIsNone(orden_id)
        self.assertEqual(tx.resultado, "rollback")
        m["borrar"].assert_not_called()  # el borrado nunca llegó a ejecutarse


if __name__ == "__main__":
    unittest.main()
