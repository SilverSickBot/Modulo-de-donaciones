# 🎁 Módulo de Donaciones — API RESTful

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.x-000000?style=for-the-badge&logo=flask&logoColor=white)
![Pytest](https://img.shields.io/badge/Pytest-Passed-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white)
![Coverage](https://img.shields.io/badge/Coverage-88.5%25-brightgreen?style=for-the-badge)
![Security](https://img.shields.io/badge/OWASP_ZAP-Mitigated-blue?style=for-the-badge)

API RESTful desarrollada en **Python con Flask** para la gestión centralizada de donaciones (alimentos, ropa, etc.), autenticación basada en **JWT (JSON Web Tokens)**, control de acceso basado en roles (**RBAC**), validación estricta de datos y pruebas unitarias automatizadas.

---

## 📋 Tabla de Contenidos

1. [Características Principales](#-características-principales)
2. [Estructura del Proyecto](#-estructura-del-proyecto)
3. [Requisitos Previos](#-requisitos-previos)
4. [Instalación y Configuración](#-instalación-y-configuración)
5. [Ejecución del Servidor](#-ejecución-del-servidor)
6. [Pruebas Automatizadas y Cobertura](#-pruebas-automatizadas-y-cobertura)
7. [Seguridad y Calidad de Código](#-seguridad-y-calidad-de-código)
8. [Endpoints de la API](#-endpoints-de-la-api)

---

## 🚀 Características Principales

* **Autenticación JWT:** Emisión y validación de tokens de acceso seguros.
* **Control de Acceso (RBAC):**
  * **Usuario:** Puede registrar sus propias donaciones y listar sus envíos.
  * **Administrador:** Puede aprobar, rechazar o eliminar cualquier donación y generar reportes consolidados.
* **Validación de Entradas:** Filtrado de datos obligatorios, tipos válidos (`comida`, `ropa`) y cantidades numéricas positivas.
* **Cabeceras de Seguridad HTTP:** Protección contra Clickjacking (`X-Frame-Options`) y MIME Sniffing (`X-Content-Type-Options`).
* **Suite de Pruebas:** 28 pruebas unitarias integradas con reporte de cobertura > 85%.

---

## 📁 Estructura del Proyecto

```text
Modulo donaciones/
└── donaciones_app/
    └── donaciones_app/
        ├── app.py                 # Punto de entrada de la aplicación Flask
        ├── models.py              # Modelos de datos e instancias en memoria
        ├── routes/                # Controladores y endpoints de la API
        │   └── donaciones_routes.py
        ├── tests/                 # Suite de pruebas unitarias
        │   └── test_donaciones.py
        └── requirements.txt       # Dependencias del proyecto
