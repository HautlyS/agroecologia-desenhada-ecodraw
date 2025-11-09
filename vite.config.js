import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'
import { copyFileSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

export default defineConfig({
  plugins: [
    vue(),
    // Copy SQLite database to public folder
    {
      name: 'copy-sqlite-db',
      buildStart() {
        const dbSource = resolve(__dirname, 'src/components/Library/botanical_library.db')
        const dbDest = resolve(__dirname, 'public/botanical_library.db')
        
        if (existsSync(dbSource)) {
          copyFileSync(dbSource, dbDest)
          console.log('✓ Copied botanical_library.db to public folder')
        } else {
          console.warn('⚠ botanical_library.db not found, run: python src/components/Library/convert_to_sqlite.py')
        }
      }
    },
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'robots.txt', 'apple-touch-icon.png'],
      manifest: {
        name: 'EcoDraw - Botanical Drawing App',
        short_name: 'EcoDraw',
        description: 'Modern botanical drawing and garden planning application',
        theme_color: '#FF4015',
        background_color: '#0a0a0a',
        display: 'standalone',
        orientation: 'landscape',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ]
      },
      workbox: {
        globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2,db}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 10,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          }
        ]
      }
    })
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  build: {
    target: 'esnext',
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'vue-vendor': ['vue'],
          'konva-vendor': ['konva', 'vue-konva']
        }
      }
    }
  },
  server: {
    port: 3000,
    open: true
  }
})
