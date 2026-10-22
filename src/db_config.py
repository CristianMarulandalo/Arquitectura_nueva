"""
Conexión a MySQL (versión re-arquitectada de db_config.py).

Antes: cada petición abría una conexión nueva y la cerraba al final, sin
try/finally (si algo fallaba, la conexión quedaba abierta) y sin
transacciones explícitas (Problema 3 del Entregable 1).

Ahora:
  - Se crea UN pool de conexiones al primer uso y se reutiliza.
  - conexion()    -> presta una conexión y SIEMPRE la devuelve al pool.
  - transaccion() -> agrupa varios pasos como una sola unidad: si todo sale
                     bien se confirma (commit); si algo falla se revierte
                     (rollback) y no queda nada a medias.
Las variables de entorno son las mismas que ya usaba el proyecto.
"""

import os
import time
from contextlib import contextmanager

# Si existe un archivo .env y python-dotenv está instalado, se leen de ahí
# las variables (MYSQL_HOST, etc.). Si no, se usan las del sistema.
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_pool = None


def _crear_pool():
    from mysql.connector import pooling  # import perezoso: las pruebas no lo necesitan

    return pooling.MySQLConnectionPool(
        pool_name="pool_unimarket",
        pool_size=int(os.getenv("MYSQL_POOL_SIZE", "10")),
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DB"),
        port=int(os.getenv("MYSQL_PORT", "3306")),
        auth_plugin="mysql_native_password",
        autocommit=True,  # cada consulta suelta se confirma sola; las transacciones se abren a mano
    )


def get_connection():
    """Toma una conexión del pool. Si todas están ocupadas espera unos
    segundos (el pool de MySQL, por sí solo, falla de inmediato)."""
    global _pool
    from mysql.connector.errors import PoolError

    if _pool is None:
        _pool = _crear_pool()

    limite = time.time() + float(os.getenv("MYSQL_POOL_TIMEOUT", "5"))
    while True:
        try:
            return _pool.get_connection()
        except PoolError:
            if time.time() >= limite:
                raise
            time.sleep(0.02)


@contextmanager
def conexion():
    """Con 'with conexion() as conn:' la conexión vuelve siempre al pool."""
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def transaccion():
    """Con 'with transaccion() as cur:' todo lo que se haga con el cursor
    se confirma junto, o se revierte junto si ocurre un error."""
    conn = get_connection()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        yield cur
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()
