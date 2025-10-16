import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

print("🔍 Probando conexión a Supabase...")
print(f"Host: {os.getenv('DB_HOST')}")
print(f"DB: {os.getenv('DB_NAME')}")
print(f"User: {os.getenv('DB_USER')}")

try:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASS'),
        port=os.getenv('DB_PORT'),
        connect_timeout=10
    )
    print("✅ CONEXIÓN EXITOSA a Supabase!")
    
    # Probar una consulta simple
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM productos")
    count = cur.fetchone()[0]
    print(f"📊 Productos en BD: {count}")
    
    conn.close()
    
except Exception as e:
    print(f"❌ ERROR de conexión: {e}")
    print("💡 Posibles soluciones:")
    print("1. Verifica que DB_HOST, DB_USER, DB_PASS sean correctos")
    print("2. Verifica que tu IP esté autorizada en Supabase")
    print("3. Verifica que la BD esté activa")
