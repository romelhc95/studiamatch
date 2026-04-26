import os
import requests
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(".env.local")
url = os.getenv("SUPABASE_URL", os.getenv("SUPABASE_URL"))
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

def analyze_noise():
    print("🤖 Noise AI-Sentinel: Iniciando escaneo de staging_raw...")
    res_inst = requests.get(f"{url}/rest/v1/institutions?select=id,name", headers=headers)
    if res_inst.status_code != 200:
        print("❌ Error obteniendo instituciones")
        return
        
    institutions = {i['id']: i['name'] for i in res_inst.json()}
    
    report_lines = []
    report_lines.append(f"# Reporte de Sugerencias de Exclusión (Noise AI-Sentinel)")
    report_lines.append(f"**Fecha de Análisis:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("\nEste reporte analiza los patrones de URL recurrentes en `staging_raw` que no han resultado en ningún curso válido, sugiriendo su exclusión para optimizar el Harvester.\n")
    
    total_suggestions = 0
    
    for inst_id, inst_name in institutions.items():
        # Obtener URLs crudas
        res_staging = requests.get(f"{url}/rest/v1/staging_raw?institution_id=eq.{inst_id}&select=url", headers=headers)
        if res_staging.status_code != 200: continue
        staging_urls = [r['url'] for r in res_staging.json()]
        
        if not staging_urls: continue
        
        # Obtener URLs legitimas
        res_courses = requests.get(f"{url}/rest/v1/courses?institution_id=eq.{inst_id}&select=url", headers=headers)
        course_urls = [r['url'] for r in res_courses.json()] if res_courses.status_code == 200 else []
        
        # Tokenizar por directorio base
        token_counts = defaultdict(int)
        for u in staging_urls:
            path = urlparse(u).path
            segments = [s for s in path.split('/') if s]
            if not segments: continue
            
            first_folder = f"/{segments[0]}/"
            token_counts[first_folder] += 1
                
        # Filtrar candidatos ruidosos (> 10 apariciones)
        candidates = {k: v for k, v in token_counts.items() if v > 10}
        
        safe_exclusions = []
        for candidate, count in sorted(candidates.items(), key=lambda x: x[1], reverse=True):
            # Validar si este directorio produjo algún curso real
            is_risky = any(candidate in cu for cu in course_urls)
            if not is_risky:
                safe_exclusions.append((candidate, count))
                
        if safe_exclusions:
            report_lines.append(f"## 🏛️ {inst_name}")
            report_lines.append(f"**Total URLs capturadas:** {len(staging_urls)} | **Cursos válidos actuales:** {len(course_urls)}\n")
            report_lines.append("| Patrón Sugerido | Frecuencia (Ruido) | Nivel de Riesgo |")
            report_lines.append("| :--- | :--- | :--- |")
            for pat, count in safe_exclusions:
                report_lines.append(f"| `{pat}` | {count} URLs inútiles | 🟢 Seguro |")
                total_suggestions += 1
            report_lines.append("\n---\n")
            
    if total_suggestions == 0:
        report_lines.append("## ✅ Sistema Limpio\nNo se detectaron nuevos patrones de ruido masivo que requieran atención en este momento.")
        
    # Guardar reporte
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f"docs/data-analyst/reporte_sugerencias_exclusion_{timestamp}.md"
    os.makedirs("docs/data-analyst", exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
        
    print(f"✅ Análisis completado. Reporte generado en: {report_path}")
    print(f"Sugerencias encontradas: {total_suggestions}")
    print("Revisa el informe y si estás de acuerdo, inyectaremos estas reglas en crawler_exclusions.")

if __name__ == "__main__":
    analyze_noise()