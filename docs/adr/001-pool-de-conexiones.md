# ADR-001: Pool de conexiones, préstamo seguro y transacciones

- **Problema que resuelve (Problema 3, Entregable 1):** `get_connection()` abría y cerraba una conexión MySQL nueva en cada petición, sin `try/finally` (si algo fallaba la conexión quedaba abierta) y sin transacciones. Con varios usuarios simultáneos se puede agotar el servidor de base de datos.
- **Cambio propuesto:** un pool de conexiones creado una vez (`MYSQL_POOL_SIZE`, 10 por defecto) que espera hasta `MYSQL_POOL_TIMEOUT` segundos si todas están ocupadas. `conexion()` presta una conexión y siempre la devuelve; `transaccion()` agrupa pasos con commit si todo sale bien y rollback si algo falla. Las conexiones usan autocommit para no reutilizar lecturas viejas.
- **Código afectado:** `src/db_config.py` (antes `db_config.py`); todas las rutas y repositorios que antes llamaban `get_connection()`.
- **Atributo de calidad que mejora:** Eficiencia de ejecución (y Confiabilidad, de E1).
- **Verificación:** la prueba de carga (`python -m tests.prueba_carga_pool`) debe correrse contra MySQL real; aún no se ha medido el criterio de 500 ms.
