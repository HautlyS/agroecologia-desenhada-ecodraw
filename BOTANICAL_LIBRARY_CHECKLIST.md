# Botanical Library - Implementation Checklist ✅

## Pre-Flight Checklist

Before using the Botanical Library, verify:

### ✅ Python Setup
- [ ] Python 3.7+ installed
- [ ] `python --version` works in terminal
- [ ] pip is available

### ✅ Dependencies Installed
- [ ] Flask installed: `pip show Flask`
- [ ] flask-cors installed: `pip show flask-cors`
- [ ] Or run: `pip install Flask flask-cors`

### ✅ Database Created
- [ ] File exists: `src/components/Library/botanical_library.db`
- [ ] Database size: ~360 KB
- [ ] If missing, run: `python src/components/Library/convert_to_sqlite.py`

### ✅ API Server Running
- [ ] Terminal shows: "Running on http://127.0.0.1:5000"
- [ ] Health check works: `curl http://localhost:5000/api/health`
- [ ] Test passes: `python src/components/Library/test_api.py`

### ✅ Vue App Running
- [ ] `npm run dev` executed
- [ ] App accessible in browser
- [ ] No console errors

### ✅ Component Working
- [ ] Botanical Library opens
- [ ] Shows 🟢 Online indicator
- [ ] Plants load successfully
- [ ] Search works
- [ ] Filters work

## Startup Checklist

Every time you want to use the Botanical Library:

### Option 1: Automated (Recommended)
- [ ] Run: `start_botanical_library.bat`
- [ ] Wait for "SETUP COMPLETE!" message
- [ ] API server window opens
- [ ] Run: `npm run dev`
- [ ] Open Botanical Library

### Option 2: Manual
- [ ] Terminal 1: `python src/components/Library/api_server.py`
- [ ] Wait for "Running on http://127.0.0.1:5000"
- [ ] Terminal 2: `npm run dev`
- [ ] Open Botanical Library
- [ ] Verify 🟢 Online indicator

## Testing Checklist

### API Tests
- [ ] Health check: `curl http://localhost:5000/api/health`
- [ ] Get plants: `curl "http://localhost:5000/api/plants?limit=5"`
- [ ] Search: `curl "http://localhost:5000/api/search?q=açaí"`
- [ ] Stats: `curl http://localhost:5000/api/stats`
- [ ] Full test suite: `python src/components/Library/test_api.py`

### UI Tests
- [ ] Component opens without errors
- [ ] Loading spinner appears briefly
- [ ] Plants display correctly
- [ ] Search box works
- [ ] Filters work (type, origin, etc.)
- [ ] Pagination works
- [ ] Plant cards expand/collapse
- [ ] Favorite button works
- [ ] API status shows 🟢 Online

### Error Handling Tests
- [ ] Stop API server → Shows 🔴 Offline
- [ ] Shows error message
- [ ] Retry button appears
- [ ] Click retry → Attempts reconnection
- [ ] Restart API → Shows 🟢 Online again

## File Verification Checklist

### Required Files Exist
- [ ] `src/components/Library/BotanicalLibrary.vue` (updated)
- [ ] `src/components/Library/data.js` (original, kept)
- [ ] `src/components/Library/convert_to_sqlite.py`
- [ ] `src/components/Library/api_server.py`
- [ ] `src/components/Library/botanical_library.db` (generated)
- [ ] `src/components/Library/test_api.py`
- [ ] `src/components/Library/requirements.txt`
- [ ] `src/components/Library/README.md`
- [ ] `src/composables/useBotanicalAPI.js`

### Documentation Files
- [ ] `README_BOTANICAL_LIBRARY.md`
- [ ] `BOTANICAL_LIBRARY_STARTUP_GUIDE.md`
- [ ] `BOTANICAL_LIBRARY_SQLITE_MIGRATION.md`
- [ ] `BOTANICAL_LIBRARY_API_MIGRATION_COMPLETE.md`
- [ ] `BOTANICAL_LIBRARY_FINAL_SUMMARY.md`
- [ ] `BOTANICAL_LIBRARY_CHECKLIST.md` (this file)

### Scripts
- [ ] `start_botanical_library.bat`
- [ ] `src/components/Library/start_api.bat`

## Troubleshooting Checklist

### If Component Shows 🔴 Offline

1. Check API Server
   - [ ] Is the API server terminal open?
   - [ ] Does it show "Running on http://127.0.0.1:5000"?
   - [ ] Any error messages in terminal?
   - [ ] Try: `curl http://localhost:5000/api/health`

2. Check Port
   - [ ] Is port 5000 available?
   - [ ] Try: `netstat -an | findstr :5000`
   - [ ] Another app using port 5000?

