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

# 🔐 CONFIGURACIÓN DE SEGURIDAD
app.secret_key = os.environ.get('SECRET_KEY', 'clave-secreta-desarrollo-32-caracteres-aqui')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'  # Solo True en producción
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_DOMAIN'] = None
app.config['SESSION_COOKIE_PATH'] = '/'
app.config['SESSION_COOKIE_NAME'] = 'inventario_session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_REFRESH_EACH_REQUEST'] = True

# CORS CONFIGURACIÓN
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

# --- CONFIGURACIÓN MEJORADA QUE FUNCIONA EN LOCAL Y RENDER ---
def get_db_connection():
    """Establece la conexión con la base de datos - funciona en LOCAL y RENDER"""
    try:
        # 1️⃣ PRIMERO: Intentar con DATABASE_URL de RENDER
        DATABASE_URL = os.environ.get('DATABASE_URL')
        
        if DATABASE_URL:
            # ✅ CONEXIÓN RENDER
            parsed_url = urlparse(DATABASE_URL)
            DB_HOST = parsed_url.hostname
            DB_PORT = parsed_url.port
            DB_NAME = parsed_url.path[1:]  # Eliminar el '/' inicial
            DB_USER = parsed_url.username
            DB_PASS = parsed_url.password
            
            print(f"🔍 CONEXIÓN BD RENDER - Host: {DB_HOST}:{DB_PORT}, User: {DB_USER}, DB: {DB_NAME}")
            
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                connect_timeout=30,
                sslmode='require'
            )
            print("✅ CONEXIÓN A BD RENDER EXITOSA!")
            return conn
        else:
            # 2️⃣ SEGUNDO: Conexión LOCAL con valores por defecto
            DB_HOST = os.environ.get('DB_HOST', 'localhost')
            DB_PORT = os.environ.get('DB_PORT', '5432')
            DB_NAME = os.environ.get('DB_NAME', 'inventario_db')
            DB_USER = os.environ.get('DB_USER', 'postgres')
            DB_PASS = os.environ.get('DB_PASS', 'password')
            
            print(f"🔧 CONEXIÓN LOCAL - Host: {DB_HOST}:{DB_PORT}, DB: {DB_NAME}, User: {DB_USER}")
            
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS,
                port=DB_PORT,
                connect_timeout=30
                # Sin sslmode para desarrollo local
            )
            print("✅ CONEXIÓN A BD LOCAL EXITOSA!")
            return conn
            
    except Exception as e:
        print(f"❌ ERROR CONEXIÓN BD: {str(e)}")
        print("💡 ¿Tienes PostgreSQL corriendo localmente?")
        return None

# ------------------------------------------------------------------
# MIDDLEWARE DE DEBUG
# ------------------------------------------------------------------
@app.before_request
def debug_session():
    """Debug para ver sesiones en TODOS los requests"""
    print(f"🔍 {request.method} {request.path}")
    print(f"🔍 Session: {dict(session)}")
    print(f"🔍 Cookies recibidas: {request.cookies}")

