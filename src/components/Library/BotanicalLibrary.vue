<script setup>
import { ref, computed, reactive, inject, onMounted, onUnmounted, watch } from 'vue'
import { useSQLite } from '@/composables/useSQLite'

// ============================================================================
// COMPONENT STATE
// ============================================================================

const emit = defineEmits(['close', 'select', 'favorite'])

// Get accent color from app theme
const accentColor = inject('primaryColor', ref('#FF4015'))

// SQLite composable (browser-based, no backend needed!)
const { 
  initDatabase, 
  getPlants, 
  searchPlants, 
  getStats,
  isLoading: dbLoading, 
  isInitialized,
  error: dbError,
  closeDatabase
} = useSQLite()

// UI State
const selectedCategory = ref('ALL')
const searchQuery = ref('')
const viewMode = ref('grid') // 'grid' or 'list'
const sortBy = ref('name') // 'name', 'region', 'origin', 'uses', 'nutrition'
const favorites = reactive(new Set())
const expandedItems = reactive(new Set())
const isLoading = ref(false)
const loadError = ref(null)

// Data state
const allItems = ref([])
const dbStats = ref(null)

// Filter options
const activeFilters = reactive({
  origin: 'ALL', // 'ALL', 'NATIVE', 'INTRODUCED'
  hasWarning: false,
  harvestMonth: null, // 1-12 or null
  minNutritionScore: 0 // 0-10
})

// Pagination
const itemsPerPage = ref(12)
const currentPage = ref(1)

// Performance optimization - debounced search
const debouncedSearch = ref('')
let searchTimeout = null

// ============================================================================
// PLANT DATA - COMPREHENSIVE BRAZILIAN BOTANICAL DATABASE
// ============================================================================

const categories = [
  'ALL',
  'FRUITS',
  'HERBS',
  'VEGETABLES',
  'ROOTS',
  'TREES',
  'FLOWERS',
  'CROPS',
  'SPICES',
  'PANCS',
  'INVASIVE_SPECIES'
]

// ============================================================================
// DATA LOADING
// ============================================================================

// Initialize database and load data
onMounted(async () => {
  try {
    // Initialize the database (loads from /botanical_library.db)
    await initDatabase('/botanical_library.db')
    
    // Load initial data
    await loadPlants()
    await loadStats()
  } catch (err) {
    loadError.value = 'Failed to initialize database: ' + err.message
    console.error('Database initialization failed:', err)
  }
})

// Cleanup on unmount
onUnmounted(() => {
  closeDatabase()
})

// Watch for filter changes and reload data
watch([selectedCategory, () => activeFilters.origin, () => activeFilters.hasWarning, 
       () => activeFilters.harvestMonth, () => activeFilters.minNutritionScore], 
  () => {
    currentPage.value = 1
    loadPlants()
  }
)

// Load plants from SQLite database
const loadPlants = () => {
  if (!isInitialized.value) {
    return
  }

  isLoading.value = true
  loadError.value = null
  
  try {
    const filters = {
      type: selectedCategory.value !== 'ALL' ? selectedCategory.value : undefined,
      origin: activeFilters.origin !== 'ALL' ? activeFilters.origin : undefined,
      hasWarning: activeFilters.hasWarning,
      harvestMonth: activeFilters.harvestMonth || undefined,
      minNutrition: activeFilters.minNutritionScore > 0 ? activeFilters.minNutritionScore : undefined
    }
    
    allItems.value = getPlants(filters)
  } catch (err) {
    loadError.value = err.message
    console.error('Failed to load plants:', err)
    allItems.value = []
  } finally {
    isLoading.value = false
  }
}

// Load statistics
const loadStats = () => {
  if (!isInitialized.value) {
    return
  }

  try {
    dbStats.value = getStats()
  } catch (err) {
    console.error('Failed to load stats:', err)
  }
}

// Search plants
const performSearch = (query) => {
  if (!isInitialized.value) {
    return
  }

  if (!query || query.trim().length === 0) {
    loadPlants()
    return
  }
  
  isLoading.value = true
  loadError.value = null
  
  try {
    allItems.value = searchPlants(query)
  } catch (err) {
    loadError.value = err.message
    console.error('Search failed:', err)
    allItems.value = []
  } finally {
    isLoading.value = false
  }
}

// ============================================================================
// COMPUTED PROPERTIES & FILTERING LOGIC
// ============================================================================

