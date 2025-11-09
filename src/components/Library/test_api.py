#!/usr/bin/env python3
"""
Quick API test script
Tests all endpoints to verify the API is working correctly.
"""

import requests
import json
from pathlib import Path

API_BASE = 'http://localhost:5000/api'

def test_health():
    """Test health endpoint."""
    print("Testing /api/health...")
    response = requests.get(f'{API_BASE}/health')
    data = response.json()
    assert data['success'], "Health check failed"
    assert data['status'] == 'healthy', "API is not healthy"
    print(f"  ✓ API is healthy, {data['plants']} plants in database")

def test_stats():
    """Test stats endpoint."""
    print("\nTesting /api/stats...")
    response = requests.get(f'{API_BASE}/stats')
    data = response.json()
    assert data['success'], "Stats request failed"
    stats = data['data']
    print(f"  ✓ Total plants: {stats['total']}")
    print(f"  ✓ Native: {stats['byOrigin'].get('NATIVE', 0)}")
    print(f"  ✓ Introduced: {stats['byOrigin'].get('INTRODUCED', 0)}")
    print(f"  ✓ With warnings: {stats['withWarnings']}")

def test_categories():
    """Test categories endpoint."""
    print("\nTesting /api/categories...")
    response = requests.get(f'{API_BASE}/categories')
    data = response.json()
    assert data['success'], "Categories request failed"
    categories = data['data']
    print(f"  ✓ Found {len(categories)} categories:")
    for cat in categories[:5]:
        print(f"    - {cat['name']}: {cat['count']}")

def test_plants():
    """Test plants endpoint."""
    print("\nTesting /api/plants...")
    response = requests.get(f'{API_BASE}/plants?limit=5')
    data = response.json()
    assert data['success'], "Plants request failed"
    plants = data['data']
    print(f"  ✓ Retrieved {len(plants)} plants (limit=5)")
    if plants:
        plant = plants[0]
        print(f"    First plant: {plant['name']} ({plant['scientificName']})")

def test_plants_filtered():
    """Test plants endpoint with filters."""
    print("\nTesting /api/plants with filters...")
    response = requests.get(f'{API_BASE}/plants?type=FRUITS&origin=NATIVE&limit=3')
    data = response.json()
    assert data['success'], "Filtered plants request failed"
    plants = data['data']
    print(f"  ✓ Found {len(plants)} native fruits (limit=3)")
    for plant in plants:
        print(f"    - {plant['name']}")

def test_single_plant():
    """Test single plant endpoint."""
    print("\nTesting /api/plants/:id...")
    response = requests.get(f'{API_BASE}/plants/F1')
    data = response.json()
    assert data['success'], "Single plant request failed"
    plant = data['data']
    print(f"  ✓ Retrieved plant: {plant['name']}")
    print(f"    Scientific name: {plant['scientificName']}")
    print(f"    Type: {plant['type']}")
    print(f"    Origin: {plant['origin']}")
    print(f"    Uses: {', '.join(plant['uses'][:3])}...")

def test_search():
    """Test search endpoint."""
    print("\nTesting /api/search...")
    response = requests.get(f'{API_BASE}/search?q=açaí')
    data = response.json()
    assert data['success'], "Search request failed"
    results = data['data']
    print(f"  ✓ Search for 'açaí' found {len(results)} results")
    if results:
        print(f"    First result: {results[0]['name']}")

def main():
    """Run all tests."""
    print("="*60)
    print("BOTANICAL LIBRARY API TESTS")
    print("="*60)
    
    # Check if database exists
    db_path = Path(__file__).parent / 'botanical_library.db'
    if not db_path.exists():
        print("\n✗ ERROR: Database not found!")
        print("  Please run: python convert_to_sqlite.py")
        return False
    
    try:
        test_health()
        test_stats()
        test_categories()
        test_plants()
        test_plants_filtered()
        test_single_plant()
        test_search()
        
        print("\n" + "="*60)
        print("✓ ALL TESTS PASSED")
        print("="*60)
        return True
        
    except requests.exceptions.ConnectionError:
        print("\n✗ ERROR: Could not connect to API server")
        print("  Please start the server: python api_server.py")
        return False
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n✗ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
