"""
Pruebas de los repositorios con una conexión falsa (sin MySQL): comprueban
qué SQL se envía. Sobre todo, que borrar/actualizar un pedido SIEMPRE filtre
por usuario_id (corrección del IDOR, Problema 2 del Entregable 1).
"""

import unittest
from contextlib import contextmanager
from unittest.mock import patch

from src.carrito import pedidos_repository as repo, ordenes_repository as ordenes


class CursorFalso:
    def __init__(self, filas=None, rowcount=1):
        self.sql = []
        self.filas = filas or []
        self.rowcount = rowcount
        self.lastrowid = 7

    def execute(self, sql, params=None):
        self.sql.append((" ".join(sql.split()), params))

    def fetchone(self):
        return self.filas[0] if self.filas else None

    def fetchall(self):
        return self.filas

    def close(self):
        pass


class ConexionFalsa:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0

    def cursor(self, **kw):
        return self._cursor

    def commit(self):
        self.commits += 1


def conexion_falsa(cursor):
    @contextmanager
    def _conexion():
        yield ConexionFalsa(cursor)
    return _conexion


class TestControlDeAcceso(unittest.TestCase):
    def test_eliminar_filtra_por_usuario(self):
        cur = CursorFalso(rowcount=1)
        with patch.object(repo, "conexion", conexion_falsa(cur)):
            self.assertTrue(repo.eliminar_pedido(5, 3))
        sql, params = cur.sql[0]
        self.assertIn("DELETE FROM pedidos", sql)
        self.assertIn("usuario_id=%s", sql)
        self.assertEqual(params, (5, 3))

    def test_eliminar_pedido_de_otro_usuario_no_borra_nada(self):
        cur = CursorFalso(rowcount=0)  # la base no encontró fila con ese id Y ese usuario
        with patch.object(repo, "conexion", conexion_falsa(cur)):
            self.assertFalse(repo.eliminar_pedido(5, 999))

    def test_actualizar_filtra_por_usuario(self):
        cur = CursorFalso(filas=[{"id": 5}])
        with patch.object(repo, "conexion", conexion_falsa(cur)):
            self.assertTrue(repo.actualizar_pedido(5, 3, "PS5", 2))
        sql, params = cur.sql[0]
        self.assertIn("UPDATE pedidos", sql)
        self.assertIn("usuario_id=%s", sql)
        self.assertEqual(params, ("PS5", 2, 5, 3))

    def test_actualizar_pedido_ajeno_devuelve_false(self):
        cur = CursorFalso(filas=[])  # el SELECT de verificación no encuentra nada
        with patch.object(repo, "conexion", conexion_falsa(cur)):
            self.assertFalse(repo.actualizar_pedido(5, 999, "PS5", 2))

    def test_carrito_siempre_se_consulta_por_usuario(self):
        cur = CursorFalso()
        with patch.object(repo, "conexion", conexion_falsa(cur)):
            repo.listar_pedidos_usuario(3)
        sql, params = cur.sql[0]
        self.assertIn("WHERE pedidos.usuario_id = %s", sql)
        self.assertEqual(params, (3,))


class TestHistorialDeOrdenes(unittest.TestCase):
    def test_detalle_de_orden_guarda_el_id_del_producto(self):
        cur = CursorFalso()
        with patch.object(ordenes, "conexion", conexion_falsa(cur)):
            ordenes.insertar_detalle(cur, 8, 17, "PS5", 2, 100, 200)
        sql, params = cur.sql[0]
        self.assertIn("INSERT INTO detalle_orden", sql)
        self.assertIn("producto_id", sql)
        self.assertEqual(params, (8, 17, "PS5", 2, 100, 200))

    def test_agrupa_los_productos_por_orden(self):
        filas = [
            {"orden_id": 2, "total": 300, "fecha": "f2", "producto": "A", "cantidad": 1, "precio": 100, "subtotal": 100},
            {"orden_id": 2, "total": 300, "fecha": "f2", "producto": "B", "cantidad": 2, "precio": 100, "subtotal": 200},
            {"orden_id": 1, "total": 50, "fecha": "f1", "producto": "C", "cantidad": 1, "precio": 50, "subtotal": 50},
        ]
        cur = CursorFalso(filas=filas)
        with patch.object(ordenes, "conexion", conexion_falsa(cur)):
            resultado = ordenes.listar_ordenes_usuario(1)
        self.assertEqual([o["id"] for o in resultado], [2, 1])
        self.assertEqual(len(resultado[0]["detalle"]), 2)
        self.assertEqual(resultado[1]["detalle"][0]["producto"], "C")
        self.assertEqual(len(cur.sql), 1)  # una sola consulta, no una por orden


if __name__ == "__main__":
    unittest.main()
