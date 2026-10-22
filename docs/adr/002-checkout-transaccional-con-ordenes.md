# ADR-002: Pago atómico con modelo de Orden y validación de disponibilidad

- **Problema que resuelve (Problema 4, Entregable 1):** `/pagar` solo ejecutaba `DELETE FROM pedidos`: sin historial, sin validación y sin un límite transaccional que agrupara leer el carrito, registrar la orden y vaciarlo.
- **Cambio propuesto:** nuevas tablas `ordenes` y `detalle_orden`. `confirmar_compra` abre UNA transacción que bloquea el carrito del usuario, lo lee, lo valida (vacío o con productos que ya no existen => no se cobra), inserta la orden y su detalle y vacía el carrito. Si algo falla, rollback: el carrito queda igual. El bloqueo evita que un doble clic cree dos órdenes. Nueva ruta `/mis_ordenes` para consultar el historial.
- **Código afectado:** `src/carrito/carrito_service.py`, `pedidos_repository.py`, `ordenes_repository.py`, `routes.py` (`/pagar`, `/mis_ordenes`), `db/schema.sql`, `templates/ordenes.html`, `templates/pedidos_lista.html`.
- **Atributo de calidad que mejora:** Idoneidad funcional (y Confiabilidad/consistencia, de E1).
- **Alcance:** la pasarela de pago real queda fuera del MVP; "disponible" = el producto sigue publicado (no hay stock en el esquema).
