import { Link } from 'react-router-dom'
import { ShoppingCart, Heart, Eye, Zap } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'
import { useState, useEffect } from 'react'
import QuickViewModal from '@/components/QuickViewModal'
import FlyToCart from '@/components/animations/FlyToCart'

interface Product {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    quantity: number
    is_in_stock: boolean
    description?: string
}

interface ProductCardProps {
    product: Product
    viewMode?: 'grid' | 'list'
}

export default function ProductCard({ product, viewMode = 'grid' }: ProductCardProps) {
    const addItem = useCartStore((state) => state.addItem)
    const { isWishlisted, toggleWishlist, fetchWishlist, isLoaded } = useWishlistStore()
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
    const [imageLoaded, setImageLoaded] = useState(false)
    const [showQuickView, setShowQuickView] = useState(false)
    const [triggerFly, setTriggerFly] = useState(false)

    useEffect(() => {
        if (isAuthenticated && !isLoaded) fetchWishlist()
    }, [isAuthenticated])

    const wishlisted = isWishlisted(product.id)
    const savings = product.mrp - product.selling_price
    const isLowStock = product.is_in_stock && product.quantity > 0 && product.quantity <= 5

    const handleAddToCart = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!product.is_in_stock) { toast.error('This product is out of stock'); return }
        addItem({ product_id: product.id, name: product.name, price: product.selling_price, image: product.thumbnail, max_quantity: product.quantity })
        setTriggerFly(true)
        toast.success('Added to cart', product.name)
    }

    const handleWishlist = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!isAuthenticated) { toast.info('Sign in to save items to wishlist'); return }
        toggleWishlist(product.id)
    }

    /* ── List view ─────────────────────────────────────────────────────── */
    if (viewMode === 'list') {
        return (
            <Link to={`/products/${product.id}`} className="card card-hover flex gap-5 group overflow-hidden p-4">
                {/* Image */}
                <div className="relative w-28 sm:w-36 flex-shrink-0 rounded-[var(--radius-xl)] overflow-hidden bg-bg-tertiary self-start aspect-square">
                    {product.thumbnail ? (
                        <img
                            src={product.thumbnail}
                            alt={product.name}
                            className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-text-quaternary text-xs">No image</div>
                    )}
                    {product.discount_percent > 0 && (
                        <span className="absolute top-1.5 left-1.5 badge badge-danger shadow-sm text-[10px]">
                            -{product.discount_percent}%
                        </span>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 flex flex-col justify-between min-w-0 py-1">
                    <div>
                        <h3 className="font-semibold text-text-primary group-hover:text-theme-primary transition-colors line-clamp-2 text-base leading-snug mb-1">
                            {product.name}
                        </h3>
                        {product.description && (
                            <p className="text-text-tertiary text-sm line-clamp-2 leading-relaxed">{product.description}</p>
                        )}
                    </div>
                    <div className="flex items-center justify-between mt-4 gap-3">
                        <div>
                            <div className="flex items-baseline gap-2">
                                <span className="text-xl font-black text-text-primary">₹{product.selling_price.toLocaleString('en-IN')}</span>
                                {product.discount_percent > 0 && (
                                    <span className="text-sm text-text-quaternary line-through">₹{product.mrp.toLocaleString('en-IN')}</span>
                                )}
                            </div>
                            {savings > 0 && (
                                <p className="text-xs font-medium text-emerald-600 dark:text-emerald-400 mt-0.5">
                                    Save ₹{savings.toLocaleString('en-IN')}
                                </p>
                            )}
                        </div>
                        <button
                            onClick={handleAddToCart}
                            disabled={!product.is_in_stock}
                            className="btn btn-primary btn-sm flex-shrink-0"
                        >
                            <ShoppingCart className="h-3.5 w-3.5" />
                            <span className="hidden sm:inline">Add to Cart</span>
                        </button>
                    </div>
                </div>
            </Link>
        )
    }

    /* ── Grid view ─────────────────────────────────────────────────────── */
    return (
        <div className="group relative">
            <FlyToCart 
                trigger={triggerFly} 
                image={product.thumbnail} 
                onAnimationComplete={() => setTriggerFly(false)} 
            />
            <Link
                to={`/products/${product.id}`}
                className="block rounded-[var(--radius-2xl)] border border-border-color bg-bg-primary overflow-hidden transition-all duration-300 hover-lift-premium"
            >
                {/* Image */}
                <div className="aspect-[4/3] bg-bg-tertiary relative overflow-hidden">
                    {!imageLoaded && <div className="absolute inset-0 skeleton" />}
                    {product.thumbnail ? (
                        <img
                            src={product.thumbnail}
                            alt={product.name}
                            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-105 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                            onLoad={() => setImageLoaded(true)}
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-text-quaternary text-xs">No image</div>
                    )}

                    {/* Top badges */}
                    <div className="absolute top-3 left-3 flex flex-col gap-1.5">
                        {product.discount_percent > 0 && (
                            <span className="badge badge-danger shadow-sm text-[10px] font-bold">
                                <Zap className="h-2.5 w-2.5" />
                                -{product.discount_percent}%
                            </span>
                        )}
                        {!product.is_in_stock && (
                            <span className="inline-flex items-center rounded-full border border-border-color bg-bg-primary/85 px-2 py-0.5 text-[10px] font-semibold text-text-secondary backdrop-blur-sm">
                                Out of stock
                            </span>
                        )}
                        {isLowStock && (
                            <span className="inline-flex items-center rounded-full bg-orange-500/90 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur-sm">
                                Only {product.quantity} left
                            </span>
                        )}
                    </div>

                    {/* Action buttons */}
                    <div className="absolute top-3 right-3 flex flex-col gap-2">
                        <button
                            onClick={handleWishlist}
                            aria-label={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
                            className={`h-8 w-8 rounded-full shadow-md flex items-center justify-center transition-all duration-200
                                ${wishlisted
                                    ? 'bg-red-500 text-white scale-100 opacity-100'
                                    : 'bg-bg-primary/90 text-text-tertiary opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 backdrop-blur-sm hover:bg-red-500 hover:text-white'
                                }`}
                        >
                            <Heart className={`h-3.5 w-3.5 ${wishlisted ? 'fill-current' : ''}`} />
                        </button>
                        <button
                            onClick={e => { e.preventDefault(); e.stopPropagation(); setShowQuickView(true) }}
                            aria-label="Quick view"
                            className="h-8 w-8 rounded-full bg-bg-primary/90 text-text-tertiary shadow-md flex items-center justify-center opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 backdrop-blur-sm hover:bg-theme-primary hover:text-white transition-all duration-200 delay-50"
                        >
                            <Eye className="h-3.5 w-3.5" />
                        </button>
                    </div>

                    {/* Add to cart slide-up */}
                    <div className="absolute inset-x-0 bottom-0 px-3 pb-3 pt-8 bg-gradient-to-t from-black/55 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-1 group-hover:translate-y-0">
                        <button
                            onClick={handleAddToCart}
                            disabled={!product.is_in_stock}
                            className="w-full btn btn-primary btn-sm bg-white/95 !text-gray-900 hover:bg-white border-0 shadow-md backdrop-blur-sm gap-1.5"
                        >
                            <ShoppingCart className="h-3.5 w-3.5" />
                            {product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                        </button>
                    </div>
                </div>

                {/* Card body */}
                <div className="p-4">
                    <h3 className="font-semibold text-sm text-text-primary line-clamp-2 leading-snug group-hover:text-theme-primary transition-colors mb-3 min-h-[2.75rem]">
                        {product.name}
                    </h3>

                    <div className="flex items-end justify-between gap-2">
                        <div>
                            <div className="flex items-baseline gap-1.5">
                                <span className="text-lg font-black text-text-primary tabular-nums">
                                    ₹{product.selling_price.toLocaleString('en-IN')}
                                </span>
                                {product.discount_percent > 0 && (
                                    <span className="text-xs text-text-quaternary line-through tabular-nums">
                                        ₹{product.mrp.toLocaleString('en-IN')}
                                    </span>
                                )}
                            </div>
                            {savings > 0 && (
                                <p className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">
                                    Save ₹{savings.toLocaleString('en-IN')}
                                </p>
                            )}
                        </div>
                    </div>
                </div>
            </Link>

            {showQuickView && (
                <QuickViewModal product={product} onClose={() => setShowQuickView(false)} />
            )}
        </div>
    )
}


interface Product {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    quantity: number
    is_in_stock: boolean
    description?: string
}

interface ProductCardProps {
    product: Product
    viewMode?: 'grid' | 'list'
}
