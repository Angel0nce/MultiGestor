from flask import Blueprint, render_template, current_app

Pedidos= Blueprint('Pedidos', __name__, template_folder='templates')

@Pedidos.route('/Pedidos')
def Pedidos1():
    mysql = current_app.extensions.get('mysql')
    cur = mysql.connection.cursor()

    cur.execute('''
        SELECT P.id, I.nombre, P.cantidad, (P.cantidad * I.precio) AS total, P.fecha, P.estado
        FROM Pedidos P
        JOIN Inventario I ON P.producto_id = I.id
        ORDER BY P.fecha DESC
    ''')
    pedidos = cur.fetchall()
    cur.close()

    return render_template('Pedidos.html', titulo_modulo='Órdenes Generadas', pedidos=pedidos)
