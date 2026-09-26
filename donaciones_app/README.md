# Módulo de Donaciones — API + Interfaz Gráfica con JWT y control de roles

Aplicación con **Flask** (backend) + **HTML/CSS/JS** (interfaz gráfica) que implementa un módulo de donaciones de **bienes** (comida y ropa — por ahora sin transferencias/dinero) con:

- Autenticación mediante **JWT** (JSON Web Token).
- Reconocimiento de roles **Usuario** y **Administrador**.
- Autorización basada en roles para cada acción.
- Validación de los datos necesarios para cada donación.
- Manejo centralizado de errores.
- Interfaz gráfica que se adapta según el rol de quien inicia sesión.
- Suite de **28 pruebas unitarias automatizadas** (100% exitosas).

> Los datos se guardan **en memoria** (diccionarios de Python). Al reiniciar el servidor, los datos vuelven a su estado inicial (usuarios semilla, sin donaciones).

---

## 1. Instalación y ejecución

```bash
# 1. (Opcional) Crear entorno virtual
python3 -m venv venv
source venv/bin/activate        # En Windows: venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Ejecutar el servidor
python3 app.py
```

- **Interfaz gráfica:** abre tu navegador en **http://127.0.0.1:5000/app**
- **API (JSON):** disponible en `http://127.0.0.1:5000/api/...`

### Usuarios de prueba (semilla)

| Usuario  | Password      | Rol            |
|----------|---------------|----------------|
| `admin`  | `Admin123!`   | administrador  |
| `jperez` | `Usuario123!` | usuario        |

---

## 2. Interfaz gráfica

Al entrar a `/app` verás una pantalla de inicio de sesión. Según el rol del usuario autenticado, la interfaz muestra distintas secciones:

**Vista Usuario:**
- Formulario "Nueva donación" — solo pide los datos necesarios: tipo (Comida/Ropa), cantidad, nombre del donante, organización beneficiaria, dirección y una descripción opcional.
- Al registrar una donación se muestra un mensaje: **"¡Felicidades, donación registrada! Gracias por tu generosidad: esta donación ayudará a muchas personas."**
- Lista de "Mis donaciones" con su estado (pendiente / aprobada / rechazada).
- **No ve** botones de aprobar/rechazar/eliminar ni el reporte general (están ocultos porque el rol no lo permite; y aunque se forzara la petición desde la consola del navegador, el backend la rechaza con 403).

**Vista Administrador:**
- Tarjetas de resumen (totales, pendientes, aprobadas, rechazadas, unidades entregadas por tipo).
- Tabla con **todas** las donaciones de todos los usuarios.
- Botones exclusivos: **Aprobar**, **Rechazar** y **Eliminar** por cada donación.

---

## 3. Tabla de roles y permisos

| Acción                                                | Endpoint                         | Método | Usuario | Administrador |
|--------------------------------------------------------|-----------------------------------|--------|:-------:|:--------------:|
| Iniciar sesión / obtener JWT                            | `/api/auth/login`                | POST   | ✅      | ✅             |
| Registrar una donación (comida o ropa)                  | `/api/donaciones`                | POST   | ✅      | ✅             |
| Ver lista de donaciones (Usuario: solo las propias)      | `/api/donaciones`                | GET    | ✅ (propias) | ✅ (todas) |
| Ver el detalle de una donación propia                    | `/api/donaciones/<id>`           | GET    | ✅      | ✅             |
| Ver el detalle de una donación de otro usuario           | `/api/donaciones/<id>`           | GET    | ❌ (403) | ✅            |
| **Aprobar** una donación                                | `/api/donaciones/<id>/aprobar`   | PUT    | ❌ (403) | ✅ (exclusivo)|
| **Rechazar** una donación                               | `/api/donaciones/<id>/rechazar`  | PUT    | ❌ (403) | ✅ (exclusivo)|
| **Eliminar** una donación                               | `/api/donaciones/<id>`           | DELETE | ❌ (403) | ✅ (exclusivo)|
| **Ver reporte** general (totales por tipo/estado)        | `/api/donaciones/reporte`        | GET    | ❌ (403) | ✅ (exclusivo)|
| Acceder a cualquier endpoint de donaciones sin token     | cualquiera                        | *      | ❌ (401) | ❌ (401)      |

---

## 4. Datos que se piden por cada donación

| Campo          | Obligatorio | Validación aplicada                              |
|----------------|:-----------:|---------------------------------------------------|
| `tipo`         | Sí          | Debe ser `comida` o `ropa`                        |
| `cantidad`     | Sí          | Numérico, mayor a 0 (paquetes para comida, piezas para ropa) |
| `donante`      | Sí          | Texto, mínimo 2 caracteres                        |
| `organizacion` | Sí          | Organización beneficiaria, mínimo 2 caracteres    |
| `direccion`    | Sí          | Dirección de recolección/entrega, mínimo 5 caracteres |
| `descripcion`  | No          | Texto libre (ej. "ropa de invierno para niños")   |

---

## 5. Seguridad implementada

