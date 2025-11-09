#!/usr/bin/env python3
"""
Botanical Library API Server
Simple Flask API to serve plant data from SQLite database to Vue frontend.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional

app = Flask(__name__)
CORS(app)  # Enable CORS for Vue development server

# Database path
DB_PATH = Path(__file__).parent / 'botanical_library.db'


def get_db_connection():
    """Create a database connection."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    return conn


def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert SQLite row to dictionary."""
    return {key: row[key] for key in row.keys()}


def get_plant_details(conn: sqlite3.Connection, plant_id: str) -> Optional[Dict[str, Any]]:
    """Get complete plant details including related data."""
    cursor = conn.cursor()
    
    # Get main plant data
    cursor.execute('SELECT * FROM plants WHERE id = ?', (plant_id,))
    plant_row = cursor.fetchone()
    
    if not plant_row:
        return None
    
    plant = row_to_dict(plant_row)
    
    # Get uses
    cursor.execute('SELECT use_name FROM plant_uses WHERE plant_id = ?', (plant_id,))
    plant['uses'] = [row['use_name'] for row in cursor.fetchall()]
    
    # Get harvest months
    cursor.execute('SELECT month FROM harvest_months WHERE plant_id = ? ORDER BY month', (plant_id,))
    plant['harvestMonths'] = [row['month'] for row in cursor.fetchall()]
    
    # Get certifications
    cursor.execute('SELECT certification FROM certifications WHERE plant_id = ?', (plant_id,))
    plant['certification'] = [row['certification'] for row in cursor.fetchall()]
    
    # Get keywords
    cursor.execute('SELECT keyword FROM keywords WHERE plant_id = ?', (plant_id,))
    plant['keywords'] = [row['keyword'] for row in cursor.fetchall()]
    
    return plant


@app.route('/api/plants', methods=['GET'])
def get_plants():
    """
    Get all plants with optional filtering.
    
    Query parameters:
    - type: Filter by plant type
    - origin: Filter by origin (NATIVE/INTRODUCED)
    - region: Filter by region
    - search: Full-text search query
    - hasWarning: Filter plants with warnings (true/false)
    - minNutrition: Minimum nutrition score
    - harvestMonth: Filter by harvest month (1-12)
    - limit: Maximum number of results
    - offset: Pagination offset
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build query
        query = 'SELECT * FROM plants WHERE 1=1'
        params = []
        
        # Apply filters
        plant_type = request.args.get('type')
        if plant_type and plant_type != 'ALL':
            query += ' AND type = ?'
            params.append(plant_type)
        
        origin = request.args.get('origin')
        if origin and origin != 'ALL':
            query += ' AND origin = ?'
            params.append(origin)
        
        region = request.args.get('region')
        if region:
            query += ' AND region LIKE ?'
            params.append(f'%{region}%')
        
        has_warning = request.args.get('hasWarning')
        if has_warning == 'true':
            query += ' AND warning IS NOT NULL'
        
        min_nutrition = request.args.get('minNutrition')
        if min_nutrition:
            query += ' AND (nutritionScore >= ? OR efficacyScore >= ?)'
            params.extend([float(min_nutrition), float(min_nutrition)])
        
        harvest_month = request.args.get('harvestMonth')
        if harvest_month:
            query += ''' AND id IN (
                SELECT plant_id FROM harvest_months WHERE month = ?
            )'''
            params.append(int(harvest_month))
        
        # Full-text search
        search = request.args.get('search')
        if search:
            query += ''' AND id IN (
                SELECT id FROM plants_fts WHERE plants_fts MATCH ?
            )'''
            params.append(search)
        
        # Pagination
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        plants = []
        
        for row in cursor.fetchall():
            plant = get_plant_details(conn, row['id'])
            if plant:
                plants.append(plant)
        
        # Get total count
        count_query = query.split('LIMIT')[0]
        cursor.execute(f'SELECT COUNT(*) as count FROM ({count_query})', params[:-2])
        total = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': plants,
            'total': total,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/plants/<plant_id>', methods=['GET'])
def get_plant(plant_id: str):
    """Get a single plant by ID."""
    try:
        conn = get_db_connection()
        plant = get_plant_details(conn, plant_id)
        conn.close()
        
        if plant:
            return jsonify({
                'success': True,
                'data': plant
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Plant not found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total plants
        cursor.execute('SELECT COUNT(*) as count FROM plants')
        total = cursor.fetchone()['count']
        
        # By type
        cursor.execute('SELECT type, COUNT(*) as count FROM plants GROUP BY type')
        by_type = {row['type']: row['count'] for row in cursor.fetchall()}
        
        # By origin
        cursor.execute('SELECT origin, COUNT(*) as count FROM plants GROUP BY origin')
        by_origin = {row['origin']: row['count'] for row in cursor.fetchall()}
        
        # With warnings
        cursor.execute('SELECT COUNT(*) as count FROM plants WHERE warning IS NOT NULL')
        with_warnings = cursor.fetchone()['count']
        
        # Unique uses
        cursor.execute('SELECT COUNT(DISTINCT use_name) as count FROM plant_uses')
        unique_uses = cursor.fetchone()['count']
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'total': total,
                'byType': by_type,
                'byOrigin': by_origin,
                'withWarnings': with_warnings,
                'uniqueUses': unique_uses
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['GET'])
def search_plants():
    """Full-text search across plants."""
    query = request.args.get('q', '')
    
    if not query:
        return jsonify({
            'success': False,
            'error': 'Search query required'
        }), 400
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Full-text search
        cursor.execute('''
            SELECT id FROM plants_fts 
            WHERE plants_fts MATCH ? 
            ORDER BY rank
            LIMIT 50
        ''', (query,))
        
        plant_ids = [row['id'] for row in cursor.fetchall()]
        plants = [get_plant_details(conn, pid) for pid in plant_ids]
        plants = [p for p in plants if p]  # Filter out None values
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': plants,
            'total': len(plants)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all plant categories with counts."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT type, COUNT(*) as count 
            FROM plants 
            GROUP BY type 
            ORDER BY count DESC
        ''')
        
        categories = [
            {'name': row['type'], 'count': row['count']}
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'data': categories
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM plants')
        count = cursor.fetchone()['count']
        conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'database': 'connected',
            'plants': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Check if database exists
    if not DB_PATH.exists():
        print(f"ERROR: Database not found at {DB_PATH}")
        print("Please run convert_to_sqlite.py first to create the database.")
        exit(1)
    
    print("="*60)
    print("BOTANICAL LIBRARY API SERVER")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Server: http://localhost:5000")
    print("="*60)
    print("\nAvailable endpoints:")
    print("  GET /api/plants - Get all plants (with filters)")
    print("  GET /api/plants/<id> - Get single plant")
    print("  GET /api/stats - Get statistics")
    print("  GET /api/search?q=<query> - Search plants")
    print("  GET /api/categories - Get categories")
    print("  GET /api/health - Health check")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5000)
