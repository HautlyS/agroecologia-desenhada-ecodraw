#!/usr/bin/env python3
"""
Botanical Library Data Converter
Converts JavaScript data.js to SQLite database with improved parsing and validation.
"""

import sqlite3
import json
import re
import sys
from pathlib import Path
from typing import List, Dict, Any


def extract_js_data(js_file_path: str) -> List[Dict[str, Any]]:
    """
    Extract the data array from the JavaScript file using improved parsing.
    
    Args:
        js_file_path: Path to the JavaScript file
        
    Returns:
        List of plant dictionaries
        
    Raises:
        ValueError: If data array cannot be found or parsed
    """
    print(f"Reading JavaScript file: {js_file_path}")
    
    with open(js_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the data array with better regex - try multiple patterns
    patterns = [
        r'const\s+allItems\s*=\s*\[(.*?)\];',  # const allItems = [...]
        r'const\s+data\s*=\s*\[(.*?)\];',      # const data = [...]
        r'export\s+const\s+data\s*=\s*\[(.*?)\]',  # export const data = [...]
    ]
    
    match = None
    for pattern in patterns:
        match = re.search(pattern, content, re.DOTALL)
        if match:
            break
    
    if not match:
        raise ValueError("Could not find data array in JS file (tried: allItems, data)")
    
    array_content = match.group(1).strip()
    
    # Try JSON parsing first (if data is already in JSON format)
    try:
        json_str = '[' + array_content + ']'
        plants = json.loads(json_str)
        print(f"Successfully parsed {len(plants)} plant entries using JSON parser")
        return plants
    except json.JSONDecodeError:
        print("JSON parsing failed, using JavaScript parser...")
        # Fallback to manual parser for JavaScript syntax
        plants = parse_js_objects(array_content)
        print(f"Successfully parsed {len(plants)} plant entries using JS parser")
        return plants


def parse_js_objects(content: str) -> List[Dict[str, Any]]:
    """
    Parse JavaScript object literals into Python dictionaries.
    Handles nested objects, arrays, strings with quotes, and comments.
    
    Args:
        content: JavaScript array content (without outer brackets)
        
    Returns:
        List of parsed plant dictionaries
    """
    plants = []
    current_obj = {}
    stack = []
    i = 0
    
    # Remove comments
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Split into individual objects by finding balanced braces
    obj_strings = []
    brace_count = 0
    current_obj_str = ""
    
    for char in content:
        if char == '{':
            if brace_count == 0:
                current_obj_str = "{"
            else:
                current_obj_str += char
            brace_count += 1
        elif char == '}':
            brace_count -= 1
            current_obj_str += char
            if brace_count == 0 and current_obj_str.strip():
                obj_strings.append(current_obj_str)
                current_obj_str = ""
        elif brace_count > 0:
            current_obj_str += char
    
    # Parse each object
    for obj_str in obj_strings:
        try:
            plant = parse_single_object(obj_str)
            if plant and 'id' in plant:
                plants.append(plant)
        except Exception as e:
            print(f"Warning: Failed to parse object: {e}")
            continue
    
    return plants


def parse_single_object(obj_str: str) -> Dict[str, Any]:
    """Parse a single JavaScript object literal."""
    obj = {}
    
    # Remove outer braces
    obj_str = obj_str.strip()[1:-1]
    
    # Find all key-value pairs
    # Pattern matches: key: value (handling strings, arrays, numbers, etc.)
    pattern = r'(\w+)\s*:\s*(.+?)(?=,\s*\w+\s*:|$)'
    
    matches = re.finditer(pattern, obj_str, re.DOTALL)
    
    for match in matches:
        key = match.group(1).strip()
        value_str = match.group(2).strip().rstrip(',')
        
        # Parse the value
        value = parse_value(value_str)
        obj[key] = value
    
    return obj


def parse_value(value_str: str) -> Any:
    """Parse a JavaScript value into Python equivalent."""
    value_str = value_str.strip()
    
    # Array
    if value_str.startswith('['):
        # Extract array content
        array_match = re.match(r'\[(.*?)\]', value_str, re.DOTALL)
        if array_match:
            array_content = array_match.group(1)
            # Split by comma, handling quoted strings
            items = []
            current_item = ""
            in_quotes = False
            quote_char = None
            
            for char in array_content:
                if char in ('"', "'") and (not in_quotes or char == quote_char):
                    in_quotes = not in_quotes
                    quote_char = char if in_quotes else None
                    current_item += char
                elif char == ',' and not in_quotes:
                    if current_item.strip():
                        items.append(parse_value(current_item.strip()))
                    current_item = ""
                else:
                    current_item += char
            
            if current_item.strip():
                items.append(parse_value(current_item.strip()))
            
            return items
        return []
    
    # String
    if (value_str.startswith("'") and value_str.endswith("'")) or \
       (value_str.startswith('"') and value_str.endswith('"')):
        return value_str[1:-1]
    
    # Boolean
    if value_str.lower() == 'true':
        return True
    if value_str.lower() == 'false':
        return False
    
    # Null/undefined
    if value_str.lower() in ('null', 'undefined'):
        return None
    
    # Number
    try:
        if '.' in value_str:
            return float(value_str)
        return int(value_str)
    except ValueError:
        pass
    
    # Default: return as string
    return value_str

def create_database(db_path: str) -> sqlite3.Connection:
    """
    Create SQLite database with optimized schema and indexes.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        SQLite connection object
    """
    print(f"Creating database: {db_path}")
    
    # Remove existing database for clean slate
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print("Removed existing database")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Enable foreign keys
    cursor.execute('PRAGMA foreign_keys = ON')
    
    # Create main plants table with all fields
    cursor.execute('''
        CREATE TABLE plants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            scientificName TEXT,
            type TEXT NOT NULL,
            origin TEXT NOT NULL,
            color TEXT,
            nutritionScore REAL,
            efficacyScore REAL,
            commercialValue TEXT,
            description TEXT,
            detailedInfo TEXT,
            region TEXT,
            spacing TEXT,
            climate TEXT,
            soilType TEXT,
            warning TEXT,
            severity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create indexes for common queries
    cursor.execute('CREATE INDEX idx_plants_type ON plants(type)')
    cursor.execute('CREATE INDEX idx_plants_origin ON plants(origin)')
    cursor.execute('CREATE INDEX idx_plants_region ON plants(region)')
    cursor.execute('CREATE INDEX idx_plants_name ON plants(name)')
    
    # Create uses table (many-to-many relationship)
    cursor.execute('''
        CREATE TABLE plant_uses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id TEXT NOT NULL,
            use_name TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX idx_uses_plant_id ON plant_uses(plant_id)')
    cursor.execute('CREATE INDEX idx_uses_name ON plant_uses(use_name)')
    
    # Create harvest months table
    cursor.execute('''
        CREATE TABLE harvest_months (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id TEXT NOT NULL,
            month INTEGER NOT NULL CHECK(month >= 1 AND month <= 12),
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX idx_harvest_plant_id ON harvest_months(plant_id)')
    cursor.execute('CREATE INDEX idx_harvest_month ON harvest_months(month)')
    
    # Create certifications table
    cursor.execute('''
        CREATE TABLE certifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id TEXT NOT NULL,
            certification TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX idx_cert_plant_id ON certifications(plant_id)')
    
    # Create keywords table for search
    cursor.execute('''
        CREATE TABLE keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plant_id TEXT NOT NULL,
            keyword TEXT NOT NULL,
            FOREIGN KEY (plant_id) REFERENCES plants(id) ON DELETE CASCADE
        )
    ''')
    cursor.execute('CREATE INDEX idx_keywords_plant_id ON keywords(plant_id)')
    cursor.execute('CREATE INDEX idx_keywords_keyword ON keywords(keyword)')
    
    # Create full-text search virtual table
    cursor.execute('''
        CREATE VIRTUAL TABLE plants_fts USING fts5(
            id UNINDEXED,
            name,
            scientificName,
            description,
            detailedInfo,
            region,
            content=plants
        )
    ''')
    
    conn.commit()
    print("Database schema created successfully")
    return conn

def insert_plant_data(conn: sqlite3.Connection, plants_data: List[Dict[str, Any]]) -> None:
    """
    Insert plant data into the database with validation and error handling.
    
    Args:
        conn: SQLite connection object
        plants_data: List of plant dictionaries
    """
    cursor = conn.cursor()
    inserted_count = 0
    error_count = 0
    
    print(f"Inserting {len(plants_data)} plants...")
    
    for i, plant in enumerate(plants_data, 1):
        try:
            plant_id = plant.get('id')
            if not plant_id:
                print(f"Warning: Plant #{i} missing ID, skipping")
                error_count += 1
                continue
            
            # Insert main plant data
            cursor.execute('''
                INSERT OR REPLACE INTO plants (
                    id, name, scientificName, type, origin, color,
                    nutritionScore, efficacyScore, commercialValue,
                    description, detailedInfo, region, spacing,
                    climate, soilType, warning, severity
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plant_id,
                plant.get('name', ''),
                plant.get('scientificName', ''),
                plant.get('type', ''),
                plant.get('origin', ''),
                plant.get('color', ''),
                plant.get('nutritionScore'),
                plant.get('efficacyScore'),
                plant.get('commercialValue', ''),
                plant.get('description', ''),
                plant.get('detailedInfo', ''),
                plant.get('region', ''),
                plant.get('spacing', ''),
                plant.get('climate', ''),
                plant.get('soilType', ''),
                plant.get('warning'),
                plant.get('severity')
            ))
            
            # Insert uses
            uses = plant.get('uses', [])
            if isinstance(uses, list):
                for use in uses:
                    if use:
                        cursor.execute(
                            'INSERT INTO plant_uses (plant_id, use_name) VALUES (?, ?)',
                            (plant_id, str(use))
                        )
            
            # Insert harvest months
            harvest_months = plant.get('harvestMonths', [])
            if isinstance(harvest_months, list):
                for month in harvest_months:
                    if isinstance(month, int) and 1 <= month <= 12:
                        cursor.execute(
                            'INSERT INTO harvest_months (plant_id, month) VALUES (?, ?)',
                            (plant_id, month)
                        )
            
            # Insert certifications
            certifications = plant.get('certification', [])
            if isinstance(certifications, list):
                for cert in certifications:
                    if cert:
                        cursor.execute(
                            'INSERT INTO certifications (plant_id, certification) VALUES (?, ?)',
                            (plant_id, str(cert))
                        )
            
            # Insert keywords
            keywords = plant.get('keywords', [])
            if isinstance(keywords, list):
                for keyword in keywords:
                    if keyword:
                        cursor.execute(
                            'INSERT INTO keywords (plant_id, keyword) VALUES (?, ?)',
                            (plant_id, str(keyword))
                        )
            
            # Insert into FTS table
            cursor.execute('''
                INSERT INTO plants_fts (id, name, scientificName, description, detailedInfo, region)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                plant_id,
                plant.get('name', ''),
                plant.get('scientificName', ''),
                plant.get('description', ''),
                plant.get('detailedInfo', ''),
                plant.get('region', '')
            ))
            
            inserted_count += 1
            
            if i % 10 == 0:
                print(f"  Processed {i}/{len(plants_data)} plants...")
                
        except Exception as e:
            print(f"Error inserting plant {plant.get('id', 'unknown')}: {e}")
            error_count += 1
            continue
    
    conn.commit()
    print(f"Successfully inserted {inserted_count} plants ({error_count} errors)")

def print_statistics(conn: sqlite3.Connection) -> None:
    """Print database statistics."""
    cursor = conn.cursor()
    
    print("\n" + "="*60)
    print("DATABASE STATISTICS")
    print("="*60)
    
    # Total plants
    cursor.execute("SELECT COUNT(*) FROM plants")
    total = cursor.fetchone()[0]
    print(f"Total plants: {total}")
    
    # By type
    cursor.execute("SELECT type, COUNT(*) FROM plants GROUP BY type ORDER BY COUNT(*) DESC")
    print("\nPlants by type:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # By origin
    cursor.execute("SELECT origin, COUNT(*) FROM plants GROUP BY origin")
    print("\nPlants by origin:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}")
    
    # With warnings
    cursor.execute("SELECT COUNT(*) FROM plants WHERE warning IS NOT NULL")
    warnings = cursor.fetchone()[0]
    print(f"\nPlants with warnings: {warnings}")
    
    # Average nutrition score
    cursor.execute("SELECT AVG(nutritionScore) FROM plants WHERE nutritionScore IS NOT NULL")
    avg_nutrition = cursor.fetchone()[0]
    if avg_nutrition:
        print(f"Average nutrition score: {avg_nutrition:.2f}")
    
    # Total uses
    cursor.execute("SELECT COUNT(DISTINCT use_name) FROM plant_uses")
    uses = cursor.fetchone()[0]
    print(f"Unique uses: {uses}")
    
    # Total keywords
    cursor.execute("SELECT COUNT(DISTINCT keyword) FROM keywords")
    keywords = cursor.fetchone()[0]
    print(f"Unique keywords: {keywords}")
    
    print("="*60 + "\n")


def main():
    """Main execution function."""
    # File paths
    script_dir = Path(__file__).parent
    js_file = script_dir / 'data.js'
    db_file = script_dir / 'botanical_library.db'
    
    print("="*60)
    print("BOTANICAL LIBRARY DATA CONVERTER")
    print("="*60)
    print(f"Script directory: {script_dir}")
    print(f"Input file: {js_file}")
    print(f"Output database: {db_file}")
    print("="*60 + "\n")
    
    # Check if input file exists
    if not js_file.exists():
        print(f"ERROR: Input file not found: {js_file}")
        print("Please ensure data.js exists in the same directory as this script.")
        sys.exit(1)
    
    try:
        # Extract data from JavaScript file
        plants_data = extract_js_data(str(js_file))
        
        if not plants_data:
            print("ERROR: No plant data found in JavaScript file")
            sys.exit(1)
        
        # Create database
        conn = create_database(str(db_file))
        
        # Insert data
        insert_plant_data(conn, plants_data)
        
        # Print statistics
        print_statistics(conn)
        
        # Close connection
        conn.close()
        
        print(f"✓ Database created successfully: {db_file}")
        print(f"✓ Database size: {db_file.stat().st_size / 1024:.2f} KB")
        
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
