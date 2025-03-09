from flask import Blueprint, jsonify
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

productos_recepcion_bp = Blueprint('productos_recepcion', __name__)

@productos_recepcion_bp.route('/recepciones/<path:nombre_recepcion>/productos', methods=['GET'])
def listar_productos_recepcion(nombre_recepcion):
    """Obtiene productos con cantidad demandada, cantidad recibida (real), estado y fecha programada en una recepción específica"""
    try:
        # Obtener recepción por nombre
        recepcion = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking', 'search_read',
            [[('name', '=', nombre_recepcion)]],
            {'fields': ['id'], 'limit': 1}
        )

        if not recepcion:
            return jsonify({'error': f'La recepción "{nombre_recepcion}" no existe.'}), 404

        recepcion_id = recepcion[0]['id']

        # Obtener movimientos asociados a la recepción
        movimientos = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.move', 'search_read',
            [[('picking_id', '=', recepcion_id)]],
            {'fields': ['id', 'product_id', 'product_uom_qty', 'state', 'scheduled_date'], 'limit': False}
        )

        if not movimientos:
            return jsonify([])

        productos_agrupados = {}

        for mov in movimientos:
            move_id = mov['id']
            producto_nombre = mov['product_id'][1]

            # Obtener la cantidad recibida REAL desde stock.move.line
            move_lines = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'stock.move.line', 'search_read',
                [[('move_id', '=', move_id)]],
                {'fields': ['qty_done'], 'limit': False}
            )

            cantidad_realizada = sum(linea['qty_done'] for linea in move_lines)

            if producto_nombre not in productos_agrupados:
                productos_agrupados[producto_nombre] = {
                    'producto': producto_nombre,
                    'product_uom_qty': mov['product_uom_qty'],
                    'quantity': cantidad_realizada,
                    'estado': {mov['state']},
                    'scheduled_date': {mov['scheduled_date']}
                }
            else:
                productos_agrupados[producto_nombre]['product_uom_qty'] += mov['product_uom_qty']
                productos_agrupados[producto_nombre]['quantity'] += cantidad_realizada
                productos_agrupados[producto_nombre]['estado'].add(mov['state'])
                productos_agrupados[producto_nombre]['scheduled_date'].add(mov['scheduled_date'])

        # Construir resultado final estructurado
        resultado_final = []
        for prod in productos_agrupados.values():
            resultado_final.append({
                'producto': prod['producto'],
                'product_uom_qty': prod['product_uom_qty'],
                'quantity': prod['quantity'],
                'estado': list(prod['estado'])[0] if len(prod['estado']) == 1 else list(prod['estado']),
                'scheduled_date': list(prod['scheduled_date'])[0] if len(prod['scheduled_date']) == 1 else list(prod['scheduled_date'])
            })

        # Ordenar por nombre de producto
        resultado_final.sort(key=lambda x: x['producto'])

        return jsonify(resultado_final)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
