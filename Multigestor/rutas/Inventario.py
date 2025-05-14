# Inventario.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
import base64
import hashlib
Inventario = Blueprint('Inventario', __name__, template_folder='templates')

# Ruta principal: ver inventario
@Inventario.route('/')
def Principal():
    mysql = current_app.extensions['mysql']
    cur = mysql.connection.cursor()
    cur.execute('SELECT id, Nombre, Cantidad, Precio, Anotaciones, Foto, Codigo FROM Inventario')
    data = cur.fetchall()
    cur.close()

    productos = []
    for item in data:
        producto = list(item)
        if producto[5]:  # Si tiene foto
            producto[5] = base64.b64encode(producto[5]).decode('utf-8')
        productos.append(producto)

    return render_template('PrincipalI.html', Inventarios=productos)

# Ruta para agregar productos
@Inventario.route('/ADD', methods=['GET', 'POST'])
def ADD():
    if request.method == 'POST':
        try:
            # Obtener campos del formulario
            nombre = request.form.get('nombre', '').strip()
            descripcion = request.form.get('descripcion', '').strip()
            cantidad_raw = request.form.get('cantidad')
            precio_raw = request.form.get('precio')
            anotaciones = request.form.get('anotaciones', '').strip()
            file = request.files.get('imagen')
            foto = file.read() if file and file.filename else None

            # Validación de campos obligatorios
            if not nombre or not descripcion or not cantidad_raw or not precio_raw:
                flash("Todos los campos obligatorios deben estar completos.", "danger")
                return redirect(url_for('Inventario.ADD'))

            # Conversión de tipos
            try:
                cantidad = int(cantidad_raw)
                precio = float(precio_raw)
            except ValueError:
                flash("Cantidad o precio inválido.", "danger")
                return redirect(url_for('Inventario.ADD'))

            # Generar código único
            codigo = generar_codigo_unico(nombre, descripcion)

            # Conexión a la base de datos
            mysql = current_app.extensions.get('mysql')
            cur = mysql.connection.cursor()

            # Verificar si ya existe el producto (por código único)
            cur.execute("SELECT id, cantidad FROM Inventario WHERE codigo = %s", (codigo,))
            producto_existente = cur.fetchone()

            if producto_existente:
                # Ya existe: actualizar cantidad
                id_existente, cantidad_actual = producto_existente
                nueva_cantidad = cantidad_actual + cantidad
                cur.execute("UPDATE Inventario SET cantidad = %s WHERE id = %s", (nueva_cantidad, id_existente))
            else:
                # Nuevo producto: insertarlo
                cur.execute("""
                    INSERT INTO Inventario 
                    (codigo, nombre, descripcion, cantidad, precio, anotaciones, foto)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (codigo, nombre, descripcion, cantidad, precio, anotaciones, foto))

            mysql.connection.commit()
            cur.close()

            flash("Producto agregado correctamente.", "success")
            return redirect(url_for('Inventario.Principal'))

        except Exception as e:
            flash(f"Error al agregar el producto: {e}", "danger")
            return redirect(url_for('Inventario.ADD'))

    return render_template('ADD.html', titulo_modulo='Agregar Producto', mostrar_regresar=True)

# Ruta para editar productos
@Inventario.route('/EDIT/<int:id>')
def EDIT(id):
    mysql = current_app.extensions['mysql']
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM Inventario WHERE id = %s', (id,))
    data = cur.fetchone()
    cur.close()

    if not data:
        flash('Producto no encontrado.', 'danger')
        return redirect(url_for('Inventario.Principal'))

    return render_template('EDIT.html', producto=data)

# Ruta para actualizar productos
@Inventario.route('/UPDATE/<int:id>', methods=['POST'])
def UPDATE(id):
    try:
        Nombre = request.form.get('Nombre')
        Cantidad = request.form.get('Cantidad')
        Precio = request.form.get('Precio')
        Anotaciones = request.form.get('Anotaciones')
        file = request.files.get('Imagen')

        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()

        if file and file.filename:
            Foto = file.read()
            query = '''UPDATE Inventario SET Nombre = %s, Cantidad = %s, Precio = %s, Anotaciones = %s, Foto = %s WHERE id = %s'''
            values = (Nombre, Cantidad, Precio, Anotaciones, Foto, id)
        else:
            query = '''UPDATE Inventario SET Nombre = %s, Cantidad = %s, Precio = %s, Anotaciones = %s WHERE id = %s'''
            values = (Nombre, Cantidad, Precio, Anotaciones, id)

        cur.execute(query, values)
        mysql.connection.commit()
        cur.close()

        flash('Producto actualizado correctamente.', 'success')
        return redirect(url_for('Inventario.Principal'))

    except Exception as e:
        flash(f"Error al actualizar el producto: {e}", 'danger')
        return redirect(url_for('Inventario.EDIT', id=id))
    
# Cargar inventario desde Excel
@Inventario.route('/CARGAR', methods=['GET', 'POST'])
def CARGAR():
    mysql = current_app.extensions.get('mysql')

    if request.method == 'POST':
        archivo = request.files['archivo_excel']
        nombre_archivo = archivo.filename

        if archivo and archivo.filename.endswith('.xlsx'):
            # 1. Verificar si el archivo ya fue cargado antes
            cursor = mysql.connection.cursor()
            cursor.execute("SELECT id FROM ArchivosCargados WHERE nombre_archivo = %s", (nombre_archivo,))
            if cursor.fetchone():
                flash('Este archivo ya fue cargado anteriormente.', 'warning')
                return redirect(url_for('Inventario.Principal'))

            # 2. Leer archivo Excel
            df = pd.read_excel(archivo)

            for _, fila in df.iterrows():
                nombre = str(fila['Nombre']).strip()
                descripcion = str(fila.get('Descripcion', '')).strip()
                cantidad = int(fila['Cantidad'])
                precio = float(fila['Precio'])
                codigo = generar_codigo_unico(nombre, descripcion)

                # Buscar si ya existe un producto con el mismo código
                cursor.execute("""
                    SELECT id, cantidad FROM Inventario 
                    WHERE codigo = %s
                """, (codigo,))
                producto = cursor.fetchone()

                if producto:
                    nueva_cantidad = producto[1] + cantidad
                    cursor.execute("UPDATE Inventario SET cantidad = %s WHERE id = %s", (nueva_cantidad, producto[0]))
                else:
                    cursor.execute("""
                        INSERT INTO Inventario (codigo, nombre, descripcion, cantidad, precio)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (codigo, nombre, descripcion, cantidad, precio))

            # 3. Registrar el archivo como procesado
            cursor.execute("INSERT INTO ArchivosCargados (nombre_archivo) VALUES (%s)", (nombre_archivo,))
            mysql.connection.commit()
            cursor.close()

            flash('Inventario cargado correctamente.')
            return redirect(url_for('Inventario.Principal'))

    return render_template('Excel.html', titulo_modulo='Cargar Inventario', mostrar_regresar=True)

