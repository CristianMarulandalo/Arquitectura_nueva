# Tareas pendientes hacia la Semana 15

Para el repositorio: crear cada fila como **Issue** (o tarjeta de un tablero GitHub Projects)
y asignarla a un integrante. Cada integrante debe hacer sus propios commits.

| # | Tarea | Estado |
|---|-------|--------|
| 1 | Ejecutar `db/schema.sql` en MySQL real y probar el flujo completo: agregar, editar, eliminar, pagar, ver órdenes | Pendiente |
| 2 | Ejecutar `python -m tests.prueba_carga_pool` (50 usuarios) y registrar el resultado frente al límite de 500 ms (ADR-001) | Pendiente |
| 3 | Prueba de usabilidad con usuarios reales (meta: 90 % completa el flujo sin confusión) | Pendiente |
| 4 | Revisar el pago en dos pestañas a la vez (doble clic): debe crear una sola orden | Pendiente |
| 5 | Decidir si se cambia la clave `engranaje1` en producción y en el historial de GitHub | Pendiente |
| 6 | Pruebas de integración contra MySQL de prueba (hoy las pruebas usan repositorios falsos) | Pendiente |
| 7 | Actualizar diagramas y `docs/arquitectura.md` si cambia algo (editar `.mmd`, exportar con `mmdc`) | Pendiente |
| 8 | Preparar la demostración final del módulo (semana 15) | Pendiente |

Hecho en esta versión: capas, pool y transacciones, pago atómico con órdenes, control de
acceso por usuario, esquema completo, mensajes y confirmaciones, 30 pruebas unitarias.
