import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 3000,
        host: true,
    },
    build: {
        // Trim chunk size warnings at 600 kB
        chunkSizeWarningLimit: 600,
        rollupOptions: {
            output: {
                manualChunks: {
                    // Core React runtime — changes rarely, maximises long-term cache hits
                    'vendor-react': ['react', 'react-dom'],
                    'vendor-router': ['react-router-dom'],
                    // Data-fetching
                    'vendor-query': ['@tanstack/react-query'],
                    // Forms & validation
                    'vendor-forms': ['react-hook-form', 'zod', '@hookform/resolvers'],
                    // Charts — large, lazy-loaded only on admin pages
                    'vendor-charts': ['recharts'],
                    // Icon library
                    'vendor-icons': ['lucide-react'],
                    // State management
                    'vendor-state': ['zustand'],
                },
            },
        },
    },
})
