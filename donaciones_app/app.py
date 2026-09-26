import os

from flask import Flask, jsonify, send_from_directory

from config import Config
from errors import register_error_handlers
from models import seed_data
from routes.auth_routes import auth_bp
from routes.donaciones_routes import donaciones_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    register_error_handlers(app)
    seed_data()  # crea usuarios de prueba: admin / jperez

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(donaciones_bp, url_prefix="/api/donaciones")

    frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")

    @app.route("/app")
    def frontend_app():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/")
    def index():
        return jsonify({
            "mensaje": "API - Módulo de Donaciones",
            "version": "1.0",
            "interfaz_grafica": "/app",
            "usuarios_de_prueba": {
                "administrador": {"username": "admin", "password": "Admin123!"},
                "usuario": {"username": "jperez", "password": "Usuario123!"},
            },
        })

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
