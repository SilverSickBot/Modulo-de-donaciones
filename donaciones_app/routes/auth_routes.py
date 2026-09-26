from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

from auth import generar_token
from models import usuarios_db

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Se requiere un cuerpo JSON"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "'username' y 'password' son obligatorios"}), 400

    usuario = usuarios_db.get(username)
    if not usuario or not check_password_hash(usuario.password_hash, password):
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = generar_token(usuario)
    return jsonify({
        "mensaje": "Autenticación exitosa",
        "token": token,
        "usuario": usuario.to_dict(),
    }), 200
