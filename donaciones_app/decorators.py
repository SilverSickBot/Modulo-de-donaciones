from functools import wraps
import time
import jwt
from flask import current_app, jsonify, request


def generar_token(usuario):
  """Genera un JWT firmado con la información del usuario autenticado."""
  ahora = int(time.time())
  expiracion = ahora + (current_app.config["JWT_EXP_MINUTES"] * 60)

  # Nos aseguramos de extraer el ID como texto o usar username si id fuera None
  user_id = str(getattr(usuario, "id", usuario.username))

  payload = {
      "sub": user_id,  # Obligatorio: debe ser tipo str
      "username": usuario.username,
      "rol": usuario.rol,
      "iat": ahora,
      "exp": expiracion,
  }

  token = jwt.encode(
      payload,
      current_app.config["SECRET_KEY"],
      algorithm=current_app.config["JWT_ALGORITHM"],
  )

  if isinstance(token, bytes):
    token = token.decode("utf-8")
  return token


def decodificar_token(token):
  """Decodifica y valida el JWT."""
  return jwt.decode(
      token,
      current_app.config["SECRET_KEY"],
      algorithms=[current_app.config["JWT_ALGORITHM"]],
      options={"verify_sub": False},  # Evita errores estrictos con el campo 'sub'
  )


def token_required(f):
    """Decorador para verificar que la petición incluya un token JWT válido."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            print("❌ [401 Error]: No se encontró la cabecera Authorization.")
            return jsonify({"error": "Acceso no autorizado: Token no proporcionado"}), 401

        partes = auth_header.split()
        if len(partes) != 2 or partes[0].lower() != "bearer":
            print(f"❌ [401 Error]: Formato de cabecera inválido -> '{auth_header}'")
            return jsonify({"error": "Formato de token inválido. Debe ser 'Bearer <token>'"}), 401

        token = partes[1]

        try:
            payload = decodificar_token(token)
            request.usuario_actual = payload
        except jwt.ExpiredSignatureError:
            print("❌ [401 Error]: El token JWT ha expirado.")
            return jsonify({"error": "El token ha expirado"}), 401
        except jwt.InvalidTokenError as e:
            print(f"❌ [401 Error]: Token inválido o firma no coincide -> {e}")
            return jsonify({"error": "Token inválido o manipulado", "detalles": str(e)}), 401

        return f(*args, **kwargs)

    return decorated


def role_required(*roles_permitidos):
    """Decorador para restringir el acceso según el rol del usuario (ej: 'administrador')."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            usuario = getattr(request, "usuario_actual", None)

            if not usuario:
                print("❌ [401 Error]: Usuario no autenticado en la petición.")
                return jsonify({"error": "Acceso no autorizado: Debe autenticarse"}), 401

            if usuario.get("rol") not in roles_permitidos:
                print(f"❌ [403 Error]: Permisos insuficientes. Rol usuario: {usuario.get('rol')}")
                return jsonify({"error": "Acceso denegado: No tiene permisos suficientes"}), 403

            return f(*args, **kwargs)

        return decorated

    return decorator