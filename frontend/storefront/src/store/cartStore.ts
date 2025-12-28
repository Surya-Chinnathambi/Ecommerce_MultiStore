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
    items: CartItem[]
    addItem: (item: Omit<CartItem, 'quantity'> & { quantity?: number }) => void
    removeItem: (productId: string) => void
    updateQuantity: (productId: string, quantity: number) => void
    clearCart: () => void
    getTotalItems: () => number
    getTotalPrice: () => number
}

export const useCartStore = create<CartStore>()(
    persist(
        (set, get) => ({
            items: [],

            addItem: (item) => {
                const items = get().items
                const existingItem = items.find((i) => i.product_id === item.product_id)

                if (existingItem) {
                    set({
                        items: items.map((i) =>
                            i.product_id === item.product_id
                                ? { ...i, quantity: Math.min(i.quantity + (item.quantity || 1), i.max_quantity) }
                                : i
                        ),
                    })
                } else {
                    set({
                        items: [...items, { ...item, quantity: item.quantity || 1 }],
                    })
                }
            },

            removeItem: (productId) => {
                set({ items: get().items.filter((i) => i.product_id !== productId) })
            },

            updateQuantity: (productId, quantity) => {
                if (quantity <= 0) {
                    get().removeItem(productId)
                } else {
                    set({
                        items: get().items.map((i) =>
                            i.product_id === productId
                                ? { ...i, quantity: Math.min(quantity, i.max_quantity) }
                                : i
                        ),
                    })
                }
            },

            clearCart: () => set({ items: [] }),

            getTotalItems: () => get().items.reduce((sum, item) => sum + item.quantity, 0),

            getTotalPrice: () => get().items.reduce((sum, item) => sum + item.price * item.quantity, 0),
        }),
        {
            name: 'cart-storage',
        }
    )
)
