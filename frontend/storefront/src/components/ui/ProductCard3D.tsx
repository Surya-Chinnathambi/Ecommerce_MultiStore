import { Link } from 'react-router-dom'
import { ShoppingCart, Heart, Eye, Zap } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'
import { useState, useEffect } from 'react'
import QuickViewModal from '@/components/QuickViewModal'
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

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

export default function ProductCard3D({ product, viewMode = 'grid' }: ProductCardProps) {
    const addItem = useCartStore((state) => state.addItem)
    const { isWishlisted, toggleWishlist, fetchWishlist, isLoaded } = useWishlistStore()
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
    const [imageLoaded, setImageLoaded] = useState(false)
    const [showQuickView, setShowQuickView] = useState(false)

    // 3D Tilt Effect
    const x = useMotionValue(0)
    const y = useMotionValue(0)
    
    const mouseXSpring = useSpring(x, { stiffness: 300, damping: 20 })
    const mouseYSpring = useSpring(y, { stiffness: 300, damping: 20 })

    const rotateX = useTransform(mouseYSpring, [-0.5, 0.5], ['7.5deg', '-7.5deg'])
    const rotateY = useTransform(mouseXSpring, [-0.5, 0.5], ['-7.5deg', '7.5deg'])

    const handleMouseMove = (e: React.MouseEvent<HTMLDivElement, MouseEvent>) => {
        const rect = e.currentTarget.getBoundingClientRect()
        const width = rect.width
        const height = rect.height
        const mouseX = e.clientX - rect.left
        const mouseY = e.clientY - rect.top
        const xPct = mouseX / width - 0.5
        const yPct = mouseY / height - 0.5
        x.set(xPct)
        y.set(yPct)
    }

    const handleMouseLeave = () => {
        x.set(0)
        y.set(0)
    }

    useEffect(() => {
        if (isAuthenticated && !isLoaded) fetchWishlist()
    }, [isAuthenticated, isLoaded, fetchWishlist])

    const wishlisted = isWishlisted(product.id)
    const savings = product.mrp - product.selling_price
    const isLowStock = product.is_in_stock && product.quantity > 0 && product.quantity <= 5

    const handleAddToCart = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!product.is_in_stock) { toast.error('This product is out of stock'); return }
        addItem({ product_id: product.id, name: product.name, price: product.selling_price, image: product.thumbnail, max_quantity: product.quantity })
        toast.success('Added to cart', product.name)
    }

    const handleWishlist = (e: React.MouseEvent) => {
        e.preventDefault()
        e.stopPropagation()
        if (!isAuthenticated) { toast.info('Sign in to save items to wishlist'); return }
        toggleWishlist(product.id)
    }

    return (
        <motion.div 
            style={{ perspective: 1000 }}
            className="group relative"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ type: 'spring', stiffness: 300, damping: 24 }}
        >
            <motion.div
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
                whileHover={{ scale: 1.02 }}
                className={twMerge(
                    "block rounded-[var(--radius-2xl)] border border-border-color bg-bg-primary overflow-hidden transition-colors hover:border-border-strong",
                    viewMode === 'list' ? 'flex flex-row p-4 gap-5' : 'flex flex-col'
                )}
            >
                {/* Wrap Link for the entire card to keep styling simple */}
                <Link to={`/products/${product.id}`} className={twMerge(
                    "flex-1", viewMode === 'list' && "flex flex-row gap-5"
                )}>
                    {/* Image Area */}
                    <div 
                        className={twMerge(
                            "relative overflow-hidden bg-bg-tertiary",
                            viewMode === 'list' ? 'w-28 sm:w-36 rounded-[var(--radius-xl)] flex-shrink-0 aspect-square' : 'aspect-[4/3] w-full'
                        )}
                        style={{ transform: 'translateZ(20px)' }}
                    >
                        {!imageLoaded && <div className="absolute inset-0 skeleton" />}
                        {product.thumbnail ? (
                            <img
                                src={product.thumbnail}
                                alt={product.name}
                                className={clsx(
                                    "w-full h-full object-cover transition-all duration-500",
                                    imageLoaded ? 'opacity-100' : 'opacity-0'
                                )}
                                onLoad={() => setImageLoaded(true)}
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-text-quaternary text-xs">No image</div>
                        )}

                        {/* Top badges */}
                        <div className="absolute top-3 left-3 flex flex-col gap-1.5" style={{ transform: 'translateZ(30px)' }}>
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

                        {/* Action buttons (Grid View) */}
                        {viewMode === 'grid' && (
                            <div className="absolute top-3 right-3 flex flex-col gap-2" style={{ transform: 'translateZ(40px)' }}>
                                <motion.button
                                    whileTap={{ scale: 0.9 }}
                                    onClick={handleWishlist}
                                    aria-label={wishlisted ? 'Remove from wishlist' : 'Add to wishlist'}
                                    className={clsx(
                                        "h-8 w-8 rounded-full shadow-md flex items-center justify-center transition-all duration-200 backdrop-blur-sm",
                                        wishlisted ? "bg-red-500 text-white" : "bg-bg-primary/90 text-text-tertiary opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 hover:bg-red-500 hover:text-white"
                                    )}
                                >
                                    <Heart className={clsx("h-3.5 w-3.5", wishlisted && "fill-current")} />
                                </motion.button>
                                <motion.button
                                    whileTap={{ scale: 0.9 }}
                                    onClick={(e: React.MouseEvent) => { e.preventDefault(); e.stopPropagation(); setShowQuickView(true) }}
                                    aria-label="Quick view"
                                    className="h-8 w-8 rounded-full bg-bg-primary/90 text-text-tertiary shadow-md flex items-center justify-center opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 backdrop-blur-sm hover:bg-theme-primary hover:text-white transition-all duration-200 delay-50"
                                >
                                    <Eye className="h-3.5 w-3.5" />
                                </motion.button>
                            </div>
                        )}

                        {/* Add to cart slide-up (Grid view) */}
                        {viewMode === 'grid' && (
                            <div className="absolute inset-x-0 bottom-0 px-3 pb-3 pt-8 bg-gradient-to-t from-black/55 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-1 group-hover:translate-y-0" style={{ transform: 'translateZ(35px)' }}>
                                <motion.button
                                    whileTap={{ scale: 0.95 }}
                                    onClick={handleAddToCart}
                                    disabled={!product.is_in_stock}
                                    className="w-full btn btn-primary btn-sm bg-white/95 !text-gray-900 border-0 shadow-md backdrop-blur-sm gap-1.5 hover:bg-white"
                                >
                                    <ShoppingCart className="h-3.5 w-3.5" />
                                    {product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}
                                </motion.button>
                            </div>
                        )}
                    </div>

                    {/* Card Body */}
                    <div 
                        className={clsx("flex flex-col justify-between", viewMode === 'grid' ? "p-4" : "flex-1 min-w-0 py-1 pe-4")}
                        style={{ transform: 'translateZ(25px)' }}
                    >
                        <div>
                            <h3 className="font-semibold text-text-primary group-hover:text-theme-primary transition-colors line-clamp-2 leading-snug mb-2 text-sm md:text-base">
                                {product.name}
                            </h3>
                            {viewMode === 'list' && product.description && (
                                <p className="text-text-tertiary text-sm line-clamp-2 leading-relaxed">{product.description}</p>
                            )}
                        </div>

                        <div className={clsx(viewMode === 'list' ? "flex items-center justify-between mt-4 gap-3" : "flex items-end justify-between gap-2")}>
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
                            
                            {viewMode === 'list' && (
                                <motion.button
                                    whileTap={{ scale: 0.9 }}
                                    onClick={handleAddToCart}
                                    disabled={!product.is_in_stock}
                                    className="btn btn-primary btn-sm flex-shrink-0"
                                >
                                    <ShoppingCart className="h-3.5 w-3.5" />
                                    <span className="hidden sm:inline">Add to Cart</span>
                                </motion.button>
                            )}
                        </div>
                    </div>
                </Link>
            </motion.div>

            {showQuickView && (
                <QuickViewModal product={product} onClose={() => setShowQuickView(false)} />
            )}
        </motion.div>
    )
}
