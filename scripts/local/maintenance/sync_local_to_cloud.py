import os
import sys
import logging
from typing import List, Dict, Any
from datetime import datetime
from decimal import Decimal

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from cloud.shared.db_client import DatabaseClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [SYNC] - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("SmartSync")

def json_serializable(obj):
    """Helper to convert complex types for JSON API."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

def sync_table(local_db: DatabaseClient, cloud_db: DatabaseClient, table: str, on_conflict: str = "id", batch_size: int = 200):
    logger.info(f"🚀 Iniciando sincronización de tabla: {table} (Batch: {batch_size})")
    
    try:
        local_records = local_db.select(table)
        total = len(local_records)
        
        if total == 0:
            logger.info(f"∅ Tabla {table} vacía en local. Saltando.")
            return

        logger.info(f"Found {total} records in local {table}. Sending to cloud...")

        for i in range(0, total, batch_size):
            batch = local_records[i : i + batch_size]
            
            sanitized_batch = []
            for record in batch:
                clean_record = {k: json_serializable(v) for k, v in record.items()}
                
                # Special handling for cleansed_programs large text
                if table == "cleansed_programs" and "clean_description" in clean_record:
                    if clean_record["clean_description"]:
                        clean_record["clean_description"] = clean_record["clean_description"][:2000]
                
                sanitized_batch.append(clean_record)
            
            res = cloud_db.upsert(table, sanitized_batch, on_conflict=on_conflict)
            if res:
                logger.info(f"✅ [CHUNK {i//batch_size + 1}] {len(batch)} registros sincronizados en {table}.")
            else:
                logger.error(f"❌ [CHUNK {i//batch_size + 1}] Error al sincronizar {table}.")
        
    except Exception as e:
        logger.error(f"❌ Fallo crítico en tabla {table}: {e}")

def main():
    # 1. Initialize Clients
    # Local Client (uses DATABASE_URL)
    local_db = DatabaseClient() 
    if not local_db.use_local:
        logger.error("No se detectó DATABASE_URL para conexión local. Abortando.")
        return

    # Cloud Client (force API mode by NOT providing database_url)
    cloud_url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    cloud_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not cloud_url or not cloud_key:
        logger.error("Faltan credenciales de Supabase Cloud (URL/KEY).")
        return
        
    # Initialize forcing API mode (database_url=None)
    cloud_db = DatabaseClient(supabase_url=cloud_url, supabase_key=cloud_key, database_url=None)
    
    if cloud_db.use_local:
        logger.error("El cliente de nube se inicializó en modo local incorrectamente.")
        return

    logger.info("--- SMART SYNC: LOCAL -> SUPABASE FREE ---")
    
    # Order matters for Foreign Keys
    # 1. Master Tables
    sync_table(local_db, cloud_db, "institutions", on_conflict="id")
    sync_table(local_db, cloud_db, "categories", on_conflict="id")
    sync_table(local_db, cloud_db, "category_rules", on_conflict="id")
    sync_table(local_db, cloud_db, "market_salaries", on_conflict="id")
    sync_table(local_db, cloud_db, "crawler_exclusions", on_conflict="id")
    
    # 2. Pipeline Data (Large)
    # We use micro-batches (5) for cleansed_programs to avoid payload size errors in Supabase Free
    # sync_table(local_db, cloud_db, "staging_raw", on_conflict="url", batch_size=20) # Skipped for now
    sync_table(local_db, cloud_db, "cleansed_programs", on_conflict="url", batch_size=5)

    logger.info("🏁 Sincronización finalizada exitosamente.")

if __name__ == "__main__":
    main()
