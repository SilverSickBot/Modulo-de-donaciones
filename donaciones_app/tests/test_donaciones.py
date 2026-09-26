import json
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
from models import seed_data


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config.update({"TESTING": True})
        seed_data()
        self.client = self.app.test_client()

    def login(self, username, password):
        return self.client.post(
            "/api/auth/login",
            data=json.dumps({"username": username, "password": password}),
            content_type="application/json",
        )

    def token_admin(self):
        resp = self.login("admin", "Admin123!")
        return resp.get_json()["token"]

    def token_usuario(self):
        resp = self.login("jperez", "Usuario123!")
        return resp.get_json()["token"]

    def auth_header(self, token):
        return {"Authorization": f"Bearer {token}"}

    def post_json(self, url, body, token=None):
        headers = self.auth_header(token) if token else {}
        return self.client.post(url, data=json.dumps(body), content_type="application/json", headers=headers)

    def donacion_comida(self, **overrides):
        base = {
            "tipo": "comida",
            "cantidad": 10,
            "donante": "Juan Pérez",
            "organizacion": "Comedor Comunitario Esperanza",
            "direccion": "Av. Reforma 123, CDMX",
            "descripcion": "Paquetes de arroz y frijol",
        }
        base.update(overrides)
        return base

    def donacion_ropa(self, **overrides):
        base = {
            "tipo": "ropa",
            "cantidad": 20,
            "donante": "Juan Pérez",
            "organizacion": "Fundación Abrigo",
            "direccion": "Calle Hidalgo 45, Monterrey",
            "descripcion": "Ropa de invierno para niños",
        }
        base.update(overrides)
        return base


# ---------------------------------------------------------------------------
# 1. Autenticación
# ---------------------------------------------------------------------------
class TestAutenticacion(BaseTestCase):
    def test_login_exitoso_admin(self):
        resp = self.login("admin", "Admin123!")
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn("token", body)
        self.assertEqual(body["usuario"]["rol"], "administrador")

    def test_login_exitoso_usuario(self):
        resp = self.login("jperez", "Usuario123!")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["usuario"]["rol"], "usuario")

    def test_login_credenciales_invalidas(self):
        resp = self.login("admin", "clave_incorrecta")
        self.assertEqual(resp.status_code, 401)

    def test_login_usuario_inexistente(self):
        resp = self.login("no_existe", "1234")
        self.assertEqual(resp.status_code, 401)

    def test_login_sin_datos(self):
        resp = self.client.post("/api/auth/login", data=json.dumps({}), content_type="application/json")
        self.assertEqual(resp.status_code, 400)


# ---------------------------------------------------------------------------
# 2. Seguridad / JWT
# ---------------------------------------------------------------------------
class TestSeguridadJWT(BaseTestCase):
    def test_acceso_sin_token(self):
        resp = self.client.get("/api/donaciones")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["code"], "TOKEN_MISSING")

    def test_acceso_token_invalido(self):
        resp = self.client.get("/api/donaciones", headers=self.auth_header("token.falso.123"))
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["code"], "TOKEN_INVALID")

    def test_acceso_con_token_valido(self):
        resp = self.client.get("/api/donaciones", headers=self.auth_header(self.token_usuario()))
        self.assertEqual(resp.status_code, 200)


# ---------------------------------------------------------------------------
# 3. Permisos de Usuario
# ---------------------------------------------------------------------------
class TestPermisosUsuario(BaseTestCase):
    def test_usuario_puede_crear_donacion_comida(self):
        resp = self.post_json("/api/donaciones", self.donacion_comida(), token=self.token_usuario())
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["estado"], "pendiente")
        self.assertEqual(body["tipo"], "comida")

    def test_usuario_puede_crear_donacion_ropa(self):
        resp = self.post_json("/api/donaciones", self.donacion_ropa(), token=self.token_usuario())
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.get_json()["tipo"], "ropa")

    def test_usuario_no_puede_aprobar_donacion(self):
        token_u = self.token_usuario()
        crear = self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)
        donacion_id = crear.get_json()["id"]

        resp = self.client.put(f"/api/donaciones/{donacion_id}/aprobar", headers=self.auth_header(token_u))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["code"], "FORBIDDEN")

    def test_usuario_no_puede_eliminar_donacion(self):
        token_u = self.token_usuario()
        crear = self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)
        donacion_id = crear.get_json()["id"]

        resp = self.client.delete(f"/api/donaciones/{donacion_id}", headers=self.auth_header(token_u))
        self.assertEqual(resp.status_code, 403)

    def test_usuario_no_puede_ver_reporte(self):
        resp = self.client.get("/api/donaciones/reporte", headers=self.auth_header(self.token_usuario()))
        self.assertEqual(resp.status_code, 403)

    def test_usuario_solo_ve_sus_propias_donaciones(self):
        token_u = self.token_usuario()
        token_a = self.token_admin()
        self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)
        self.post_json("/api/donaciones", self.donacion_ropa(donante="Admin"), token=token_a)

        resp = self.client.get("/api/donaciones", headers=self.auth_header(token_u))
        data = resp.get_json()
        self.assertTrue(all(d["usuario_id"] == 2 for d in data))
        self.assertEqual(len(data), 1)


