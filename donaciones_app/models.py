from datetime import datetime, timezone
from itertools import count

from werkzeug.security import generate_password_hash


class Rol:
    """Roles reconocidos por el módulo."""
    USUARIO = "usuario"
    ADMINISTRADOR = "administrador"


class TipoDonacion:
    """Tipos de donación aceptados (por ahora no se incluyen transferencias/dinero)."""
    COMIDA = "comida"
    ROPA = "ropa"
    TIPOS_VALIDOS = [COMIDA, ROPA]


class Usuario:
    def __init__(self, id, username, password_hash, rol, nombre):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.rol = rol
        self.nombre = nombre

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "rol": self.rol,
            "nombre": self.nombre,
        }


class Donacion:
    _id_counter = count(1)

    def __init__(self, tipo, cantidad, donante, direccion, organizacion, usuario_id, descripcion=""):
        self.id = next(Donacion._id_counter)
        self.tipo = tipo                      # "comida" | "ropa"
        self.cantidad = cantidad               # número de paquetes/piezas
        self.donante = donante                 # nombre de quien dona
        self.direccion = direccion             # dirección de recolección/envío
        self.organizacion = organizacion       # organización beneficiaria
        self.descripcion = descripcion         # detalle opcional (ej. "ropa de invierno para niños")
        self.usuario_id = usuario_id
        self.estado = "pendiente"              # pendiente | aprobada | rechazada
        self.fecha_creacion = datetime.now(timezone.utc).isoformat()
        self.fecha_actualizacion = None

    def to_dict(self):
        return {
            "id": self.id,
            "tipo": self.tipo,
            "cantidad": self.cantidad,
            "donante": self.donante,
            "direccion": self.direccion,
            "organizacion": self.organizacion,
            "descripcion": self.descripcion,
            "usuario_id": self.usuario_id,
            "estado": self.estado,
            "fecha_creacion": self.fecha_creacion,
            "fecha_actualizacion": self.fecha_actualizacion,
        }


# "Bases de datos" en memoria (solo para fines de prueba/demo)
usuarios_db = {}
donaciones_db = {}


def seed_data():
    """Reinicia el estado en memoria y crea usuarios de prueba."""
    usuarios_db.clear()
    donaciones_db.clear()
    Donacion._id_counter = count(1)

    admin = Usuario(
        id=1,
        username="admin",
        password_hash=generate_password_hash("Admin123!"),
        rol=Rol.ADMINISTRADOR,
        nombre="Administrador General",
    )
    usuario = Usuario(
        id=2,
        username="jperez",
        password_hash=generate_password_hash("Usuario123!"),
        rol=Rol.USUARIO,
        nombre="Juan Pérez",
    )

    usuarios_db[admin.username] = admin
    usuarios_db[usuario.username] = usuario
