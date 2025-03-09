# routes/productos_recepcion.py
from flask import Blueprint, jsonify
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

productos_recepcion_bp = Blueprint('productos_recepcion', __name__)

# Aquí está la modificación clave: cambiar <string:...> por <path:...>
@productos_recepcion_bp.route('/recepciones/<path:nombre_recepcion>/productos', methods=['GET'])
def listar_productos_recepcion(nombre_recepcion):
    """Obtiene los productos únicos de una recepción específica"""
    try:
        recepcion = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking', 'search_read',
            [[('name', '=', nombre_recepcion)]],
            {'fields': ['id'], 'limit': 1}
        )

        if not recepcion:
            return jsonify({'error': f'La recepción "{nombre_recepcion}" no existe.'}), 404

        recepcion_id = recepcion[0]['id']

        movimientos = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.move', 'search_read',
            [[('picking_id', '=', recepcion_id)]],
            {'fields': ['product_id'], 'limit': False}
        )

        if not movimientos:
            return jsonify([])

        productos_unicos = list({mov['product_id'][1] for mov in movimientos if mov.get('product_id')})
        productos_unicos.sort()

        return jsonify(productos_unicos)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