const filteredAndSortedItems = computed(() => {
  let items = [...allItems.value]

  // Apply client-side search filter if debounced search is active
  if (debouncedSearch.value && debouncedSearch.value.length > 0) {
    const query = debouncedSearch.value.toLowerCase()
    items = items.filter(item =>
      item.name?.toLowerCase().includes(query) ||
      item.scientificName?.toLowerCase().includes(query) ||
      item.region?.toLowerCase().includes(query) ||
      item.description?.toLowerCase().includes(query) ||
      item.uses?.some(u => u.toLowerCase().includes(query)) ||
      item.keywords?.some(k => k.toLowerCase().includes(query))
    )
  }

  // Apply sorting
  items.sort((a, b) => {
    switch (sortBy.value) {
      case 'name':
        return (a.name || '').localeCompare(b.name || '', 'pt-BR')
      case 'region':
        return (a.region || '').localeCompare(b.region || '', 'pt-BR')
      case 'origin':
        return (a.origin || '').localeCompare(b.origin || '')
      case 'commercial':
        const commercialOrder = { 'HIGHEST': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'HISTORIC': 4, 'NEGATIVE': 5 }
        return (commercialOrder[a.commercialValue] || 5) - (commercialOrder[b.commercialValue] || 5)
      case 'nutrition':
        const scoreA = a.nutritionScore || a.efficacyScore || 0
        const scoreB = b.nutritionScore || b.efficacyScore || 0
        return scoreB - scoreA
      default:
        return 0
    }
  })

  return items
})

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * itemsPerPage.value
  const end = start + itemsPerPage.value
  return filteredAndSortedItems.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredAndSortedItems.value.length / itemsPerPage.value)
})

const stats = computed(() => {
  if (dbStats.value) {
    return {
      total: filteredAndSortedItems.value.length,
      native: dbStats.value.byOrigin?.NATIVE || 0,
      introduced: dbStats.value.byOrigin?.INTRODUCED || 0,
      withWarnings: dbStats.value.withWarnings || 0,
      favorites: favorites.size
    }
  }
  
  return {
    total: filteredAndSortedItems.value.length,
    native: filteredAndSortedItems.value.filter(i => i.origin === 'NATIVE').length,
    introduced: filteredAndSortedItems.value.filter(i => i.origin === 'INTRODUCED').length,
    withWarnings: filteredAndSortedItems.value.filter(i => i.warning).length,
    favorites: favorites.size
  }
})

const categoryCount = computed(() => {
  const counts = {}
  
  if (dbStats.value?.byType) {
    categories.forEach(cat => {
      if (cat === 'ALL') {
        counts[cat] = dbStats.value.total || 0
      } else {
        counts[cat] = dbStats.value.byType[cat] || 0
      }
    })
  } else {
    categories.forEach(cat => {
      if (cat === 'ALL') {
        counts[cat] = allItems.value.length
      } else {
        counts[cat] = allItems.value.filter(item => item.type === cat).length
      }
    })
  }
  
  return counts
})

// ============================================================================
// METHODS
// ============================================================================

const toggleFavorite = (itemId) => {
  if (favorites.has(itemId)) {
    favorites.delete(itemId)
  } else {
    favorites.add(itemId)
  }
  emit('favorite', { id: itemId, isFavorite: favorites.has(itemId) })
}

const toggleExpanded = (itemId) => {
  if (expandedItems.has(itemId)) {
    expandedItems.delete(itemId)
  } else {
    // Close other expanded items for better UX
    expandedItems.clear()
    expandedItems.add(itemId)
  }
}

const selectItem = (item) => {
  // Show detailed view by expanding the item
  if (!expandedItems.has(item.id)) {
    expandedItems.add(item.id)
  }
  emit('select', item)
}

const clearFilters = () => {
  selectedCategory.value = 'ALL'
  activeFilters.origin = 'ALL'
  activeFilters.hasWarning = false
  activeFilters.harvestMonth = null
  activeFilters.minNutritionScore = 0
  searchQuery.value = ''
  debouncedSearch.value = ''
  currentPage.value = 1
  loadPlants()
}

const getItemIcon = (type) => {
  const iconMap = {
    'FRUITS': '🍎',
    'HERBS': '�',
    'VEGETABLES': '🥕',
    'ROOTS': '🥔',
    'TREES': '🌳',
    'FLOWERS': '🌸',
    'CROPS': '🌾',
    'INVASIVE_SPECIES': '⚠️'
  }
  return iconMap[type] || '🌱'
}

const getOriginBadge = (origin) => {
  return origin === 'NATIVE' ? '🇧🇷 Nativo' : '🌍 Introduzido'
}

const getSeverityColor = (severity) => {
  const colors = {
    'CRÍTICA': '#DC143C',
    'ALTA': '#FF6347',
    'MÉDIA': '#FFA500',
    'BAIXA': '#FFD700'
  }
  return colors[severity] || '#808080'
}

const getNutritionScore = (item) => {
  return item.nutritionScore || item.efficacyScore || 0
}

const getScoreColor = (score) => {
  if (score >= 9) return '#4caf50'
  if (score >= 8) return '#8bc34a'
  if (score >= 7) return '#ffc107'
  if (score >= 6) return '#ff9800'
  return '#ff5722'
}

