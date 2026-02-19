import { Link } from 'react-router-dom'
import { ShoppingCart, Heart, Eye } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'
import { useState, useEffect } from 'react'
import QuickViewModal from '@/components/QuickViewModal'

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

    // Load wishlist once per session when user is authenticated
    useEffect(() => {
        if (isAuthenticated && !isLoaded) fetchWishlist()
    }, [isAuthenticated])

    const wishlisted = isWishlisted(product.id)

    const handleAddToCart = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()

        if (!product.is_in_stock) {
            toast.error('Product is out of stock')
            return
        }

        addItem({
            product_id: product.id,
            name: product.name,
            price: product.selling_price,
            image: product.thumbnail,
            max_quantity: product.quantity,
        })
        toast.success('Added to cart')
    }

    const handleWishlist = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!isAuthenticated) {
            toast.error('Please sign in to save to wishlist')
            return
        }
        toggleWishlist(product.id)
    }

    if (viewMode === 'list') {
        return (
            <Link to={`/products/${product.id}`} className="card card-hover flex gap-4 md:gap-6 group">
                <div className="w-32 md:w-48 flex-shrink-0">
                    <div className="aspect-square bg-bg-tertiary rounded-xl overflow-hidden relative">
                        {product.thumbnail ? (
                            <img
                                src={product.thumbnail}
                                alt={product.name}
                                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                                No Image
                            </div>
                        )}
                        {product.discount_percent > 0 && (
                            <div className="absolute top-2 left-2 badge badge-danger">
                                -{product.discount_percent}%
                            </div>
                        )}
                    </div>
                </div>
                <div className="flex-1 flex flex-col justify-between py-2">
                    <div>
                        <h3 className="font-semibold text-lg text-text-primary group-hover:text-theme-primary transition-colors line-clamp-2">
                            {product.name}
                        </h3>
                        {product.description && (
                            <p className="text-text-secondary text-sm mt-2 line-clamp-2">{product.description}</p>
                        )}
                    </div>
                    <div className="flex items-center justify-between mt-4">
                        <div className="flex items-baseline gap-2">
                            <span className="text-2xl font-bold text-gradient">₹{product.selling_price.toFixed(2)}</span>
                            {product.discount_percent > 0 && (
                                <span className="text-sm text-text-tertiary line-through">₹{product.mrp.toFixed(2)}</span>
                            )}
                        </div>
                        <button
                            onClick={handleAddToCart}
                            disabled={!product.is_in_stock}
                            className="btn btn-primary"
                        >
                            <ShoppingCart className="h-4 w-4" />
                            <span className="hidden md:inline">Add to Cart</span>
                        </button>
                    </div>
                </div>
            </Link>
        )
    }

    return (
        <div className="group relative">
            <Link to={`/products/${product.id}`} className="block card card-hover overflow-hidden p-0">
                {/* Image Container */}
                <div className="aspect-square bg-bg-tertiary relative overflow-hidden">
                    {!imageLoaded && (
                        <div className="absolute inset-0 skeleton" />
                    )}
                    {product.thumbnail ? (
                        <img
                            src={product.thumbnail}
                            alt={product.name}
                            className={`w-full h-full object-cover transition-all duration-500 group-hover:scale-110 ${imageLoaded ? 'opacity-100' : 'opacity-0'}`}
                            onLoad={() => setImageLoaded(true)}
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                            No Image
                        </div>
                    )}

                    {/* Badges */}
                    <div className="absolute top-3 left-3 flex flex-col gap-2">
                        {product.discount_percent > 0 && (
                            <span className="badge badge-danger shadow-sm">
                                -{product.discount_percent}%
                            </span>
                        )}
                        {!product.is_in_stock && (
                            <span className="badge bg-bg-tertiary/90 text-text-primary backdrop-blur-sm">
                                Out of Stock
                            </span>
                        )}
                        {product.is_in_stock && product.quantity > 0 && product.quantity <= 10 && (
                            <span className="badge bg-orange-500/90 text-white backdrop-blur-sm">
                                Only {product.quantity} left!
                            </span>
                        )}
                    </div>

                    {/* Quick Actions */}
                    <div className="absolute top-3 right-3 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-x-2 group-hover:translate-x-0">
                        <button
                            onClick={handleWishlist}
                            className={`p-2 rounded-full shadow-lg transition-all duration-300 ${wishlisted
                                ? 'bg-red-500 text-white'
                                : 'bg-bg-primary/90 text-text-secondary hover:bg-red-500 hover:text-white backdrop-blur-sm'
                                }`}
                            aria-label="Add to wishlist"
                        >
                            <Heart className={`h-4 w-4 ${wishlisted ? 'fill-current' : ''}`} />
                        </button>
                        <button
                            onClick={(e) => { e.preventDefault(); e.stopPropagation(); setShowQuickView(true) }}
                            className="p-2 rounded-full bg-bg-primary/90 text-text-secondary hover:bg-theme-primary hover:text-white shadow-lg transition-all duration-300 backdrop-blur-sm"
                            aria-label="Quick view"
                        >
                            <Eye className="h-4 w-4" />
                        </button>
                    </div>

                    {/* Add to Cart Overlay */}
                    <div className="absolute inset-x-0 bottom-0 p-3 bg-gradient-to-t from-black/60 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0">
                        <button
                            onClick={handleAddToCart}
                            disabled={!product.is_in_stock}
                            className="w-full btn btn-primary btn-sm backdrop-blur-sm"
                        >
                            <ShoppingCart className="h-4 w-4" />
                            <span>{product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}</span>
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="p-4">
                    <h3 className="font-semibold text-text-primary mb-2 line-clamp-2 group-hover:text-theme-primary transition-colors min-h-[2.5rem]">
                        {product.name}
                    </h3>

                    <div className="flex items-baseline gap-2">
                        <span className="text-xl font-bold text-gradient">
                            ₹{product.selling_price.toFixed(2)}
                        </span>
                        {product.discount_percent > 0 && (
                            <span className="text-sm text-text-tertiary line-through">
                                ₹{product.mrp.toFixed(2)}
                            </span>
                        )}
                    </div>

                    {product.discount_percent > 0 && (
                        <p className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                            You save ₹{(product.mrp - product.selling_price).toFixed(2)}
                        </p>
                    )}
                </div>
            </Link>
            {showQuickView && (
                <QuickViewModal
                    product={product}
                    onClose={() => setShowQuickView(false)}
                />
            )}
        </div>
    )
}
