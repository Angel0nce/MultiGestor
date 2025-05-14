# Ventas.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
import base64
from datetime import datetime
import random
import string

Ventas = Blueprint('Ventas', __name__, template_folder='templates')

# Función para generar ID único de grupo de pedido
def generar_id_pedido():
    ahora = datetime.now()
    aleatorio = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"PED{ahora.strftime('%Y%m%d%H%M%S')}{aleatorio}"

# Ruta para mostrar productos
@Ventas.route('/')
def PrincipalV():
    mysql = current_app.extensions.get('mysql')
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, Nombre, Cantidad, Precio, Anotaciones, Foto FROM Inventario')
    data = cur.fetchall()
    cur.close()

    productos = []
    for item in data:
        producto = list(item)
        if producto[5]:  # Si tiene imagen, la convierte a Base64
            producto[5] = base64.b64encode(producto[5]).decode('utf-8')
        productos.append(producto)

    return render_template('PrincipalV.html', titulo_modulo='Gestor de Ventas', Inventarios=productos)

# Ruta para generar pedidos
@Ventas.route('/ORD', endpoint='ORD', methods=['GET', 'POST'])
def ORDEN():
    mysql = current_app.extensions.get('mysql')
    cur = mysql.connection.cursor()

    if request.method == 'POST':
        cliente = request.form.get('cliente')
        producto_ids = request.form.getlist('producto_id[]')
        cantidades = request.form.getlist('cantidad[]')

        # Validación básica
        if not cliente:
            flash('El nombre del cliente es requerido', 'danger')
            return redirect(url_for('venta.ORD'))

        if not producto_ids or len(producto_ids) != len(cantidades):
            flash('Error en los productos seleccionados', 'danger')
            return redirect(url_for('venta.Orden'))

        errores = []
        pedidos_creados = 0
        grupo_id = generar_id_pedido()  # Generar identificador del pedido

        try:
            for i in range(len(producto_ids)):
                producto_id = producto_ids[i]
                try:
                    cantidad = int(cantidades[i])
                    if cantidad <= 0:
                        errores.append(f"Cantidad inválida para el producto {i+1}")
                        continue
                except ValueError:
                    errores.append(f"Cantidad no válida para el producto {i+1}")
                    continue

                # Verificar stock y obtener precio
                cur.execute("""
                    SELECT id, Nombre, Descripcion, Cantidad, Precio 
                    FROM Inventario 
                    WHERE id = %s FOR UPDATE
                """, (producto_id,))
                result = cur.fetchone()

                if not result:
                    errores.append(f"Producto {i+1} no encontrado")
                    continue

                producto_id_db, nombre, descripcion, stock, precio = result

                # Validar código generado a partir del nombre y descripción
                codigo_generado = generar_codigo_unico_producto(nombre, descripcion)
                cur.execute("SELECT COUNT(*) FROM Inventario WHERE id = %s AND codigo = %s", (producto_id_db, codigo_generado))
                valido = cur.fetchone()[0]

                if valido == 0:
                    errores.append(f"Producto '{nombre}' tiene un código inválido o corrupto")
                    continue

                if stock < cantidad:
                    errores.append(f"Stock insuficiente de {nombre}. Disponible: {stock}")
                    continue

                # Crear pedido individual con ID de grupo
                cur.execute("""
                    INSERT INTO Pedidos 
                    (cliente, producto_id, cantidad, estado, pedido_grupo_id) 
                    VALUES (%s, %s, %s, 'pendiente', %s)
                """, (cliente, producto_id, cantidad, grupo_id))

                # Actualizar inventario
                cur.execute("""
                    UPDATE Inventario 
                    SET Cantidad = Cantidad - %s 
                    WHERE id = %s
                """, (cantidad, producto_id))

                pedidos_creados += 1

            if errores:
                mysql.connection.rollback()
                for error in errores:
                    flash(error, 'danger')
            else:
                mysql.connection.commit()
                flash(f'Se crearon {pedidos_creados} pedidos correctamente. ID: {grupo_id}', 'success')
                return redirect(url_for('venta.Principal1'))

        except Exception as e:
            mysql.connection.rollback()
            flash(f'Error al procesar los pedidos: {str(e)}', 'danger')

        return redirect(url_for('venta.ORD'))

    # GET: Mostrar formulario
    cur.execute("""
        SELECT id, Nombre, Precio 
        FROM Inventario 
        WHERE Cantidad > 0
        ORDER BY Nombre
    """)
    productos = cur.fetchall()
    cur.close()

    return render_template('Orden.html',
                           titulo_modulo='Gestor de Ordenes',
                           productos=productos)
