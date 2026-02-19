import { createPortal } from 'react-dom'
import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { X, ShoppingCart, Heart, ExternalLink, Star, PackageX } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'

export interface QuickViewProduct {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    is_in_stock: boolean
    quantity: number
    description?: string
}

interface Props {
    product: QuickViewProduct
    onClose: () => void
}

export default function QuickViewModal({ product, onClose }: Props) {
    const addItem = useCartStore(s => s.addItem)
    const { isWishlisted, toggleWishlist } = useWishlistStore()
    const isAuthenticated = useAuthStore(s => s.isAuthenticated)

    const wishlisted = isWishlisted(product.id)

    // Close on Escape key
    useEffect(() => {
        const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
        document.addEventListener('keydown', handler)
        // Prevent body scroll while open
        const prev = document.body.style.overflow
        document.body.style.overflow = 'hidden'
        return () => {
            document.removeEventListener('keydown', handler)
            document.body.style.overflow = prev
        }
    }, [onClose])

    const handleAddToCart = () => {
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
        toast.success('Added to cart!')
        onClose()
    }

    const handleWishlist = (e: React.MouseEvent) => {
        e.preventDefault()
        if (!isAuthenticated) {
            toast.error('Please sign in to save to wishlist')
            return
        }
        toggleWishlist(product.id)
    }

    const savings = product.mrp - product.selling_price

    return createPortal(
        /* Backdrop */
        <div
            className="fixed inset-0 z-[200] flex items-center justify-center p-4 sm:p-6"
            onClick={onClose}
        >
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-fade-in" />

            {/* Modal panel */}
            <div
                className="relative z-10 w-full max-w-2xl bg-bg-primary rounded-2xl shadow-2xl overflow-hidden animate-scale-in"
                onClick={e => e.stopPropagation()}
            >
                {/* Close button */}
                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 z-20 p-2 rounded-full bg-bg-tertiary/80 text-text-secondary hover:bg-bg-tertiary hover:text-text-primary transition-colors"
                    aria-label="Close"
                >
                    <X className="h-5 w-5" />
                </button>

                <div className="grid sm:grid-cols-2">
                    {/* Image */}
                    <div className="aspect-square bg-bg-tertiary relative overflow-hidden">
                        {product.thumbnail ? (
                            <img
                                src={product.thumbnail}
                                alt={product.name}
                                className="w-full h-full object-cover"
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                                <PackageX className="h-16 w-16" />
                            </div>
                        )}
                        {product.discount_percent > 0 && (
                            <span className="absolute top-3 left-3 badge badge-danger shadow-md">
                                -{product.discount_percent}% OFF
                            </span>
                        )}
                    </div>

                    {/* Details */}
                    <div className="p-6 flex flex-col">
                        <h2 className="text-xl font-bold text-text-primary mb-3 leading-tight">
                            {product.name}
                        </h2>

                        {/* Stars placeholder */}
                        <div className="flex items-center gap-1 mb-4">
                            {[1, 2, 3, 4, 5].map(s => (
                                <Star key={s} className="h-4 w-4 text-yellow-400 fill-current" />
                            ))}
                            <span className="text-xs text-text-tertiary ml-1">Reviews</span>
                        </div>

                        {/* Price */}
                        <div className="mb-4">
                            <div className="flex items-baseline gap-2 flex-wrap">
                                <span className="text-3xl font-bold text-gradient">
                                    ₹{product.selling_price.toFixed(2)}
                                </span>
                                {product.discount_percent > 0 && (
                                    <span className="text-base text-text-tertiary line-through">
                                        ₹{product.mrp.toFixed(2)}
                                    </span>
                                )}
                            </div>
                            {savings > 0 && (
                                <p className="text-sm text-green-600 dark:text-green-400 mt-1 font-medium">
                                    You save ₹{savings.toFixed(2)}
                                </p>
                            )}
                        </div>

                        {/* Stock status */}
                        <div className={`mb-4 inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium w-fit ${product.is_in_stock
                            ? 'bg-green-500/10 text-green-600 dark:text-green-400'
                            : 'bg-red-500/10 text-red-600 dark:text-red-400'
                            }`}>
                            <span className={`h-2 w-2 rounded-full ${product.is_in_stock ? 'bg-green-500' : 'bg-red-500'}`} />
                            {product.is_in_stock ? `In Stock (${product.quantity})` : 'Out of Stock'}
                        </div>

                        {/* Description */}
                        {product.description && (
                            <p className="text-sm text-text-secondary mb-5 line-clamp-3 leading-relaxed flex-1">
                                {product.description}
                            </p>
                        )}

                        {/* Actions */}
                        <div className="mt-auto space-y-3">
                            <button
                                onClick={handleAddToCart}
                                disabled={!product.is_in_stock}
                                className="w-full btn btn-primary"
                            >
                                <ShoppingCart className="h-4 w-4" />
                                {product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                            </button>

                            <div className="grid grid-cols-2 gap-2">
                                <button
                                    onClick={handleWishlist}
                                    className={`btn border-2 text-sm ${wishlisted
                                        ? 'border-red-500 bg-red-500/10 text-red-500'
                                        : 'border-border-color text-text-secondary hover:border-red-500 hover:text-red-500'
                                        }`}
                                >
                                    <Heart className={`h-4 w-4 ${wishlisted ? 'fill-current' : ''}`} />
                                    {wishlisted ? 'Wishlisted' : 'Wishlist'}
                                </button>

                                <Link
                                    to={`/products/${product.id}`}
                                    onClick={onClose}
                                    className="btn btn-secondary text-sm"
                                >
                                    <ExternalLink className="h-4 w-4" />
                                    View Full Page
                                </Link>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>,
        document.body
    )
}
