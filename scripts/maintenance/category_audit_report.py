import os
import requests
from collections import Counter
import re
from pathlib import Path

# Intentar cargar .env si dotenv estÃ¡ instalado
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
except ImportError:
    pass

def get_general_courses():
    url = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    key = os.getenv("NEXT_SUPABASE_PUBLISHABLE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY son requeridos.")
        return []

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    # 1. Intentar obtener el ID de la categorÃ­a 'General / Por Clasificar'
    cat_api_url = f"{url}/rest/v1/categories?name=eq.General%20/%20Por%20Clasificar&select=id"
    res = requests.get(cat_api_url, headers=headers)
    
    general_cat_id = None
    if res.status_code == 200 and res.json():
        general_cat_id = res.json()[0]['id']
        
    # 2. Obtener cursos
    courses = []
    
    # PodrÃ­a haber paginaciÃ³n, pero para este reporte pediremos hasta 1000 cursos
    courses_url = f"{url}/rest/v1/courses?select=name,category_confirmed,category_id&limit=1000"
    
    if general_cat_id:
        # Traer cursos en General o no confirmados o sin categorÃ­a
        # Para simplificar en Supabase, traemos todos y filtramos en Python si es mÃ¡s fÃ¡cil, 
        # o usamos or=(category_id.eq.ID,category_confirmed.eq.false,category_id.is.null)
        courses_url += f"&or=(category_id.eq.{general_cat_id},category_confirmed.eq.false,category_id.is.null)"
    else:
        # Si no existe la categorÃ­a aÃºn (pre-migraciÃ³n), traemos los no confirmados o nulos
        courses_url += "&or=(category_confirmed.eq.false,category_id.is.null)"
        
    res = requests.get(courses_url, headers=headers)
    if res.status_code == 200:
        courses = res.json()
    else:
        print(f"Error fetching courses: {res.status_code} - {res.text}")
        
    return courses

def get_stopwords():
    return {
        "de", "la", "el", "en", "y", "a", "los", "las", "del", "para", "con",
        "por", "una", "un", "como", "sobre", "o", "al", "su", "se", "curso",
        "programa", "diplomado", "especializaciÃ³n", "taller", "seminario",
        "oficial", "internacional", "certificaciÃ³n", "introducciÃ³n", "bÃ¡sico",
        "avanzado", "aplicado", "aplicada", "integral", "nivel", "gestiÃ³n",
        "fundamentos", "tÃ©cnicas", "desarrollo", "sistema", "sistemas", "anÃ¡lisis"
    }

def generate_report():
    courses = get_general_courses()
    if not courses:
        print("No se encontraron cursos para auditar o hubo un error.")
        return

    print(f"Total de cursos sin categorÃ­a especÃ­fica/confirmada: {len(courses)}")
    
    stopwords = get_stopwords()
    word_counter = Counter()
    
    for course in courses:
        name = course.get("name")
        if not name:
            continue
        
        # Limpiar puntuaciÃ³n y convertir a minÃºsculas
        words = re.findall(r'\b\w+\b', name.lower())
        
        # Filtrar stopwords y palabras cortas (menos de 3 letras)
        filtered_words = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Opcional: formar bigramas para encontrar conceptos compuestos
        bigrams = [" ".join(filtered_words[i:i+2]) for i in range(len(filtered_words)-1)]
        
        word_counter.update(filtered_words)
        word_counter.update(bigrams)
        
    print("\n--- Top 30 Palabras Clave / Bigramas ---")
    for word, count in word_counter.most_common(30):
        print(f"{word}: {count} ocurrencias")
        
    print("\nRecomendaciÃ³n: Usa estas palabras clave para agregar nuevas reglas a la tabla 'category_rules'.")

if __name__ == "__main__":
    generate_report()
