import { useState, useEffect } from 'react'
import { useCartStore } from '@/store/cartStore'
import { Link } from 'react-router-dom'
import EmptyState3D from '@/components/ui/EmptyState3D'
import { Trash2, Plus, Minus, ShoppingBag, ArrowRight, Package, ShieldCheck, Truck, Tag, X, Gift } from 'lucide-react'
import { couponsApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import { motion, AnimatePresence } from 'framer-motion'
import confetti from 'canvas-confetti'
import Button3D from '@/components/ui/Button3D'

const FREE_SHIPPING_THRESHOLD = 499

export default function CartPage() {
    const { items: itemsMap, removeItem, updateQuantity, getTotalPrice, getItemCount, clearCart } = useCartStore()
    const [couponCode, setCouponCode] = useState('')
    const [couponApplied, setCouponApplied] = useState<{ discount: number; code: string } | null>(null)
    const [couponLoading, setCouponLoading] = useState(false)

    const items = Object.values(itemsMap)
    const cartTotal = getTotalPrice()
    const freeShippingRemaining = Math.max(0, FREE_SHIPPING_THRESHOLD - cartTotal)
    const freeShippingProgress = Math.min(100, (cartTotal / FREE_SHIPPING_THRESHOLD) * 100)
    const hasFreeShipping = cartTotal >= FREE_SHIPPING_THRESHOLD

    // Trigger confetti when free shipping is hit
    useEffect(() => {
        if (hasFreeShipping && items.length > 0) {
            confetti({
                particleCount: 100,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#10B981', '#34D399', '#6EE7B7']
            })
        }
    }, [hasFreeShipping, items.length])

    const handleCoupon = async () => {
        if (!couponCode.trim()) return
        setCouponLoading(true)
        try {
            const res = await couponsApi.validate({
                code: couponCode.trim().toUpperCase(),
                order_amount: cartTotal,
                item_count: getItemCount(),
            })
            const discount = res.data.data?.discount_amount ?? 0
            setCouponApplied({ discount, code: couponCode.trim().toUpperCase() })
            toast.success(`Coupon applied! You save ₹${discount.toFixed(2)}`)
        } catch {
            toast.error('Invalid or expired coupon code')
            setCouponApplied(null)
        } finally {
            setCouponLoading(false)
        }
    }

    if (items.length === 0) {
        return (
            <motion.div 
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="container mx-auto px-4 py-16"
            >
                <div>
                    <EmptyState3D 
                        title="Your cart is empty" 
                        description="Looks like you haven't added anything yet. Start shopping!" 
                    />
                    <div className="flex justify-center mt-8">
                        <Link to="/products">
                            <Button3D className="w-64">
                                <Package className="h-5 w-5" />
                                <span>Browse Products</span>
                            </Button3D>
                        </Link>
                    </div>
                </div>
            </motion.div>
        )
    }

    return (
        <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="container mx-auto px-4 py-8"
        >
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="section-title">Shopping Cart</h1>
                    <p className="section-subtitle">{getItemCount()} items in your cart</p>
                </div>
                <button
                    onClick={clearCart}
                    className="btn btn-ghost text-red-500 hover:bg-red-500/10"
                >
                    <Trash2 className="h-4 w-4" />
                    <span>Clear All</span>
                </button>
            </div>

            {/* ── Free Shipping Progress Bar ─────────────────────────────────────────────── */}
            <motion.div 
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                whileHover={{ scale: 1.01 }}
                className={`rounded-2xl p-4 mb-6 border transition-all duration-300 ${hasFreeShipping
                    ? 'bg-green-500/10 border-green-500/20 shadow-[0_0_20px_rgba(16,185,129,0.2)]'
                    : 'bg-theme-primary/5 border-theme-primary/10'
                }`}
            >
                <div className="flex items-center gap-2 mb-2">
                    <Truck className={`h-4 w-4 ${hasFreeShipping ? 'text-green-500' : 'text-theme-primary'}`} />
                    {hasFreeShipping ? (
                        <motion.p 
                            initial={{ x: -10, opacity: 0 }}
                            animate={{ x: 0, opacity: 1 }}
                            className="text-sm font-semibold text-green-600 dark:text-green-400"
                        >
                            🎉 You’ve unlocked <strong>Free Shipping</strong>!
                        </motion.p>
                    ) : (
                        <p className="text-sm font-medium text-text-secondary">
                            Add <span className="font-bold text-theme-primary">₹{freeShippingRemaining.toFixed(2)}</span> more to get <strong>Free Shipping</strong>
                        </p>
                    )}
                </div>
                <div className="h-3 bg-bg-tertiary rounded-full overflow-hidden relative">
                    <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${freeShippingProgress}%` }}
                        transition={{ type: 'spring', stiffness: 50, damping: 15 }}
                        className={`absolute top-0 left-0 h-full rounded-full ${hasFreeShipping ? 'bg-green-500' : 'bg-gradient-to-r from-theme-primary to-theme-accent'}`} 
                    />
                    {hasFreeShipping && (
                        <motion.div 
                            initial={{ x: '-100%' }}
                            animate={{ x: '200%' }}
                            transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                            className="absolute top-0 left-0 h-full w-1/3 bg-gradient-to-r from-transparent via-white/30 to-transparent skew-x-[-20deg]"
                        />
                    )}
                </div>
            </motion.div>

            <div className="grid lg:grid-cols-3 gap-8">
                {/* Cart Items */}
                <div className="lg:col-span-2 space-y-4">
                    <AnimatePresence mode='popLayout'>
                    {items.map((item) => (
                        <motion.div
                            key={item.product_id}
                            layout
                            initial={{ opacity: 0, scale: 0.9, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.8, x: -50 }}
                            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                            className="card card-hover p-4 flex gap-4"
                        >
                            {/* Product Image */}
                            <Link to={`/products/${item.product_id}`} className="flex-shrink-0">
                                {item.image ? (
                                    <img
                                        src={item.image}
                                        alt={item.name}
                                        className="w-24 h-24 md:w-32 md:h-32 object-cover rounded-xl"
                                    />
                                ) : (
                                    <div className="w-24 h-24 md:w-32 md:h-32 bg-bg-tertiary rounded-xl flex items-center justify-center">
                                        <Package className="h-8 w-8 text-text-tertiary" />
                                    </div>
                                )}
                            </Link>

                            {/* Product Info */}
                            <div className="flex-1 min-w-0">
                                <Link to={`/products/${item.product_id}`}>
                                    <h3 className="font-semibold text-lg text-text-primary hover:text-theme-primary transition-colors line-clamp-2">
                                        {item.name}
                                    </h3>
                                </Link>
                                <p className="text-text-secondary mt-1">₹{item.price.toFixed(2)} each</p>

                                {/* Quantity Controls */}
                                <div className="flex items-center gap-3 mt-4">
                                    <div className="flex items-center border-2 border-border-color rounded-xl overflow-hidden">
                                        <button
                                            onClick={() => updateQuantity(item.product_id, item.quantity - 1)}
                                            className="p-2 hover:bg-bg-tertiary transition-colors"
                                            aria-label="Decrease quantity"
                                        >
                                            <Minus className="h-4 w-4 text-text-primary" />
                                        </button>
                                        <span className="font-semibold w-10 text-center text-text-primary">{item.quantity}</span>
                                        <button
                                            onClick={() => updateQuantity(item.product_id, item.quantity + 1)}
                                            className="p-2 hover:bg-bg-tertiary transition-colors"
                                            disabled={item.quantity >= item.max_quantity}
                                            aria-label="Increase quantity"
                                        >
                                            <Plus className="h-4 w-4 text-text-primary" />
                                        </button>
                                    </div>
                                    {item.quantity >= item.max_quantity && (
                                        <span className="text-xs text-text-tertiary">Max qty</span>
                                    )}
                                </div>
                            </div>

                            {/* Price & Remove */}
                            <div className="flex flex-col items-end justify-between">
                                <span className="text-xl font-bold text-gradient">
                                    ₹{(item.price * item.quantity).toFixed(2)}
                                </span>
                                <button
                                    onClick={() => removeItem(item.product_id)}
                                    className="p-2 text-text-tertiary hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-all"
                                    aria-label="Remove item from cart"
                                >
                                    <Trash2 className="h-5 w-5" />
                                </button>
                            </div>
                        </motion.div>
                    ))}
                    </AnimatePresence>
                </div>

                {/* Order Summary */}
                <div className="lg:col-span-1">
                    <div className="card sticky top-24 space-y-6">
                        <h2 className="text-xl font-bold text-text-primary">Order Summary</h2>

                        {/* Summary Details */}
                        <div className="space-y-3">
                            <div className="flex justify-between text-text-secondary">
                                <span>Subtotal ({getItemCount()} items)</span>
                                <span className="font-medium text-text-primary">₹{getTotalPrice().toFixed(2)}</span>
                            </div>
                            <div className="flex justify-between text-text-secondary">
                                <span>Delivery</span>
                                <span className="font-medium text-green-600">FREE</span>
                            </div>
                            {couponApplied && (
                                <div className="flex justify-between text-green-600 dark:text-green-400">
                                    <span className="flex items-center gap-1.5">
                                        <Tag className="h-3.5 w-3.5" />
                                        Coupon ({couponApplied.code})
                                    </span>
                                    <span className="font-semibold">-₹{couponApplied.discount.toFixed(2)}</span>
                                </div>
                            )}
                        </div>

                        <div className="divider" />

                        <div className="flex justify-between text-lg font-bold text-text-primary">
                            <span>Total</span>
                            <span className="text-gradient">₹{(cartTotal - (couponApplied?.discount ?? 0)).toFixed(2)}</span>
                        </div>

                        {/* Trust Badges */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="flex items-center gap-2 text-sm text-text-secondary">
                                <ShieldCheck className="h-4 w-4 text-green-500" />
                                <span>Secure checkout</span>
                            </div>
                            <div className="flex items-center gap-2 text-sm text-text-secondary">
                                <Truck className="h-4 w-4 text-theme-primary" />
                                <span>Fast delivery</span>
                            </div>
                        </div>

                        {/* ── Coupon Code ── */}
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
                                <Gift className="h-4 w-4 text-theme-primary" />
                                Coupon Code
                            </label>
                            {couponApplied ? (
                                <div className="flex items-center justify-between rounded-xl bg-green-500/10 border border-green-500/20 px-3 py-2.5">
                                    <span className="text-sm font-semibold text-green-600 dark:text-green-400 flex items-center gap-1.5">
                                        <Tag className="h-3.5 w-3.5" />{couponApplied.code}
                                    </span>
                                    <button
                                        onClick={() => { setCouponApplied(null); setCouponCode('') }}
                                        className="text-text-tertiary hover:text-red-500 transition-colors"
                                        aria-label="Remove coupon"
                                    >
                                        <X className="h-4 w-4" />
                                    </button>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        value={couponCode}
                                        onChange={e => setCouponCode(e.target.value.toUpperCase())}
                                        onKeyDown={e => e.key === 'Enter' && handleCoupon()}
                                        placeholder="Enter coupon code"
                                        className="input flex-1 text-sm uppercase tracking-wider"
                                    />
                                    <button
                                        onClick={handleCoupon}
                                        disabled={couponLoading || !couponCode.trim()}
                                        className="btn btn-outline btn-sm flex-shrink-0"
                                    >
                                        {couponLoading ? '...' : 'Apply'}
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="divider" />

                        {/* Actions */}
                        <div className="space-y-4">
                            <Link to="/checkout">
                                <Button3D className="w-full">
                                    <span>Proceed to Checkout</span>
                                    <ArrowRight className="h-5 w-5" />
                                </Button3D>
                            </Link>

                            <Link to="/products">
                                <Button3D variant="secondary" className="w-full">
                                    Continue Shopping
                                </Button3D>
                            </Link>
                        </div>
                    </div>
                </div>
            </div>
        </motion.div>
    )
}
