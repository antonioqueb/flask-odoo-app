from flask import Blueprint, jsonify
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

productos_recepcion_bp = Blueprint('productos_recepcion', __name__)

@productos_recepcion_bp.route('/recepciones/<path:nombre_recepcion>/productos', methods=['GET'])
def listar_productos_recepcion(nombre_recepcion):
    """Obtiene productos con cantidad demandada, cantidad recibida, estado y fecha programada en una recepción específica"""
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

        # Obtener movimientos con datos completos
        movimientos = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.move', 'search_read',
            [[('picking_id', '=', recepcion_id)]],
            {
                'fields': ['product_id', 'product_uom_qty', 'quantity_done', 'state', 'date_expected'],
                'limit': False
            }
        )

        if not movimientos:
            return jsonify([])

        productos_agrupados = {}
        for mov in movimientos:
            clave = mov['product_id'][1]

            if clave not in productos_agrupados:
                productos_agrupados[clave] = {
                    'producto': clave,
                    'product_uom_qty': mov['product_uom_qty'],
                    'quantity': mov['quantity_done'],
                    'estado': {mov['state']},
                    'scheduled_date': {mov['date_expected']}
                }
            else:
                productos_agrupados[clave]['product_uom_qty'] += mov['product_uom_qty']
                productos_agrupados[clave]['quantity'] += mov['quantity_done']
                productos_agrupados[clave]['estado'].add(mov['state'])
                productos_agrupados[clave]['scheduled_date'].add(mov['date_expected'])

        resultado_final = []
        for prod in productos_agrupados.values():
            resultado_final.append({
                'producto': prod['producto'],
                'product_uom_qty': prod['product_uom_qty'],
                'quantity': prod['quantity'],
                'estado': list(prod['estado']) if len(prod['estado']) > 1 else list(prod['estado'])[0],
                'scheduled_date': list(prod['scheduled_date']) if len(prod['scheduled_date']) > 1 else list(prod['scheduled_date'])[0]
            })

        resultado_final = sorted(resultado_final, key=lambda x: x['producto'])

        return jsonify(resultado_final)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