// Debounce search input
const handleSearchInput = (event) => {
  searchQuery.value = event.target.value
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    debouncedSearch.value = searchQuery.value
    currentPage.value = 1
    
    // Use full-text search for better performance
    if (searchQuery.value.length > 2) {
      performSearch(searchQuery.value)
    } else if (searchQuery.value.length === 0) {
      loadPlants()
    }
  }, 300)
}

// Keyboard navigation
const handleKeydown = (event) => {
  if (event.key === 'Escape') {
    if (expandedItems.size > 0) {
      expandedItems.clear()
    } else {
      emit('close')
    }
  }
}

</script>

<template>
  <div class="botanic-library" @click.self="emit('close')" @keydown="handleKeydown" tabindex="0">
    <div class="library-container">
      <!-- HEADER -->
      <div class="library-header">
        <div class="header-top">
          <h1>🌿 BRAZILIAN BOTANICAL LIBRARY</h1>
          <button class="close-btn" @click="emit('close')" aria-label="Close">
            <span>✕</span>
          </button>
        </div>

        <!-- SEARCH BAR -->
        <div class="search-container">
          <input
            :value="searchQuery"
            @input="handleSearchInput"
            type="text"
            placeholder="Buscar por nome, científico, região, usos..."
            class="search-input"
            autocomplete="off"
          />
          <span class="search-icon">🔍</span>
          <button
            v-if="searchQuery"
            class="clear-search-btn"
            @click="searchQuery = ''; debouncedSearch = ''; currentPage = 1"
            aria-label="Clear search"
          >
            ✕
          </button>
        </div>

        <!-- STATS -->
        <div class="stats-bar">
          <div class="stat">
            <span class="stat-label">Total:</span>
            <span class="stat-value">{{ stats.total }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Nativas:</span>
            <span class="stat-value">{{ stats.native }}</span>
          </div>
          <div class="stat">
            <span class="stat-label">Introduzidas:</span>
            <span class="stat-value">{{ stats.introduced }}</span>
          </div>
          <div class="stat" v-if="stats.withWarnings > 0">
            <span class="stat-label">⚠️ Avisos:</span>
            <span class="stat-value warning">{{ stats.withWarnings }}</span>
          </div>
          <div class="stat" v-if="stats.favorites > 0">
            <span class="stat-label">❤️ Favoritos:</span>
            <span class="stat-value favorite">{{ stats.favorites }}</span>
          </div>
          <div class="stat api-status">
            <span class="stat-label">DB:</span>
            <span :class="['stat-value', 'status-indicator', { 'connected': isInitialized, 'disconnected': !isInitialized }]">
              {{ isInitialized ? '🟢 Carregado' : (dbLoading ? '🟡 Carregando...' : '🔴 Erro') }}
            </span>
          </div>
        </div>
      </div>

      <!-- MAIN CONTENT -->
      <div class="library-main">
        <!-- SIDEBAR FILTERS -->
        <aside class="filters-sidebar">
          <div class="filter-section">
            <h3>Categorias</h3>
            <div class="category-buttons">
              <button
                v-for="cat in categories"
                :key="cat"
                :class="['cat-btn', { active: selectedCategory === cat }]"
                @click="selectedCategory = cat; currentPage = 1"
              >
                {{ getItemIcon(cat) }} {{ cat }}
                <span class="cat-count">{{ categoryCount[cat] }}</span>
              </button>
            </div>
          </div>

          <div class="filter-section">
            <h3>Origem</h3>
            <div class="filter-options">
              <label>
                <input
                  v-model="activeFilters.origin"
                  type="radio"
                  value="ALL"
                  @change="currentPage = 1"
                />
                Todas
              </label>
              <label>
                <input
                  v-model="activeFilters.origin"
                  type="radio"
                  value="NATIVE"
                  @change="currentPage = 1"
                />
                Nativas 🇧🇷
              </label>
              <label>
                <input
                  v-model="activeFilters.origin"
                  type="radio"
                  value="INTRODUCED"
                  @change="currentPage = 1"
                />
                Introduzidas 🌍
              </label>
            </div>
          </div>

          <div class="filter-section">
            <h3>Opções</h3>
            <label>
              <input
                v-model="activeFilters.hasWarning"
                type="checkbox"
                @change="currentPage = 1"
              />
              Mostrar avisos apenas
            </label>
          </div>

          <div class="filter-section">
            <h3>Qualidade Nutricional</h3>
            <div class="nutrition-filter">
              <input
                v-model.number="activeFilters.minNutritionScore"
                type="range"
                min="0"
                max="10"
                step="0.5"
                @change="currentPage = 1"
                class="nutrition-slider"
              />
              <span class="nutrition-value">{{ activeFilters.minNutritionScore.toFixed(1) }}+</span>
            </div>
          </div>

          <div class="filter-section">
            <h3>Ordenar por</h3>
            <select v-model="sortBy" @change="currentPage = 1" class="sort-select">
              <option value="name">Nome</option>
              <option value="region">Região</option>
              <option value="origin">Origem</option>
              <option value="commercial">Valor Comercial</option>
              <option value="nutrition">Qualidade Nutricional</option>
            </select>
          </div>

          <button class="clear-btn" @click="clearFilters">
            Limpar Filtros
          </button>
        </aside>

        <!-- ITEMS GRID -->
        <div class="items-container">
          <!-- Loading State -->
          <div v-if="isLoading || dbLoading" class="loading-state">
            <div class="spinner"></div>
            <p>{{ dbLoading ? 'Inicializando banco de dados...' : 'Carregando plantas...' }}</p>
          </div>

          <!-- Error State -->
          <div v-else-if="loadError || dbError" class="error-state">
            <p>⚠️ Erro: {{ loadError || dbError }}</p>
            <button @click="loadPlants" class="retry-btn">Tentar Novamente</button>
          </div>

          <!-- No Results -->
          <div
            v-else-if="filteredAndSortedItems.length === 0"
            class="no-results"
          >
            <p>❌ Nenhuma planta encontrada com esses filtros.</p>
          </div>

          <!-- Items Grid -->
          <div v-else class="items-grid">
            <transition-group name="card-fade">
              <div
                v-for="item in paginatedItems"
                :key="item.id"
                :class="['plant-card', { expanded: expandedItems.has(item.id), warning: item.warning }]"
                :style="{ '--item-color': item.color }"
              >
              <!-- Card Header -->
              <div class="card-header" @click="toggleExpanded(item.id)">
                <div class="header-left">
                  <span class="type-icon">{{ getItemIcon(item.type) }}</span>
                  <div class="header-text">
                    <h4>{{ item.name }}</h4>
                    <p class="scientific">{{ item.scientificName }}</p>
                  </div>
                </div>
                <div class="header-right">
                  <button
                    class="favorite-btn"
                    :class="{ active: favorites.has(item.id) }"
                    @click.stop="toggleFavorite(item.id)"
                    aria-label="Add to favorites"
                  >
                    ❤️
                  </button>
                  <span class="expand-icon">{{ expandedItems.has(item.id) ? '▼' : '▶' }}</span>
                </div>
              </div>

              <!-- Quick Info -->
              <div class="quick-info">
                <span class="origin-badge">{{ getOriginBadge(item.origin) }}</span>
                <span class="region-badge">📍 {{ item.region }}</span>
                <span class="value-badge">{{ item.climate }}</span>
                <span
                  v-if="getNutritionScore(item) > 0"
                  class="nutrition-badge"
                  :style="{ color: getScoreColor(getNutritionScore(item)) }"
                >
                  ⭐ {{ getNutritionScore(item).toFixed(1) }}
                </span>
              </div>

              <!-- Warning Banner -->
              <div v-if="item.warning" class="warning-banner">
                <span class="warning-icon">⚠️</span>
                <span class="warning-text">{{ item.warning }}</span>
              </div>

              <!-- Expanded Content -->
              <div v-if="expandedItems.has(item.id)" class="expanded-content">
                <div class="content-section">
                  <h5>Descrição</h5>
                  <p>{{ item.description }}</p>
                </div>

                <div class="content-section">
                  <h5>Informações Detalhadas</h5>
                  <p>{{ item.detailedInfo }}</p>
                </div>

                <div class="info-grid">
                  <div class="info-item">
                    <label>Clima</label>
                    <span>{{ item.climate }}</span>
                  </div>
                  <div class="info-item">
                    <label>Tipo de Solo</label>
                    <span>{{ item.soilType }}</span>
                  </div>
                  <div class="info-item">
                    <label>Espaçamento</label>
                    <span>{{ item.spacing }}</span>
                  </div>
                  <div class="info-item">
                    <label>Meses de Colheita</label>
                    <span>{{ item.harvestMonths.length > 0 ? item.harvestMonths.join(', ') : 'N/A' }}</span>
                  </div>
                </div>

                <div class="content-section">
                  <h5>Usos</h5>
                  <div class="tags">
                    <span v-for="use in item.uses" :key="use" class="tag">
                      {{ use }}
                    </span>
                  </div>
                </div>

                <div v-if="item.certification" class="content-section">
                  <h5>Certificações</h5>
                  <div class="tags">
                    <span v-for="cert in item.certification" :key="cert" class="tag cert-tag">
                      ✓ {{ cert }}
                    </span>
                  </div>
                </div>

                <button class="select-btn" @click.stop="toggleExpanded(item.id)">
                  ✕ Fechar Detalhes
                </button>
              </div>
              </div>
            </transition-group>
          </div>

          <!-- PAGINATION -->
          <div v-if="totalPages > 1" class="pagination">
            <button
              :disabled="currentPage === 1"
              @click="currentPage = Math.max(1, currentPage - 1)"
            >
              ← Anterior
            </button>
            <span class="page-info">
              Página {{ currentPage }} de {{ totalPages }}
            </span>
            <button
              :disabled="currentPage === totalPages"
              @click="currentPage = Math.min(totalPages, currentPage + 1)"
            >
              Próxima →
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ============================================================================
   GLOBAL STYLES - DARK AMOLED THEME
   ============================================================================ */

.botanic-library {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.95);
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.library-container {
  background: #000000;
  border: 1px solid rgba(255, 64, 21, 0.2);
  border-radius: 16px;
  box-shadow: 0 20px 60px rgba(255, 64, 21, 0.3);
  max-width: 1400px;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* ============================================================================
   HEADER STYLES - DARK THEME
   ============================================================================ */

.library-header {
  border-bottom: 1px solid rgba(255, 64, 21, 0.2);
  padding: 24px;
  background: linear-gradient(135deg, #0a0a0a 0%, #1a1a1a 100%);
  color: #ffffff;
}

.header-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.library-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: linear-gradient(135deg, v-bind(accentColor) 0%, #ff8c5a 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.close-btn {
  background: rgba(255, 64, 21, 0.1);
  border: 1px solid rgba(255, 64, 21, 0.3);
  color: v-bind(accentColor);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 64, 21, 0.2);
  border-color: v-bind(accentColor);
  transform: rotate(90deg);
}

.search-container {
  position: relative;
  margin-bottom: 12px;
}

.search-input {
  width: 100%;
  padding: 12px 40px 12px 16px;
  border: 1px solid rgba(255, 64, 21, 0.2);
  border-radius: 8px;
  font-size: 14px;
  background: #0a0a0a;
  color: #ffffff;
  transition: all 0.2s;
}

.search-input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.search-input:focus {
  outline: none;
  background: #000000;
  border-color: v-bind(accentColor);
  box-shadow: 0 0 0 3px rgba(255, 64, 21, 0.1);
}

.search-icon {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  color: rgba(255, 255, 255, 0.4);
}

.stats-bar {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.stat {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-label {
  font-size: 12px;
  opacity: 0.7;
  color: rgba(255, 255, 255, 0.7);
}

.stat-value {
  font-size: 18px;
  font-weight: 700;
  background: rgba(255, 64, 21, 0.15);
  color: v-bind(accentColor);
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(255, 64, 21, 0.3);
}

.stat-value.warning {
  background: rgba(255, 68, 68, 0.15);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.3);
}

/* ============================================================================
   MAIN CONTENT - DARK THEME
   ============================================================================ */

.library-main {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 0;
  background: #000000;
}

/* SIDEBAR */
.filters-sidebar {
  width: 280px;
  padding: 20px;
  background: #0a0a0a;
  border-right: 1px solid rgba(255, 64, 21, 0.1);
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.filter-section h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 700;
  color: v-bind(accentColor);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.category-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.cat-btn {
  padding: 10px 12px;
  background: #000000;
  border: 1px solid rgba(255, 64, 21, 0.2);
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s;
  text-align: left;
  color: rgba(255, 255, 255, 0.7);
}

.cat-btn:hover {
  border-color: v-bind(accentColor);
  background: rgba(255, 64, 21, 0.05);
  color: #ffffff;
}

.cat-btn.active {
  background: v-bind(accentColor);
  color: #000000;
  border-color: v-bind(accentColor);
  box-shadow: 0 0 20px rgba(255, 64, 21, 0.3);
}

.filter-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filter-options label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.7);
  transition: color 0.2s;
}

.filter-options label:hover {
  color: #ffffff;
}

.filter-options input[type="radio"],
.filter-options input[type="checkbox"] {
  cursor: pointer;
  width: 14px;
  height: 14px;
  accent-color: v-bind(accentColor);
}

.sort-select {
  width: 100%;
  padding: 8px;
  border: 1px solid rgba(255, 64, 21, 0.2);
  border-radius: 8px;
  font-size: 13px;
  cursor: pointer;
  background: #000000;
  color: #ffffff;
  transition: all 0.2s;
}

.sort-select:focus {
  outline: none;
  border-color: v-bind(accentColor);
}

.clear-btn {
  padding: 10px;
  background: rgba(220, 53, 69, 0.2);
  color: #ff4444;
  border: 1px solid rgba(220, 53, 69, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s;
  margin-top: auto;
}

.clear-btn:hover {
  background: rgba(220, 53, 69, 0.3);
  border-color: #ff4444;
}

.clear-search-btn {
  position: absolute;
  right: 40px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 64, 21, 0.2);
  border: 1px solid rgba(255, 64, 21, 0.3);
  color: v-bind(accentColor);
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.clear-search-btn:hover {
  background: rgba(255, 64, 21, 0.3);
  transform: translateY(-50%) rotate(90deg);
}

.nutrition-filter {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nutrition-slider {
  flex: 1;
  height: 4px;
  border-radius: 2px;
  background: rgba(255, 64, 21, 0.2);
  outline: none;
  cursor: pointer;
  accent-color: v-bind(accentColor);
}

.nutrition-slider::-webkit-slider-thumb {
  appearance: none;
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: v-bind(accentColor);
  cursor: pointer;
  box-shadow: 0 0 8px rgba(255, 64, 21, 0.5);
}

.nutrition-slider::-moz-range-thumb {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: v-bind(accentColor);
  cursor: pointer;
  border: none;
  box-shadow: 0 0 8px rgba(255, 64, 21, 0.5);
}

.nutrition-value {
  font-size: 12px;
  font-weight: 700;
  color: v-bind(accentColor);
  min-width: 35px;
  text-align: right;
}

.cat-count {
  margin-left: auto;
  font-size: 10px;
  background: rgba(255, 64, 21, 0.2);
  color: rgba(255, 255, 255, 0.6);
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 700;
}

.cat-btn.active .cat-count {
  background: rgba(0, 0, 0, 0.3);
  color: #000000;
}

.nutrition-badge {
  background: rgba(255, 193, 7, 0.2);
  border-color: rgba(255, 193, 7, 0.3);
  font-weight: 700;
}

.stat-value.favorite {
  background: rgba(255, 64, 21, 0.15);
  color: #ff4444;
  border-color: rgba(255, 68, 68, 0.3);
}

.api-status .status-indicator {
  font-size: 12px;
  padding: 2px 8px;
}

.api-status .status-indicator.connected {
  background: rgba(76, 175, 80, 0.15);
  color: #4caf50;
  border-color: rgba(76, 175, 80, 0.3);
}

.api-status .status-indicator.disconnected {
  background: rgba(244, 67, 54, 0.15);
  color: #f44336;
  border-color: rgba(244, 67, 54, 0.3);
  animation: pulse-error 2s infinite;
}

@keyframes pulse-error {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ============================================================================
   TRANSITIONS & ANIMATIONS
   ============================================================================ */

.card-fade-enter-active,
.card-fade-leave-active {
  transition: all 0.3s ease;
}

.card-fade-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

.card-fade-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

.card-fade-move {
  transition: transform 0.3s ease;
}

/* Loading state */
.items-grid.loading {
  opacity: 0.5;
  pointer-events: none;
}

/* Focus styles for accessibility */
.botanic-library:focus {
  outline: none;
}

.plant-card:focus-within {
  box-shadow: 0 0 0 3px rgba(255, 64, 21, 0.3);
}

/* Smooth scroll behavior */
.items-container {
  scroll-behavior: smooth;
}

/* Performance optimization */
.plant-card {
  will-change: transform, opacity;
  contain: layout style paint;
}

.expanded-content {
  contain: layout style;
}

/* ITEMS CONTAINER */
.items-container {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  background: #000000;
}

.loading-state,
.error-state,
.no-results {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
  gap: 16px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 16px;
  text-align: center;
}

.loading-state .spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(255, 64, 21, 0.2);
  border-top-color: v-bind(accentColor);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-state {
  color: #ff4444;
}

.retry-btn {
  padding: 10px 20px;
  background: rgba(255, 64, 21, 0.2);
  color: v-bind(accentColor);
  border: 1px solid rgba(255, 64, 21, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: rgba(255, 64, 21, 0.3);
  border-color: v-bind(accentColor);
  transform: translateY(-1px);
}

.no-results {
  color: rgba(255, 255, 255, 0.4);
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
  flex: 1;
}

/* ============================================================================
   PLANT CARD STYLES - DARK THEME
   ============================================================================ */

.plant-card {
  --item-color: v-bind(accentColor);
  background: #0a0a0a;
  border: 1px solid var(--item-color);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  height: fit-content;
}

.plant-card:hover {
  box-shadow: 0 4px 20px color-mix(in srgb, var(--item-color) 25%, transparent);
  transform: translateY(-2px);
  border-color: var(--item-color);
}

.plant-card.warning {
  border-color: rgba(255, 68, 68, 0.5);
  background: rgba(255, 68, 68, 0.05);
}

.plant-card.expanded {
  position: relative;
  z-index: 100;
  box-shadow: 0 8px 30px color-mix(in srgb, var(--item-color) 30%, transparent);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 14px;
  background: linear-gradient(135deg, color-mix(in srgb, var(--item-color) 15%, transparent) 0%, color-mix(in srgb, var(--item-color) 5%, transparent) 100%);
  border-bottom: 1px solid color-mix(in srgb, var(--item-color) 30%, transparent);
  cursor: pointer;
  min-height: 60px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
  min-width: 0;
}

.type-icon {
  font-size: 24px;
  flex-shrink: 0;
  filter: drop-shadow(0 0 6px color-mix(in srgb, var(--item-color) 40%, transparent));
}

.header-text h4 {
  margin: 0 0 2px 0;
  font-size: 15px;
  font-weight: 700;
  color: #ffffff;
}

.scientific {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-style: italic;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.favorite-btn {
  background: none;
  border: none;
  font-size: 18px;
  cursor: pointer;
  opacity: 0.3;
  transition: all 0.2s;
  filter: grayscale(1);
  padding: 0;
}

.favorite-btn:hover {
  opacity: 0.7;
  filter: grayscale(0);
  transform: scale(1.1);
}

.favorite-btn.active {
  opacity: 1;
  filter: grayscale(0);
  animation: heartbeat 0.3s ease;
}

@keyframes heartbeat {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.2); }
}

.expand-icon {
  font-size: 11px;
  color: var(--item-color);
  transition: transform 0.2s;
}

.quick-info {
  display: flex;
  gap: 6px;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.3);
  flex-wrap: wrap;
}

.quick-info span {
  font-size: 10px;
  padding: 3px 7px;
  background: color-mix(in srgb, var(--item-color) 10%, transparent);
  border-radius: 6px;
  border: 1px solid color-mix(in srgb, var(--item-color) 20%, transparent);
  color: rgba(255, 255, 255, 0.8);
}

.origin-badge {
  background: rgba(46, 125, 50, 0.2);
  color: #4caf50;
  border-color: rgba(76, 175, 80, 0.3);
}

.region-badge {
  background: rgba(21, 101, 192, 0.2);
  color: #42a5f5;
  border-color: rgba(66, 165, 245, 0.3);
}

.value-badge {
  background: color-mix(in srgb, var(--item-color) 20%, transparent);
  color: var(--item-color);
  border-color: color-mix(in srgb, var(--item-color) 30%, transparent);
}

.warning-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  background: rgba(255, 193, 7, 0.1);
  border-bottom: 1px solid rgba(255, 193, 7, 0.3);
  color: #ffc107;
  font-size: 12px;
}

.warning-icon {
  font-size: 16px;
  flex-shrink: 0;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.expanded-content {
  padding: 14px;
  border-top: 1px solid color-mix(in srgb, var(--item-color) 20%, transparent);
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #000000;
  animation: expandDown 0.3s ease-out;
}

@keyframes expandDown {
  from {
    opacity: 0;
    max-height: 0;
  }
  to {
    opacity: 1;
    max-height: 1000px;
  }
}

.content-section h5 {
  margin: 0 0 6px 0;
  font-size: 11px;
  font-weight: 700;
  color: var(--item-color);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.content-section p {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 3px;
  padding: 6px 8px;
  background: color-mix(in srgb, var(--item-color) 5%, transparent);
  border-radius: 6px;
  border: 1px solid color-mix(in srgb, var(--item-color) 10%, transparent);
}

.info-item label {
  font-size: 9px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
}

.info-item span {
  font-size: 12px;
  color: #ffffff;
}

.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: 4px 8px;
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  transition: all 0.2s;
}

.tag:hover {
  background: rgba(76, 175, 80, 0.3);
  transform: translateY(-1px);
}

.tag.cert-tag {
  background: rgba(156, 39, 176, 0.2);
  color: #ab47bc;
  border-color: rgba(171, 71, 188, 0.3);
}

.select-btn {
  padding: 10px 16px;
  background: rgba(255, 64, 21, 0.2);
  color: v-bind(accentColor);
  border: 1px solid rgba(255, 64, 21, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 13px;
  transition: all 0.2s;
}

.select-btn:hover {
  background: rgba(255, 64, 21, 0.3);
  border-color: v-bind(accentColor);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(255, 64, 21, 0.2);
}

/* ============================================================================
   PAGINATION - DARK THEME
   ============================================================================ */

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 64, 21, 0.2);
}

.pagination button {
  padding: 8px 12px;
  background: rgba(255, 64, 21, 0.2);
  color: v-bind(accentColor);
  border: 1px solid rgba(255, 64, 21, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  background: rgba(255, 64, 21, 0.3);
  border-color: v-bind(accentColor);
  transform: translateY(-1px);
}

.pagination button:disabled {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.1);
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  min-width: 120px;
  text-align: center;
}

/* ============================================================================
   RESPONSIVE DESIGN
   ============================================================================ */

@media (max-width: 1024px) {
  .items-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .library-container {
    flex-direction: column;
    max-height: 95vh;
  }

  .library-main {
    flex-direction: column;
  }

  .filters-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid #e0e0e0;
    max-height: 300px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .library-header h1 {
    font-size: 20px;
  }

  .items-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .botanic-library {
    padding: 10px;
  }

  .library-header {
    padding: 16px;
  }

  .library-header h1 {
    font-size: 18px;
  }

  .filters-sidebar {
    grid-template-columns: 1fr;
    max-height: none;
  }

  .stats-bar {
    gap: 12px;
  }

  .stat-label {
    display: none;
  }
}

/* ============================================================================
   SCROLLBAR STYLES - DARK THEME
   ============================================================================ */

.filters-sidebar::-webkit-scrollbar,
.items-container::-webkit-scrollbar,
.expanded-content::-webkit-scrollbar {
  width: 8px;
}

.filters-sidebar::-webkit-scrollbar-track,
.items-container::-webkit-scrollbar-track,
.expanded-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.3);
}

.filters-sidebar::-webkit-scrollbar-thumb,
.items-container::-webkit-scrollbar-thumb,
.expanded-content::-webkit-scrollbar-thumb {
  background: rgba(255, 64, 21, 0.3);
  border-radius: 4px;
}

.filters-sidebar::-webkit-scrollbar-thumb:hover,
.items-container::-webkit-scrollbar-thumb:hover,
.expanded-content::-webkit-scrollbar-thumb:hover {
  background: v-bind(accentColor);
}

.info-item span {
  font-size: 11px;
  color: #ffffff;
}

.tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.tag {
  display: inline-block;
  padding: 3px 7px;
  background: rgba(76, 175, 80, 0.2);
  color: #4caf50;
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 6px;
  font-size: 10px;
  font-weight: 600;
  transition: all 0.2s;
}

.tag:hover {
  background: rgba(76, 175, 80, 0.3);
  transform: translateY(-1px);
}

.tag.cert-tag {
  background: rgba(156, 39, 176, 0.2);
  color: #ab47bc;
  border-color: rgba(171, 71, 188, 0.3);
}

.select-btn {
  padding: 8px 14px;
  background: color-mix(in srgb, var(--item-color) 20%, transparent);
  color: var(--item-color);
  border: 1px solid color-mix(in srgb, var(--item-color) 30%, transparent);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s;
  margin-top: 4px;
}

.select-btn:hover {
  background: color-mix(in srgb, var(--item-color) 30%, transparent);
  border-color: var(--item-color);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--item-color) 20%, transparent);
}