- **Autenticación (JWT):** al iniciar sesión (`/api/auth/login`) se genera un token firmado (HS256) con `sub` (id), `username`, `rol`, `iat` y `exp` (expira en 60 min).
- **Verificación del token:** `token_required` exige el header `Authorization: Bearer <token>`; rechaza solicitudes sin token (401 `TOKEN_MISSING`), con token inválido (401 `TOKEN_INVALID`) o expirado (401 `TOKEN_EXPIRED`).
- **Autorización por rol:** `role_required(*roles)` valida el rol embebido en el JWT; si no coincide, responde 403 `FORBIDDEN`. La interfaz gráfica también oculta los botones que el rol no puede usar, pero la restricción real vive en el backend (defensa en profundidad).
- **Contraseñas:** almacenadas con hash (`werkzeug.security.generate_password_hash`), nunca en texto plano.
- **Validación de datos:** `validar_donacion()` valida tipo, cantidad, donante, organización y dirección; errores devuelven 400 con detalle por campo.
- **Manejo de errores:** handlers centralizados para `ValidationError` (400), 404, 405 y 500.
- **Mismo origen (sin CORS):** la interfaz gráfica se sirve desde el mismo servidor Flask (`/app`), por lo que las peticiones `fetch` a `/api/...` funcionan sin configuración adicional de CORS.

---

## 6. Cómo generar tus evidencias (capturas)

### a) Pruebas unitarias automatizadas
```bash
python3 -m unittest tests.test_donaciones -v
```
Verás 28 pruebas, todas `ok`. Esta salida de terminal es tu **evidencia de pruebas automatizadas** (archivo de referencia: `evidencia_pruebas.txt`).

### b) Inicio de sesión / autenticación (interfaz gráfica)
1. Abre `http://127.0.0.1:5000/app`
2. Ingresa con `admin` / `Admin123!` → captura la pantalla de login y luego el panel de Administrador.
3. Cierra sesión, entra con `jperez` / `Usuario123!` → captura el panel de Usuario (notarás que no ves los botones de aprobar/rechazar ni el reporte).

### c) Evidencia del funcionamiento de JWT
Abre las **herramientas de desarrollador del navegador → pestaña Network**, inicia sesión, y haz clic en la petición `login`: en la respuesta verás el `token` generado. También puedes pegarlo en https://jwt.io para mostrar el payload decodificado (`sub`, `username`, `rol`, `exp`).

### d) Acción permitida para Usuario
Con la sesión de `jperez` activa, llena el formulario "Nueva donación" (Comida o Ropa) y da clic en **Registrar donación** → captura el mensaje de felicitación y la donación apareciendo en "Mis donaciones" con estado *pendiente*.

### e) Acción exclusiva del Administrador
Inicia sesión como `admin`, busca esa donación en la tabla y da clic en **Aprobar** → captura el cambio de estado a *aprobada* y el reporte actualizado.

### f) Usuario NO puede realizar una acción exclusiva de Administrador
Como evidencia adicional (a nivel API, más contundente para el profesor), con la sesión de `jperez`:
```bash
curl -X PUT http://127.0.0.1:5000/api/donaciones/1/aprobar \
  -H "Authorization: Bearer <TOKEN_USUARIO>"
```
Respuesta esperada: **403 Forbidden**, `"code": "FORBIDDEN"`. (En la interfaz gráfica, este botón directamente no se muestra al Usuario, pero el archivo `evidencia_ejecucion.txt` incluido documenta el bloqueo real del backend).

> El archivo **`evidencia_ejecucion.txt`** incluido ya contiene una corrida real contra el servidor (login, JWT, creación de donaciones, bloqueo 403, aprobación 200, reporte, validaciones). Puedes regenerarlo ejecutando `bash generar_evidencia.sh` con el servidor apagado (el script lo levanta y lo apaga automáticamente).

---

## 7. Estructura del proyecto

```
donaciones_app/
├── app.py                       # Factory de la app Flask, registro de blueprints y ruta /app
├── config.py                    # Configuración (SECRET_KEY, algoritmo y expiración JWT)
├── models.py                    # Modelos Usuario/Donacion (tipo comida|ropa) + almacenamiento en memoria
├── auth.py                      # Generación y decodificación de JWT
├── decorators.py                # token_required, role_required
├── errors.py                    # ValidationError + manejadores de error globales
├── routes/
│   ├── auth_routes.py           # POST /api/auth/login
│   └── donaciones_routes.py     # CRUD y acciones sobre donaciones
├── frontend/
│   └── index.html               # Interfaz gráfica (login + vista Usuario/Administrador)
├── tests/
│   └── test_donaciones.py       # 28 pruebas unitarias (unittest)
├── evidencia_ejecucion.txt      # Corrida real de ejemplo (login, JWT, permisos, errores)
├── evidencia_pruebas.txt        # Salida real de la suite de pruebas
├── generar_evidencia.sh         # Script para regenerar evidencia_ejecucion.txt
├── requirements.txt
└── README.md
```

---

## 8. Endpoints completos

| Método | Endpoint                              | Auth | Rol requerido                    | Descripción |
|--------|----------------------------------------|------|-----------------------------------|-------------|
| GET    | `/app`                                 | No   | —                                  | Sirve la interfaz gráfica |
| POST   | `/api/auth/login`                     | No   | —                                  | Autentica y devuelve JWT |
| POST   | `/api/donaciones`                     | Sí   | usuario, administrador            | Crea una donación de comida o ropa |
| GET    | `/api/donaciones`                     | Sí   | usuario, administrador            | Lista donaciones (propias o todas) |
| GET    | `/api/donaciones/<id>`                | Sí   | usuario (propia), administrador   | Detalle de una donación |
| PUT    | `/api/donaciones/<id>/aprobar`        | Sí   | administrador                      | Aprueba una donación |
| PUT    | `/api/donaciones/<id>/rechazar`       | Sí   | administrador                      | Rechaza una donación |
| DELETE | `/api/donaciones/<id>`                | Sí   | administrador                      | Elimina una donación |
| GET    | `/api/donaciones/reporte`             | Sí   | administrador                      | Reporte de totales y unidades por tipo |
