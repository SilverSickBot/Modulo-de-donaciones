import datetime

import jwt
from flask import current_app


def generar_token(usuario):
    """Genera un JWT firmado con la información del usuario autenticado."""
    ahora = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        "sub": usuario.id,
        "username": usuario.username,
        "rol": usuario.rol,
        "iat": ahora,
        "exp": ahora + datetime.timedelta(minutes=current_app.config["JWT_EXP_MINUTES"]),
    }
    token = jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )
    return token


def decodificar_token(token):
    """Decodifica y valida un JWT. Lanza jwt.PyJWTError si es inválido/expiró."""
    payload = jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )
    return payload
