"""
Pruebas de las rutas del carrito con el cliente de pruebas de Flask. El
servicio se reemplaza por uno falso, así que no hace falta MySQL.
"""

import unittest
from unittest.mock import patch

from src.app import app


class TestRutasCarrito(unittest.TestCase):
    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    def _iniciar_sesion(self, usuario_id=1):
        with self.client.session_transaction() as s:
            s["usuario_id"] = usuario_id
            s["nombre"] = "Prueba"

    def test_pagar_sin_sesion_devuelve_401(self):
        r = self.client.post("/pagar")
        self.assertEqual(r.status_code, 401)
        self.assertFalse(r.get_json()["success"])

    def test_eliminar_y_actualizar_sin_sesion_devuelven_401(self):
        self.assertEqual(self.client.post("/eliminar_pedido/1").status_code, 401)
        r = self.client.post("/actualizar_pedido/1", json={"producto": "x", "cantidad": 1})
        self.assertEqual(r.status_code, 401)

    def test_paginas_del_carrito_sin_sesion_redirigen_al_login(self):
        for ruta in ["/pedido", "/pedidos_lista", "/mis_ordenes"]:
            r = self.client.get(ruta)
            self.assertEqual(r.status_code, 302, ruta)
            self.assertTrue(r.headers["Location"].endswith("/login"), ruta)

    def test_eliminar_usa_el_usuario_de_la_sesion(self):
        self._iniciar_sesion(usuario_id=3)
        with patch("src.carrito.routes.carrito_service.eliminar_item", return_value=(False, "No se encontró")) as f:
            r = self.client.post("/eliminar_pedido/55")
        f.assert_called_once_with(55, 3)
        self.assertFalse(r.get_json()["success"])
        self.assertEqual(r.get_json()["mensaje"], "No se encontró")

    def test_pagar_devuelve_mensaje_y_orden(self):
        self._iniciar_sesion(usuario_id=3)
        with patch("src.carrito.routes.carrito_service.confirmar_compra", return_value=(True, "Pago realizado", 9)):
            r = self.client.post("/pagar")
        self.assertEqual(r.get_json(), {"success": True, "mensaje": "Pago realizado", "orden_id": 9})

    def test_agregar_al_carrito_redirige_a_pedido(self):
        self._iniciar_sesion()
        with patch("src.carrito.routes.carrito_service.agregar_al_carrito", return_value=(True, "Agregado")):
            r = self.client.post("/pedido", data={"producto": "PS5", "cantidad": "2"})
        self.assertEqual(r.status_code, 302)
        self.assertTrue(r.headers["Location"].endswith("/pedido"))

    def test_carrito_muestra_aviso_de_producto_no_disponible(self):
        self._iniciar_sesion()
        pedidos = [{"id": 1, "producto": "Viejo", "cantidad": 1, "precio": None, "subtotal": 0, "disponible": False}]
        with patch("src.carrito.routes.carrito_service.obtener_carrito", return_value=(pedidos, 0, ["Viejo"])):
            r = self.client.get("/pedidos_lista")
        html = r.get_data(as_text=True)
        self.assertEqual(r.status_code, 200)
        self.assertIn("ya no están disponibles", html)
        self.assertIn("disabled", html)  # el botón Pagar queda deshabilitado

    def test_historial_de_ordenes(self):
        self._iniciar_sesion()
        ordenes = [{"id": 4, "total": 100, "fecha": "hoy", "detalle": [
            {"producto": "PS5", "cantidad": 1, "precio": 100, "subtotal": 100}]}]
        with patch("src.carrito.routes.carrito_service.obtener_historial", return_value=ordenes):
            r = self.client.get("/mis_ordenes")
        html = r.get_data(as_text=True)
        self.assertIn("Orden #4", html)
        self.assertIn("PS5", html)


if __name__ == "__main__":
    unittest.main()
