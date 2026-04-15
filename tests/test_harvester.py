import pytest
import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY")

@pytest.fixture(scope="module")
def api_headers():
    """Fixture to provide API headers."""
    return {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': f'Bearer {SUPABASE_ANON_KEY}'
    }

def test_no_null_prices(api_headers):
    """Verify that no courses have null prices (must have status or numeric price)."""
    # Note: In our current logic, price_pen can be null if price_status is 'consultar'
    # But for quality, we want to ensure we don't have records without both.
    url = f"{SUPABASE_URL}/rest/v1/courses?price_pen=is.null&price_status=neq.consultar&select=count"
    response = requests.get(url, headers=api_headers)
    count = int(response.headers.get('Preference-Applied', '0').split('=')[-1]) if 'count' in url else response.json()[0]['count']
    # Simplified check for this environment's REST response
    data = response.json()
    # If using select=count, Supabase returns [{'count': X}]
    assert data[0]['count'] == 0, f"Found {data[0]['count']} courses with NULL price and no status."

def test_no_duplicate_courses(api_headers):
    """Verify that there are no duplicate courses (same name + same institution)."""
    # This is harder to do in a single REST call without an edge function.
    # We'll fetch the names and institution IDs and check in Python.
    url = f"{SUPABASE_URL}/rest/v1/courses?select=name,institution_id"
    response = requests.get(url, headers=api_headers)
    courses = response.json()
    
    seen = set()
    duplicates = []
    for c in courses:
        key = (c['name'], c['institution_id'])
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    
    assert len(duplicates) == 0, f"Found duplicate courses: {duplicates[:5]}"

def test_pilot_institutions_exist(api_headers):
    """Ensure key institutions are present."""
    url = f"{SUPABASE_URL}/rest/v1/institutions?slug=in.(utec,upc,nh-peru)&select=slug"
    response = requests.get(url, headers=api_headers)
    found_slugs = [r['slug'] for r in response.json()]
    
    assert len(found_slugs) >= 1
    assert 'utec' in found_slugs

def test_rest_api_is_healthy(api_headers):
    """Health check for the connection."""
    url = f"{SUPABASE_URL}/rest/v1/courses?select=id&limit=1"
    response = requests.get(url, headers=api_headers)
    assert response.status_code == 200
