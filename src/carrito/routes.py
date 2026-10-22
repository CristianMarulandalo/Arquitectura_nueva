"""
Rutas del carrito. Mismas direcciones que antes (/pedido, /pedidos_lista,
/actualizar_pedido/<id>, /eliminar_pedido/<id>, /pagar) más /mis_ordenes.
Cada ruta solo recibe la petición, le pide el trabajo a carrito_service y
responde (tabla A.1 del Entregable 2: HTML con redirect o JSON según el caso).
"""

from flask import Blueprint, render_template, request, redirect, session, jsonify, flash

from src.carrito import carrito_service

carrito_bp = Blueprint("carrito", __name__)

_SIN_SESION = {"success": False, "mensaje": "Debes iniciar sesión."}


@carrito_bp.route("/pedido", methods=["GET", "POST"])
def pedido():
    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":
        ok, mensaje = carrito_service.agregar_al_carrito(
            session["usuario_id"], request.form.get("producto"), request.form.get("cantidad")
        )
        flash(mensaje, "success" if ok else "danger")
        return redirect("/pedido")

    productos = carrito_service.obtener_catalogo()
    return render_template("pedido.html", nombre=session["nombre"], productos=productos)


@carrito_bp.route("/pedidos_lista")
def pedidos_lista():
    if "usuario_id" not in session:
        return redirect("/login")

    pedidos, total, no_disponibles = carrito_service.obtener_carrito(session["usuario_id"])
    return render_template("pedidos_lista.html", pedidos=pedidos, total=total, no_disponibles=no_disponibles)


@carrito_bp.route("/eliminar_pedido/<int:id>", methods=["POST"])
def eliminar_pedido(id):
    if "usuario_id" not in session:
        return jsonify(_SIN_SESION), 401

    ok, mensaje = carrito_service.eliminar_item(id, session["usuario_id"])
    return jsonify({"success": ok, "mensaje": mensaje})


@carrito_bp.route("/actualizar_pedido/<int:id>", methods=["POST"])
def actualizar_pedido(id):
    if "usuario_id" not in session:
        return jsonify(_SIN_SESION), 401

    data = request.get_json(silent=True) or {}
    ok, mensaje = carrito_service.actualizar_item(
        id, session["usuario_id"], data.get("producto"), data.get("cantidad")
    )
    return jsonify({"success": ok, "mensaje": mensaje})


@carrito_bp.route("/pagar", methods=["POST"])
def pagar():
    if "usuario_id" not in session:
        return jsonify(_SIN_SESION), 401

    ok, mensaje, orden_id = carrito_service.confirmar_compra(session["usuario_id"])
    return jsonify({"success": ok, "mensaje": mensaje, "orden_id": orden_id})


@carrito_bp.route("/mis_ordenes")
def mis_ordenes():
    if "usuario_id" not in session:
        return redirect("/login")

    ordenes = carrito_service.obtener_historial(session["usuario_id"])
    return render_template("ordenes.html", ordenes=ordenes)
