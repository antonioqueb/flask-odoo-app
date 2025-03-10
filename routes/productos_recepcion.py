from flask import Blueprint, jsonify
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

productos_recepcion_bp = Blueprint('productos_recepcion', __name__)

@productos_recepcion_bp.route('/recepciones/<path:nombre_recepcion>/productos', methods=['GET'])
def listar_productos_recepcion(nombre_recepcion):
    """Obtiene productos con cantidad demandada, cantidad recibida real, estado, scheduled_date, origin y lotes de una recepción específica"""
    try:
        recepcion = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.picking', 'search_read',
            [[('name', '=', nombre_recepcion)]],
            {'fields': ['id', 'scheduled_date', 'origin'], 'limit': 1}
        )

        if not recepcion:
            return jsonify({'error': f'La recepción "{nombre_recepcion}" no existe.'}), 404

        recepcion_id = recepcion[0]['id']
        scheduled_date = recepcion[0]['scheduled_date']
        origin = recepcion[0]['origin']

        # Obtener movimientos asociados a la recepción
        movimientos = models.execute_kw(
            ODOO_DB, uid, ODOO_PASSWORD,
            'stock.move', 'search_read',
            [[('picking_id', '=', recepcion_id)]],
            {'fields': ['id', 'product_id', 'product_uom_qty', 'state'], 'limit': False}
        )

        if not movimientos:
            return jsonify([])

        productos_agrupados = {}

        for mov in movimientos:
            move_id = mov['id']
            producto_nombre = mov['product_id'][1]

            # Obtener cantidades reales recibidas desde stock.move.line junto con el lote
            move_lines = models.execute_kw(
                ODOO_DB, uid, ODOO_PASSWORD,
                'stock.move.line', 'search_read',
                [[('move_id', '=', move_id)]],
                {'fields': ['quantity', 'lot_id'], 'limit': False}
            )

            cantidad_realizada = sum(linea['quantity'] for linea in move_lines)
            lotes = {linea['lot_id'][1] for linea in move_lines if linea['lot_id']}  # Capturar los lotes

            if producto_nombre not in productos_agrupados:
                productos_agrupados[producto_nombre] = {
                    'producto': producto_nombre,
                    'product_uom_qty': mov['product_uom_qty'],
                    'quantity': cantidad_realizada,
                    'estado': {mov['state']},
                    'scheduled_date': scheduled_date,
                    'origin': origin,
                    'lotes': lotes  # Guardamos los lotes asociados
                }
            else:
                productos_agrupados[producto_nombre]['product_uom_qty'] += mov['product_uom_qty']
                productos_agrupados[producto_nombre]['quantity'] += cantidad_realizada
                productos_agrupados[producto_nombre]['estado'].add(mov['state'])
                productos_agrupados[producto_nombre]['lotes'].update(lotes)

        resultado_final = []
        for prod in productos_agrupados.values():
            resultado_final.append({
                'producto': prod['producto'],
                'product_uom_qty': prod['product_uom_qty'],
                'quantity': prod['quantity'],
                'estado': list(prod['estado'])[0] if len(prod['estado']) == 1 else list(prod['estado']),
                'scheduled_date': prod['scheduled_date'],
                'origin': prod['origin'],
                'lotes': list(prod['lotes'])  # Convertimos a lista para JSON
            })

        resultado_final.sort(key=lambda x: x['producto'])

        return jsonify(resultado_final)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
