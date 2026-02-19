import { create } from 'zustand'
import { wishlistApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'

export interface WishlistProduct {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    is_in_stock: boolean
    slug?: string
}

export interface WishlistItem {
    id: string
    product_id: string
    added_at: string
    product: WishlistProduct
}

interface WishlistState {
    items: WishlistItem[]
    productIds: Set<string>  // fast O(1) lookup
    isLoaded: boolean
    isLoading: boolean

    // Actions
    fetchWishlist: () => Promise<void>
    addToWishlist: (productId: string) => Promise<void>
    removeFromWishlist: (productId: string) => Promise<void>
    isWishlisted: (productId: string) => boolean
    toggleWishlist: (productId: string) => Promise<void>
    clearWishlist: () => Promise<void>
}

export const useWishlistStore = create<WishlistState>((set, get) => ({
    items: [],
    productIds: new Set(),
    isLoaded: false,
    isLoading: false,

    fetchWishlist: async () => {
        const { isLoaded, isLoading } = get()
        if (isLoaded || isLoading) return
        set({ isLoading: true })
        try {
            const res = await wishlistApi.getWishlist()
            const items: WishlistItem[] = res.data.data ?? []
            set({
                items,
                productIds: new Set(items.map((i) => i.product_id)),
                isLoaded: true,
            })
        } catch {
            // User may not be logged in — silently skip
        } finally {
            set({ isLoading: false })
        }
    },

    addToWishlist: async (productId: string) => {
        // Optimistic
        set((s) => ({ productIds: new Set([...s.productIds, productId]) }))
        try {
            const res = await wishlistApi.addToWishlist(productId)
            const newItem: WishlistItem = res.data.data
            if (newItem) {
                set((s) => ({
                    items: [newItem, ...s.items.filter((i) => i.product_id !== productId)],
                }))
            }
        } catch {
            // Rollback
            set((s) => {
                const ids = new Set(s.productIds)
                ids.delete(productId)
                return { productIds: ids }
            })
            toast.error('Failed to add to wishlist')
        }
    },

    removeFromWishlist: async (productId: string) => {
        // Optimistic
        set((s) => {
            const ids = new Set(s.productIds)
            ids.delete(productId)
            return { productIds: ids, items: s.items.filter((i) => i.product_id !== productId) }
        })
        try {
            await wishlistApi.removeFromWishlist(productId)
        } catch {
            toast.error('Failed to remove from wishlist')
            // Reload to re-sync
            set({ isLoaded: false })
            get().fetchWishlist()
        }
    },

    isWishlisted: (productId: string) => get().productIds.has(productId),

    toggleWishlist: async (productId: string) => {
        const { isWishlisted, addToWishlist, removeFromWishlist } = get()
        if (isWishlisted(productId)) {
            await removeFromWishlist(productId)
            toast.success('Removed from wishlist')
        } else {
            await addToWishlist(productId)
            toast.success('Added to wishlist')
        }
    },

    clearWishlist: async () => {
        try {
            await wishlistApi.clearWishlist()
            set({ items: [], productIds: new Set() })
            toast.success('Wishlist cleared')
        } catch {
            toast.error('Failed to clear wishlist')
        }
    },
}))
