# Prueba de conexión original (antes test_db.py en la raíz del proyecto), conservada.
# Necesita MySQL real y tu .env. Ejecutar desde la raíz:  python -m tests.test_db
from src.db_config import conexion

if __name__ == "__main__":
    try:
        with conexion():
            print("✅ Conexión exitosa a MySQL")
    except Exception as e:
        print("❌ Error de conexión:", e)
