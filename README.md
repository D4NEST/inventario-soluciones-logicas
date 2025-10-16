# Sistema de Gestión de Inventario - Seriales

Sistema completo de gestión de inventario con seguimiento de seriales conectado a Supabase PostgreSQL.

## 🚀 Instalación

1. **Instalar dependencias:**
\`\`\`bash
pip install -r requirements.txt
\`\`\`

2. **Configurar base de datos:**
   - Las credenciales de Supabase ya están configuradas en `app.py`
   - Asegúrate de que las tablas `productos`, `tipos_pieza` y `seriales` existan en tu base de datos

3. **Iniciar el servidor:**
\`\`\`bash
python app.py
\`\`\`

4. **Abrir en el navegador:**
   - Ir a: http://127.0.0.1:5000
   - Usuario: `admin`
   - Contraseña: `admin123`

## 📁 Estructura del Proyecto

\`\`\`
inventario-seriales/
├── app.py                 # Backend Flask con API REST
├── requirements.txt       # Dependencias Python
├── templates/
│   └── index.html        # Frontend HTML
└── static/
    ├── styles.css        # Estilos CSS
    └── app.js            # Lógica JavaScript con llamadas API
\`\`\`

## 🔌 Endpoints de la API

- `GET /api/inventario/stock` - Obtener inventario con stock
- `POST /api/inventario/serial` - Registrar nuevo serial
- `GET /api/inventario/productos` - Listar todos los productos
- `GET /api/inventario/seriales/<producto_id>` - Ver seriales de un producto
- `GET /api/test-db` - Verificar conexión a base de datos

## ✅ Funcionalidades

✅ Login de usuarios
✅ Dashboard con estadísticas en tiempo real
✅ Visualización de inventario desde la base de datos
✅ Registro de seriales en la base de datos
✅ Ver detalle de seriales por producto
✅ Búsqueda y filtrado
✅ Indicadores de stock bajo
✅ Interfaz responsive

## 🔧 Solución de Problemas

Si ves "Error al conectar con la base de datos":
1. Verifica que Flask esté corriendo (`python app.py`)
2. Revisa las credenciales de Supabase en `app.py`
3. Verifica la conexión a internet
4. Prueba el endpoint: http://127.0.0.1:5000/api/test-db
