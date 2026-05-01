import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.db_client import get_db_client

db = get_db_client()

BASE_URL = "https://studiamatch.com"


def generate_sitemap(output_path="web/public/sitemap.xml"):
    courses = db.select_all('courses',
                            filters="is_active=eq.true",
                            columns="slug,url,institutions(name,slug)",
                            order="name.asc")

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')

    # Static pages
    lines.append('  <url>')
    lines.append(f'    <loc>{BASE_URL}/</loc>')
    lines.append('    <changefreq>daily</changefreq>')
    lines.append('    <priority>1.0</priority>')
    lines.append('  </url>')

    lines.append('  <url>')
    lines.append(f'    <loc>{BASE_URL}/compare/</loc>')
    lines.append('    <changefreq>weekly</changefreq>')
    lines.append('    <priority>0.6</priority>')
    lines.append('  </url>')

    # Course pages
    for course in courses:
        inst_slug = course.get('institutions', {}).get('slug', 'general')
        course_slug = course.get('slug', '')
        if not inst_slug or not course_slug:
            continue

        loc = f"{BASE_URL}/courses/{inst_slug}/{course_slug}/"
        lines.append('  <url>')
        lines.append(f'    <loc>{loc}</loc>')
        lines.append('    <changefreq>weekly</changefreq>')
        lines.append('    <priority>0.8</priority>')
        lines.append('  </url>')

    lines.append('</urlset>')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Generated sitemap with {len(courses) + 2} URLs -> {output_path}")


if __name__ == "__main__":
    generate_sitemap()
