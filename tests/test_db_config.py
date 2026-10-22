"""
Pruebas de src/db_config.py con un "mysql.connector" falso (sin MySQL):
préstamo seguro de conexiones, espera cuando el pool está lleno y
commit / rollback de las transacciones.
"""

import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

from src import db_config


class PoolError(Exception):
    pass


class ConexionFalsa:
    def __init__(self, pool):
        self.pool = pool
        self.eventos = []

    def cursor(self, **kw):
        return types.SimpleNamespace(close=lambda: self.eventos.append("cursor_close"))

    def start_transaction(self):
        self.eventos.append("start")

    def commit(self):
        self.eventos.append("commit")

    def rollback(self):
        self.eventos.append("rollback")

    def close(self):
        self.eventos.append("close")
        self.pool.libres += 1


class PoolFalso:
    def __init__(self, tamano=1):
        self.libres = tamano
        self.entregadas = []

    def get_connection(self):
        if self.libres == 0:
            raise PoolError("pool agotado")
        self.libres -= 1
        c = ConexionFalsa(self)
        self.entregadas.append(c)
        return c


def mysql_falso():
    errors = types.ModuleType("mysql.connector.errors")
    errors.PoolError = PoolError
    connector = types.ModuleType("mysql.connector")
    connector.errors = errors
    mysql = types.ModuleType("mysql")
    mysql.connector = connector
    return {"mysql": mysql, "mysql.connector": connector, "mysql.connector.errors": errors}


class TestDbConfig(unittest.TestCase):
    def setUp(self):
        self.pool = PoolFalso(tamano=1)
        p1 = patch.dict(sys.modules, mysql_falso())
        p2 = patch.object(db_config, "_pool", self.pool)
        p1.start(); p2.start()
        self.addCleanup(p1.stop); self.addCleanup(p2.stop)

    def test_conexion_siempre_se_devuelve_al_pool_aunque_haya_error(self):
        with self.assertRaises(ValueError):
            with db_config.conexion():
                raise ValueError("falla dentro de la ruta")
        self.assertEqual(self.pool.libres, 1)
        self.assertIn("close", self.pool.entregadas[0].eventos)

    def test_transaccion_confirma_si_todo_sale_bien(self):
        with db_config.transaccion():
            pass
        ev = self.pool.entregadas[0].eventos
        self.assertEqual(ev[:2], ["start", "commit"])
        self.assertNotIn("rollback", ev)
        self.assertEqual(self.pool.libres, 1)

    def test_transaccion_revierte_si_algo_falla(self):
        with self.assertRaises(RuntimeError):
            with db_config.transaccion():
                raise RuntimeError("falla a mitad del pago")
        ev = self.pool.entregadas[0].eventos
        self.assertIn("rollback", ev)
        self.assertNotIn("commit", ev)
        self.assertEqual(self.pool.libres, 1)

    def test_espera_a_que_se_libere_una_conexion(self):
        ocupada = db_config.get_connection()   # el pool (tamaño 1) queda lleno
        threading.Timer(0.1, ocupada.close).start()
        inicio = time.time()
        otra = db_config.get_connection()      # debe esperar, no fallar
        self.assertGreaterEqual(time.time() - inicio, 0.05)
        otra.close()

    def test_si_nunca_se_libera_falla_despues_del_tiempo_limite(self):
        db_config.get_connection()             # pool lleno y nadie lo libera
        with patch.dict("os.environ", {"MYSQL_POOL_TIMEOUT": "0.1"}):
            with self.assertRaises(PoolError):
                db_config.get_connection()


if __name__ == "__main__":
    unittest.main()
