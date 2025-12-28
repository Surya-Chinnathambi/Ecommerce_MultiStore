export { }

declare global {
    interface CartItem {
        product_id: string
        name: string
        price: number
        quantity: number
        image?: string
        max_quantity?: number
    }
}
