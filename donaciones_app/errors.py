from flask import jsonify


class ValidationError(Exception):
    """Error de validación de datos de entrada (HTTP 400)."""
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors or {}


def register_error_handlers(app):
    @app.errorhandler(ValidationError)
    def handle_validation_error(e):
        return jsonify({"error": e.message, "detalles": e.errors}), 400

    @app.errorhandler(404)
    def handle_404(e):
        return jsonify({"error": "Recurso no encontrado"}), 404

    @app.errorhandler(405)
    def handle_405(e):
        return jsonify({"error": "Método no permitido"}), 405

    @app.errorhandler(400)
    def handle_400(e):
        return jsonify({"error": "Solicitud inválida"}), 400

    @app.errorhandler(500)
    def handle_500(e):
        return jsonify({"error": "Error interno del servidor"}), 500
