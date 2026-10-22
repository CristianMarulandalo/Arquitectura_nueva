# ADR-006: Esquema completo y clave secreta por variable de entorno

- **Problema que resuelve (Problema 5, Entregable 1):** el dump no incluía la tabla `productos`, así que `GET /pedido` fallaba al levantar el proyecto desde cero; y `app.secret_key = "engranaje1"` estaba escrita en el código versionado.
- **Cambio propuesto:** `db/schema.sql` define todas las tablas (incluida `productos`, con tipos supuestos, y las nuevas de órdenes) y sirve también para actualizar una base existente sin borrar datos. La clave sale de `FLASK_SECRET_KEY` (si falta, se usa una temporal y se avisa). Las variables se pueden dejar en un `.env` (plantilla `.env.example`, ignorado por git).
- **Código afectado:** `db/schema.sql`, `src/app.py`, `src/db_config.py`, `.env.example`, `.gitignore`.
- **Atributo de calidad que mejora:** Idoneidad funcional (el sistema funciona al entregarlo); Seguridad y Mantenibilidad/reproducibilidad en el Entregable 1.
- **Pendiente:** si la clave `engranaje1` se usó en producción o ya está en el historial de GitHub, conviene cambiarla.
