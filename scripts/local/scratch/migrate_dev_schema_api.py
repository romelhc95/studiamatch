import os
import requests
import psycopg2

DEV_URL = "https://fmcxwoqvxatbrawwtqke.supabase.co"
DEV_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZtY3h3b3F2eGF0YnJhd3d0cWtlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc3NDcyMTkyNywiZXhwIjoyMDkwMjk3OTI3fQ.AoT1r4wOEz0IB67VhyKd2k_BtZkb03n_BTyJutDl0BA"

LOCAL_DB_DSN = "postgresql://postgres:predesarrollo_password@localhost:5432/studiamatch_predesa"

def migrate():
    print("Obteniendo esquema OpenAPI de Supabase Dev...")
    headers = {"apikey": DEV_KEY, "Authorization": f"Bearer {DEV_KEY}"}
    res = requests.get(f"{DEV_URL}/rest/v1/?apikey={DEV_KEY}")
    if res.status_code != 200:
        print("Error obteniendo esquema:", res.text)
        return
    
    openapi = res.json()
    definitions = openapi.get("definitions", {})
    
    print(f"Tablas encontradas: {list(definitions.keys())}")
    
    # Conectar a la BD local
    conn = psycopg2.connect(LOCAL_DB_DSN)
    conn.autocommit = True
    cur = conn.cursor()
    
    # Limpiar BD local (Drop schema public cascade)
    print("Limpiando base de datos local...")
    cur.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO postgres; GRANT ALL ON SCHEMA public TO public;")
    
    # Crear tablas
    # We must sort by dependencies if possible, but OpenAPI doesn't give FKs easily.
    # To avoid FK issues during creation and insertion, we will create tables without FKs first, or just create them as they come since we only use REST.
    
    type_mapping = {
        "integer": "INTEGER",
        "string": "TEXT",
        "boolean": "BOOLEAN",
        "number": "NUMERIC",
        "array": "JSONB" # Fallback
    }

    for table_name, schema in definitions.items():
        # Algunas definiciones OpenAPI en Supabase son vistas o RPCs, pero asumiremos que son tablas
        properties = schema.get("properties", {})
        if not properties:
            continue
            
        columns = []
        for col_name, col_info in properties.items():
            fmt = col_info.get("format", "")
            t = col_info.get("type", "string")
            
            sql_type = "TEXT"
            if t == "integer":
                sql_type = "INTEGER"
            elif t == "boolean":
                sql_type = "BOOLEAN"
            elif t == "number":
                sql_type = "NUMERIC"
            
            if fmt == "uuid":
                sql_type = "UUID"
            elif fmt == "timestamp with time zone" or fmt == "timestamp without time zone":
                sql_type = "TIMESTAMPTZ"
            elif fmt == "jsonb" or fmt == "json":
                sql_type = "JSONB"
            elif fmt == "text" or fmt == "character varying":
                sql_type = "TEXT"
            elif fmt == "bigint":
                sql_type = "BIGINT"
                
            columns.append(f'"{col_name}" {sql_type}')
            
        create_stmt = f'CREATE TABLE IF NOT EXISTS "{table_name}" (\n    ' + ",\n    ".join(columns) + '\n);'
        print(f"Creando tabla {table_name}...")
        try:
            cur.execute(create_stmt)
        except Exception as e:
            print(f"Error creando {table_name}: {e}")
            
    # Migrar datos
    for table_name in definitions.keys():
        print(f"Migrando datos para {table_name}...")
        data_res = requests.get(f"{DEV_URL}/rest/v1/{table_name}?select=*", headers=headers)
        if data_res.status_code != 200:
            print(f"No se pudo leer {table_name} (puede ser una RPC o estar vacía)")
            continue
            
        rows = data_res.json()
        if not rows:
            print(f"Tabla {table_name} vacía.")
            continue
            
        cols = list(rows[0].keys())
        col_names = ", ".join([f'"{c}"' for c in cols])
        placeholders = ", ".join(["%s"] * len(cols))
        insert_stmt = f'INSERT INTO "{table_name}" ({col_names}) VALUES ({placeholders})'
        
        for r in rows:
            values = [r[c] for c in cols]
            try:
                cur.execute(insert_stmt, values)
            except Exception as e:
                print(f"Error insertando en {table_name}: {e}")
                
    print("Migración completada con éxito.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
