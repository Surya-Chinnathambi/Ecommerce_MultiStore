import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export interface CartItem {
    product_id: string
    name: string
    price: number
    quantity: number
    image?: string
    max_quantity: number
}

interface CartStore {
    items: Record<string, CartItem>
    addItem: (item: Omit<CartItem, 'quantity'> & { quantity?: number }) => void
    removeItem: (productId: string) => void
    updateQuantity: (productId: string, quantity: number) => void
    clearCart: () => void
    getItemCount: () => number
    getTotalPrice: () => number
}

export const useCartStore = create<CartStore>()(
    persist(
        (set, get) => ({
            items: {},

            addItem: (item) => {
                const currentItems = get().items
                const pid = item.product_id
                const existing = currentItems[pid]

                if (existing) {
                    const newQty = Math.min(existing.quantity + (item.quantity || 1), existing.max_quantity)
                    set({
                        items: {
                            ...currentItems,
                            [pid]: { ...existing, quantity: newQty }
                        }
                    })
                } else {
                    set({
                        items: {
                            ...currentItems,
                            [pid]: { ...item, quantity: item.quantity || 1 }
                        }
                    })
                }
            },

            removeItem: (productId) => {
                const newItems = { ...get().items }
                delete newItems[productId]
                set({ items: newItems })
            },

            updateQuantity: (productId, quantity) => {
                const currentItems = get().items
                const item = currentItems[productId]
                if (!item) return

                if (quantity <= 0) {
                    get().removeItem(productId)
                } else {
                    set({
                        items: {
                            ...currentItems,
                            [productId]: { ...item, quantity: Math.min(quantity, item.max_quantity) }
                        }
                    })
                }
            },

            clearCart: () => set({ items: {} }),

            getItemCount: () => Object.values(get().items).reduce((sum, item) => sum + item.quantity, 0),

            getTotalPrice: () => Object.values(get().items).reduce((sum, item) => sum + item.price * item.quantity, 0),
        }),
        {
            name: 'cart-storage',
            // Migration: Convert old array-based storage to object-based
            migrate: (persistedState: any) => {
                if (Array.isArray(persistedState.items)) {
                    const normalized: Record<string, CartItem> = {}
                    persistedState.items.forEach((item: CartItem) => {
                        normalized[item.product_id] = item
                    })
                    return { ...persistedState, items: normalized }
                }
                return persistedState
            },
            version: 1,
        }
    )
)
