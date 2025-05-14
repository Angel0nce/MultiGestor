from flask import Flask, render_template
from flask_mysqldb import MySQL

# Crear instancia de la aplicación Flask
app = Flask(__name__)

# Configuración de la base de datos MySQL
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = '77954004'
app.config['MYSQL_DB'] = 'tempo'

app.secret_key = 'mysecretkey'

# Inicializar MySQL
mysql = MySQL(app)
app.extensions['mysql'] = mysql

# Registrar Blueprints existentes
from rutas.Ventas import Ventas
from rutas.Inventario import Inventario
from rutas.Reportes import Reportes
from rutas.Pedidos import Pedidos

app.register_blueprint(Ventas, url_prefix='/Ventas')
app.register_blueprint(Inventario, url_prefix='/inventario')
app.register_blueprint(Reportes, url_prefix='/Reportes')
app.register_blueprint(Pedidos, url_prefix='/Pedidos')

# Ruta principal
@app.route('/')
def Principal():
    return render_template('PrincipalI.html')

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
