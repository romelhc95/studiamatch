import os
import json
import logging
import re
import sys
from datetime import datetime
import requests
from dotenv import load_dotenv

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category,
    slugify,
    standardize_mode
)
from shared.db_client import get_db_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("HarvestProcessor")

load_dotenv()

class HarvestProcessor:
    def __init__(self):
        self.db = get_db_client()
        # Mapeo manual de categorías para poblar filtros rápidamente
        self.cat_map = {
            "Data Science & IA": "d10b87c4-7b95-47ed-9b06-74c36435d4e4",
            "Data Analytics": "31e042f0-1571-4bc7-800e-f63e26820ac0",
            "Marketing y Ventas": "69dae276-bd42-47d2-ad2f-5e0bcb9d2e75",
            "Finanzas y Legal": "028906bf-aa60-47e2-b11f-382073be8f67",
            "Gestión y Agilidad": "4a0de3b6-30de-456e-8301-b1c993d99cfc",
            "Logística y Operaciones": "90866a67-9cf3-45e5-ad74-49dc1cd6cef6",
            "Tecnología": "811644b2-b226-43cd-9a6f-bfca066a1cc2",
            "Desarrollo y Web": "56396b45-7eab-40c1-a373-6187069e33a6"
        }

    def get_pending_records(self, limit=100):
        # Procesar tanto los descubiertos como los que no tienen categoría
        return self.db.select('staging_raw', filters="status=eq.discovered", limit=limit)

    def get_unmapped_courses(self, limit=100):
        return self.db.select('courses', filters="category_id=is.null", limit=limit)

    def process_record(self, record, is_full_course=False):
        if not is_full_course:
            url = record['url']
            raw_name = record.get('raw_name') or url.split('/')[-1].replace('-', ' ').replace('_', ' ').title()
            inst_id = record['institution_id']
            clean_name = clean_course_name(raw_name)
            course_id = None
        else:
            course_id = record['id']
            url = record['url']
            clean_name = record['name']
            inst_id = record['institution_id']

        course_slug = slugify(clean_name)
        course_type = infer_course_type(clean_name)
        
        # Heurística mejorada para categorías
        cat_name = "Tecnología" # Default
        cn = clean_name.lower()
        if any(x in cn for x in ['data', 'analytics', 'bi', 'power bi']): cat_name = "Data Analytics"
        if any(x in cn for x in ['ia', 'inteligencia artificial', 'machine learning', 'python']): cat_name = "Data Science & IA"
        if any(x in cn for x in ['marketing', 'ventas', 'comercial']): cat_name = "Marketing y Ventas"
        if any(x in cn for x in ['finanzas', 'contabilidad', 'tributaria', 'legal', 'niif', 'tesoreria']): cat_name = "Finanzas y Legal"
        if any(x in cn for x in ['gestion', 'proyectos', 'mba', 'administracion', 'liderazgo', 'compliance']): cat_name = "Gestión y Agilidad"
        if any(x in cn for x in ['operaciones', 'logistica', 'compras']): cat_name = "Logística y Operaciones"
        if any(x in cn for x in ['desarrollo', 'web', 'full stack', 'app']): cat_name = "Desarrollo y Web"

        cat_id = self.cat_map.get(cat_name)

        course_data = {
            "institution_id": inst_id,
            "name": clean_name,
            "slug": course_slug,
            "url": url,
            "category_id": cat_id,
            "course_type": course_type,
            "is_active": True,
            "is_verified": True,
            "last_scraped_at": datetime.now().isoformat()
        }

        if course_id:
            res = self.db.patch('courses', filters=f"id=eq.{course_id}", data=course_data)
        else:
            res = self.db.upsert('courses', course_data, on_conflict="url")

        if res:
            logger.info(f"MAPPED: {clean_name} -> {cat_name}")
            if not is_full_course:
                self.db.patch('staging_raw', filters=f"id=eq.{record['id']}", data={"status": "processed"})
        else:
            logger.error(f"FAILED: {url}")

if __name__ == "__main__":
    processor = HarvestProcessor()
    
    # 1. Mapear cursos existentes sin categoría
    logger.info("Fase 1: Mapeando categorías de cursos existentes...")
    existing = processor.get_unmapped_courses(limit=200)
    for r in existing:
        processor.process_record(r, is_full_course=True)

    # 2. Promocionar nuevos
    logger.info("Fase 2: Promocionando nuevos registros desde staging...")
    records = processor.get_pending_records(limit=200)
    for r in records:
        processor.process_record(r)
        
    logger.info("✅ Proceso de normalización completado.")