# ------------------------------------------------------------------
# AUTENTICACIÓN
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
                    "role": "admin",
                    "username": "admin"
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
    print(f"🔍 CHECK AUTH - Session: {dict(session)}")
    
    if 'user_id' in session:
        print(f"✅ Usuario autenticado: {session.get('username')}")
        return jsonify({
            "authenticated": True,
            "user": {
                "name": session.get('name'),
                "role": session.get('role'),
                "username": session.get('username')
            }
        })
    else:
        print("❌ Usuario NO autenticado")
        return jsonify({"authenticated": False}), 200

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
# MIDDLEWARE PARA HEADERS DE SEGURIDAD
# ------------------------------------------------------------------
@app.after_request
def after_request(response):
    """Agregar headers de seguridad a todas las respuestas"""
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# ------------------------------------------------------------------
# RUTAS PRINCIPALES
# ------------------------------------------------------------------
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

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
# API: INICIALIZAR TIPOS DE PIEZA PREDEFINIDOS
# ------------------------------------------------------------------
@app.route('/api/inventario/inicializar_tipos', methods=['POST'])
@protected_route
def inicializar_tipos_pieza():
    """Inicializar tipos de pieza predeterminados para Soluciones Lógicas"""
    conn = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Tipos predeterminados para una empresa de informática
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
        
        # Verificar cuáles tipos ya existen
        cur.execute('SELECT "tipo_modelo" FROM "tipos_pieza"')
        tipos_existentes = [row['tipo_modelo'] for row in cur.fetchall()]
        
        # Insertar solo los tipos que no existen
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
            "mensaje": f"Se inicializaron {tipos_insertados} nuevos tipos de producto",
            "tipos_insertados": tipos_insertados,
            "total_tipos": len(tipos_predeterminados)
        })
        
    except Exception as e:
        print(f"Error en /inicializar_tipos: {e}")
        return jsonify({"error": f"Error al inicializar tipos: {str(e)}"}), 500
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
# API: ELIMINAR PRODUCTO
# ------------------------------------------------------------------
@app.route('/api/inventario/productos/<int:producto_id>', methods=['DELETE'])
@protected_route
def eliminar_producto(producto_id):
    conn = None
    try:
        if session.get('role') != 'admin':
            return jsonify({"error": "Solo administradores pueden eliminar productos"}), 403

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Verificar si tiene seriales
        cur.execute('SELECT COUNT(*) as total FROM seriales WHERE producto_id = %s', (producto_id,))
        if cur.fetchone()['total'] > 0:
            return jsonify({"error": "Elimina primero los seriales de este producto"}), 400
        
        # Obtener nombre para el mensaje
        cur.execute('SELECT nombre FROM productos WHERE producto_id = %s', (producto_id,))
        producto = cur.fetchone()
        if not producto:
            return jsonify({"error": "Producto no encontrado"}), 404
        
        # Eliminar
        cur.execute('DELETE FROM productos WHERE producto_id = %s', (producto_id,))
        conn.commit()
        
        return jsonify({"mensaje": f"Producto '{producto['nombre']}' eliminado"})
        
    except Exception as e:
        print(f"Error eliminando producto: {e}")
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
               TO_CHAR("fecha_registro", 'YYYY-MM-DD HH24:MI') AS fecha_ingreso,
               "notas"
        FROM "seriales" 
        WHERE "producto_id" = %s
        ORDER BY "estado", "codigo_unico_serial";
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
# API: ACTUALIZAR ESTADO DE SERIAL
# ------------------------------------------------------------------
@app.route('/api/inventario/serial/<int:serial_id>', methods=['PUT'])
@protected_route
def actualizar_estado_serial(serial_id):
    """Actualizar el estado de un serial (INSTALADO, DAÑADO, RETIRADO)"""
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
        print(f"Error de DB en /serial (PUT): {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# API: ELIMINAR SERIAL (SOLO ADMIN)
# ------------------------------------------------------------------
@app.route('/api/inventario/serial/<int:serial_id>', methods=['DELETE'])
@protected_route
def eliminar_serial(serial_id):
    """Eliminar un serial permanentemente (solo administradores)"""
    conn = None
    try:
        # Verificar si es administrador
        if session.get('role') != 'admin':
            return jsonify({"error": "Solo administradores pueden eliminar seriales"}), 403

        conn = get_db_connection()
        if not conn:
            return jsonify({"error": "No se pudo conectar a la base de datos"}), 500
            
        cur = conn.cursor(cursor_factory=DictCursor)
        
        # Primero obtener información del serial para el mensaje
        cur.execute('SELECT "codigo_unico_serial" FROM "seriales" WHERE "serial_id" = %s', (serial_id,))
        serial = cur.fetchone()
        
        if not serial:
            return jsonify({"error": "Serial no encontrado"}), 404
        
        # Eliminar el serial
        delete_query = 'DELETE FROM "seriales" WHERE "serial_id" = %s'
        cur.execute(delete_query, (serial_id,))
        
        conn.commit()
        cur.close()
        
        return jsonify({
            "mensaje": f"Serial {serial['codigo_unico_serial']} eliminado permanentemente"
        })
        
    except Exception as e:
        print(f"Error de DB en /serial (DELETE): {e}")
        return jsonify({"error": f"Error de base de datos: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# CONSULTAS ESPECÍFICAS PARA SOLUCIONES LÓGICAS
# ------------------------------------------------------------------

@app.route('/api/inventario/stock_bajo', methods=['GET'])
@protected_route
def obtener_stock_bajo():
    """Obtener productos con stock bajo (alerta)"""
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
        stock_bajo = cur.fetchall()
        cur.close()
        
        stock_list = [dict(row) for row in stock_bajo]
        return jsonify(stock_list)
    
    except Exception as e:
        print(f"Error en /stock_bajo: {e}")
        return jsonify({"error": f"Error al obtener stock bajo: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/inventario/estadisticas', methods=['GET'])
@protected_route
def obtener_estadisticas():
    """Obtener estadísticas generales para el dashboard"""
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
        stats = cur.fetchone()
        cur.close()
        
        return jsonify(dict(stats))
    
    except Exception as e:
        print(f"Error en /estadisticas: {e}")
        return jsonify({"error": f"Error al obtener estadísticas: {str(e)}"}), 500
    finally:
        if conn:
            conn.close()

# ------------------------------------------------------------------
# INICIO DE LA APLICACIÓN
# ------------------------------------------------------------------
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    print("🚀 Iniciando servidor Flask para Soluciones Lógicas...")
    print(f"🔐 Usuario: admin")
    print(f"🔐 Contraseña: Admin123!")
    print(f"🌐 Servidor ejecutándose en puerto: {port}")
    print("📦 Sistema de inventario listo para usar!")
    app.run(debug=True, host='0.0.0.0', port=port)