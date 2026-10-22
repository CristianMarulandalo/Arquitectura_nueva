"""
Prueba de carga del pool de conexiones (escenario de Eficiencia de ejecución
del Entregable 2: 50 usuarios simultáneos, respuesta bajo 500 ms, sin errores
por falta de conexiones).

Necesita MySQL real con el esquema creado y tu .env.
Ejecutar desde la raíz del proyecto:   python -m tests.prueba_carga_pool
Opcional: python -m tests.prueba_carga_pool 100     (otro número de usuarios)

Cada "usuario" pide una conexión al pool y lee el carrito y el catálogo, igual
que lo hace la aplicación. Se mide el tiempo de cada uno.
"""

import sys
import threading
import time

from src.db_config import conexion

LIMITE_MS = 500


def un_usuario(resultados, i):
    inicio = time.perf_counter()
    try:
        with conexion() as conn:
            cur = conn.cursor(dictionary=True)
            cur.execute("SELECT COUNT(*) AS n FROM pedidos")
            cur.fetchall()
            cur.execute("SELECT COUNT(*) AS n FROM productos")
            cur.fetchall()
            cur.close()
        resultados[i] = ((time.perf_counter() - inicio) * 1000, None)
    except Exception as e:
        resultados[i] = ((time.perf_counter() - inicio) * 1000, str(e))


def main(usuarios=50):
    resultados = [None] * usuarios
    hilos = [threading.Thread(target=un_usuario, args=(resultados, i)) for i in range(usuarios)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    tiempos = sorted(r[0] for r in resultados)
    errores = [r[1] for r in resultados if r[1]]
    print(f"Usuarios simultáneos: {usuarios}")
    print(f"Tiempo promedio: {sum(tiempos) / len(tiempos):.1f} ms")
    print(f"Tiempo máximo:   {tiempos[-1]:.1f} ms")
    print(f"Errores:         {len(errores)}")
    cumple = tiempos[-1] <= LIMITE_MS and not errores
    print("✅ Cumple el escenario (<= 500 ms y sin errores)" if cumple else "❌ No cumple el escenario")
    for e in errores[:3]:
        print("   ejemplo de error:", e)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 50)
