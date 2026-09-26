from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from decorators import role_required, token_required
from errors import ValidationError
from models import Donacion, Rol, TipoDonacion, donaciones_db

donaciones_bp = Blueprint("donaciones_bp", __name__)


def validar_donacion(data):
  """Valida los datos de entrada para crear una donación de bienes (comida/ropa)."""
  if not data:
    raise ValidationError("Se requiere un cuerpo JSON", {"body": "faltante"})

  errores = {}

  tipo = data.get("tipo")
  cantidad = data.get("cantidad")
  donante = data.get("donante")
  direccion = data.get("direccion")
  organizacion = data.get("organizacion")
  descripcion = data.get("descripcion", "") or ""

  if (
      not tipo
      or not isinstance(tipo, str)
      or tipo.strip().lower() not in TipoDonacion.TIPOS_VALIDOS
  ):
    errores["tipo"] = (
        f"El tipo debe ser uno de: {', '.join(TipoDonacion.TIPOS_VALIDOS)}"
    )

  cantidad_valida = None
  if cantidad is None:
    errores["cantidad"] = "La cantidad es obligatoria"
  else:
    try:
      cantidad_valida = float(cantidad)
      if cantidad_valida <= 0:
        errores["cantidad"] = "La cantidad debe ser mayor que cero"
    except (TypeError, ValueError):
      errores["cantidad"] = "La cantidad debe ser numérica"

  if not donante or not isinstance(donante, str) or len(donante.strip()) < 2:
    errores["donante"] = (
        "El nombre del donante es obligatorio (mínimo 2 caracteres)"
    )

  if (
      not direccion
      or not isinstance(direccion, str)
      or len(direccion.strip()) < 5
  ):
    errores["direccion"] = (
        "La dirección es obligatoria (mínimo 5 caracteres)"
    )

  if (
      not organizacion
      or not isinstance(organizacion, str)
      or len(organizacion.strip()) < 2
  ):
    errores["organizacion"] = (
        "La organización beneficiaria es obligatoria (mínimo 2 caracteres)"
    )

  if errores:
    raise ValidationError("Datos de donación inválidos", errores)

  return {
      "tipo": tipo.strip().lower(),
      "cantidad": cantidad_valida,
      "donante": donante.strip(),
      "direccion": direccion.strip(),
      "organizacion": organizacion.strip(),
      "descripcion": descripcion.strip() if isinstance(descripcion, str) else "",
  }


# --- Crear Donación ---
@donaciones_bp.route("", methods=["POST"])
@token_required
@role_required(Rol.USUARIO, Rol.ADMINISTRADOR)
def crear_donacion():
  data = request.get_json(silent=True)
  datos = validar_donacion(data)

  usuario = request.usuario_actual
  usuario_id = usuario.get("sub")

  donacion = Donacion(
      tipo=datos["tipo"],
      cantidad=datos["cantidad"],
      donante=datos["donante"],
      direccion=datos["direccion"],
      organizacion=datos["organizacion"],
      descripcion=datos["descripcion"],
      usuario_id=usuario_id,
  )
  donaciones_db[donacion.id] = donacion
  return jsonify(donacion.to_dict()), 201


# --- Listar Donaciones (Administrador ve todas, Usuario solo las suyas) ---
@donaciones_bp.route("", methods=["GET"])
@token_required
@role_required(Rol.USUARIO, Rol.ADMINISTRADOR)
def listar_donaciones():
  usuario = request.usuario_actual
  rol = usuario.get("rol")
  usuario_id = usuario.get("sub")

  if rol == Rol.ADMINISTRADOR:
    resultado = [d.to_dict() for d in donaciones_db.values()]
  else:
    resultado = [
        d.to_dict()
        for d in donaciones_db.values()
        if str(d.usuario_id) == str(usuario_id)
    ]

  resultado.sort(key=lambda d: d["id"], reverse=True)
  return jsonify(resultado), 200


# --- Obtener una Donación por ID ---
@donaciones_bp.route("/<int:donacion_id>", methods=["GET"])
@token_required
@role_required(Rol.USUARIO, Rol.ADMINISTRADOR)
def obtener_donacion(donacion_id):
  donacion = donaciones_db.get(donacion_id)
  if not donacion:
    return jsonify({"error": "Donación no encontrada"}), 404

  usuario = request.usuario_actual
  rol = usuario.get("rol")
  usuario_id = usuario.get("sub")

  if rol != Rol.ADMINISTRADOR and str(donacion.usuario_id) != str(usuario_id):
    return (
        jsonify({
            "error": "Acceso denegado: No tienes permiso para ver esta donación"
        }),
        403,
    )

  return jsonify(donacion.to_dict()), 200


# --- Acciones EXCLUSIVAS del Administrador ---
@donaciones_bp.route("/reporte", methods=["GET"])
@token_required
@role_required(Rol.ADMINISTRADOR)
def reporte_donaciones():
  todas = list(donaciones_db.values())

  resumen_por_tipo = {}
  for tipo in TipoDonacion.TIPOS_VALIDOS:
    aprobadas_tipo = [
        d for d in todas if d.tipo == tipo and d.estado == "aprobada"
    ]
    resumen_por_tipo[tipo] = {
        "donaciones_aprobadas": len(aprobadas_tipo),
        "total_unidades": sum(d.cantidad for d in aprobadas_tipo),
    }

  return (
      jsonify({
          "total_donaciones": len(todas),
          "pendientes": len([d for d in todas if d.estado == "pendiente"]),
          "aprobadas": len([d for d in todas if d.estado == "aprobada"]),
          "rechazadas": len([d for d in todas if d.estado == "rechazada"]),
          "resumen_por_tipo": resumen_por_tipo,
      }),
      200,
  )


@donaciones_bp.route("/<int:donacion_id>/aprobar", methods=["PUT"])
@token_required
@role_required(Rol.ADMINISTRADOR)
def aprobar_donacion(donacion_id):
  donacion = donaciones_db.get(donacion_id)
  if not donacion:
    return jsonify({"error": "Donación no encontrada"}), 404

  donacion.estado = "aprobada"
  donacion.fecha_actualizacion = datetime.now(timezone.utc).isoformat()
  return jsonify(donacion.to_dict()), 200


@donaciones_bp.route("/<int:donacion_id>/rechazar", methods=["PUT"])
@token_required
@role_required(Rol.ADMINISTRADOR)
def rechazar_donacion(donacion_id):
  donacion = donaciones_db.get(donacion_id)
  if not donacion:
    return jsonify({"error": "Donación no encontrada"}), 404

  donacion.estado = "rechazada"
  donacion.fecha_actualizacion = datetime.now(timezone.utc).isoformat()
  return jsonify(donacion.to_dict()), 200


@donaciones_bp.route("/<int:donacion_id>", methods=["DELETE"])
@token_required
@role_required(Rol.ADMINISTRADOR)
def eliminar_donacion(donacion_id):
  donacion = donaciones_db.get(donacion_id)
  if not donacion:
    return jsonify({"error": "Donación no encontrada"}), 404

  del donaciones_db[donacion_id]
  return jsonify({"mensaje": "Donación eliminada correctamente"}), 200