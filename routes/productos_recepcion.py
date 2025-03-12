from flask import Blueprint, jsonify
from odoo_connector import models, ODOO_DB, ODOO_PASSWORD, uid

productos_recepcion_bp = Blueprint('productos_recepcion', __name__)

@productos_recepcion_bp.route('/recepciones/<path:nombre_recepcion>/productos', methods=['GET'])
def listar_productos_recepcion(nombre_recepcion):
    """Obtiene productos con cantidad demandada, cantidad recibida real, estado,
    fecha programada, origen y detalle de lotes + cantidad recibida por cada lote
    de una recepción específica."""
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

            # Cantidad total recibida en este movimiento
            cantidad_realizada = sum(linea['quantity'] for linea in move_lines)

            # Diccionario para almacenar (lote -> cantidad)
            lotes_cantidades = {}
            for linea in move_lines:
                if linea['lot_id']:  # lot_id es un array [id, "nombre_lote"]
                    lote_nombre = linea['lot_id'][1]
                    lotes_cantidades[lote_nombre] = lotes_cantidades.get(lote_nombre, 0.0) + linea['quantity']

            # Si aún no existe el producto en el diccionario, lo creamos
            if producto_nombre not in productos_agrupados:
                productos_agrupados[producto_nombre] = {
                    'producto': producto_nombre,
                    'product_uom_qty': mov['product_uom_qty'],
                    'quantity': cantidad_realizada,
                    'estado': {mov['state']},
                    'scheduled_date': scheduled_date,
                    'origin': origin,
                    'lotes_cantidades': lotes_cantidades
                }
            else:
                # Sumamos cantidades demandadas y recibidas
                productos_agrupados[producto_nombre]['product_uom_qty'] += mov['product_uom_qty']
                productos_agrupados[producto_nombre]['quantity'] += cantidad_realizada
                productos_agrupados[producto_nombre]['estado'].add(mov['state'])

                # Unificamos las cantidades por lote
                for nombre_lote, cant in lotes_cantidades.items():
                    productos_agrupados[producto_nombre]['lotes_cantidades'][nombre_lote] = (
                        productos_agrupados[producto_nombre]['lotes_cantidades'].get(nombre_lote, 0.0) + cant
                    )

        # Construimos el resultado final
        resultado_final = []
        for prod in productos_agrupados.values():
            # Convertimos el diccionario de lotes en una lista de objetos con { 'lote': '...', 'cantidad': ... }
            lotes_list = []
            for lote, cant in prod['lotes_cantidades'].items():
                lotes_list.append({
                    'lote': lote,
                    'cantidad': cant
                })

            # Para el estado, si hay uno solo en el set, lo mostramos directamente.
            # Si son varios, los convertimos en lista.
            estado_final = list(prod['estado'])
            if len(estado_final) == 1:
                estado_final = estado_final[0]

            resultado_final.append({
                'producto': prod['producto'],
                'product_uom_qty': prod['product_uom_qty'],
                'quantity': prod['quantity'],
                'estado': estado_final,
                'scheduled_date': prod['scheduled_date'],
                'origin': prod['origin'],
                'lotes': lotes_list
            })

        # Ordenamos por nombre de producto
        resultado_final.sort(key=lambda x: x['producto'])

        return jsonify(resultado_final)

    except Exception as e:
        return jsonify({'error': str(e)}), 500
