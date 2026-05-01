import asyncio
from playwright.async_api import async_playwright
import os
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
import sys
import re

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.utils import (
    clean_course_name,
    infer_course_type,
    standardize_category
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ULimaHarvester")

load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_KEY = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

URIS_BY_SECTION = {
    "pregrado": [
        "https://www.ulima.edu.pe/pregrado/administracion",
        "https://www.ulima.edu.pe/pregrado/comunicacion",
        "https://www.ulima.edu.pe/pregrado/derecho",
        "https://www.ulima.edu.pe/pregrado/ingenieria-ambiental",
        "https://www.ulima.edu.pe/pregrado/ingenieria-industrial",
        "https://www.ulima.edu.pe/pregrado/ingenieria-de-sistemas",
        "https://www.ulima.edu.pe/pregrado/arquitectura",
        "https://www.ulima.edu.pe/pregrado/contabilidad-y-finanzas",
        "https://www.ulima.edu.pe/pregrado/economia",
        "https://www.ulima.edu.pe/pregrado/ingenieria-civil",
        "https://www.ulima.edu.pe/pregrado/ingenieria-mecatronica",
        "https://www.ulima.edu.pe/pregrado/marketing",
    ],
    "maestria": [
        "https://www.ulima.edu.pe/posgrado/maestria/macp",
        "https://www.ulima.edu.pe/posgrado/maestria/mbf",
        "https://www.ulima.edu.pe/posgrado/maestria/mcdn",
        "https://www.ulima.edu.pe/posgrado/maestria/mcgc",
        "https://www.ulima.edu.pe/posgrado/maestria/mde",
        "https://www.ulima.edu.pe/posgrado/maestria/mdop",
        "https://www.ulima.edu.pe/posgrado/maestria/mdie",
        "https://www.ulima.edu.pe/posgrado/maestria/mgi",
        "https://www.ulima.edu.pe/posgrado/maestria/mgc",
        "https://www.ulima.edu.pe/posgrado/maestria/mid",
        "https://www.ulima.edu.pe/posgrado/maestria/mlp",
        "https://www.ulima.edu.pe/posgrado/maestria/mmgc",
        "https://www.ulima.edu.pe/posgrado/maestria/mtpf",
        "https://www.ulima.edu.pe/posgrado/maestria/mba",
    ],
    "doctorado": [
        "https://www.ulima.edu.pe/posgrado/doctorado/da",
        "https://www.ulima.edu.pe/posgrado/doctorado/dc",
        "https://www.ulima.edu.pe/posgrado/doctorado/dge",
    ],
    "idiomas": [
        "https://www.ulima.edu.pe/idiomas/programa-integral-ingles",
        "https://www.ulima.edu.pe/idiomas/english-business",
        "https://www.ulima.edu.pe/idiomas/english-media",
        "https://www.ulima.edu.pe/idiomas/english-engineering",
        "https://www.ulima.edu.pe/idiomas/extension-workshops",
        "https://www.ulima.edu.pe/idiomas/intensive-graduation",
        "https://www.ulima.edu.pe/idiomas/b2-first",
    ],
    "cursos-talleres": [
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-comunicacion-marketing-politico",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-cultura-organizacional",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-presentaciones-alto-impacto",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-alto-impacto-presentaciones",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arbitraje",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-app",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-corporate-compliance",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-legaltech-ia-abogados",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ley-contrataciones-estado",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-obras-impuesto",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-obras-publicas",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-resolucion-conflictos",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-compensacion-total",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-people-analytics",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-domina-tiempo",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-expresate-lidera",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-power-skills",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-soft-skills",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-liderazgo-alto-desempeno",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-fundamental",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-analisis-tecnico",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-elaboracion-presupuestos",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-finanzas-no-especialistas",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-tesoreria",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-riesgo-compliance",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-impuesto-renta",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-control-interno",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-niif",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-inversion-bolsa",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-python-aplicado-finanzas",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-fraude-auditoria-forense",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-bloomberg",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-construccion",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-marca-ia",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-growth-hacking",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-marketing-digital",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-kam",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-negociacion-comercial",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-marketing-digital",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-retail-category-management",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-social-media",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-creadores-contenido",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-metodologias-agiles",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-direccion-supply-chain",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gestion-proyectos",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-mejora-rediseno-procesos",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-planeamiento-estrategico",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/vir-seguridad-salud-trabajo",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-future-thinking",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-arquitectura-soluciones-digitales",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-business-analytics",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-data-analytics",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-visualizacion-datos-power-bi",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-excel",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-gobierno-datos",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-ia-generativa-negocios",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-modernizacion-aplicaciones",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-power-bi-desde-cero",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/cec-transformacion-digital",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-fundamentos-power-bi",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-ia-contenido-textual",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-talent-shift",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-transformacion-digital",
        "https://www.ulima.edu.pe/educacion-ejecutiva/cursos-talleres/taller-sql-decisiones-negocio",
    ],
}

INSTITUTION_SLUG = "universidad-de-lima"

SECTION_LABELS = {
    "pregrado": "Carrera de Pregrado",
    "maestria": "MaestrÃ­a",
    "doctorado": "Doctorado",
    "idiomas": "Idiomas",
    "cursos-talleres": "Curso-Taller",
}

class ULimaHarvester:
    def __init__(self):
        self.institution_slug = INSTITUTION_SLUG
        self.api_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }

    async def scrape_course_detail(self, page, url: str, section: str):
        logger.info(f"[{section}] Scraping: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await asyncio.sleep(3)

            title = None
            title_el = await page.query_selector("h1")
            if title_el:
                title = (await title_el.inner_text()).strip()
            if not title:
                title = await page.title()

            if " | " in title:
                title = title.split(" | ")[0].strip()
            if " - " in title and len(title.split(" - ")) == 2:
                title = title.split(" - ")[0].strip()

            if not title or len(title) < 4:
                logger.warning(f"Invalid title skipped: {title}")
                return None

            description_elements = await page.query_selector_all("p")
            description_text = []
            for el in description_elements:
                txt = (await el.inner_text()).strip()
                if len(txt) > 30:
                    description_text.append(txt)

            description_long = "\n\n".join(description_text[:5])

            mode_map = {
                "pregrado": "Presencial",
                "maestria": "Presencial",
                "doctorado": "Presencial",
                "idiomas": "Presencial",
                "cursos-talleres": "Remoto",
            }

            course_type = SECTION_LABELS.get(section, "Curso")

            return {
                "name": clean_course_name(title),
                "url": url,
                "price_pen": None,
                "price_status": "consultar",
                "mode": mode_map.get(section, "Presencial"),
                "duration": "A consultar",
                "category": standardize_category(title),
                "course_type": course_type,
                "description_long": description_long,
                "target_audience": "",
                "syllabus": "",
                "institution_slug": self.institution_slug,
                "is_verified": True,
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def save_to_db(self, item):
        if not item or not item.get('name'): return

        try:
            inst_url = f"{self.api_url}/institutions?slug=eq.{item['institution_slug']}"
            inst_res = requests.get(inst_url, headers=self.headers).json()

            if not inst_res:
                logger.error(f"Institution {item['institution_slug']} not found.")
                return

            inst_id = inst_res[0]['id']

            course_slug = item['name'].lower().replace(" ", "-").replace("/", "-")[:250]
            course_slug = re.sub(r'[^a-z0-9-]', '', course_slug).lstrip('-') or 'curso'

            course_data = {
                "institution_id": inst_id,
                "name": item['name'],
                "slug": course_slug,
                "url": item['url'],
                "price_pen": item['price_pen'],
                "price_status": item['price_status'],
                "mode": item['mode'],
                "duration": item.get('duration', ''),
                "category": item.get('category', 'General'),
                "course_type": item.get('course_type', 'Curso'),
                "description_long": item.get('description_long', ''),
                "is_active": True,
                "is_verified": True,
                "last_scraped_at": datetime.now().isoformat()
            }

            upsert_headers = self.headers.copy()
            upsert_headers["Prefer"] = "resolution=merge-duplicates"

            res = requests.post(
                f"{self.api_url}/courses?on_conflict=url",
                headers=upsert_headers,
                json=course_data
            )

            if res.status_code in [201, 204, 200]:
                logger.info(f"Saved/Updated: {item['name']}")
            else:
                logger.warning(f"Save issue {item['name']} ({res.status_code}): {res.text[:200]}")

        except Exception as e:
            logger.error(f"Processing error for {item['name']}: {e}")


async def main():
    harvester = ULimaHarvester()
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
        page = await context.new_page()

        total = sum(len(urls) for urls in URIS_BY_SECTION.values())
        processed = 0

        for section, urls in URIS_BY_SECTION.items():
            logger.info(f"--- Section: {section} ({len(urls)} URLs) ---")
            for url in urls:
                data = await harvester.scrape_course_detail(page, url, section)
                if data:
                    harvester.save_to_db(data)
                processed += 1
                logger.info(f"Progress: {processed}/{total}")
                await asyncio.sleep(1)

        await browser.close()
        logger.info(f"ULima Harvest complete. Processed: {processed}/{total}")


if __name__ == "__main__":
    asyncio.run(main())
