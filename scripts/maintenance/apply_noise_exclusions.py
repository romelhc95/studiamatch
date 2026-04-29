import os
import sys
import json
import argparse
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client

db = get_db_client()


def load_from_json(json_path, confidence_filter, institution_name=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    patterns = []
    for entry in data:
        if institution_name and entry['institution_name'].lower() != institution_name.lower():
            continue

        inst_id = entry['institution_id']
        inst_name = entry['institution_name']

        for sug in entry.get('suggestions', []):
            level = sug['confidence']
            if confidence_filter == 'ALL' or level == confidence_filter:
                patterns.append({
                    "institution_id": inst_id,
                    "institution_name": inst_name,
                    "pattern": sug['exclusion'],
                    "reason": f"Noise AI-Sentinel {level} ({sug['frequency']} URLs, 0% conversion)",
                    "frequency": sug['frequency'],
                    "confidence": level
                })

    return patterns


def load_manual_patterns(raw_patterns, institution_id, institution_name="Manual"):
    return [{
        "institution_id": institution_id,
        "institution_name": institution_name,
        "pattern": p.strip(),
        "reason": "Ruido detectado manualmente (Fase 50)",
        "frequency": 0,
        "confidence": "MANUAL"
    } for p in raw_patterns]


def apply_exclusions(patterns, dry_run=False):
    if not patterns:
        print("No hay patrones para aplicar.")
        return 0, 0

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Aplicando {len(patterns)} patrones...\n")

    applied = 0
    skipped = 0

    for p in patterns:
        inst_name = p['institution_name']
        inst_id = p['institution_id']
        pattern = p['pattern']

        existing = db.select('crawler_exclusions',
                             filters=f"institution_id=eq.{inst_id}&pattern=eq.{pattern}")

        if existing and len(existing) > 0:
            if not dry_run:
                print(f"  SKIP (ya existe): {inst_name} -> {pattern}")
            skipped += 1
            continue

        if dry_run:
            print(f"  [DRY-RUN] {inst_name} -> {pattern} ({p['confidence']}, {p['frequency']} URLs)")
            applied += 1
            continue

        result = db.insert('crawler_exclusions', {
            "institution_id": inst_id,
            "pattern": pattern,
            "reason": p['reason']
        })

        if result:
            print(f"  INSERT {inst_name} -> {pattern} ({p['confidence']})")
            applied += 1
        else:
            print(f"  FAIL {inst_name} -> {pattern}")
            skipped += 1

    return applied, skipped


def cleanup_retroactive(patterns, dry_run=False):
    if not patterns:
        return 0

    print(f"\n{'[DRY-RUN] ' if dry_run else ''}Limpieza retroactiva de staging_raw...\n")
    total = 0

    for p in patterns:
        inst_id = p['institution_id']
        pattern = p['pattern']
        clean_p = pattern.replace('/', '')

        count = db.count('staging_raw',
                         filters=f"institution_id=eq.{inst_id}&url=ilike.*{clean_p}*")

        if count == 0:
            continue

        if dry_run:
            print(f"  [DRY-RUN] staging_raw: {count} registros -> {pattern} ({p['institution_name']})")
            total += count
            continue

        result = db.delete('staging_raw',
                           filters=f"institution_id=eq.{inst_id}&url=ilike.*{clean_p}*")
        if result:
            print(f"  DELETE staging_raw: {count} registros -> {pattern} ({p['institution_name']})")
            total += count
        else:
            print(f"  FAIL staging_raw: {pattern} ({p['institution_name']})")

    print(f"\n  Total eliminados: {total}")
    return total


def main():
    parser = argparse.ArgumentParser(description="Apply noise exclusions to crawler_exclusions table.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--json", type=str, help="JSON file from noise_discovery_engine.py")
    src.add_argument("--pattern", type=str, nargs='+', help="Manual pattern(s) to exclude")

    parser.add_argument("--institution", type=str, help="Institution name (filters JSON) or ID (for --pattern)")
    parser.add_argument("--confidence", type=str, default="HIGH",
                        choices=["HIGH", "MEDIUM", "LOW", "ALL"],
                        help="Confidence filter for JSON patterns (default: HIGH)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without applying")
    parser.add_argument("--cleanup", action="store_true", help="Also delete matching staging_raw records")
    args = parser.parse_args()

    patterns = []

    if args.json:
        institution_name = args.institution
        patterns = load_from_json(args.json, args.confidence, institution_name)
        print(f"Cargados {len(patterns)} patrones desde {args.json}")
        if args.confidence != 'ALL':
            print(f"  Filtro: confidence >= {args.confidence}")

    elif args.pattern:
        if not args.institution:
            print("ERROR: --institution required with --pattern")
            sys.exit(1)

        institution_id = args.institution
        try:
            inst = db.select('institutions', filters=f"id=eq.{institution_id}")
            if inst and len(inst) > 0:
                inst_name = inst[0]['name']
            else:
                inst = db.select('institutions', filters=f"name=ilike.*{institution_id}*")
                if inst and len(inst) > 0:
                    inst_name = inst[0]['name']
                    institution_id = inst[0]['id']
                else:
                    print(f"ERROR: Institucion no encontrada: {institution_id}")
                    sys.exit(1)
        except Exception:
            print(f"ERROR: Institucion no encontrada: {institution_id}")
            sys.exit(1)

        patterns = load_manual_patterns(args.pattern, institution_id, inst_name)
        print(f"Cargados {len(patterns)} patrones manuales para {inst_name}")

    if args.dry_run:
        print(">>> MODO DRY-RUN (sin cambios) <<<\n")

    applied, skipped = apply_exclusions(patterns, dry_run=args.dry_run)
    print(f"\nResultados exclusions: {applied} aplicadas, {skipped} saltadas")

    if args.cleanup:
        cleanup_retroactive(patterns, dry_run=args.dry_run)

    if not args.dry_run and applied > 0:
        print("Nota: Los nuevos patrones tomaran efecto en la proxima ejecucion del harvester.")

    print("Done.")


if __name__ == "__main__":
    main()