# ---------------------------------------------------------------------------
# 4. Permisos de Administrador (acciones exclusivas)
# ---------------------------------------------------------------------------
class TestPermisosAdministrador(BaseTestCase):
    def test_admin_puede_aprobar_donacion(self):
        token_u = self.token_usuario()
        token_a = self.token_admin()
        crear = self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)
        donacion_id = crear.get_json()["id"]

        resp = self.client.put(f"/api/donaciones/{donacion_id}/aprobar", headers=self.auth_header(token_a))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["estado"], "aprobada")

    def test_admin_puede_rechazar_donacion(self):
        token_u = self.token_usuario()
        token_a = self.token_admin()
        crear = self.post_json("/api/donaciones", self.donacion_ropa(), token=token_u)
        donacion_id = crear.get_json()["id"]

        resp = self.client.put(f"/api/donaciones/{donacion_id}/rechazar", headers=self.auth_header(token_a))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["estado"], "rechazada")

    def test_admin_puede_eliminar_donacion(self):
        token_u = self.token_usuario()
        token_a = self.token_admin()
        crear = self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)
        donacion_id = crear.get_json()["id"]

        resp = self.client.delete(f"/api/donaciones/{donacion_id}", headers=self.auth_header(token_a))
        self.assertEqual(resp.status_code, 200)

    def test_admin_puede_ver_reporte(self):
        resp = self.client.get("/api/donaciones/reporte", headers=self.auth_header(self.token_admin()))
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn("resumen_por_tipo", body)
        self.assertIn("comida", body["resumen_por_tipo"])
        self.assertIn("ropa", body["resumen_por_tipo"])

    def test_admin_ve_todas_las_donaciones(self):
        token_u = self.token_usuario()
        token_a = self.token_admin()
        self.post_json("/api/donaciones", self.donacion_comida(), token=token_u)

        resp = self.client.get("/api/donaciones", headers=self.auth_header(token_a))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.get_json()), 1)


# ---------------------------------------------------------------------------
# 5. Validación de datos
# ---------------------------------------------------------------------------
class TestValidacionDatos(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.token_u = self.token_usuario()

    def test_crear_donacion_tipo_invalido(self):
        resp = self.post_json("/api/donaciones", self.donacion_comida(tipo="dinero"), token=self.token_u)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("tipo", resp.get_json()["detalles"])

    def test_crear_donacion_sin_cantidad(self):
        datos = self.donacion_comida()
        del datos["cantidad"]
        resp = self.post_json("/api/donaciones", datos, token=self.token_u)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("cantidad", resp.get_json()["detalles"])

    def test_crear_donacion_cantidad_negativa(self):
        resp = self.post_json("/api/donaciones", self.donacion_comida(cantidad=-5), token=self.token_u)
        self.assertEqual(resp.status_code, 400)

    def test_crear_donacion_cantidad_no_numerica(self):
        resp = self.post_json("/api/donaciones", self.donacion_comida(cantidad="muchas"), token=self.token_u)
        self.assertEqual(resp.status_code, 400)

    def test_crear_donacion_sin_donante(self):
        datos = self.donacion_comida()
        del datos["donante"]
        resp = self.post_json("/api/donaciones", datos, token=self.token_u)
        self.assertEqual(resp.status_code, 400)

    def test_crear_donacion_sin_direccion(self):
        datos = self.donacion_comida(direccion="")
        resp = self.post_json("/api/donaciones", datos, token=self.token_u)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("direccion", resp.get_json()["detalles"])

    def test_crear_donacion_sin_organizacion(self):
        datos = self.donacion_comida(organizacion="")
        resp = self.post_json("/api/donaciones", datos, token=self.token_u)
        self.assertEqual(resp.status_code, 400)
        self.assertIn("organizacion", resp.get_json()["detalles"])


# ---------------------------------------------------------------------------
# 6. Manejo de errores
# ---------------------------------------------------------------------------
class TestManejoErrores(BaseTestCase):
    def test_donacion_inexistente_404(self):
        resp = self.client.get("/api/donaciones/9999", headers=self.auth_header(self.token_admin()))
        self.assertEqual(resp.status_code, 404)

    def test_aprobar_donacion_inexistente_404(self):
        resp = self.client.put("/api/donaciones/9999/aprobar", headers=self.auth_header(self.token_admin()))
        self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
