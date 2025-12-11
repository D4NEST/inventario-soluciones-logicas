from flask import Flask, jsonify, request, send_from_directory, session
from flask_cors import CORS
import os
import bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
from urllib.parse import urlparse

try:
    import psycopg2
    from psycopg2 import IntegrityError
    from psycopg2.extras import DictCursor
    print('✅ psycopg2 importado correctamente')
except ImportError:
    print('❌ psycopg2 no disponible')

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')

# ====================================================================
# 🔐 CONFIGURACIÓN DE SEGURIDAD ADAPTABLE
# ====================================================================
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-desarrollo-32-caracteres-aqui')

# Configuración BASE común
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    SESSION_COOKIE_NAME='inventario_session',
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_REFRESH_EACH_REQUEST=True,
    SESSION_COOKIE_PATH='/',
    SESSION_COOKIE_DOMAIN=None,
)

# 🔄 Configuración DIFERENCIADA por entorno
FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
print(f"🚀 Entorno Flask: {FLASK_ENV}")

if FLASK_ENV == 'production':
    # PRODUCCIÓN (Render.com) - MÁXIMA SEGURIDAD
    app.config.update(
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_DOMAIN=None,
        PREFERRED_URL_SCHEME='https'
    )
    print("🔒 Configuración de PRODUCCIÓN aplicada (HTTPS Only)")
else:
    # DESARROLLO/LOCAL - SEGURO PERO FUNCIONAL
    app.config.update(
        SESSION_COOKIE_SECURE=False,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    print("🔓 Configuración de DESARROLLO aplicada (HTTP permitido)")

# ====================================================================
# CORS CONFIGURACIÓN MEJORADA
# ====================================================================
CORS(app, 
     supports_credentials=True,
     origins=[
         'http://localhost:10000',
         'http://127.0.0.1:10000', 
         'http://192.168.1.112:10000',
         'http://localhost:5000',
         'http://127.0.0.1:5000',
         'https://inventario-soluciones-logicas.onrender.com'
     ],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     expose_headers=['Set-Cookie'])

# ====================================================================
# CONEXIÓN A BASE DE DATOS - OPTIMIZADA
# ====================================================================
def get_db_connection():
    """Establece conexión con PostgreSQL - Optimizada para Render y Local"""
    try:
        # 1️⃣ Intentar con DATABASE_URL de RENDER
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        if DATABASE_URL:
            parsed_url = urlparse(DATABASE_URL)
            conn_params = {
                'host': parsed_url.hostname,
                'database': parsed_url.path[1:],
                'user': parsed_url.username,
                'password': parsed_url.password,
                'port': parsed_url.port,
                'connect_timeout': 30,
                'sslmode': 'require'
            }
            
            conn = psycopg2.connect(**conn_params)
            print("✅ Conexión RENDER exitosa")
            return conn
        else:
            # 2️⃣ Conexión LOCAL
            conn_params = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'database': os.environ.get('DB_NAME', 'inventario_sistema'),
                'user': os.environ.get('DB_USER', 'postgres'),
                'password': os.environ.get('DB_PASS', 'password'),
                'port': os.environ.get('DB_PORT', '5432'),
                'connect_timeout': 30
            }
            
            conn = psycopg2.connect(**conn_params)
            print("✅ Conexión LOCAL exitosa")
            return conn
            
    except Exception as e:
        print(f"❌ ERROR CONEXIÓN BD: {str(e)}")
        return None

# ====================================================================
# MIDDLEWARE MEJORADO
# ====================================================================
@app.before_request
def verificar_entorno():
    """Middleware para logging y debugging"""
    if request.endpoint not in ['health_check', 'static'] and FLASK_ENV != 'production':
        print(f"🔍 {request.method} {request.path}")

