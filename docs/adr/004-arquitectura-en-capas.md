# ADR-004: Separar rutas, servicio y repositorios

- **Problema que resuelve (Problema 1, Entregable 1):** enrutamiento, reglas de negocio y SQL mezclados en las mismas funciones de `app.py`: alto acoplamiento y pruebas imposibles sin Flask y MySQL.
- **Cambio propuesto:** capas Rutas (`routes.py`) → Servicio (`carrito_service.py`) → Repositorios (`pedidos_repository.py`, `ordenes_repository.py`) → `db_config.py`. Solo los repositorios tienen SQL; el servicio no conoce Flask ni SQL. El resto de la aplicación (login, catálogo, LUNA) no se modifica en su lógica.
- **Código afectado:** `app.py` (original) → `src/app.py` + `src/carrito/`.
- **Atributo de calidad que mejora:** soporta los tres priorizados; en el Entregable 1 corresponde a Mantenibilidad y Testabilidad (ahora hay 30 pruebas que corren sin MySQL).
