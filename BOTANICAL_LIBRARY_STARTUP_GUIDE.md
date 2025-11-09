# Botanical Library - Quick Start Guide

## Prerequisites

- Python 3.7+ installed
- Node.js and npm installed (for Vue app)

## Step-by-Step Setup

### 1. Install Python Dependencies

```bash
pip install Flask flask-cors
```

Or use the requirements file:

```bash
pip install -r src/components/Library/requirements.txt
```

### 2. Create the Database (First Time Only)

```bash
python src/components/Library/convert_to_sqlite.py
```

**Expected Output:**
```
============================================================
BOTANICAL LIBRARY DATA CONVERTER
============================================================
...
Successfully parsed 185 plant entries using JSON parser
Creating database: botanical_library.db
Database schema created successfully
Inserting 185 plants...
Successfully inserted 185 plants (0 errors)

DATABASE STATISTICS
Total plants: 175
...
✓ Database created successfully
✓ Database size: 360.00 KB
```

### 3. Start the API Server

**Option A: Using the batch script (Windows)**
```bash
src/components/Library/start_api.bat
```

**Option B: Manual start**
```bash
python src/components/Library/api_server.py
```

**Expected Output:**
```
============================================================
BOTANICAL LIBRARY API SERVER
============================================================
Database: botanical_library.db
Server: http://localhost:5000
============================================================

Available endpoints:
  GET /api/plants - Get all plants (with filters)
  GET /api/plants/<id> - Get single plant
  GET /api/stats - Get statistics
  GET /api/search?q=<query> - Search plants
  GET /api/categories - Get categories
  GET /api/health - Health check
============================================================

 * Running on http://127.0.0.1:5000
```

### 4. Verify API is Working

Open a new terminal and test:

```bash
# Health check
curl http://localhost:5000/api/health

# Get first 5 plants
curl "http://localhost:5000/api/plants?limit=5"

# Search for açaí
curl "http://localhost:5000/api/search?q=açaí"
```

Or run the test script:

```bash
python src/components/Library/test_api.py
```

### 5. Start Your Vue Application

In a separate terminal:

```bash
npm run dev
```

### 6. Open the Botanical Library

1. Navigate to your Vue app (usually http://localhost:5173)
2. Open the Botanical Library component
3. You should see the API status indicator showing "🟢 Online"

## Troubleshooting

### Problem: "Database not found"

**Solution:**
```bash
python src/components/Library/convert_to_sqlite.py
```

### Problem: "API connection refused" or "🔴 Offline"

**Cause:** API server is not running

**Solution:**
```bash
python src/components/Library/api_server.py
```

Keep this terminal open while using the app.

### Problem: "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
pip install Flask flask-cors
```

### Problem: "CORS error" in browser console

**Cause:** API server not configured for your frontend URL

**Solution:** The API server has CORS enabled for all origins in development. If you still see errors, check that the API server is running on port 5000.

### Problem: Plants not loading

**Checklist:**
1. ✓ Is the API server running? Check http://localhost:5000/api/health
2. ✓ Does the database exist? Check `src/components/Library/botanical_library.db`
3. ✓ Check browser console for errors
4. ✓ Check API server terminal for errors

## Development Workflow

### Making Changes to Plant Data

1. Edit `src/components/Library/data.js`
2. Regenerate database:
   ```bash
   python src/components/Library/convert_to_sqlite.py
   ```
3. Restart API server (Ctrl+C, then restart)
4. Refresh your Vue app

### Testing API Endpoints

Use curl, Postman, or the test script:

```bash
# Run all tests
python src/components/Library/test_api.py

# Test specific endpoint
curl "http://localhost:5000/api/plants?type=FRUITS&origin=NATIVE"
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Vue Frontend                         │
│  (BotanicalLibrary.vue + useBotanicalAPI.js)          │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP Requests
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Flask REST API Server                      │
│              (api_server.py)                            │
│              Port: 5000                                 │
└────────────────────┬────────────────────────────────────┘
                     │ SQL Queries
                     ↓
┌─────────────────────────────────────────────────────────┐
│              SQLite Database                            │
│              (botanical_library.db)                     │
│              Size: ~360 KB                              │
│              Plants: 185                                │
└─────────────────────────────────────────────────────────┘
```

## API Endpoints Reference

### GET /api/plants
Get all plants with optional filtering.

**Parameters:**
- `type` - FRUITS, HERBS, VEGETABLES, etc.
- `origin` - NATIVE, INTRODUCED
- `region` - Region name (partial match)
- `hasWarning` - true/false
- `minNutrition` - 0-10
- `harvestMonth` - 1-12
- `limit` - Max results (default: 100)
- `offset` - Pagination offset

**Example:**
```bash
curl "http://localhost:5000/api/plants?type=FRUITS&origin=NATIVE&limit=10"
```

### GET /api/plants/:id
Get single plant by ID.

**Example:**
```bash
curl "http://localhost:5000/api/plants/F1"
```

### GET /api/search?q=query
Full-text search.

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
Get all categories with counts.

**Example:**
```bash
curl "http://localhost:5000/api/categories"
```

### GET /api/health
Health check.

**Example:**
```bash
curl "http://localhost:5000/api/health"
```

## Performance Tips

1. **Use filters** - Filter on the server side for better performance
2. **Pagination** - Use limit/offset for large result sets
3. **Caching** - The Vue composable caches results automatically
4. **Search** - Use the search endpoint for text queries (faster than client-side filtering)

## Production Deployment

For production, you'll need:

1. **Production WSGI server** (e.g., Gunicorn, uWSGI)
2. **Reverse proxy** (e.g., Nginx)
3. **Environment variables** for configuration
4. **Proper CORS settings**
5. **Database backups**

Example with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api_server:app
```

## Support

If you encounter issues:

1. Check this guide's troubleshooting section
2. Review the API server logs in the terminal
3. Check browser console for frontend errors
4. Run the test script: `python test_api.py`

## Summary

**To use the Botanical Library:**

1. ✓ Install dependencies: `pip install Flask flask-cors`
2. ✓ Create database: `python convert_to_sqlite.py` (first time only)
3. ✓ Start API server: `python api_server.py` (keep running)
4. ✓ Start Vue app: `npm run dev`
5. ✓ Open Botanical Library in your app

**The API server must be running for the library to work!**