3. Check CORS
   - [ ] Open browser console (F12)
   - [ ] Any CORS errors?
   - [ ] API server has CORS enabled?

4. Restart Everything
   - [ ] Stop API server (Ctrl+C)
   - [ ] Start API server again
   - [ ] Refresh browser
   - [ ] Check 🟢 Online indicator

### If Database Missing

1. Create Database
   - [ ] Run: `python src/components/Library/convert_to_sqlite.py`
   - [ ] Check for success message
   - [ ] Verify file exists: `src/components/Library/botanical_library.db`
   - [ ] Check file size: ~360 KB

2. If Converter Fails
   - [ ] Check `data.js` exists
   - [ ] Check Python version: `python --version`
   - [ ] Check for error messages
   - [ ] Try running in verbose mode

### If Plants Don't Load

1. Check API Response
   - [ ] Open browser DevTools (F12)
   - [ ] Go to Network tab
   - [ ] Refresh page
   - [ ] Look for `/api/plants` request
   - [ ] Check response status (should be 200)
   - [ ] Check response data

2. Check Console
   - [ ] Any JavaScript errors?
   - [ ] Any API errors?
   - [ ] Any CORS errors?

3. Check API Server
   - [ ] Look at API server terminal
   - [ ] Any error messages?
   - [ ] Any 500 errors?

### If Search Doesn't Work

1. Check Search Query
   - [ ] Query length > 2 characters?
   - [ ] Special characters causing issues?
   - [ ] Try simple query: "açaí"

2. Check API
   - [ ] Test: `curl "http://localhost:5000/api/search?q=açaí"`
   - [ ] Returns results?
   - [ ] Check FTS table exists in database

3. Check Browser
   - [ ] Console errors?
   - [ ] Network request successful?
   - [ ] Response contains data?

## Performance Checklist

### Expected Performance
- [ ] Database queries: < 50ms
- [ ] Full-text search: < 10ms
- [ ] API response time: < 100ms
- [ ] Page load time: < 2s
- [ ] Search results: < 500ms

### If Slow Performance
- [ ] Check database size (should be ~360 KB)
- [ ] Check number of plants (should be ~185)
- [ ] Check indexes exist
- [ ] Check API server not overloaded
- [ ] Check network latency
- [ ] Try clearing cache

## Production Checklist

Before deploying to production:

### Security
- [ ] Change default CORS settings
- [ ] Add authentication if needed
- [ ] Add rate limiting
- [ ] Validate all inputs
- [ ] Sanitize SQL queries (already done with parameterized queries)
- [ ] Use HTTPS
- [ ] Set secure headers

### Performance
- [ ] Use production WSGI server (Gunicorn)
- [ ] Enable caching (Redis)
- [ ] Use CDN for static assets
- [ ] Optimize database indexes
- [ ] Enable compression
- [ ] Monitor performance

### Reliability
- [ ] Set up database backups
- [ ] Add health monitoring
- [ ] Set up logging
- [ ] Add error tracking (Sentry)
- [ ] Set up alerts
- [ ] Document recovery procedures

### Deployment
- [ ] Use environment variables
- [ ] Set up CI/CD
- [ ] Test in staging environment
- [ ] Create deployment checklist
- [ ] Document rollback procedure
- [ ] Set up monitoring dashboard

## Maintenance Checklist

### Weekly
- [ ] Check API server logs
- [ ] Monitor error rates
- [ ] Check database size
- [ ] Review performance metrics

### Monthly
- [ ] Update dependencies
- [ ] Review and optimize queries
- [ ] Check for security updates
- [ ] Backup database
- [ ] Review documentation

### Quarterly
- [ ] Performance audit
- [ ] Security audit
- [ ] User feedback review
- [ ] Feature planning
- [ ] Documentation update

## Success Criteria

The Botanical Library is working correctly when:

- ✅ API server starts without errors
- ✅ Database contains 185 plants
- ✅ Health check returns success
- ✅ Component shows 🟢 Online
- ✅ Plants load and display
- ✅ Search returns results
- ✅ Filters work correctly
- ✅ No console errors
- ✅ Performance is acceptable
- ✅ Error handling works

## Quick Reference

### Start Everything
```bash
start_botanical_library.bat  # Automated
# OR
python src/components/Library/api_server.py  # Manual
npm run dev
```

### Test Everything
```bash
python src/components/Library/test_api.py
curl http://localhost:5000/api/health
```

### Fix Everything
```bash
# Recreate database
python src/components/Library/convert_to_sqlite.py

# Reinstall dependencies
pip install Flask flask-cors

# Restart API server
# Ctrl+C to stop, then restart
python src/components/Library/api_server.py
```

---

**Use this checklist every time you work with the Botanical Library!**
