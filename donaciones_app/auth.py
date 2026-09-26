import time
import jwt
from flask import current_app


def generar_token(usuario):
  """Genera un JWT firmado con la información del usuario autenticado."""
  ahora = int(time.time())  # Timestamp Unix actual en segundos
  expiracion = ahora + (current_app.config["JWT_EXP_MINUTES"] * 60)

  payload = {
      "sub": usuario.id,
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
  """Decodifica y valida un JWT. Lanza jwt.PyJWTError si es inválido/expiró."""
  payload = jwt.decode(
      token,
      current_app.config["SECRET_KEY"],
      algorithms=[current_app.config["JWT_ALGORITHM"]],
  )
  return payload
