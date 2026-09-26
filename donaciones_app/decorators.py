from functools import wraps

import jwt
from flask import g, jsonify, request

from auth import decodificar_token


def token_required(f):
    """Exige un JWT válido en el header Authorization: Bearer <token>."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", None)

        if not auth_header or not auth_header.startswith("Bearer "):
            return jsonify({
                "error": "Token no proporcionado. Use el header 'Authorization: Bearer <token>'",
                "code": "TOKEN_MISSING",
            }), 401

        token = auth_header.split(" ", 1)[1].strip()

        try:
            payload = decodificar_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "El token ha expirado", "code": "TOKEN_EXPIRED"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Token inválido", "code": "TOKEN_INVALID"}), 401

        g.current_user = payload
        return f(*args, **kwargs)

    return decorated


def role_required(*roles_permitidos):
    """Restringe el acceso a los roles indicados. Debe usarse después de token_required."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(g, "current_user"):
                return jsonify({"error": "No autenticado", "code": "UNAUTHENTICATED"}), 401

            rol_actual = g.current_user.get("rol")
            if rol_actual not in roles_permitidos:
                return jsonify({
                    "error": "No tiene permisos para realizar esta acción",
                    "code": "FORBIDDEN",
                    "rol_requerido": list(roles_permitidos),
                    "rol_actual": rol_actual,
                }), 403

            return f(*args, **kwargs)

        return decorated

    return decorator
