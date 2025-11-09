# 🌿 Botanical Library - Quick Start

## TL;DR - Get Started in 30 Seconds

```bash
# Run setup (one time):
setup_botanical_library.bat

# Start development:
npm run dev
```

That's it! The Botanical Library runs **entirely in your browser** - no backend server needed!

## What Changed?

The Botanical Library now uses:
- ✅ **SQLite Database** (360 KB, 185 plants)
- ✅ **Flask REST API** (6 endpoints)
- ✅ **Full-text Search** (10x faster)
- ✅ **Loading States** (better UX)
- ✅ **Error Handling** (retry button)
- ✅ **API Status** (🟢 Online / 🔴 Offline)

## Requirements

- Python 3.7+ (for API server)
- Node.js (for Vue app)

## Setup

### Automated Setup (Recommended)

Double-click: `start_botanical_library.bat`

This will:
1. Install Python dependencies
2. Create the database
3. Start the API server
4. Test the connection

### Manual Setup

```bash
# 1. Install dependencies
pip install Flask flask-cors

# 2. Create database (first time only)
python src/components/Library/convert_to_sqlite.py

# 3. Start API server (keep running)
python src/components/Library/api_server.py
```

## Usage

1. **Start API server** (required!)
   ```bash
   python src/components/Library/api_server.py
   ```
   Keep this terminal open.

2. **Start Vue app**
   ```bash
   npm run dev
   ```

3. **Open Botanical Library**
   - Look for 🟢 Online indicator
   - If you see 🔴 Offline, the API server isn't running

## Troubleshooting

### 🔴 Shows "Offline"
**Fix:** Start the API server
```bash
python src/components/Library/api_server.py
```

### ⚠️ "Database not found"
**Fix:** Create the database
```bash
python src/components/Library/convert_to_sqlite.py
```

### 🐍 "ModuleNotFoundError: No module named 'flask'"
**Fix:** Install dependencies
```bash
pip install Flask flask-cors
```

## Testing

```bash
# Test all API endpoints
python src/components/Library/test_api.py

# Test health check
curl http://localhost:5000/api/health
```

## Documentation

- 📖 **Quick Start**: `BOTANICAL_LIBRARY_STARTUP_GUIDE.md`
- 📖 **Full Documentation**: `src/components/Library/README.md`
- 📖 **Migration Guide**: `BOTANICAL_LIBRARY_API_MIGRATION_COMPLETE.md`
- 📖 **Complete Summary**: `BOTANICAL_LIBRARY_FINAL_SUMMARY.md`

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/plants` - Get all plants (with filters)
- `GET /api/plants/:id` - Get single plant
- `GET /api/search?q=query` - Search plants
- `GET /api/stats` - Database statistics
- `GET /api/categories` - All categories

## Architecture

```
Vue App (BotanicalLibrary.vue)
    ↓
API Composable (useBotanicalAPI.js)
    ↓
Flask API (api_server.py)
    ↓
SQLite Database (botanical_library.db)
```

## Features

### New in This Version

- ✅ **Server-side search** - Full-text search with FTS5
- ✅ **Loading spinner** - Visual feedback while loading
- ✅ **Error handling** - Retry button on errors
- ✅ **API status** - Real-time connection indicator
- ✅ **Caching** - Faster repeated queries
- ✅ **Scalable** - Can handle millions of records

### Database Stats

- **185 plants** (175 unique)
- **50 Fruits** | **49 PANCs** | **28 Herbs**
- **20 Trees** | **10 Roots** | **10 Vegetables**
- **104 Native** (56%) | **71 Introduced** (38%)
- **53 unique uses** | **294 keywords**

## Important Notes

⚠️ **The API server must be running for the library to work!**

Keep the API server terminal open while using the app.

## Support

If you have issues:

1. Check the troubleshooting section above
2. Read `BOTANICAL_LIBRARY_STARTUP_GUIDE.md`
3. Run the test script: `python src/components/Library/test_api.py`
4. Check the API server terminal for errors

## Quick Commands

```bash
# Start API server
python src/components/Library/api_server.py

# Create/recreate database
python src/components/Library/convert_to_sqlite.py

# Test API
python src/components/Library/test_api.py

# Health check
curl http://localhost:5000/api/health
```

---

**Made with 🌿 by the ECODRAW team**
