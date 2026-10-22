# Punto de entrada de Unimarket (tienda_flask).
#
# El módulo de Carrito de Compras (MVP) ya no vive aquí: está en src/carrito/
# (routes.py -> carrito_service.py -> repositorios -> db_config.py).
# Las demás rutas (login, registro, productos, LUNA) se mantienen como estaban
# en el proyecto original: son dependencias del MVP, no parte de él.

import os
import re
import time

from flask import Flask, render_template, request, redirect, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from src.db_config import conexion
from src.carrito.routes import carrito_bp

app = Flask(__name__, template_folder="../templates", static_folder="../static")

# Problema 5 (Entregable 1): la clave de sesión ya no está escrita en el código.
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    app.secret_key = os.urandom(24).hex()
    print("⚠️  FLASK_SECRET_KEY no está definida: se usa una clave temporal "
          "(las sesiones se cierran al reiniciar). Defínela en tu .env.")

app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(app.root_path), "static", "uploads")

app.register_blueprint(carrito_bp)


# ---------------- INICIO ----------------
@app.route("/")
def index():
    if "usuario_id" in session:
        return redirect("/pedido")
    return redirect("/login")


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        correo = request.form["correo"]
        password = request.form["password"]

        with conexion() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE correo=%s", (correo,))
            user = cursor.fetchone()
            cursor.close()

        if user and check_password_hash(user["password"], password):
            session["usuario_id"] = user["id"]
            session["nombre"] = user["nombre"]
            return redirect("/pedido")

    return render_template("login.html")


# ---------------- PRODUCTOS (catálogo: dependencia del carrito) ----------------
@app.route("/crear_producto", methods=["POST"])
def crear_producto():
    if "usuario_id" not in session:
        return redirect("/login")

    nombre = request.form.get("nombre")
    descripcion = request.form.get("descripcion")
    precio = request.form.get("precio")
    categoria = request.form.get("categoria")

    imagen = request.files.get("imagen")
    nombre_imagen = None

    if imagen and imagen.filename != "":
        nombre_imagen = str(int(time.time())) + "_" + secure_filename(imagen.filename)
        imagen.save(os.path.join(app.config["UPLOAD_FOLDER"], nombre_imagen))

    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO productos (nombre, descripcion, precio, categoria, imagen, usuario_id)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (nombre, descripcion, precio, categoria, nombre_imagen, session["usuario_id"]),
        )
        conn.commit()
        cursor.close()

    return redirect("/pedido")


@app.route("/eliminar_producto/<int:id>", methods=["POST"])
def eliminar_producto(id):
    if "usuario_id" not in session:
        return redirect("/login")

    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT imagen FROM productos WHERE id=%s AND usuario_id=%s",
            (id, session["usuario_id"]),
        )
        producto = cursor.fetchone()

        if producto and producto["imagen"]:
            ruta = os.path.join(app.config["UPLOAD_FOLDER"], producto["imagen"])
            if os.path.exists(ruta):
                os.remove(ruta)

        cursor.execute(
            "DELETE FROM productos WHERE id=%s AND usuario_id=%s",
            (id, session["usuario_id"]),
        )
        conn.commit()
        cursor.close()

    return redirect("/pedido")


@app.route("/editar_precio/<int:id>", methods=["POST"])
def editar_precio(id):
    if "usuario_id" not in session:
        return redirect("/login")

    nuevo_precio = request.form.get("precio")

    with conexion() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE productos SET precio=%s WHERE id=%s AND usuario_id=%s",
            (nuevo_precio, id, session["usuario_id"]),
        )
        conn.commit()
        cursor.close()

    return redirect("/pedido")


# ---------------- LUNA (asistente de compras) ----------------
@app.route("/luna", methods=["POST"])
def luna():
    mensaje = request.json.get("mensaje").lower()

    if any(x in mensaje for x in ["hola", "buenas"]):
        return jsonify({"respuesta": "👋 Hola, soy LUNA tu asistente de compras 💙 dime qué producto buscas por categoria y precio y te ayudare a encontrarlo"})

    if "gracias" in mensaje:
        return jsonify({"respuesta": "💙 ¡Con gusto! Aquí estoy para ayudarte"})

    precio = None
    match = re.search(r"(\d+)", mensaje)
    if match:
        precio = int(match.group(1))
        if "millon" in mensaje:
            precio *= 1000000

    palabras = mensaje.split()
    palabras_ignorar = ["de", "menos", "mas", "quiero", "un", "una", "el", "la", "por", "favor"]
    palabras_clave = [p for p in palabras if p not in palabras_ignorar and not p.isdigit()]

    query = "SELECT * FROM productos WHERE 1=1"
    params = []

    if precio:
        query += " AND precio <= %s"
        params.append(precio)

    if palabras_clave:
        condiciones = []
        for palabra in palabras_clave:
            condiciones.append("(LOWER(nombre) LIKE %s OR LOWER(descripcion) LIKE %s OR LOWER(categoria) LIKE %s)")
            params.extend([f"%{palabra}%", f"%{palabra}%", f"%{palabra}%"])
        query += " AND (" + " OR ".join(condiciones) + ")"

    with conexion() as conn:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(query, params)
        productos = cursor.fetchall()

        if not productos:
            cursor.execute("SELECT * FROM productos ORDER BY precio ASC LIMIT 3")
            productos = cursor.fetchall()
            respuesta = "😅 No encontré exactamente eso, pero mira estas opciones:"
        else:
            respuesta = "Encontré estos productos para Ti:"
        cursor.close()

    return jsonify({"respuesta": respuesta, "productos": productos})


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ---------------- REGISTRO ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nombre = request.form.get("nombre")
        correo = request.form.get("correo")
        password = request.form.get("password")

        password_hash = generate_password_hash(password)

        with conexion() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nombre, correo, password) VALUES (%s, %s, %s)",
                (nombre, correo, password_hash),
            )
            conn.commit()
            cursor.close()

        return redirect("/login")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")
