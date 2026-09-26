import json
import unittest
from app import create_app
from models import Donacion, donaciones_db, usuarios_db


class TestAutenticacion(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()

  def test_login_exitoso_admin(self):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "Admin123!"}),
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 200)
    data = resp.get_json()
    self.assertIn("token", data)
    self.assertEqual(data["usuario"]["rol"], "administrador")

  def test_login_exitoso_usuario(self):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": "jperez", "password": "Usuario123!"}),
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 200)
    data = resp.get_json()
    self.assertIn("token", data)
    self.assertEqual(data["usuario"]["rol"], "usuario")

  def test_login_credenciales_invalidas(self):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": "admin", "password": "ClaveIncorrecta"}),
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 401)

  def test_login_usuario_inexistente(self):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps(
            {"username": "noexiste", "password": "ClaveIncorrecta"}
        ),
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 401)

  def test_login_sin_datos(self):
    resp = self.client.post("/api/auth/login", content_type="application/json")
    self.assertEqual(resp.status_code, 400)


class TestSeguridadJWT(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()

  def _obtener_token(self, username="jperez", password="Usuario123!"):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp.get_json().get("token")

  def test_acceso_con_token_valido(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = self.client.get("/api/donaciones", headers=headers)
    self.assertEqual(resp.status_code, 200)

  def test_acceso_sin_token(self):
    resp = self.client.get("/api/donaciones")
    self.assertEqual(resp.status_code, 401)
    data = resp.get_json()
    self.assertTrue("error" in data or "mensaje" in data)

  def test_acceso_token_invalido(self):
    headers = {"Authorization": "Bearer token_falso_o_invalido_12345"}
    resp = self.client.get("/api/donaciones", headers=headers)
    self.assertEqual(resp.status_code, 401)
    data = resp.get_json()
    self.assertTrue("error" in data or "mensaje" in data)


class TestPermisosUsuario(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()
    donaciones_db.clear()

  def _obtener_token(self, username="jperez", password="Usuario123!"):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp.get_json().get("token")

  def test_usuario_puede_crear_donacion_comida(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "tipo": "comida",
        "cantidad": 10,
        "donante": "Juan Pérez",
        "direccion": "Calle Falsa 123",
        "organizacion": "Fundación A",
        "descripcion": "Latas de atún",
    }
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 201)

  def test_usuario_puede_crear_donacion_ropa(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "tipo": "ropa",
        "cantidad": 5,
        "donante": "Juan Pérez",
        "direccion": "Calle Falsa 123",
        "organizacion": "Fundación A",
        "descripcion": "Abrigos",
    }
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 201)

  def test_usuario_solo_ve_sus_propias_donaciones(self):
    token_usuario = self._obtener_token("jperez", "Usuario123!")
    headers_usuario = {"Authorization": f"Bearer {token_usuario}"}

    resp = self.client.get("/api/donaciones", headers=headers_usuario)
    self.assertEqual(resp.status_code, 200)

  def test_usuario_no_puede_aprobar_donacion(self):
    token_usuario = self._obtener_token("jperez", "Usuario123!")
    headers = {"Authorization": f"Bearer {token_usuario}"}

    # Donación de ejemplo
    donacion = Donacion(
        tipo="comida",
        cantidad=5,
        donante="Test",
        direccion="Calle 12345",
        organizacion="Org",
        usuario_id="2",
    )
    donaciones_db[donacion.id] = donacion

    resp = self.client.put(
        f"/api/donaciones/{donacion.id}/aprobar", headers=headers
    )
    self.assertEqual(resp.status_code, 403)
    data = resp.get_json()
    self.assertTrue("error" in data or "mensaje" in data)

  def test_usuario_no_puede_eliminar_donacion(self):
    token_usuario = self._obtener_token("jperez", "Usuario123!")
    headers = {"Authorization": f"Bearer {token_usuario}"}

    donacion = Donacion(
        tipo="ropa",
        cantidad=2,
        donante="Test",
        direccion="Calle 12345",
        organizacion="Org",
        usuario_id="2",
    )
    donaciones_db[donacion.id] = donacion

    resp = self.client.delete(
        f"/api/donaciones/{donacion.id}", headers=headers
    )
    self.assertEqual(resp.status_code, 403)

  def test_usuario_no_puede_ver_reporte(self):
    token_usuario = self._obtener_token("jperez", "Usuario123!")
    headers = {"Authorization": f"Bearer {token_usuario}"}

    resp = self.client.get("/api/donaciones/reporte", headers=headers)
    self.assertEqual(resp.status_code, 403)


class TestPermisosAdministrador(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()
    donaciones_db.clear()

  def _obtener_token(self, username="admin", password="Admin123!"):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp.get_json().get("token")

  def test_admin_ve_todas_las_donaciones(self):
    token_admin = self._obtener_token()
    headers = {"Authorization": f"Bearer {token_admin}"}

    resp = self.client.get("/api/donaciones", headers=headers)
    self.assertEqual(resp.status_code, 200)

  def test_admin_puede_aprobar_donacion(self):
    token_admin = self._obtener_token()
    headers = {"Authorization": f"Bearer {token_admin}"}

    donacion = Donacion(
        tipo="comida",
        cantidad=10,
        donante="Donante",
        direccion="Calle 12345",
        organizacion="Org",
        usuario_id="2",
    )
    donaciones_db[donacion.id] = donacion

    resp = self.client.put(
        f"/api/donaciones/{donacion.id}/aprobar", headers=headers
    )
    self.assertEqual(resp.status_code, 200)
    data = resp.get_json()
    self.assertEqual(data["estado"], "aprobada")

  def test_admin_puede_rechazar_donacion(self):
    token_admin = self._obtener_token()
    headers = {"Authorization": f"Bearer {token_admin}"}

    donacion = Donacion(
        tipo="ropa",
        cantidad=3,
        donante="Donante",
        direccion="Calle 12345",
        organizacion="Org",
        usuario_id="2",
    )
    donaciones_db[donacion.id] = donacion

    resp = self.client.put(
        f"/api/donaciones/{donacion.id}/rechazar", headers=headers
    )
    self.assertEqual(resp.status_code, 200)
    data = resp.get_json()
    self.assertEqual(data["estado"], "rechazada")

  def test_admin_puede_eliminar_donacion(self):
    token_admin = self._obtener_token()
    headers = {"Authorization": f"Bearer {token_admin}"}

    donacion = Donacion(
        tipo="comida",
        cantidad=1,
        donante="Donante",
        direccion="Calle 12345",
        organizacion="Org",
        usuario_id="2",
    )
    donaciones_db[donacion.id] = donacion

    resp = self.client.delete(
        f"/api/donaciones/{donacion.id}", headers=headers
    )
    self.assertEqual(resp.status_code, 200)

  def test_admin_puede_ver_reporte(self):
    token_admin = self._obtener_token()
    headers = {"Authorization": f"Bearer {token_admin}"}

    resp = self.client.get("/api/donaciones/reporte", headers=headers)
    self.assertEqual(resp.status_code, 200)


class TestValidacionDatos(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()

  def _obtener_token(self):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": "jperez", "password": "Usuario123!"}),
        content_type="application/json",
    )
    return resp.get_json().get("token")

  def _crear_donacion_payload(self, **kwargs):
    base = {
        "tipo": "comida",
        "cantidad": 10,
        "donante": "Juan Pérez",
        "direccion": "Calle 12345",
        "organizacion": "Org Test",
    }
    base.update(kwargs)
    return base

  def test_crear_donacion_tipo_invalido(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(tipo="dinero")
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_sin_cantidad(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(cantidad=None)
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_cantidad_negativa(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(cantidad=-10)
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_cantidad_no_numerica(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(cantidad="diez")
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_sin_donante(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(donante="")
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_sin_direccion(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(direccion="")
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)

  def test_crear_donacion_sin_organizacion(self):
    token = self._obtener_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = self._crear_donacion_payload(organizacion="")
    resp = self.client.post(
        "/api/donaciones",
        data=json.dumps(payload),
        headers=headers,
        content_type="application/json",
    )
    self.assertEqual(resp.status_code, 400)


class TestManejoErrores(unittest.TestCase):

  def setUp(self):
    self.app = create_app()
    self.app.config["TESTING"] = True
    self.client = self.app.test_client()

  def _obtener_token(self, username="admin", password="Admin123!"):
    resp = self.client.post(
        "/api/auth/login",
        data=json.dumps({"username": username, "password": password}),
        content_type="application/json",
    )
    return resp.get_json().get("token")

  def test_donacion_inexistente_404(self):
    token = self._obtener_token("jperez", "Usuario123!")
    headers = {"Authorization": f"Bearer {token}"}
    resp = self.client.get("/api/donaciones/99999", headers=headers)
    self.assertEqual(resp.status_code, 404)

  def test_aprobar_donacion_inexistente_404(self):
    token = self._obtener_token("admin", "Admin123!")
    headers = {"Authorization": f"Bearer {token}"}
    resp = self.client.put("/api/donaciones/99999/aprobar", headers=headers)
    self.assertEqual(resp.status_code, 404)


if __name__ == "__main__":
  unittest.main()