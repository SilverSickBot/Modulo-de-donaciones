import os
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()


class Config:
    """Configuración de la aplicación Flask."""

    # Se asegura de que la SECRET_KEY sea siempre una cadena de texto (str)
    SECRET_KEY = str(
        os.environ.get(
            "SECRET_KEY", "clave-secreta-super-segura-cambiar-en-produccion"
        )
    )
    JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
    
    # Se convierte obligatoriamente a entero para evitar problemas con la expiración
    JWT_EXP_MINUTES = int(os.environ.get("JWT_EXP_MINUTES", 60))