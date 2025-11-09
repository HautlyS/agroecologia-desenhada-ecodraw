# Botanical Library - SQLite Backend

This directory contains the backend infrastructure for the Botanical Library, converting the JavaScript data to SQLite and serving it via a REST API.

## Files

- `data.js` - Original JavaScript data file (185 plants)
- `convert_to_sqlite.py` - Converter script (JS → SQLite)
- `botanical_library.db` - SQLite database (generated)
- `api_server.py` - Flask REST API server
- `requirements.txt` - Python dependencies

## Setup

### 1. Install Python Dependencies

```bash
pip install -r src/components/Library/requirements.txt
```

### 2. Convert Data to SQLite

```bash
python src/components/Library/convert_to_sqlite.py
```

This will:
- Parse `data.js`
- Create `botanical_library.db`
- Insert all plant data with relationships
- Create full-text search indexes
- Print statistics

### 3. Start the API Server

```bash
python src/components/Library/api_server.py
```

The API will be available at `http://localhost:5000`

## API Endpoints

### GET /api/plants
Get all plants with optional filtering.

**Query Parameters:**
- `type` - Filter by plant type (FRUITS, HERBS, etc.)
- `origin` - Filter by origin (NATIVE, INTRODUCED)
- `region` - Filter by region (partial match)
- `search` - Full-text search query
- `hasWarning` - Filter plants with warnings (true/false)
- `minNutrition` - Minimum nutrition score (0-10)
- `harvestMonth` - Filter by harvest month (1-12)
- `limit` - Maximum results (default: 100)
- `offset` - Pagination offset (default: 0)

**Example:**
```bash
curl "http://localhost:5000/api/plants?type=FRUITS&origin=NATIVE&limit=10"
```

### GET /api/plants/:id
Get a single plant by ID.

**Example:**
```bash
curl "http://localhost:5000/api/plants/F1"
```

### GET /api/search
Full-text search across plants.

**Query Parameters:**
- `q` - Search query (required)

**Example:**
```bash
curl "http://localhost:5000/api/search?q=açaí"
```

### GET /api/stats
Get database statistics.

**Example:**
```bash
curl "http://localhost:5000/api/stats"
```

### GET /api/categories
Get all plant categories with counts.

**Example:**
```bash
curl "http://localhost:5000/api/categories"
```

### GET /api/health
Health check endpoint.

**Example:**
```bash
curl "http://localhost:5000/api/health"
```

## Database Schema

### Tables

1. **plants** - Main plant information
   - id (PRIMARY KEY)
   - name, scientificName, type, origin, color
   - nutritionScore, efficacyScore, commercialValue
   - description, detailedInfo, region
   - spacing, climate, soilType
   - warning, severity
   - created_at

2. **plant_uses** - Plant uses (many-to-many)
   - id, plant_id, use_name

3. **harvest_months** - Harvest months
   - id, plant_id, month (1-12)

4. **certifications** - Plant certifications
   - id, plant_id, certification

5. **keywords** - Search keywords
   - id, plant_id, keyword

6. **plants_fts** - Full-text search virtual table
   - id, name, scientificName, description, detailedInfo, region

### Indexes

- Type, origin, region, name indexes on plants table
- Foreign key indexes on all relationship tables
- Full-text search index for fast searching

## Vue Integration

Use the `useBotanicalAPI` composable in your Vue components:

```javascript
import { useBotanicalAPI } from '@/composables/useBotanicalAPI'

const { fetchPlants, loading, error } = useBotanicalAPI()

// Fetch plants with filters
const result = await fetchPlants({
  type: 'FRUITS',
  origin: 'NATIVE',
  limit: 20
})

// Search plants
const searchResults = await searchPlants('açaí')

// Get single plant
const plant = await fetchPlant('F1')
```

## Statistics

Current database contains:
- **185 total plants** (175 unique after deduplication)
- **50 Fruits**
- **49 PANCs** (Plantas Alimentícias Não Convencionais)
- **28 Herbs**
- **20 Trees**
- **10 Roots**
- **10 Vegetables**
- **3 Crops**
- **3 Spices**
- **2 Invasive Species**

Origin distribution:
- **104 Native** (56%)
- **71 Introduced** (38%)

## Development

### Updating the Database

1. Edit `data.js`
2. Run converter: `python convert_to_sqlite.py`
3. Restart API server

### Adding New Fields

1. Update `create_database()` in `convert_to_sqlite.py`
2. Update `insert_plant_data()` to handle new fields
3. Update API endpoints in `api_server.py`
4. Regenerate database

## Troubleshooting

### Database not found
```
ERROR: Database not found at botanical_library.db
```
**Solution:** Run `python convert_to_sqlite.py` first

### API connection refused
```
Failed to fetch: Connection refused
```
**Solution:** Make sure API server is running: `python api_server.py`

### CORS errors
The API server has CORS enabled for development. For production, configure proper CORS settings in `api_server.py`.

## Performance

- Database size: ~360 KB
- Full-text search: < 10ms
- Filtered queries: < 50ms
- All plants query: < 100ms

## License

Same as parent project.
