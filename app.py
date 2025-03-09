from flask import Flask, jsonify
import xmlrpc.client
import os
import re
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de Odoo desde .env
ODOO_URL = os.getenv("ODOO_URL")
ODOO_DB = os.getenv("ODOO_DB")
ODOO_USER = os.getenv("ODOO_USER")
ODOO_PASSWORD = os.getenv("ODOO_PASSWORD")

# Validación de variables
if not all([ODOO_URL, ODOO_DB, ODOO_USER, ODOO_PASSWORD]):
    raise ValueError("Faltan variables de entorno en el archivo .env")

# Autenticación con Odoo
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})

if not uid:
    raise Exception("Error de autenticación con Odoo")

# Conectar con el modelo de Odoo
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

app = Flask(__name__)

@app.route('/recepciones', methods=['GET'])
def listar_recepciones():
    """Obtiene todas las órdenes de recepción y salida desde Odoo y las ordena de mayor a menor por el número final"""
    try:
        # Obtener los ID de los tipos de picking "incoming" (recepciones) y "outgoing" (envíos/salidas)
        picking_types = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking.type', 'search_read',
            [[('code', 'in', ['incoming', 'outgoing'])]],  # Filtra IN y OUT
            {'fields': ['id'], 'limit': False}
        )
        picking_type_ids = [pt['id'] for pt in picking_types]

        if not picking_type_ids:
            return jsonify({'error': 'No se encontraron tipos de picking para recepciones y salidas'}), 404

        # Buscar todas las recepciones y salidas en stock.picking
        recepciones_y_salidas = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking', 'search_read',
            [[('picking_type_id', 'in', picking_type_ids)]],  # Buscar en ambos tipos
            {'fields': ['name'], 'limit': False}  # Sin límite para traer todas
        )

        # Extraer los nombres
        resultado = [rec['name'] for rec in recepciones_y_salidas]

        # Función para extraer los números del final del string
        def extraer_numero(name):
            match = re.search(r'(\d+)$', name)  # Busca el número al final
            return int(match.group(0)) if match else 0  # Convierte a entero

        # Ordenar la lista de mayor a menor según los números finales
        resultado_ordenado = sorted(resultado, key=extraer_numero, reverse=True)

        return jsonify(resultado_ordenado)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv("FLASK_PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
