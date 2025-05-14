from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

Reportes = Blueprint('Reportes', __name__, template_folder='templates')

@Reportes.route('/Reportes')
def Reportes1():
    mysql = current_app.extensions.get('mysql')
    cur = mysql.connection.cursor()

    # Productos más vendidos (basado en cantidad en pedidos completados)
    cur.execute('''
        SELECT I.nombre, SUM(P.cantidad) AS total_vendido
        FROM Pedidos P
        JOIN Inventario I ON P.producto_id = I.id
        WHERE P.estado = 'completado'
        GROUP BY P.producto_id
        ORDER BY total_vendido DESC
    ''')
    productos_mas_vendidos = cur.fetchall()

    # Ventas por día
    cur.execute('''
        SELECT DATE(P.fecha) AS dia, SUM(P.cantidad) AS total_vendido
        FROM Pedidos P
        WHERE P.estado = 'completado'
        GROUP BY dia
        ORDER BY total_vendido DESC
    ''')
    ventas_dias = cur.fetchall()
    dia_mas = ventas_dias[0] if ventas_dias else None
    dia_menos = ventas_dias[-1] if ventas_dias else None

    cur.close()

    return render_template('ReportesR.html',
                           productos=productos_mas_vendidos,
                           ventas_dias=ventas_dias,
                           dia_max=dia_mas,
                           dia_min=dia_menos,
                           tipo_mas_vendido=[])  # vacía porque no existe la columna tipo


