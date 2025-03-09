from flask import Blueprint, jsonify
import re
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

# Crear el Blueprint para modularizar las rutas
recepciones_bp = Blueprint('recepciones', __name__)

@recepciones_bp.route('/recepciones', methods=['GET'])
def listar_recepciones():
    """Obtiene todas las órdenes de recepción que contengan productos con 'ROLLO' desde Odoo"""
    try:
        # Obtener los ID del tipo de picking "Recepciones" (incoming)
        picking_type_ids = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking.type', 'search_read',
            [[('code', '=', 'incoming')]],
            {'fields': ['id'], 'limit': False}
        )
        picking_type_ids = [pt['id'] for pt in picking_type_ids]

        if not picking_type_ids:
            return jsonify({'error': 'No se encontraron tipos de picking para recepciones'}), 404

        # Obtener los IDs de `stock.picking` (recepciones)
        recepciones = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking', 'search_read',
            [[('picking_type_id', 'in', picking_type_ids)]],  # Solo recepciones
            {'fields': ['id', 'name'], 'limit': False}  # Obtener ID y nombre
        )

        if not recepciones:
            return jsonify([])  # No hay recepciones

        # Obtener los IDs de recepciones
        recepcion_ids = [rec['id'] for rec in recepciones]

        # Obtener movimientos de stock que contengan "ROLLO" en el producto
        movimientos = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.move', 'search_read',
            [[('picking_id', 'in', recepcion_ids), ('product_id', 'ilike', 'ROLLO')]],
            {'fields': ['picking_id'], 'limit': False}
        )

        # Obtener los IDs de recepciones que contienen productos con "ROLLO"
        recepciones_con_rollo = {mov['picking_id'][0] for mov in movimientos if mov.get('picking_id')}

        # Filtrar las recepciones que cumplen con el criterio
        resultado = [rec['name'] for rec in recepciones if rec['id'] in recepciones_con_rollo]

        # Función para extraer los números finales de los nombres
        def extraer_numero(name):
            match = re.search(r'(\d+)$', name)  # Busca el número al final
            return int(match.group(0)) if match else 0  # Convierte a entero

        # Ordenar la lista de mayor a menor según los números finales
        resultado_ordenado = sorted(resultado, key=extraer_numero, reverse=True)

        return jsonify(resultado_ordenado)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
