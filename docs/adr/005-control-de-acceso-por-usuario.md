# ADR-005: El carrito solo opera sobre pedidos del usuario en sesión

- **Problema que resuelve (Problema 2, Entregable 1):** `/eliminar_pedido/<id>` y `/actualizar_pedido/<id>` usaban solo el `id` de la URL, sin revisar la sesión ni el dueño (IDOR): cualquier usuario podía borrar o editar el carrito de otro.
- **Cambio propuesto:** ambas rutas exigen sesión (401 si no hay) y el SQL incluye `AND usuario_id=%s`; si el pedido no es del usuario no se modifica nada y se responde con un mensaje.
- **Código afectado:** `src/carrito/routes.py`, `src/carrito/pedidos_repository.py` (`eliminar_pedido`, `actualizar_pedido`).
- **Atributo de calidad que mejora:** Idoneidad funcional (cada usuario opera solo su carrito); Seguridad y Confiabilidad de los datos en el Entregable 1.
- **Verificación:** `tests/test_repositorios.py` y `tests/test_rutas.py`.
