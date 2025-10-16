from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
import os
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv

try:
    import psycopg2
    from psycopg2 import IntegrityError
    from psycopg2.extras import DictCursor
    print('✅ psycopg2 importado correctamente')
except ImportError:
    print('❌ psycopg2 no disponible')

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# 🔐 CONFIGURACIÓN DE SEGURIDAD MEJORADA
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-desarrollo-32-caracteres-aqui')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = False  # False para desarrollo HTTP
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'inventario_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

# CORS CONFIGURACIÓN MEJORADA
CORS(app, 
     supports_credentials=True,
     origins=['https://inventario-soluciones-logicas-production.up.railway.app', 'http://localhost:5000', 'http://127.0.0.1:5000'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     expose_headers=['Set-Cookie'])

# --- CONFIGURACIÓN DE SUPABASE ---
DB_HOST = os.environ.get('DB_HOST')
DB_PORT = os.environ.get('DB_PORT')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASS')

def get_db_connection():
    """Establece la conexión con Supabase usando psycopg2."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            port=DB_PORT,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None

# ------------------------------------------------------------------
# MIDDLEWARE DE DEBUG
# ------------------------------------------------------------------
@app.before_request
def debug_session():
    """Debug para ver sesiones en requests de API"""
    if request.endpoint and 'api' in request.endpoint:
        print(f"🔍 {request.method} {request.path} - Session: {dict(session)}")

# ------------------------------------------------------------------
# AUTENTICACIÓN SEGURA
# ------------------------------------------------------------------
@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400

        # 🔐 Usuario hardcodeado temporal para pruebas
        if username == 'admin' and password == 'Admin123!':
            # 🎫 Crear sesión segura
            session.permanent = True
            session['user_id'] = 1
            session['username'] = 'admin'
            session['role'] = 'admin'
            session['name'] = 'Administrador'
            session['login_time'] = datetime.now().isoformat()
            
            print(f"✅ Sesión creada para: {session['username']}")
            
            return jsonify({
                "mensaje": "Login exitoso",
                "user": {
                    "name": "Administrador",
                    "role": "admin"
                }
            })
        else:
            # Delay para prevenir timing attacks
            import time
            time.sleep(0.5)
            return jsonify({"error": "Credenciales inválidas"}), 401
        
    except Exception as e:
        print(f"Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    user = session.get('username', 'Unknown')
    session.clear()
    print(f"✅ Sesión cerrada para: {user}")
    return jsonify({"mensaje": "Logout exitoso"})

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    """Verificar si el usuario está autenticado"""
    if 'user_id' in session:
        return jsonify({
            "authenticated": True,
            "user": {
                "name": session.get('name'),
                "role": session.get('role')
            }
        })
    return jsonify({"authenticated": False}), 401

# ------------------------------------------------------------------
# MIDDLEWARE DE SEGURIDAD
# ------------------------------------------------------------------
def require_auth():
    """Middleware para verificar autenticación"""
    if 'user_id' not in session:
        print("❌ Acceso no autorizado - Sesión inválida")
        return jsonify({"error": "No autorizado"}), 401
    return None

def protected_route(f):
    """Decorator para rutas protegidas"""
    def decorated_function(*args, **kwargs):
        auth_error = require_auth()
        if auth_error:
            return auth_error
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ------------------------------------------------------------------
# RUTAS PROTEGIDAS
# ------------------------------------------------------------------

# ------------------------------------------------------------------
# RUTA PRINCIPAL
# ------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

# ------------------------------------------------------------------
# SERVIR ARCHIVOS ESTÁTICOS
# ------------------------------------------------------------------
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# ------------------------------------------------------------------
# API: OBTENER INVENTARIO DE STOCK
# ------------------------------------------------------------------
@app.route('/api/inventario/stock', methods=['GET'])
@protected_route
def obtener_inventario_stock():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            p."producto_id",
            p."nombre" AS producto,
            tp."tipo_modelo" AS tipo_pieza, 
            p."codigo_sku",
            (
                SELECT COUNT(*) 
                FROM "seriales" s 
                WHERE s."producto_id" = p."producto_id" AND s."estado" = 'ALMACEN'
            ) AS stock_disponible,
            (
                SELECT 
                    s_last."estado" || ' (' || TO_CHAR(s_last."fecha_registro", 'YYYY-MM-DD') || ')' 
                FROM 
                    "seriales" s_last
                WHERE 
                    s_last."producto_id" = p."producto_id"
                ORDER BY 
                    s_last."fecha_registro" DESC 
                LIMIT 1
            ) AS ultima_actividad_desc
        FROM 
            "productos" p
        JOIN 
            "tipos_pieza" tp ON p."tipo_pieza_id" = tp."tipo_id"
        ORDER BY 
            p."nombre";
        """
        
        cur.execute(query)
        inventario = cur.fetchall()
        cur.close()
        
        # Convertir a lista de diccionarios
        inventario_list = []
        for row in inventario:
            inventario_list.append(dict(row))
            
        return jsonify(inventario_list)
    
    except Exception as e:
        print(f"Error de DB en /stock: {e}")
        return jsonify({"error": f"Error al obtener el inventario: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: OBTENER TIPOS DE PIEZA
# ------------------------------------------------------------------
@app.route('/api/inventario/tipos_pieza', methods=['GET'])
@protected_route
def obtener_tipos_pieza():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT "tipo_id", "tipo_modelo"
        FROM "tipos_pieza" 
        ORDER BY "tipo_modelo";
        """
        
        cur.execute(query)
        tipos = cur.fetchall()
        cur.close()
        
        tipos_list = [dict(row) for row in tipos]
        return jsonify(tipos_list)
    
    except Exception as e:
        print(f"Error de DB en /tipos_pieza: {e}")
        return jsonify({"error": f"Error al obtener tipos de pieza: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: OBTENER TODOS LOS PRODUCTOS
# ------------------------------------------------------------------
@app.route('/api/inventario/productos', methods=['GET'])
@protected_route
def obtener_todos_los_productos():
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT "producto_id", "nombre", "codigo_sku", "tipo_pieza_id"
        FROM "productos" 
        ORDER BY "nombre";
        """
        
        cur.execute(query)
        productos = cur.fetchall()
        cur.close()
        
        productos_list = [dict(row) for row in productos]
        return jsonify(productos_list)
    
    except Exception as e:
        print(f"Error de DB en /productos: {e}")
        return jsonify({"error": f"Error al obtener productos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: AGREGAR NUEVO PRODUCTO
# ------------------------------------------------------------------
@app.route('/api/inventario/productos', methods=['POST'])
@protected_route
def agregar_producto():
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'nombre' not in data or 'tipo_pieza_id' not in data or 'codigo_sku' not in data:
            return jsonify({"error": "Faltan datos requeridos (nombre, tipo_pieza_id o codigo_sku)"}), 400

        nombre = data['nombre']
        descripcion = data.get('descripcion', '')
        tipo_pieza_id = data['tipo_pieza_id']
        codigo_sku = data['codigo_sku']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        insert_query = """
        INSERT INTO "productos" ("nombre", "descripcion", "tipo_pieza_id", "codigo_sku")
        VALUES (%s, %s, %s, %s)
        RETURNING "producto_id";
        """
        cur.execute(insert_query, (nombre, descripcion, tipo_pieza_id, codigo_sku))
        
        result = cur.fetchone()
        producto_id = result['producto_id'] if result else None
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Producto {nombre} agregado correctamente",
            "producto_id": producto_id
        }), 201

    except IntegrityError:
        return jsonify({"error": f"El código SKU {codigo_sku} ya existe"}), 409
    except Exception as e:
        print(f"Error de DB en /productos (POST): {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: INGRESAR NUEVO SERIAL
# ------------------------------------------------------------------
@app.route('/api/inventario/serial', methods=['POST'])
@protected_route
def agregar_serial():
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'producto_id' not in data or 'codigo_unico_serial' not in data:
            return jsonify({"error": "Faltan datos (producto_id o codigo_unico_serial)"}), 400

        producto_id = data['producto_id']
        codigo_unico_serial = data['codigo_unico_serial']
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        insert_query = """
        INSERT INTO "seriales" ("producto_id", "codigo_unico_serial", "estado")
        VALUES (%s, %s, 'ALMACEN')
        RETURNING "serial_id";
        """
        cur.execute(insert_query, (producto_id, codigo_unico_serial))
        
        result = cur.fetchone()
        serial_id = result['serial_id'] if result else None
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Serial {codigo_unico_serial} agregado correctamente",
            "serial_id": serial_id
        }), 201

    except IntegrityError:
        return jsonify({"error": f"El serial {codigo_unico_serial} ya existe o el producto_id no es válido"}), 409
    except Exception as e:
        print(f"Error de DB en /serial (POST): {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: OBTENER SERIALES POR PRODUCTO
# ------------------------------------------------------------------
@app.route('/api/inventario/seriales/<int:producto_id>', methods=['GET'])
@protected_route
def obtener_seriales_por_producto(producto_id):
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT "serial_id", "codigo_unico_serial", "estado", 
               TO_CHAR("fecha_registro", 'YYYY-MM-DD HH24:MI') AS ultima_actividad
        FROM "seriales" 
        WHERE "producto_id" = %s AND "estado" = 'ALMACEN'
        ORDER BY "codigo_unico_serial";
        """
        
        cur.execute(query, (producto_id,))
        seriales = cur.fetchall()
        cur.close()
        
        seriales_list = [dict(row) for row in seriales]
        return jsonify(seriales_list)
    
    except Exception as e:
        print(f"Error de DB en /seriales: {e}")
        return jsonify({"error": f"Error al obtener seriales: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# INICIO DE LA APLICACIÓN
# ------------------------------------------------------------------
if __name__ == '__main__':
    print("🚀 Iniciando servidor Flask seguro...")
    print(f"🔐 Usuario: admin")
    print(f"🔐 Contraseña: Admin123!")
    print("🌐 Servidor: http://0.0.0.0:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
