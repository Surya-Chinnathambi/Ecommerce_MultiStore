import { Link } from 'react-router-dom'
import { ShoppingCart, Heart, Zap } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'
import { useState, useEffect } from 'react'
import QuickViewModal from '@/components/QuickViewModal'
import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from 'framer-motion'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'
import ProductCanvas from './ProductCanvas'
import { MOTION_DURATION, MOTION_EASE, motionTransition } from '@/lib/motion'

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
    const shouldReduceMotion = useReducedMotion()

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
            className="group relative perspective-1000"
            initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={motionTransition(!!shouldReduceMotion, { type: 'spring', stiffness: 300, damping: 24 })}
        >
            <motion.div
                onMouseMove={handleMouseMove}
                onMouseLeave={handleMouseLeave}
                style={{ rotateX, rotateY, transformStyle: 'preserve-3d' }}
                whileHover={shouldReduceMotion ? undefined : { scale: 1.02 }}
                transition={motionTransition(!!shouldReduceMotion, { duration: MOTION_DURATION.fast, ease: MOTION_EASE })}
                className={twMerge(
                    "block rounded-[var(--radius-2xl)] border border-border-color bg-bg-primary overflow-hidden transition-colors hover:border-border-strong",
                    viewMode === 'list' ? 'flex flex-row p-4 gap-5' : 'flex flex-col'
                )}
            >
                <Link to={`/products/${product.id}`} className={twMerge(
                    "flex-1", viewMode === 'list' && "flex flex-row gap-5"
                )}>
                    {/* Image Area with 3D Canvas Background */}
                    <div
                        className={twMerge(
                            "relative overflow-hidden bg-bg-tertiary translate-z-20",
                            viewMode === 'list' ? 'w-28 sm:w-36 rounded-[var(--radius-xl)] flex-shrink-0 aspect-square' : 'aspect-[4/3] w-full'
                        )}
                    >
                        <div className="absolute inset-0 z-0 opacity-40 group-hover:opacity-100 transition-opacity">
                            <ProductCanvas imageUrl={product.thumbnail} interactive={false} />
                        </div>

                        {!imageLoaded && <div className="absolute inset-0 skeleton" />}
                        {product.thumbnail ? (
                            <img
                                src={product.thumbnail}
                                alt={product.name}
                                className={clsx(
                                    "w-full h-full object-cover transition-all duration-500 relative z-10 mix-blend-multiply",
                                    imageLoaded ? 'opacity-100' : 'opacity-0'
                                )}
                                onLoad={() => setImageLoaded(true)}
                            />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-text-quaternary text-xs relative z-10">No image</div>
                        )}

                        {/* Top badges */}
                        <div className="absolute top-3 left-3 flex flex-col gap-1.5 translate-z-30">
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
                            <div className="absolute top-3 right-3 flex flex-col gap-2 translate-z-40">
                                <motion.button
                                    whileTap={shouldReduceMotion ? undefined : { scale: 0.9 }}
                                    onClick={handleWishlist}
                                    className={clsx(
                                        "h-8 w-8 rounded-full shadow-md flex items-center justify-center transition-all duration-200 backdrop-blur-sm",
                                        wishlisted ? "bg-red-500 text-white" : "bg-bg-primary/90 text-text-tertiary opacity-0 group-hover:opacity-100 translate-x-2 group-hover:translate-x-0 hover:bg-red-500 hover:text-white"
                                    )}
                                >
                                    <Heart className={clsx("h-3.5 w-3.5", wishlisted && "fill-current")} />
                                </motion.button>
                            </div>
                        )}
                    </div>

                    {/* Card Body */}
                    <div
                        className={clsx("flex flex-col justify-between translate-z-25", viewMode === 'grid' ? "p-4" : "flex-1 min-w-0 py-1 pe-4")}
                    >
                        <div>
                            <h3 className="font-semibold text-text-primary group-hover:text-theme-primary transition-colors line-clamp-2 leading-snug mb-2 text-sm md:text-base">
                                {product.name}
                            </h3>
                        </div>

                        <div className={clsx(viewMode === 'list' ? "flex items-center justify-between mt-4 gap-3" : "flex items-end justify-between gap-2")}>
                            <div>
                                <div className="flex items-baseline gap-1.5">
                                    <span className="text-lg font-black text-text-primary tabular-nums">
                                        ₹{product.selling_price.toLocaleString('en-IN')}
                                    </span>
                                </div>
                            </div>

                            {viewMode === 'list' && (
                                <motion.button
                                    whileTap={shouldReduceMotion ? undefined : { scale: 0.9 }}
                                    onClick={handleAddToCart}
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
