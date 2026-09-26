import os


class Config:
    """Configuración de la aplicación Flask."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "clave-secreta-super-segura-cambiar-en-produccion")
    JWT_ALGORITHM = "HS256"
    JWT_EXP_MINUTES = 60
