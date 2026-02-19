import { useState, useCallback } from 'react'

const STORAGE_KEY = 'rv_products'
const MAX_ITEMS = 6

export interface RecentProduct {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    is_in_stock: boolean
    quantity: number
}

function readStorage(): RecentProduct[] {
    try {
        return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    } catch {
        return []
    }
}

/** Reads recently-viewed products directly from localStorage (no React state). */
export function readRecentlyViewed(): RecentProduct[] {
    return readStorage()
}

/** React hook that keeps recently-viewed list in sync with localStorage. */
export function useRecentlyViewed() {
    const [viewed, setViewed] = useState<RecentProduct[]>(readStorage)

    const addProduct = useCallback((product: RecentProduct) => {
        setViewed(prev => {
            const filtered = prev.filter(p => p.id !== product.id)
            const next = [product, ...filtered].slice(0, MAX_ITEMS)
            try {
                localStorage.setItem(STORAGE_KEY, JSON.stringify(next))
            } catch { /* storage quota exceeded — ignore */ }
            return next
        })
    }, [])

    const clearViewed = useCallback(() => {
        localStorage.removeItem(STORAGE_KEY)
        setViewed([])
    }, [])

    return { viewed, addProduct, clearViewed }
}