@Inventario.route('/Inventario/CargarFactura', methods=['GET', 'POST'])
def cargar_factura():
    if request.method == 'POST':
        if 'archivo' not in request.files:
            flash('No se encontró ningún archivo')
            return redirect(request.url)

        archivo = request.files['archivo']
        if archivo.filename == '':
            flash('Archivo no seleccionado')
            return redirect(request.url)

        nombre_archivo = archivo.filename
        filepath = os.path.join(UPLOAD_FOLDER, nombre_archivo)

        # Comprobación si ya fue cargado antes
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        cur.execute('SELECT COUNT(*) FROM ArchivosCargados WHERE nombre_archivo = %s', (nombre_archivo,))
        if cur.fetchone()[0] > 0:
            flash('Este archivo ya fue cargado anteriormente. Operación cancelada.')
            return redirect(request.url)

        archivo.save(filepath)

        try:
            productos = []
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    tabla = page.extract_table()
                    if tabla:
                        for row in tabla[1:]:
                            if len(row) >= 6:
                                codigo_original = row[0] or None
                                nombre = row[1].strip()
                                descripcion = row[2].strip()
                                cantidad = int(row[3])
                                precio = float(row[4])
                                total = float(row[5])

                                # Si no hay código en el PDF, lo generamos
                                if not codigo_original or codigo_original.lower() == 'none':
                                    base_str = (nombre + descripcion).lower().strip()
                                    hash_code = hashlib.md5(base_str.encode()).hexdigest()[:8].upper()
                                    codigo_generado = f"AUTO-{hash_code}"
                                else:
                                    codigo_generado = codigo_original.strip()

                                productos.append({
                                    'codigo': codigo_generado,
                                    'nombre': nombre,
                                    'descripcion': descripcion,
                                    'cantidad': cantidad,
                                    'precio': precio,
                                    'total': total
                                })

            if not productos:
                flash('No se encontraron productos en la factura')
                return redirect(request.url)

            # Guardar productos
            for prod in productos:
                cur.execute("""
                    SELECT id, cantidad FROM Inventario
                    WHERE codigo = %s AND nombre = %s AND descripcion = %s AND precio = %s
                """, (prod['codigo'], prod['nombre'], prod['descripcion'], prod['precio']))
                resultado = cur.fetchone()

                if resultado:
                    nueva_cantidad = resultado[1] + prod['cantidad']
                    cur.execute("""
                        UPDATE Inventario SET cantidad = %s WHERE id = %s
                    """, (nueva_cantidad, resultado[0]))
                else:
                    cur.execute("""
                        INSERT INTO Inventario (codigo, nombre, descripcion, cantidad, precio, total)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """, (prod['codigo'], prod['nombre'], prod['descripcion'],
                          prod['cantidad'], prod['precio'], prod['total']))

            # Registrar archivo cargado
            cur.execute("INSERT INTO ArchivosCargados (nombre_archivo) VALUES (%s)", (nombre_archivo,))
            mysql.connection.commit()
            cur.close()

            flash('Factura PDF cargada exitosamente')
            return redirect(url_for('Inventario.Principal'))

        except Exception as e:
            flash(f'Error al procesar el archivo: {str(e)}')
            return redirect(request.url)

    return render_template('PDF.html')

# Ruta para eliminar productos
@Inventario.route('/delete/<int:id>')
def deleteP(id):
    try:
        mysql = current_app.extensions['mysql']
        cur = mysql.connection.cursor()
        cur.execute('DELETE FROM Inventario WHERE id = %s', (id,))
        mysql.connection.commit()
        cur.close()
        flash('Producto eliminado correctamente.', 'success')
    except Exception as e:
        flash(f"Error al eliminar el producto: {e}", 'danger')
    return redirect(url_for('Inventario.Principal'))
