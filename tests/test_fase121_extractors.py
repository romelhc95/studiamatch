import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.core.enrichment_worker import EnrichmentWorker


def _worker():
    return EnrichmentWorker.__new__(EnrichmentWorker)


def _idat_profile():
    return {
        "field_selectors": {
            "official_name": {"selector": "h1", "transform": "text", "confidence": "authoritative"},
            "curriculum_summary": {"selector": ".accordion-timeline", "transform": "accordion_to_bullets", "confidence": "authoritative"},
            "brochure_url": {"selector": "a[download][href$='.pdf'], a[href*='.pdf']", "attribute": "href", "transform": "absolute_url", "confidence": "authoritative"},
        },
        "label_selectors": {
            "Duración": {"container": ".field-name-descripcion", "value_selector": "strong", "field": "duration_text", "transform": "text", "confidence": "authoritative"},
            "Modalidad": {"container": ".field-name-descripcion", "value_selector": "strong", "field": "modality", "transform": "normalize_mode", "fallback": "Presencial", "confidence": "authoritative_or_default"},
            "Horarios": {"container": ".field-name-descripcion", "value_selector": "strong", "field": "schedule_info", "transform": "text", "confidence": "authoritative"},
        },
        "url_type_rules": [
            {
                "match": "/carreras-profesionales-tecnicas/",
                "program_family": "carreras_profesionales_tecnicas",
                "defaults": {"degree_type": "Carrera Técnica", "price_status": "consultar"},
            },
            {
                "match": "/cursos-de-formacion-continua/",
                "program_family": "formacion_continua",
                "defaults": {"degree_type": "Curso", "modality": "Presencial", "price_status": "consultar"},
            },
        ],
    }


def test_idat_professional_career_extracts_authoritative_fields():
    html = """
    <h1>Administración <strong>Bancaria</strong></h1>
    <div class="field-name-descripcion"><p>Modalidad:</p><p><strong>Campus - Virtual</strong></p></div>
    <div class="field-name-descripcion"><p>Duración</p><p><strong>2 años</strong></p></div>
    <div class="accordion accordion-timeline">
      <div class="accordion-item"><h2><button class="accordion-button">Ciclo 1</button></h2><div class="accordion-body"><ul><li>Lectura Comprensiva</li><li>Operaciones Financieras</li></ul></div></div>
    </div>
    <a download href="/sites/default/files/brochure/brochure-administracion-bancaria.pdf">Descargar malla</a>
    """
    worker = _worker()
    values, trace = worker._extract_profile_pillars(
        html,
        _idat_profile(),
        "https://www.idat.edu.pe/carreras-profesionales-tecnicas/administracion-bancaria-y-financiera",
    )
    assert values["official_name"] == "Administración Bancaria"
    assert values["modality"] == "Remoto"
    assert values["duration_text"] == "2 años"
    assert values["duration_months"] == 24
    assert values["degree_type"] == "Carrera Técnica"
    assert values["program_family"] == "carreras_profesionales_tecnicas"
    assert values["brochure_url"] == "https://www.idat.edu.pe/sites/default/files/brochure/brochure-administracion-bancaria.pdf"
    assert values["curriculum_summary"]["pilares"][0].startswith("Ciclo 1:")
    assert any(item["source"].startswith("css:") for item in trace)


def test_idat_continuing_course_uses_segment_defaults_and_schedule():
    html = """
    <h1>Data <strong>Analytics</strong></h1>
    <div class="field-name-descripcion"><p>Duración</p><p><strong>24 horas académicas</strong><br><strong>(1 mes aproximadamente)</strong></p></div>
    <div class="field-name-descripcion"><p>Horarios</p><p><strong>Inicio: 27 de mayo</strong><br><strong>Lunes - Miércoles (7:30 p.m - 9:45 p.m)</strong></p></div>
    <div class="accordion accordion-timeline">
      <div class="accordion-item"><h2><button class="accordion-button">Excel parte 1</button></h2><div class="accordion-body"><ul><li>Excel y Power BI</li><li>Tablas Dinámicas</li></ul></div></div>
      <div class="accordion-item"><h2><button class="accordion-button">Power bi parte 4</button></h2><div class="accordion-body"><ul><li>Visualizaciones</li></ul></div></div>
    </div>
    <a class="btn" download href="/sites/default/files/brochure/data-analytics-2.pdf">Ver Brochure</a>
    """
    worker = _worker()
    values, trace = worker._extract_profile_pillars(
        html,
        _idat_profile(),
        "https://www.idat.edu.pe/cursos-de-formacion-continua/data-analytics-i",
    )
    assert values["official_name"] == "Data Analytics"
    assert values["modality"] == "Presencial"
    assert values["duration_text"] == "24 horas académicas (1 mes aproximadamente)"
    assert values["duration_months"] == 1
    assert values["schedule_info"] == "Inicio: 27 de mayo Lunes - Miércoles (7:30 p.m - 9:45 p.m)"
    assert values["degree_type"] == "Curso"
    assert values["program_family"] == "formacion_continua"
    assert values["brochure_url"] == "https://www.idat.edu.pe/sites/default/files/brochure/data-analytics-2.pdf"
    assert len(values["curriculum_summary"]["pilares"]) == 2
    assert any(item["source"] == "label_fallback:Modalidad" and item["field"] == "modality" for item in trace)


def test_pre_extracted_values_override_llm_output():
    worker = _worker()
    merged = worker._merge_pre_extracted(
        {"official_name": "Wrong", "modality": "Presencial", "categories": []},
        {"official_name": "Data Analytics", "modality": "Remoto", "category_hint": "Tecnología"},
    )
    assert merged["official_name"] == "Data Analytics"
    assert merged["modality"] == "Remoto"
    assert merged["categories"] == ["Tecnología"]
