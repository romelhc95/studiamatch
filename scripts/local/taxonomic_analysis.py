import subprocess
import json
import os

def run_query(query):
    command = [
        "docker", "exec", "studiamatch-db-predesa",
        "psql", "-U", "postgres", "-d", "studiamatch_predesa", "-t", "-c", query
    ]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing query: {result.stderr}")
        return None
    return result.stdout.strip()

def main():
    print("Starting Taxonomic Analysis of URLs in public.cleansed_programs...")
    
    # 1. Top Segments Overall
    query_top_segments = """
    WITH path_extraction AS (
        SELECT regexp_replace(url, '^https?://[^/]+', '') as path
        FROM public.cleansed_programs
    ),
    segments AS (
        SELECT unnest(string_to_array(trim(both '/' from path), '/')) as segment
        FROM path_extraction
    )
    SELECT segment, COUNT(*) as frequency
    FROM segments
    WHERE segment <> ''
    GROUP BY segment
    ORDER BY frequency DESC
    LIMIT 30;
    """
    
    print("\n--- Top 30 Segments Overall ---")
    top_segments = run_query(query_top_segments)
    print(top_segments)

    # 2. Analysis by Level
    query_by_level = """
    WITH path_extraction AS (
        SELECT regexp_replace(url, '^https?://[^/]+', '') as path
        FROM public.cleansed_programs
    ),
    segments AS (
        SELECT segment, level
        FROM path_extraction,
        LATERAL unnest(string_to_array(trim(both '/' from path), '/')) WITH ORDINALITY AS t(segment, level)
        WHERE segment <> ''
    )
    SELECT level, segment, COUNT(*) as frequency
    FROM segments
    WHERE level <= 3
    GROUP BY level, segment
    ORDER BY level ASC, frequency DESC
    LIMIT 60;
    """
    
    print("\n--- Top Segments by Level (Levels 1-3) ---")
    by_level = run_query(query_by_level)
    print(by_level)

    # 3. Categorization (Semantic Search in segments)
    # We want to know how many are /maestrias/, /cursos/, /diplomados/, etc.
    categories = ['maestrias', 'cursos', 'diplomados', 'producto', 'especializacion', 'programas', 'noticias', 'eventos', 'postgrado', 'pregrado']
    
    print("\n--- Frequency of Key Semantic Categories ---")
    for cat in categories:
        query_cat = f"""
        SELECT COUNT(*) 
        FROM public.cleansed_programs 
        WHERE url ~* '/{cat}/' OR url ~* '/{cat}$';
        """
        count = run_query(query_cat)
        print(f"{cat}: {count}")

    # 4. Total records
    total = run_query("SELECT COUNT(*) FROM public.cleansed_programs;")
    print(f"\nTotal records in cleansed_programs: {total}")

if __name__ == "__main__":
    main()
