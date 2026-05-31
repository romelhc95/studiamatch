#!/usr/bin/env python3
"""Fase 121: Script de revision de perfiles auto-generados.

Lista instituciones con perfil auto_generated=true y pipeline_ready=false
para que un humano los revise y active.

Uso:
    python3 scripts/maintenance/review_autogen_profiles.py
    python3 scripts/maintenance/review_autogen_profiles.py --approve <slug>
"""

import json
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.db_client import get_db_client

db = get_db_client()


def list_autogen():
    profiles = db.select_pipeline(
        'institution_site_profiles',
        filters='auto_generated=eq.true',
        columns='institution_id,site_type,discovery_mode,pipeline_ready,auto_generated,created_at'
    )

    if not profiles:
        print("No hay perfiles auto-generados pendientes de revision.")
        return []

    institutions = db.select('institutions', columns='id,name,slug,website_url')
    inst_map = {i['id']: i for i in institutions}

    print(f"\n{'='*80}")
    print(f"PERFILES AUTO-GENERADOS PENDIENTES DE REVISION ({len(profiles)})")
    print(f"{'='*80}")

    pending = []
    for p in profiles:
        inst = inst_map.get(p['institution_id'], {})
        slug = inst.get('slug', '?')
        name = inst.get('name', 'Desconocida')
        site_type = p.get('site_type', '?')
        discovery = p.get('discovery_mode', '?')
        ready = p.get('pipeline_ready', False)
        status = "LISTO" if ready else "PENDIENTE"

        print(f"\n  [{status}] {name} ({slug})")
        print(f"    site_type: {site_type}")
        print(f"    discovery_mode: {discovery}")
        print(f"    Para aprobar: python3 scripts/maintenance/review_autogen_profiles.py --approve {slug}")

        if not ready:
            pending.append(slug)

    return pending


def approve(slug):
    inst = db.select('institutions', filters=f'slug=eq.{slug}', columns='id,name', limit=1)
    if not inst:
        print(f"Error: institucion '{slug}' no encontrada.")
        return

    inst_id = inst[0]['id']
    db.patch('institution_site_profiles',
             filters=f'institution_id=eq.{inst_id}',
             data={'pipeline_ready': True, 'auto_generated': False})

    print(f"Perfil de '{inst[0]['name']}' ({slug}) aprobado: pipeline_ready=true, auto_generated=false.")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == '--approve':
        approve(sys.argv[2])
    else:
        pending = list_autogen()
        if pending:
            print(f"\nTotal pendientes: {len(pending)}")
        print()