@app.after_request
def after_request(response):
    """Headers de seguridad y CORS"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    origin = request.headers.get('Origin', '')
    allowed_origins = [
        'http://localhost:10000',
        'http://127.0.0.1:10000',
        'https://inventario-soluciones-logicas.onrender.com'
    ]
    
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    
    return response

# ====================================================================
# DECORATOR PARA RUTAS PROTEGIDAS
# ====================================================================
def require_auth():
    """Verifica autenticación"""
    if 'user_id' not in session:
        return jsonify({"error": "No autorizado"}), 401
    return None

def protected_route(f):
    """Decorator para rutas que requieren autenticación"""
    def decorated_function(*args, **kwargs):
        auth_error = require_auth()
        if auth_error:
            return auth_error
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# ====================================================================
# HEALTH CHECK
# ====================================================================
@app.route('/health')
def health_check():
    """Health check para Render"""
    return jsonify({
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "environment": FLASK_ENV
    }), 200

# ====================================================================
# RUTAS PRINCIPALES
# ====================================================================
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# ====================================================================
# AUTENTICACIÓN MEJORADA
# ====================================================================
@app.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Login seguro con validación robusta"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Datos JSON requeridos"}), 400
            
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        print(f"🔐 Intento de login: {username}")
        
        if not username or not password:
            return jsonify({"error": "Usuario y contraseña requeridos"}), 400
        
        # 🔐 VALIDACIÓN ROBUSTA
        if username == 'admin' and password == 'Admin123!':
            session.permanent = True
            session['user_id'] = 1
            session['username'] = 'admin'
            session['role'] = 'admin'
            session['name'] = 'Administrador'
            session['login_time'] = datetime.now().isoformat()
            session['last_activity'] = datetime.now().isoformat()
            
            print(f"✅ Login exitoso para: {username}")
            
            return jsonify({
                "mensaje": "Login exitoso",
                "user": {
                    "name": "Administrador",
                    "role": "admin",
                    "username": "admin"
                }
            })
            
        else:
            import time
            time.sleep(0.5)  # Prevenir timing attacks
            print(f"❌ Credenciales inválidas para: {username}")
            return jsonify({"error": "Credenciales inválidas"}), 401
        
    except Exception as e:
        print(f"🔥 Error en login: {e}")
        return jsonify({"error": "Error interno del servidor"}), 500

@app.route('/api/auth/logout', methods=['POST', 'OPTIONS'])
def logout():
    """Cerrar sesión de forma segura"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    user = session.get('username', 'Unknown')
    session.clear()
    print(f"✅ Sesión cerrada para: {user}")
    
    response = jsonify({"mensaje": "Logout exitoso"})
    response.set_cookie(
        key=app.config['SESSION_COOKIE_NAME'],
        value='',
        expires=0,
        path='/'
    )
    return response

