import asyncio
import os
import sys
import json
import random
from datetime import datetime

# Add root to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'scripts'))

from core.universal_harvester import UniversalHarvester
from shared.db_client import get_db_client
from shared.utils import get_random_user_agent
from playwright.async_api import async_playwright
from curl_cffi.requests import AsyncSession

async def force_harvest_institutions():
    db = get_db_client()
    institutions = [
        {"id": "cf64d254-733d-4a92-8a2d-5df5b9dc80ac", "name": "Universidad del Pacífico", "website_url": "https://www.up.edu.pe"},
        {"id": "ccd04100-1bde-427b-b94f-ab24ae233a2a", "name": "Universidad de Lima", "website_url": "https://www.ulima.edu.pe"}
    ]
    
    async with async_playwright() as p:
        # Usamos chromium para asegurar compatibilidad con sitios modernos
        browser = await p.chromium.launch(headless=True)
        async with AsyncSession() as session:
            for inst_config in institutions:
                inst_id = inst_config["id"]
                print(f"\n--- Procesando: {inst_config['name']} ---")
                
                # Obtener URLs que no tienen HTML
                query = f"institution_id=eq.{inst_id}"
                records = db.select("staging_raw", filters=query)
                
                pending_harvest = [r for r in records if not r.get('raw_html')]
                print(f"Total registros encontrados: {len(records)}")
                print(f"Registros sin HTML para cosechar: {len(pending_harvest)}")
                
                if not pending_harvest:
                    print("No hay nada que cosechar para esta institución.")
                    continue
                
                harvester = UniversalHarvester(inst_config)
                
                for i, record in enumerate(pending_harvest):
                    url = record['url']
                    print(f"[{i+1}/{len(pending_harvest)}] Harvesting: {url}")
                    
                    page = await browser.new_page(user_agent=get_random_user_agent())
                    try:
                        item = await harvester.scrape_course_detail(session, page, url)
                        if item and item.get('raw_html'):
                            item["status"] = "pending" # Reset status for CleansingWorker
                            db.upsert("staging_raw", item, on_conflict="url")
                            print(f"  Successfully harvested: {item.get('raw_name') or 'No Title'}")
                        else:
                            print(f"  Failed to harvest content for {url}")
                    except Exception as e:
                        print(f"  Error processing {url}: {e}")
                    finally:
                        await page.close()
                    
                    # Pequeño delay para ser amables con el servidor
                    await asyncio.sleep(random.uniform(1, 3))
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(force_harvest_institutions())
