/**
 * Botanical Library API Composable
 * Provides methods to fetch plant data from the backend API
 */

import { ref, computed } from 'vue'

const API_BASE_URL = 'http://localhost:5000/api'

// Shared state for caching
const plantsCache = ref(new Map())
const statsCache = ref(null)

export function useBotanicalAPI() {
  const loading = ref(false)
  const error = ref(null)

  /**
   * Fetch plants with optional filters
   */
  const fetchPlants = async (filters = {}) => {
    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams()
      
      // Add filters to query params
      Object.entries(filters).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== '' && value !== 'ALL') {
          params.append(key, value)
        }
      })

      const response = await fetch(`${API_BASE_URL}/plants?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch plants')
      }

      // Cache the results
      result.data.forEach(plant => {
        plantsCache.value.set(plant.id, plant)
      })

      return result
    } catch (err) {
      error.value = err.message
      console.error('Error fetching plants:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch a single plant by ID
   */
  const fetchPlant = async (plantId) => {
    // Check cache first
    if (plantsCache.value.has(plantId)) {
      return plantsCache.value.get(plantId)
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/plants/${plantId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.error || 'Plant not found')
      }

      // Cache the result
      plantsCache.value.set(plantId, result.data)

      return result.data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching plant:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Search plants using full-text search
   */
  const searchPlants = async (query) => {
    if (!query || query.trim().length === 0) {
      return { data: [], total: 0 }
    }

    loading.value = true
    error.value = null

    try {
      const params = new URLSearchParams({ q: query })
      const response = await fetch(`${API_BASE_URL}/search?${params}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.error || 'Search failed')
      }

      return result
    } catch (err) {
      error.value = err.message
      console.error('Error searching plants:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch database statistics
   */
  const fetchStats = async () => {
    // Return cached stats if available
    if (statsCache.value) {
      return statsCache.value
    }

    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/stats`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch stats')
      }

      // Cache the stats
      statsCache.value = result.data

      return result.data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching stats:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch all categories
   */
  const fetchCategories = async () => {
    loading.value = true
    error.value = null

    try {
      const response = await fetch(`${API_BASE_URL}/categories`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const result = await response.json()
      
      if (!result.success) {
        throw new Error(result.error || 'Failed to fetch categories')
      }

      return result.data
    } catch (err) {
      error.value = err.message
      console.error('Error fetching categories:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Check API health
   */
  const checkHealth = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/health`)
      const result = await response.json()
      return result.success && result.status === 'healthy'
    } catch (err) {
      console.error('API health check failed:', err)
      return false
    }
  }

  /**
   * Clear all caches
   */
  const clearCache = () => {
    plantsCache.value.clear()
    statsCache.value = null
  }

  return {
    // State
    loading: computed(() => loading.value),
    error: computed(() => error.value),
    
    // Methods
    fetchPlants,
    fetchPlant,
    searchPlants,
    fetchStats,
    fetchCategories,
    checkHealth,
    clearCache
  }
}