/* ============================================================================
   PAGINATION - DARK THEME
   ============================================================================ */

.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid rgba(255, 64, 21, 0.2);
}

.pagination button {
  padding: 8px 12px;
  background: rgba(255, 64, 21, 0.2);
  color: v-bind(accentColor);
  border: 1px solid rgba(255, 64, 21, 0.3);
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  font-size: 12px;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  background: rgba(255, 64, 21, 0.3);
  border-color: v-bind(accentColor);
  transform: translateY(-1px);
}

.pagination button:disabled {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.3);
  border-color: rgba(255, 255, 255, 0.1);
  cursor: not-allowed;
}

.page-info {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  min-width: 120px;
  text-align: center;
}

/* ============================================================================
   RESPONSIVE DESIGN
   ============================================================================ */

@media (max-width: 1024px) {
  .items-grid {
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  }
}

@media (max-width: 768px) {
  .library-container {
    flex-direction: column;
    max-height: 95vh;
  }

  .library-main {
    flex-direction: column;
  }

  .filters-sidebar {
    width: 100%;
    border-right: none;
    border-bottom: 1px solid rgba(255, 64, 21, 0.1);
    max-height: 300px;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .library-header h1 {
    font-size: 20px;
  }

  .items-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .botanic-library {
    padding: 10px;
  }

  .library-header {
    padding: 16px;
  }

  .library-header h1 {
    font-size: 18px;
  }

  .filters-sidebar {
    grid-template-columns: 1fr;
    max-height: none;
  }

  .stats-bar {
    gap: 12px;
  }

  .stat-label {
    display: none;
  }
}

/* ============================================================================
   SCROLLBAR STYLES - DARK THEME
   ============================================================================ */

.filters-sidebar::-webkit-scrollbar,
.items-container::-webkit-scrollbar,
.expanded-content::-webkit-scrollbar {
  width: 8px;
}

.filters-sidebar::-webkit-scrollbar-track,
.items-container::-webkit-scrollbar-track,
.expanded-content::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.3);
}

.filters-sidebar::-webkit-scrollbar-thumb,
.items-container::-webkit-scrollbar-thumb,
.expanded-content::-webkit-scrollbar-thumb {
  background: rgba(255, 64, 21, 0.3);
  border-radius: 4px;
}

.filters-sidebar::-webkit-scrollbar-thumb:hover,
.items-container::-webkit-scrollbar-thumb:hover,
.expanded-content::-webkit-scrollbar-thumb:hover {
  background: v-bind(accentColor);
}
</style>
