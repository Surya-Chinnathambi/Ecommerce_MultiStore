import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { Heart, ShoppingCart, Trash2, Package, Share2 } from 'lucide-react'
import { useWishlistStore } from '@/store/wishlistStore'
import { useCartStore } from '@/store/cartStore'
import { toast } from '@/components/ui/Toaster'
import { useAuthStore } from '@/store/authStore'

export default function WishlistPage() {
    const { items, isLoading, fetchWishlist, removeFromWishlist, clearWishlist } = useWishlistStore()
    const addItem = useCartStore((s) => s.addItem)
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

    useEffect(() => {
        if (isAuthenticated) fetchWishlist()
    }, [isAuthenticated])

    const handleMoveAllToCart = () => {
        const inStockItems = items.filter(item => item.product.is_in_stock)
        if (inStockItems.length === 0) {
            toast.error('No in-stock items to move')
            return
        }
        inStockItems.forEach(item => {
            addItem({
                product_id: item.product.id,
                name: item.product.name,
                price: item.product.selling_price,
                image: item.product.thumbnail,
                max_quantity: 99,
            })
            removeFromWishlist(item.product_id)
        })
        toast.success(`${inStockItems.length} item${inStockItems.length > 1 ? 's' : ''} moved to cart!`)
    }

    const handleShareWishlist = () => {
        const url = window.location.href
        navigator.clipboard.writeText(url).then(
            () => toast.success('Wishlist link copied to clipboard!'),
            () => toast.error('Could not copy link')
        )
    }

    const handleMoveToCart = (item: typeof items[0]) => {
        if (!item.product.is_in_stock) {
            toast.error('This product is currently out of stock')
            return
        }
        addItem({
            product_id: item.product.id,
            name: item.product.name,
            price: item.product.selling_price,
            image: item.product.thumbnail,
            max_quantity: 99,
        })
        removeFromWishlist(item.product_id)
        toast.success('Moved to cart')
    }

    if (!isAuthenticated) {
        return (
            <div className="container mx-auto px-4 py-16">
                <div className="empty-state">
                    <Heart className="empty-state-icon" />
                    <h2 className="empty-state-title">Your wishlist is waiting</h2>
                    <p className="empty-state-description">Sign in to save and view your wishlist</p>
                    <Link to="/login" className="btn btn-primary">Sign In</Link>
                </div>
            </div>
        )
    }

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="skeleton h-8 w-48 rounded-lg mb-6" />
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {[...Array(8)].map((_, i) => (
                        <div key={i} className="skeleton rounded-2xl aspect-[3/4]" />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-3">
                        <Heart className="h-7 w-7 text-red-500 fill-current" />
                        <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
                            My Wishlist
                        </h1>
                        {items.length > 0 && (
                            <span className="badge bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400">
                                {items.length} {items.length === 1 ? 'item' : 'items'}
                            </span>
                        )}
                    </div>
                    {items.length > 0 && (
                        <div className="flex items-center gap-2">
                            <button
                                onClick={handleMoveAllToCart}
                                className="btn btn-primary btn-sm"
                                title="Move all in-stock items to cart"
                            >
                                <ShoppingCart className="h-4 w-4" />
                                Move All to Cart
                            </button>
                            <button
                                onClick={handleShareWishlist}
                                className="btn btn-ghost btn-sm text-text-secondary hover:text-theme-primary"
                                title="Share wishlist"
                                aria-label="Share wishlist"
                            >
                                <Share2 className="h-4 w-4" />
                            </button>
                            <button
                                onClick={clearWishlist}
                                className="btn btn-ghost btn-sm text-text-secondary hover:text-red-500"
                                title="Clear wishlist"
                                aria-label="Clear all"
                            >
                                <Trash2 className="h-4 w-4" />
                            </button>
                        </div>
                    )}
                </div>

                {items.length === 0 ? (
                    <div className="empty-state">
                        <Heart className="empty-state-icon" />
                        <h2 className="empty-state-title">Your wishlist is empty</h2>
                        <p className="empty-state-description">
                            Save items you love by tapping the heart icon on any product.
                        </p>
                        <Link to="/products" className="btn btn-primary">
                            <Package className="h-4 w-4" />
                            Browse Products
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        {items.map((item) => (
                            <div
                                key={item.id}
                                className="card card-hover group overflow-hidden"
                            >
                                {/* Image */}
                                <Link to={`/products/${item.product_id}`} className="block">
                                    <div className="aspect-square bg-bg-tertiary overflow-hidden relative">
                                        {item.product.thumbnail ? (
                                            <img
                                                src={item.product.thumbnail}
                                                alt={item.product.name}
                                                className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                                                <Package className="h-12 w-12" />
                                            </div>
                                        )}
                                        {item.product.discount_percent > 0 && (
                                            <span className="absolute top-2 left-2 badge badge-danger text-xs">
                                                -{item.product.discount_percent}%
                                            </span>
                                        )}
                                        {!item.product.is_in_stock && (
                                            <div className="absolute inset-0 bg-black/40 flex items-center justify-center">
                                                <span className="text-white font-semibold text-sm bg-black/60 px-3 py-1 rounded-full">
                                                    Out of Stock
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </Link>

                                {/* Details */}
                                <div className="p-3 flex flex-col gap-2">
                                    <Link to={`/products/${item.product_id}`}>
                                        <h3 className="text-sm font-medium text-text-primary line-clamp-2 hover:text-theme-primary">
                                            {item.product.name}
                                        </h3>
                                    </Link>

                                    <div className="flex items-baseline gap-1.5">
                                        <span className="font-bold text-theme-primary">
                                            ₹{item.product.selling_price.toLocaleString()}
                                        </span>
                                        {item.product.discount_percent > 0 && (
                                            <span className="text-xs text-text-tertiary line-through">
                                                ₹{item.product.mrp.toLocaleString()}
                                            </span>
                                        )}
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 mt-1">
                                        <button
                                            onClick={() => handleMoveToCart(item)}
                                            disabled={!item.product.is_in_stock}
                                            className="flex-1 btn btn-primary btn-sm text-xs py-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                        >
                                            <ShoppingCart className="h-3.5 w-3.5" />
                                            {item.product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                                        </button>
                                        <button
                                            onClick={() => removeFromWishlist(item.product_id)}
                                            className="p-2 rounded-lg text-text-tertiary hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors"
                                            aria-label="Remove from wishlist"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    )
}
