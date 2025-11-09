/**
 * Browser-based SQLite using sql.js (WebAssembly)
 * No backend server required!
 */

import { ref, computed } from 'vue'
import initSqlJs from 'sql.js'

// Shared state
const db = ref(null)
const isInitialized = ref(false)
const isLoading = ref(false)
const error = ref(null)

// Cache for query results
const queryCache = new Map()

export function useSQLite() {
  /**
   * Initialize sql.js and load the database
   */
  const initDatabase = async (dbPath = '/botanical_library.db') => {
    if (isInitialized.value) {
      return db.value
    }

    isLoading.value = true
    error.value = null

    try {
      console.log('Initializing sql.js...')
      
      // Initialize sql.js with CDN
      const SQL = await initSqlJs({
        locateFile: file => `https://sql.js.org/dist/${file}`
      })

      console.log('Loading database from:', dbPath)
      
      // Fetch the database file
      const response = await fetch(dbPath)
      if (!response.ok) {
        throw new Error(`Failed to load database: ${response.statusText}`)
      }

      const buffer = await response.arrayBuffer()
      const uint8Array = new Uint8Array(buffer)

      console.log(`Database loaded: ${(buffer.byteLength / 1024).toFixed(2)} KB`)

      // Create database instance
      db.value = new SQL.Database(uint8Array)
      isInitialized.value = true

      console.log('Database initialized successfully')
      return db.value

    } catch (err) {
      error.value = err.message
      console.error('Failed to initialize database:', err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  /**
   * Execute a SQL query
   */
  const query = (sql, params = []) => {
    if (!db.value) {
      throw new Error('Database not initialized. Call initDatabase() first.')
    }

    try {
      const results = db.value.exec(sql, params)
      return results
    } catch (err) {
      console.error('Query error:', err)
      throw err
    }
  }

  /**
   * Execute a query and return results as array of objects
   */
  const queryAsObjects = (sql, params = []) => {
    const results = query(sql, params)
    
    if (!results || results.length === 0) {
      return []
    }

    const { columns, values } = results[0]
    
    return values.map(row => {
      const obj = {}
      columns.forEach((col, i) => {
        obj[col] = row[i]
      })
      return obj
    })
  }

  /**
   * Get all plants with optional filters
   */
  const getPlants = (filters = {}) => {
    let sql = 'SELECT * FROM plants WHERE 1=1'
    const params = []

    // Apply filters
    if (filters.type && filters.type !== 'ALL') {
      sql += ' AND type = ?'
      params.push(filters.type)
    }

    if (filters.origin && filters.origin !== 'ALL') {
      sql += ' AND origin = ?'
      params.push(filters.origin)
    }

    if (filters.hasWarning) {
      sql += ' AND warning IS NOT NULL'
    }

    if (filters.minNutrition > 0) {
      sql += ' AND (nutritionScore >= ? OR efficacyScore >= ?)'
      params.push(filters.minNutrition, filters.minNutrition)
    }

    if (filters.harvestMonth) {
      sql += ` AND id IN (
        SELECT plant_id FROM harvest_months WHERE month = ?
      )`
      params.push(filters.harvestMonth)
    }

    if (filters.region) {
      sql += ' AND region LIKE ?'
      params.push(`%${filters.region}%`)
    }

    // Execute query
    const plants = queryAsObjects(sql, params)

    // Enrich with related data
    return plants.map(plant => enrichPlant(plant))
  }

  /**
   * Get a single plant by ID
   */
  const getPlant = (plantId) => {
    const plants = queryAsObjects('SELECT * FROM plants WHERE id = ?', [plantId])
    
    if (plants.length === 0) {
      return null
    }

    return enrichPlant(plants[0])
  }

  /**
   * Enrich plant with related data (uses, harvest months, etc.)
   */
  const enrichPlant = (plant) => {
    // Get uses
    const uses = queryAsObjects(
      'SELECT use_name FROM plant_uses WHERE plant_id = ?',
      [plant.id]
    ).map(row => row.use_name)

    // Get harvest months
    const harvestMonths = queryAsObjects(
      'SELECT month FROM harvest_months WHERE plant_id = ? ORDER BY month',
      [plant.id]
    ).map(row => row.month)

    // Get certifications
    const certification = queryAsObjects(
      'SELECT certification FROM certifications WHERE plant_id = ?',
      [plant.id]
    ).map(row => row.certification)

    // Get keywords
    const keywords = queryAsObjects(
      'SELECT keyword FROM keywords WHERE plant_id = ?',
      [plant.id]
    ).map(row => row.keyword)

    return {
      ...plant,
      uses,
      harvestMonths,
      certification,
      keywords
    }
  }

  /**
   * Full-text search
   */
  const searchPlants = (searchQuery) => {
    if (!searchQuery || searchQuery.trim().length === 0) {
      return []
    }

    // Use FTS5 if available, otherwise fallback to LIKE
    try {
      const plantIds = queryAsObjects(
        'SELECT id FROM plants_fts WHERE plants_fts MATCH ? ORDER BY rank LIMIT 50',
        [searchQuery]
      ).map(row => row.id)

      if (plantIds.length === 0) {
        return []
      }

      // Get full plant data
      const placeholders = plantIds.map(() => '?').join(',')
      const plants = queryAsObjects(
        `SELECT * FROM plants WHERE id IN (${placeholders})`,
        plantIds
      )

      return plants.map(plant => enrichPlant(plant))

    } catch (err) {
      // Fallback to LIKE search
      console.warn('FTS search failed, using LIKE fallback:', err)
      
      const searchPattern = `%${searchQuery}%`
      const plants = queryAsObjects(
        `SELECT * FROM plants 
         WHERE name LIKE ? 
            OR scientificName LIKE ? 
            OR description LIKE ? 
            OR region LIKE ?
         LIMIT 50`,
        [searchPattern, searchPattern, searchPattern, searchPattern]
      )

      return plants.map(plant => enrichPlant(plant))
    }
  }

  /**
   * Get database statistics
   */
  const getStats = () => {
    // Total plants
    const totalResult = queryAsObjects('SELECT COUNT(*) as count FROM plants')
    const total = totalResult[0]?.count || 0

    // By type
    const byTypeResults = queryAsObjects(
      'SELECT type, COUNT(*) as count FROM plants GROUP BY type'
    )
    const byType = {}
    byTypeResults.forEach(row => {
      byType[row.type] = row.count
    })

    // By origin
    const byOriginResults = queryAsObjects(
      'SELECT origin, COUNT(*) as count FROM plants GROUP BY origin'
    )
    const byOrigin = {}
    byOriginResults.forEach(row => {
      byOrigin[row.origin] = row.count
    })

    // With warnings
    const warningsResult = queryAsObjects(
      'SELECT COUNT(*) as count FROM plants WHERE warning IS NOT NULL'
    )
    const withWarnings = warningsResult[0]?.count || 0

    // Unique uses
    const usesResult = queryAsObjects(
      'SELECT COUNT(DISTINCT use_name) as count FROM plant_uses'
    )
    const uniqueUses = usesResult[0]?.count || 0

    return {
      total,
      byType,
      byOrigin,
      withWarnings,
      uniqueUses
    }
  }

  /**
   * Get all categories with counts
   */
  const getCategories = () => {
    const results = queryAsObjects(
      'SELECT type, COUNT(*) as count FROM plants GROUP BY type ORDER BY count DESC'
    )

    return results.map(row => ({
      name: row.type,
      count: row.count
    }))
  }

  /**
   * Close the database
   */
  const closeDatabase = () => {
    if (db.value) {
      db.value.close()
      db.value = null
      isInitialized.value = false
      queryCache.clear()
    }
  }

  return {
    // State
    db: computed(() => db.value),
    isInitialized: computed(() => isInitialized.value),
    isLoading: computed(() => isLoading.value),
    error: computed(() => error.value),

    // Methods
    initDatabase,
    query,
    queryAsObjects,
    getPlants,
    getPlant,
    searchPlants,
    getStats,
    getCategories,
    closeDatabase
  }
}
