import sqlite3

conn = sqlite3.connect('data.sqlite')
cursor = conn.cursor()

# Show tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables in database:")
for table in tables:
    print(f"  - {table[0]}")

# Show sample plants
print("\nSample plants:")
cursor.execute("SELECT id, name, type, origin FROM plants LIMIT 10")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]}, {row[3]})")

# Show statistics
cursor.execute("SELECT type, COUNT(*) FROM plants GROUP BY type")
print("\nPlants by type:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Show a complete plant record
print("\nDetailed view of first plant:")
cursor.execute("SELECT * FROM plants LIMIT 1")
plant = cursor.fetchone()
cursor.execute("PRAGMA table_info(plants)")
columns = [col[1] for col in cursor.fetchall()]

for col, val in zip(columns, plant):
    if val:
        print(f"  {col}: {val}")

# Show related data
plant_id = plant[0]
cursor.execute("SELECT use_name FROM plant_uses WHERE plant_id = ?", (plant_id,))
uses = [row[0] for row in cursor.fetchall()]
print(f"\n  Uses: {', '.join(uses)}")

cursor.execute("SELECT month FROM harvest_months WHERE plant_id = ? ORDER BY month", (plant_id,))
months = [row[0] for row in cursor.fetchall()]
print(f"  Harvest months: {months}")

conn.close()
