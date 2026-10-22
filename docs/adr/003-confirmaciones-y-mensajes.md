# ADR-003: Confirmaciones y mensajes claros en el carrito

- **Problema que resuelve (Entregable 2, evidencia de Usabilidad; ligado al Problema 4):** el usuario no recibía confirmación ni comprobante al pagar, ni un mensaje claro de éxito o error al editar o eliminar.
- **Cambio propuesto:** todas las rutas del carrito responden `mensaje` (JSON) o un mensaje temporal (`flash`) y la interfaz lo muestra siempre. Se pide confirmación antes de eliminar y antes de pagar (con el total). Agregar al carrito responde con redirect a `/pedido` y un aviso. Al pagar se muestra el número de orden y se lleva al usuario a `/mis_ordenes`. Se valida la cantidad (entero ≥ 1) en el navegador y en el servidor; el botón Pagar se desactiva con el carrito vacío o con productos no disponibles y evita el doble envío.
- **Código afectado:** `src/carrito/routes.py`, `src/carrito/carrito_service.py`, `templates/pedido.html`, `templates/pedidos_lista.html`.
- **Atributo de calidad que mejora:** Usabilidad.