@app.route('/api/auth/check', methods=['GET', 'OPTIONS'])
def check_auth():
    """Verificar sesión activa"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    if 'user_id' in session:
        session['last_activity'] = datetime.now().isoformat()
        session.modified = True
        
        return jsonify({
            "authenticated": True,
            "user": {
                "name": session.get('name'),
                "role": session.get('role'),
                "username": session.get('username')
            }
        }), 200
    else:
        return jsonify({"authenticated": False}), 200

# ====================================================================
# API: DIAGNÓSTICO DEL SISTEMA
# ====================================================================
@app.route('/api/debug/database', methods=['GET'])
@protected_route
def debug_database():
    """Diagnóstico de estructura de base de datos"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # 1. Ver estructura
        cur.execute("""
            SELECT table_name, column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_schema = 'public'
            ORDER BY table_name, ordinal_position;
        """)
        estructura = [dict(row) for row in cur.fetchall()]
        
        # 2. Ver datos existentes
        cur.execute("""
            SELECT 
                p.codigo_sku,
                p.nombre,
                COUNT(s.serial_id) as unidades_existentes
            FROM productos p 
            LEFT JOIN seriales s ON p.producto_id = s.producto_id
            GROUP BY p.codigo_sku, p.nombre
            ORDER BY unidades_existentes DESC;
        """)
        datos_productos = [dict(row) for row in cur.fetchall()]
        
        cur.close()
        
        return jsonify({
            "estructura": estructura,
            "datos_productos": datos_productos,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error en debug_database: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER INVENTARIO COMPLETO
# ====================================================================
@app.route('/api/inventario/stock', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_inventario_stock():
    """Obtiene inventario completo con estadísticas"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            p."producto_id",
            p."nombre",
            COALESCE(p."marca", 'No especificada') AS marca,
            COALESCE(p."modelo", 'No especificado') AS modelo,
            tp."tipo_modelo" AS categoria,
            p."codigo_sku",
            p."descripcion",
            -- Totales por estado
            COUNT(s."serial_id") AS total_unidades,
            SUM(CASE WHEN s."estado" = 'ALMACEN' THEN 1 ELSE 0 END) AS en_almacen,
            SUM(CASE WHEN s."estado" = 'INSTALADO' THEN 1 ELSE 0 END) AS instalados,
            SUM(CASE WHEN s."estado" = 'DAÑADO' THEN 1 ELSE 0 END) AS danados,
            SUM(CASE WHEN s."estado" = 'RETIRADO' THEN 1 ELSE 0 END) AS retirados,
            -- Estado de stock
            CASE 
                WHEN COUNT(s."serial_id") = 0 THEN 'SIN_STOCK'
                WHEN SUM(CASE WHEN s."estado" = 'ALMACEN' THEN 1 ELSE 0 END) <= 3 THEN 'BAJO'
                WHEN SUM(CASE WHEN s."estado" = 'ALMACEN' THEN 1 ELSE 0 END) <= 10 THEN 'MEDIO'
                ELSE 'NORMAL'
            END AS nivel_stock
        FROM 
            "productos" p
        JOIN 
            "tipos_pieza" tp ON p."tipo_pieza_id" = tp."tipo_id"
        LEFT JOIN 
            "seriales" s ON p."producto_id" = s."producto_id"
        GROUP BY 
            p."producto_id", p."nombre", p."marca", p."modelo", 
            tp."tipo_modelo", p."codigo_sku", p."descripcion"
        ORDER BY 
            p."marca", p."modelo", p."nombre";
        """
        
        cur.execute(query)
        inventario = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(inventario)
    
    except Exception as e:
        print(f"Error en /stock: {e}")
        return jsonify({"error": f"Error al obtener inventario: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER ESTADÍSTICAS
# ====================================================================
@app.route('/api/inventario/estadisticas', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_estadisticas():
    """Obtiene estadísticas generales del inventario"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            COUNT(DISTINCT p.producto_id) as total_modelos,
            COUNT(DISTINCT s.serial_id) as total_seriales,
            COUNT(DISTINCT CASE WHEN sub.stock_actual <= 3 THEN sub.producto_id END) as modelos_stock_bajo
        FROM productos p
        CROSS JOIN LATERAL (
            SELECT 
                p2.producto_id,
                COUNT(s2.serial_id) as stock_actual
            FROM productos p2
            LEFT JOIN seriales s2 ON p2.producto_id = s2.producto_id AND s2.estado = 'ALMACEN'
            WHERE p2.producto_id = p.producto_id
            GROUP BY p2.producto_id
        ) sub
        LEFT JOIN seriales s ON p.producto_id = s.producto_id;
        """
        
        cur.execute(query)
        stats = dict(cur.fetchone())
        cur.close()
        
        return jsonify(stats)
        
    except Exception as e:
        print(f"Error en /estadisticas: {e}")
        return jsonify({"error": f"Error al obtener estadísticas: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER TIPOS DE PIEZA
# ====================================================================
@app.route('/api/inventario/tipos_pieza', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_tipos_pieza():
    """Obtiene todas las categorías de productos"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
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
        tipos = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(tipos)
    
    except Exception as e:
        print(f"Error en /tipos_pieza: {e}")
        return jsonify({"error": f"Error al obtener tipos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: CREAR NUEVA CATEGORÍA
# ====================================================================
@app.route('/api/inventario/tipos_pieza', methods=['POST', 'OPTIONS'])
@protected_route
def crear_tipo_pieza():
    """Crea una nueva categoría de producto"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'tipo_modelo' not in data:
            return jsonify({"error": "El nombre de la categoría es requerido"}), 400

        tipo_modelo = data['tipo_modelo'].strip()
        
        if not tipo_modelo or len(tipo_modelo) < 2:
            return jsonify({"error": "El nombre debe tener al menos 2 caracteres"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Verificar si ya existe
        cur.execute('SELECT "tipo_id" FROM "tipos_pieza" WHERE LOWER("tipo_modelo") = LOWER(%s)', (tipo_modelo,))
        if cur.fetchone():
            return jsonify({"error": f"La categoría '{tipo_modelo}' ya existe"}), 409
        
        # Insertar
        insert_query = """
        INSERT INTO "tipos_pieza" ("tipo_modelo")
        VALUES (%s)
        RETURNING "tipo_id", "tipo_modelo";
        """
        cur.execute(insert_query, (tipo_modelo,))
        result = dict(cur.fetchone())
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Categoría '{tipo_modelo}' creada exitosamente",
            "tipo": result
        }), 201
        
    except Exception as e:
        print(f"Error en POST /tipos_pieza: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: INICIALIZAR TIPOS PREDETERMINADOS
# ====================================================================
@app.route('/api/inventario/inicializar_tipos', methods=['POST', 'OPTIONS'])
@protected_route
def inicializar_tipos_pieza():
    """Inicializa categorías predeterminadas si no existen"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        tipos_predeterminados = [
            'Computadoras y Laptops',
            'Servidores y Mainframe',
            'Redes y Comunicaciones',
            'Almacenamiento',
            'Componentes de Hardware',
            'Periféricos',
            'Cables y Conectores',
            'Software y Licencias',
            'Equipos de Seguridad',
            'Fuentes de Poder y UPS',
            'Refacciones y Repuestos',
            'Consumibles'
        ]
        
        # Verificar cuáles ya existen
        cur.execute('SELECT "tipo_modelo" FROM "tipos_pieza"')
        tipos_existentes = [row['tipo_modelo'] for row in cur.fetchall()]
        
        # Insertar solo los que no existen
        tipos_insertados = 0
        for tipo in tipos_predeterminados:
            if tipo not in tipos_existentes:
                cur.execute(
                    'INSERT INTO "tipos_pieza" ("tipo_modelo") VALUES (%s)',
                    (tipo,)
                )
                tipos_insertados += 1
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Se inicializaron {tipos_insertados} nuevas categorías",
            "tipos_insertados": tipos_insertados
        })
        
    except Exception as e:
        print(f"Error en /inicializar_tipos: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER TODOS LOS PRODUCTOS
# ====================================================================
@app.route('/api/inventario/productos', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_todos_los_productos():
    """Obtiene lista completa de productos para selects"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
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
        productos = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(productos)
    
    except Exception as e:
        print(f"Error en /productos: {e}")
        return jsonify({"error": f"Error al obtener productos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: AGREGAR NUEVO PRODUCTO (CON MARCA Y MODELO)
# ====================================================================
@app.route('/api/inventario/productos', methods=['POST', 'OPTIONS'])
@protected_route
def agregar_producto():
    """Crea un nuevo producto con marca y modelo"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        required = ['nombre', 'tipo_pieza_id', 'codigo_sku']
        for field in required:
            if field not in data:
                return jsonify({"error": f"Falta campo: {field}"}), 400

        nombre = data['nombre'].strip()
        descripcion = data.get('descripcion', '').strip()
        tipo_pieza_id = int(data['tipo_pieza_id'])
        codigo_sku = data['codigo_sku'].strip()
        marca = data.get('marca', '').strip()
        modelo = data.get('modelo', '').strip()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        insert_query = """
        INSERT INTO "productos" ("nombre", "descripcion", "tipo_pieza_id", "codigo_sku", "marca", "modelo")
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING "producto_id";
        """
        cur.execute(insert_query, (nombre, descripcion, tipo_pieza_id, codigo_sku, marca or None, modelo or None))
        
        result = cur.fetchone()
        producto_id = result['producto_id'] if result else None
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Producto '{nombre}' agregado correctamente",
            "producto_id": producto_id
        }), 201

    except IntegrityError as e:
        return jsonify({"error": "Ya existe un producto similar"}), 409
    except Exception as e:
        print(f"Error agregando producto: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: ELIMINAR PRODUCTO
# ====================================================================
@app.route('/api/inventario/productos/<int:producto_id>', methods=['DELETE', 'OPTIONS'])
@protected_route
def eliminar_producto(producto_id):
    """Elimina un producto y sus seriales asociados"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        if session.get('role') != 'admin':
            return jsonify({"error": "Solo administradores pueden eliminar productos"}), 403

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Obtener nombre para mensaje
        cur.execute('SELECT nombre FROM productos WHERE producto_id = %s', (producto_id,))
        producto = cur.fetchone()
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Eliminar en orden: historial -> seriales -> producto
        cur.execute('DELETE FROM historial_estados WHERE serial_id IN (SELECT serial_id FROM seriales WHERE producto_id = %s)', (producto_id,))
        cur.execute('DELETE FROM seriales WHERE producto_id = %s', (producto_id,))
        cur.execute('DELETE FROM productos WHERE producto_id = %s', (producto_id,))
        
        conn.commit()
        
        return jsonify({"mensaje": f"Producto '{producto['nombre']}' eliminado"})
        
    except Exception as e:
        print(f"Error eliminando producto: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: REGISTRAR NUEVO SERIAL
# ====================================================================
@app.route('/api/inventario/serial', methods=['POST', 'OPTIONS'])
@protected_route
def agregar_serial():
    """Registra un nuevo serial para un producto"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'producto_id' not in data or 'codigo_unico_serial' not in data:
            return jsonify({"error": "Faltan datos (producto_id o codigo_unico_serial)"}), 400

        producto_id = data['producto_id']
        codigo_unico_serial = data['codigo_unico_serial'].strip().upper()
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Verificar si el producto existe
        cur.execute('SELECT nombre FROM productos WHERE producto_id = %s', (producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            return jsonify({"error": f"Producto ID {producto_id} no existe"}), 404
        
        # Verificar si el serial ya existe
        cur.execute('SELECT serial_id FROM seriales WHERE codigo_unico_serial = %s', (codigo_unico_serial,))
        if cur.fetchone():
            return jsonify({
                "error": f"El serial {codigo_unico_serial} ya existe",
                "codigo": "SERIAL_DUPLICADO"
            }), 409
        
        # Insertar
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
            "mensaje": f"Serial {codigo_unico_serial} agregado",
            "serial_id": serial_id,
            "producto": producto['nombre']
        }), 201

    except IntegrityError as e:
        return jsonify({"error": "Error de integridad de datos"}), 409
    except Exception as e:
        print(f"Error agregando serial: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: AGREGAR MÚLTIPLES SERIALES (NUEVO)
# ====================================================================
@app.route('/api/inventario/seriales/lote', methods=['POST', 'OPTIONS'])
@protected_route
def agregar_seriales_lote():
    """Agrega múltiples seriales para un producto en un solo request"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'producto_id' not in data or 'seriales' not in data:
            return jsonify({"error": "Faltan datos (producto_id o seriales)"}), 400

        producto_id = data['producto_id']
        seriales_list = data['seriales']
        estado = data.get('estado', 'ALMACEN')
        
        if not isinstance(seriales_list, list) or len(seriales_list) == 0:
            return jsonify({"error": "'seriales' debe ser una lista no vacía"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Verificar producto
        cur.execute('SELECT nombre FROM productos WHERE producto_id = %s', (producto_id,))
        producto = cur.fetchone()
        if not producto:
            return jsonify({"error": f"Producto ID {producto_id} no existe"}), 404
        
        # Verificar seriales duplicados
        seriales_duplicados = []
        seriales_validos = []
        
        for serial in seriales_list:
            serial_clean = str(serial).strip().upper()
            if not serial_clean:
                continue
                
            cur.execute('SELECT serial_id FROM seriales WHERE codigo_unico_serial = %s', (serial_clean,))
            if cur.fetchone():
                seriales_duplicados.append(serial_clean)
            else:
                seriales_validos.append(serial_clean)
        
        if seriales_duplicados:
            return jsonify({
                "error": "Algunos seriales ya existen",
                "duplicados": seriales_duplicados
            }), 409
        
        # Insertar seriales válidos
        seriales_insertados = []
        for serial in seriales_validos:
            cur.execute("""
                INSERT INTO "seriales" ("producto_id", "codigo_unico_serial", "estado")
                VALUES (%s, %s, %s)
                RETURNING "serial_id", "codigo_unico_serial";
            """, (producto_id, serial, estado))
            
            resultado = cur.fetchone()
            seriales_insertados.append(dict(resultado))
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"{len(seriales_insertados)} seriales agregados a '{producto['nombre']}'",
            "seriales_agregados": seriales_insertados,
            "total_agregado": len(seriales_insertados)
        }), 201
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Error agregando seriales en lote: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER SERIALES POR PRODUCTO
# ====================================================================
@app.route('/api/inventario/seriales/<int:producto_id>', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_seriales_por_producto(producto_id):
    """Obtiene todos los seriales de un producto específico"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT "serial_id", "codigo_unico_serial", "estado", 
               TO_CHAR("fecha_registro", 'YYYY-MM-DD HH24:MI') AS fecha_ingreso,
               "notas"
        FROM "seriales" 
        WHERE "producto_id" = %s
        ORDER BY "estado", "codigo_unico_serial";
        """
        
        cur.execute(query, (producto_id,))
        seriales = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(seriales)
    
    except Exception as e:
        print(f"Error en /seriales: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: ACTUALIZAR ESTADO DE SERIAL
# ====================================================================
@app.route('/api/inventario/serial/<int:serial_id>', methods=['PUT', 'OPTIONS'])
@protected_route
def actualizar_estado_serial(serial_id):
    """Actualiza el estado de un serial específico"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'estado' not in data:
            return jsonify({"error": "Faltan datos (estado)"}), 400

        nuevo_estado = data['estado']
        notas = data.get('notas', '')
        
        # Validar estado
        estados_permitidos = ['ALMACEN', 'INSTALADO', 'DAÑADO', 'RETIRADO']
        if nuevo_estado not in estados_permitidos:
            return jsonify({"error": f"Estado no válido. Permitidos: {estados_permitidos}"}), 400

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        update_query = """
        UPDATE "seriales" 
        SET "estado" = %s, "notas" = %s, "fecha_actualizacion" = CURRENT_TIMESTAMP
        WHERE "serial_id" = %s
        RETURNING "serial_id", "codigo_unico_serial", "estado";
        """
        cur.execute(update_query, (nuevo_estado, notas, serial_id))
        
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "Serial no encontrado"}), 404
            
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Serial {result['codigo_unico_serial']} actualizado a {nuevo_estado}",
            "serial": dict(result)
        })
        
    except Exception as e:
        print(f"Error actualizando serial: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: ELIMINAR SERIAL
# ====================================================================
@app.route('/api/inventario/serial/<int:serial_id>', methods=['DELETE', 'OPTIONS'])
@protected_route
def eliminar_serial(serial_id):
    """Elimina un serial específico"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        if session.get('role') != 'admin':
            return jsonify({"error": "Solo administradores pueden eliminar seriales"}), 403

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Obtener información del serial
        cur.execute('SELECT "codigo_unico_serial" FROM "seriales" WHERE "serial_id" = %s', (serial_id,))
        serial = cur.fetchone()
        
        if not serial:
            return jsonify({"error": "Serial no encontrado"}), 404
        
        # Eliminar primero del historial
        cur.execute('DELETE FROM "historial_estados" WHERE "serial_id" = %s', (serial_id,))
        
        # Eliminar serial
        cur.execute('DELETE FROM "seriales" WHERE "serial_id" = %s', (serial_id,))
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Serial {serial['codigo_unico_serial']} eliminado"
        })
        
    except Exception as e:
        print(f"Error eliminando serial: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER STOCK BAJO
# ====================================================================
@app.route('/api/inventario/stock_bajo', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_stock_bajo():
    """Obtiene productos con stock bajo (3 o menos unidades en almacén)"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            p.producto_id,
            p.nombre,
            p.codigo_sku,
            tp.tipo_modelo,
            COUNT(s.serial_id) as stock_actual
        FROM productos p
        JOIN tipos_pieza tp ON p.tipo_pieza_id = tp.tipo_id
        LEFT JOIN seriales s ON p.producto_id = s.producto_id AND s.estado = 'ALMACEN'
        GROUP BY p.producto_id, p.nombre, p.codigo_sku, tp.tipo_modelo
        HAVING COUNT(s.serial_id) <= 3
        ORDER BY stock_actual ASC;
        """
        
        cur.execute(query)
        stock_bajo = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(stock_bajo)
    
    except Exception as e:
        print(f"Error en /stock_bajo: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: BUSCAR PRODUCTOS
# ====================================================================
@app.route('/api/inventario/buscar', methods=['GET', 'OPTIONS'])
@protected_route
def buscar_productos():
    """Busca productos por nombre, SKU, marca o modelo"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        query = request.args.get('q', '').strip()
        
        if not query or len(query) < 2:
            return jsonify({"error": "Término de búsqueda muy corto (mínimo 2 caracteres)"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        search_query = """
        SELECT 
            p.producto_id,
            p.nombre,
            p.marca,
            p.modelo,
            p.codigo_sku,
            tp.tipo_modelo as categoria,
            COUNT(s.serial_id) as total_unidades,
            SUM(CASE WHEN s.estado = 'ALMACEN' THEN 1 ELSE 0 END) as en_almacen
        FROM productos p
        JOIN tipos_pieza tp ON p.tipo_pieza_id = tp.tipo_id
        LEFT JOIN seriales s ON p.producto_id = s.producto_id
        WHERE p.nombre ILIKE %s 
           OR p.codigo_sku ILIKE %s
           OR p.marca ILIKE %s
           OR p.modelo ILIKE %s
        GROUP BY p.producto_id, p.nombre, p.marca, p.modelo, p.codigo_sku, tp.tipo_modelo
        ORDER BY p.nombre;
        """
        
        search_term = f"%{query}%"
        cur.execute(search_query, (search_term, search_term, search_term, search_term))
        resultados = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify({
            "query": query,
            "resultados": resultados,
            "total": len(resultados)
        })
        
    except Exception as e:
        print(f"Error en búsqueda: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: OBTENER PRODUCTO POR ID
# ====================================================================
@app.route('/api/inventario/productos/<int:producto_id>', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_producto_por_id(producto_id):
    """Obtiene información detallada de un producto específico"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            p.*,
            tp.tipo_modelo as categoria_nombre,
            COUNT(s.serial_id) as total_seriales,
            SUM(CASE WHEN s.estado = 'ALMACEN' THEN 1 ELSE 0 END) as en_almacen
        FROM productos p
        JOIN tipos_pieza tp ON p.tipo_pieza_id = tp.tipo_id
        LEFT JOIN seriales s ON p.producto_id = s.producto_id
        WHERE p.producto_id = %s
        GROUP BY p.producto_id, p.nombre, p.descripcion, p.tipo_pieza_id, 
                 p.codigo_sku, p.marca, p.modelo, p.fecha_registro, 
                 p.fecha_actualizacion, tp.tipo_modelo;
        """
        
        cur.execute(query, (producto_id,))
        producto = cur.fetchone()
        cur.close()
        
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        return jsonify(dict(producto))
        
    except Exception as e:
        print(f"Error obteniendo producto: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
# ====================================================================
# API: OBTENER PRODUCTOS CON STOCK DETALLADO (NUEVO)
# ====================================================================
@app.route('/api/inventario/productos/detallado', methods=['GET', 'OPTIONS'])
@protected_route
def obtener_productos_detallado():
    """Obtiene inventario con detalles de stock por estado - NUEVA VISTA"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        query = """
        SELECT 
            p.producto_id,
            p.nombre,
            p.marca,
            p.modelo,
            p.codigo_sku,
            tp.tipo_modelo as categoria,
            -- Stock por estado
            COUNT(s.serial_id) as total,
            SUM(CASE WHEN s.estado = 'ALMACEN' THEN 1 ELSE 0 END) as almacen,
            SUM(CASE WHEN s.estado = 'INSTALADO' THEN 1 ELSE 0 END) as instalado,
            SUM(CASE WHEN s.estado = 'DAÑADO' THEN 1 ELSE 0 END) as danado,
            SUM(CASE WHEN s.estado = 'RETIRADO' THEN 1 ELSE 0 END) as retirado,
            -- Última actividad
            MAX(s.fecha_registro) as ultima_entrada,
            MAX(s.fecha_actualizacion) as ultima_actualizacion
        FROM productos p
        JOIN tipos_pieza tp ON p.tipo_pieza_id = tp.tipo_id
        LEFT JOIN seriales s ON p.producto_id = s.producto_id
        GROUP BY p.producto_id, p.nombre, p.marca, p.modelo, p.codigo_sku, tp.tipo_modelo
        ORDER BY 
            CASE WHEN p.marca IS NULL THEN 1 ELSE 0 END,
            p.marca,
            CASE WHEN p.modelo IS NULL THEN 1 ELSE 0 END,
            p.modelo,
            p.nombre;
        """
        
        cur.execute(query)
        productos = [dict(row) for row in cur.fetchall()]
        cur.close()
        
        return jsonify(productos)
        
    except Exception as e:
        print(f"❌ Error en /productos/detallado: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ====================================================================
# API: AGREGAR MÚLTIPLES SERIALES (NUEVO)
# ====================================================================
@app.route('/api/inventario/agregar_lote', methods=['POST', 'OPTIONS'])
@protected_route
def agregar_seriales_lote_masivo():
    """Agrega múltiples seriales de una vez para un producto"""
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    
    conn = None
    try:
        data = request.get_json()
        
        if not data or 'producto_id' not in data or 'cantidad' not in data:
            return jsonify({"error": "Faltan datos (producto_id o cantidad)"}), 400

        producto_id = data['producto_id']
        cantidad = int(data['cantidad'])
        estado = data.get('estado', 'ALMACEN')
        
        if cantidad < 1 or cantidad > 100:
            return jsonify({"error": "Cantidad debe estar entre 1 y 100"}), 400
        
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor()
        
        # Obtener SKU del producto
        cur.execute('SELECT codigo_sku FROM productos WHERE producto_id = %s', (producto_id,))
        producto = cur.fetchone()
        
        if not producto:
            return jsonify({"error": f"Producto ID {producto_id} no existe"}), 404
        
        sku_base = producto[0]
        
        # Obtener último número de serial
        cur.execute('''
            SELECT codigo_unico_serial 
            FROM seriales 
            WHERE producto_id = %s 
            AND codigo_unico_serial LIKE %s
            ORDER BY codigo_unico_serial DESC 
            LIMIT 1
        ''', (producto_id, f'{sku_base}-%'))
        
        ultimo_serial = cur.fetchone()
        ultimo_numero = 0
        
        if ultimo_serial:
            import re
            match = re.search(r'(\d+)$', ultimo_serial[0])
            if match:
                ultimo_numero = int(match.group(1))
        
        seriales_creados = []
        
        for i in range(1, cantidad + 1):
            numero_serial = ultimo_numero + i
            codigo_serial = f"{sku_base}-{str(numero_serial).zfill(3)}"
            
            # Insertar serial
            cur.execute('''
                INSERT INTO seriales (producto_id, codigo_unico_serial, estado)
                VALUES (%s, %s, %s)
                RETURNING serial_id
            ''', (producto_id, codigo_serial, estado))
            
            serial_id = cur.fetchone()[0]
            seriales_creados.append({
                'serial_id': serial_id,
                'codigo_serial': codigo_serial,
                'estado': estado
            })
        
        conn.commit()
        cur.close()
        
        return jsonify({
            'mensaje': f'Se agregaron {len(seriales_creados)} seriales',
            'seriales': seriales_creados
        })
        
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Error agregando seriales en lote: {e}")
        return jsonify({"error": f"Error: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()
            
# ====================================================================
# INICIO DE LA APLICACIÓN
# ====================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    
    print("\n" + "="*60)
    print("🚀 SISTEMA DE INVENTARIO - SOLUCIONES LÓGICAS")
    print("="*60)
    print(f"📦 Entorno: {FLASK_ENV}")
    print(f"🔐 Autenticación: Activa")
    print(f"👤 Usuario: admin")
    print(f"🔑 Contraseña: Admin123!")
    print(f"🌐 Puerto: {port}")
    print(f"🔒 Cookie Secure: {app.config['SESSION_COOKIE_SECURE']}")
    print("\n📊 Endpoints disponibles:")
    print(f"   /api/auth/*              - Autenticación")
    print(f"   /api/inventario/*        - Gestión completa")
    print(f"   /api/debug/database      - Diagnóstico")
    print("="*60)
    
    debug_mode = FLASK_ENV != 'production'
    app.run(debug=debug_mode, host='0.0.0.0', port=port)