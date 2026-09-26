#!/bin/bash
set -e
cd "$(dirname "$0")"

python3 -c "
from app import create_app
app = create_app()
app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
" > server.log 2>&1 &
SERVER_PID=$!
sleep 2

{
echo "=========================================================="
echo "0) INTERFAZ GRAFICA DISPONIBLE"
echo "=========================================================="
echo "GET /app -> debe devolver HTML"
curl -s -o /dev/null -w "HTTP_STATUS: %{http_code}\n" http://127.0.0.1:5000/app
curl -s http://127.0.0.1:5000/app | head -c 200
echo ""
echo ""

echo "=========================================================="
echo "1) LOGIN - ADMINISTRADOR"
echo "=========================================================="
RESP_ADMIN=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"admin","password":"Admin123!"}')
echo "$RESP_ADMIN" | python3 -m json.tool
TOKEN_ADMIN=$(echo "$RESP_ADMIN" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

echo ""
echo "=========================================================="
echo "2) LOGIN - USUARIO"
echo "=========================================================="
RESP_USER=$(curl -s -X POST http://127.0.0.1:5000/api/auth/login -H "Content-Type: application/json" -d '{"username":"jperez","password":"Usuario123!"}')
echo "$RESP_USER" | python3 -m json.tool
TOKEN_USER=$(echo "$RESP_USER" | python3 -c "import sys,json;print(json.load(sys.stdin)['token'])")

echo ""
echo "=========================================================="
echo "3) JWT decodificado"
echo "=========================================================="
python3 -c "import jwt; print('admin ->', jwt.decode('$TOKEN_ADMIN', options={'verify_signature': False}))"
python3 -c "import jwt; print('usuario ->', jwt.decode('$TOKEN_USER', options={'verify_signature': False}))"

echo ""
echo "=========================================================="
echo "4) USUARIO crea donacion de COMIDA (accion permitida)"
echo "=========================================================="
RESP_COMIDA=$(curl -s -X POST http://127.0.0.1:5000/api/donaciones -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d '{"tipo":"comida","cantidad":15,"donante":"Juan Perez","organizacion":"Comedor Comunitario Esperanza","direccion":"Av. Reforma 123, CDMX","descripcion":"Arroz y frijol"}')
echo "$RESP_COMIDA" | python3 -m json.tool
ID_COMIDA=$(echo "$RESP_COMIDA" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

echo ""
echo "=========================================================="
echo "5) USUARIO crea donacion de ROPA (accion permitida)"
echo "=========================================================="
RESP_ROPA=$(curl -s -X POST http://127.0.0.1:5000/api/donaciones -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d '{"tipo":"ropa","cantidad":25,"donante":"Juan Perez","organizacion":"Fundacion Abrigo","direccion":"Calle Hidalgo 45, Monterrey","descripcion":"Ropa de invierno"}')
echo "$RESP_ROPA" | python3 -m json.tool
ID_ROPA=$(echo "$RESP_ROPA" | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")

echo ""
echo "=========================================================="
echo "6) USUARIO intenta APROBAR (accion exclusiva admin) -> 403"
echo "=========================================================="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X PUT http://127.0.0.1:5000/api/donaciones/$ID_COMIDA/aprobar -H "Authorization: Bearer $TOKEN_USER"

echo ""
echo "=========================================================="
echo "7) ADMIN aprueba donacion de comida (accion exclusiva) -> 200"
echo "=========================================================="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X PUT http://127.0.0.1:5000/api/donaciones/$ID_COMIDA/aprobar -H "Authorization: Bearer $TOKEN_ADMIN"

echo ""
echo "=========================================================="
echo "8) ADMIN aprueba donacion de ropa -> 200"
echo "=========================================================="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X PUT http://127.0.0.1:5000/api/donaciones/$ID_ROPA/aprobar -H "Authorization: Bearer $TOKEN_ADMIN"

echo ""
echo "=========================================================="
echo "9) ADMIN consulta reporte (exclusivo) -> 200"
echo "=========================================================="
curl -s http://127.0.0.1:5000/api/donaciones/reporte -H "Authorization: Bearer $TOKEN_ADMIN" | python3 -m json.tool

echo ""
echo "=========================================================="
echo "10) USUARIO consulta 'mis donaciones' (solo ve las suyas)"
echo "=========================================================="
curl -s http://127.0.0.1:5000/api/donaciones -H "Authorization: Bearer $TOKEN_USER" | python3 -m json.tool

echo ""
echo "=========================================================="
echo "11) VALIDACION: tipo invalido -> 400"
echo "=========================================================="
curl -s -w "\nHTTP_STATUS: %{http_code}\n" -X POST http://127.0.0.1:5000/api/donaciones -H "Authorization: Bearer $TOKEN_USER" -H "Content-Type: application/json" -d '{"tipo":"dinero","cantidad":10,"donante":"Juan","organizacion":"X","direccion":"Calle 123"}'

} > evidencia_ejecucion.txt 2>&1

kill $SERVER_PID 2>/dev/null || true
echo "Listo."
