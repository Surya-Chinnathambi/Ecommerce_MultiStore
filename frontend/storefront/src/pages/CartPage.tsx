import { useCartStore } from '@/store/cartStore'
import { Link } from 'react-router-dom'
import { Trash2, Plus, Minus, ShoppingBag } from 'lucide-react'

export default function CartPage() {
    const { items, removeItem, updateQuantity, getTotalPrice, clearCart } = useCartStore()

    if (items.length === 0) {
        return (
            <div className="container mx-auto px-4 py-16 text-center">
                <ShoppingBag className="h-24 w-24 mx-auto text-text-tertiary mb-6" />
                <h2 className="text-2xl font-bold mb-4 text-text-primary">Your cart is empty</h2>
                <p className="text-text-secondary mb-8">Add some products to get started!</p>
                <Link to="/products" className="btn btn-primary">
                    Continue Shopping
                </Link>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-8 text-text-primary">Shopping Cart</h1>

            <div className="grid lg:grid-cols-3 gap-8">
                {/* Cart Items */}
                <div className="lg:col-span-2 space-y-4">
                    {items.map((item) => (
                        <div key={item.product_id} className="bg-bg-primary rounded-lg shadow-md p-4 flex items-center space-x-4 border border-border-color">
                            {item.image && (
                                <img
                                    src={item.image}
                                    alt={item.name}
                                    className="w-24 h-24 object-cover rounded"
                                />
                            )}

                            <div className="flex-1">
                                <h3 className="font-semibold text-lg mb-1 text-text-primary">{item.name}</h3>
                                <p className="text-text-secondary mb-2">₹{item.price.toFixed(2)}</p>

                                <div className="flex items-center space-x-3">
                                    <button
                                        onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                                        className="btn btn-secondary p-1"
                                        aria-label="Decrease quantity"
                                    >
                                        <Minus className="h-4 w-4" />
                                    </button>
                                    <span className="font-medium">{item.quantity}</span>
                                    <button
                                        onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                                        className="btn btn-secondary p-1"
                                        disabled={item.quantity >= item.max_quantity}
                                        aria-label="Increase quantity"
                                    >
                                        <Plus className="h-4 w-4" />
                                    </button>
                                </div>
                            </div>

                            <div className="text-right">
                                <p className="font-bold text-lg mb-2">
                                    ₹{(item.price * item.quantity).toFixed(2)}
                                </p>
                                <button
                                    onClick={() => removeItem(item.product_id)}
                                    className="text-red-600 hover:text-red-700"
                                    aria-label="Remove item from cart"
                                >
                                    <Trash2 className="h-5 w-5" />
                                </button>
                            </div>
                        </div>
                    ))}

                    <button
                        onClick={clearCart}
                        className="text-red-600 hover:text-red-700 font-medium"
                    >
                        Clear Cart
                    </button>
                </div>

                {/* Order Summary */}
                <div className="lg:col-span-1">
                    <div className="bg-bg-primary rounded-lg shadow-md p-6 sticky top-24 border border-border-color">
                        <h2 className="text-xl font-bold mb-4 text-text-primary">Order Summary</h2>

                        <div className="space-y-2 mb-4">
                            <div className="flex justify-between">
                                <span className="text-text-secondary">Subtotal ({items.reduce((sum, item) => sum + item.quantity, 0)} items)</span>
                                <span className="font-medium text-text-primary">₹{getTotalPrice().toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-text-secondary">Delivery</span>
                                <span className="font-medium text-text-primary">FREE</span>
                            </div>
                        </div>

                        <div className="border-t border-border-color pt-4 mb-6">
                            <div className="flex justify-between text-lg font-bold text-text-primary">
                                <span>Total</span>
                                <span>₹{getTotalPrice().toFixed(2)}</span>
                            </div>
                        </div>

                        <Link to="/checkout" className="w-full btn btn-primary block text-center">
                            Proceed to Checkout
                        </Link>

                        <Link to="/products" className="w-full btn btn-secondary block text-center mt-3">
                            Continue Shopping
                        </Link>
                    </div>
                </div>
            </div>
        </div>
    )
}
