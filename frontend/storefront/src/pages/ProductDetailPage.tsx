import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productsApi, pincodeApi } from '@/lib/api'
import { ShoppingCart, Package, Minus, Plus, ArrowLeft, Heart, Share2, Truck, Shield, RotateCcw, Check, Star, MapPin, Bell, Sparkles } from 'lucide-react'
import { useState, useEffect, useRef, Suspense } from 'react'
import ProductCanvas from '@/components/ui/ProductCanvas'
import Loader3D from '@/components/ui/Loader3D'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'
import WhatsAppButton from '@/components/marketing/WhatsAppButton'
import ProductReviews from '@/components/ProductReviews'
import { toast } from '@/components/ui/Toaster'
import { useRecentlyViewed } from '@/hooks/useRecentlyViewed'
import RecentlyViewed from '@/components/RecentlyViewed'

export default function ProductDetailPage() {
    const { productId } = useParams()
    const [quantity, setQuantity] = useState(1)
    const [selectedImage, setSelectedImage] = useState(0)
    const [view3D, setView3D] = useState(false)
    const [selectedVariantId, setSelectedVariantId] = useState<string | null>(null)
    const [pincode, setPincode] = useState('')
    const [deliveryInfo, setDeliveryInfo] = useState<any>(null)
    const [pincodeLoading, setPincodeLoading] = useState(false)
    const [notifyEmail, setNotifyEmail] = useState('')
    const [notifySubmitted, setNotifySubmitted] = useState(false)
    const [showDesktopSticky, setShowDesktopSticky] = useState(false)
    const cartButtonRef = useRef<HTMLButtonElement>(null)
    const { addProduct } = useRecentlyViewed()

    const addItem = useCartStore((state) => state.addItem)
    const { isWishlisted, toggleWishlist, fetchWishlist, isLoaded } = useWishlistStore()
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

    useEffect(() => {
        if (isAuthenticated && !isLoaded) fetchWishlist()
    }, [isAuthenticated])

    const { data: productData, isLoading } = useQuery({
        queryKey: ['product', productId],
        queryFn: () => productsApi.getProduct(productId!).then(res => res.data.data),
        enabled: !!productId,
    })

    // Track recently viewed
    useEffect(() => {
        if (productData && productId) {
            addProduct({
                id: productData.id,
                name: productData.name,
                selling_price: productData.selling_price,
                mrp: productData.mrp,
                discount_percent: productData.discount_percent,
                thumbnail: productData.thumbnail,
                is_in_stock: productData.is_in_stock,
                quantity: productData.quantity,
            })
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [productData?.id])

    // Desktop sticky bar: show when cart button scrolls off screen
    useEffect(() => {
        const el = cartButtonRef.current
        if (!el) return
        const observer = new IntersectionObserver(
            ([entry]) => setShowDesktopSticky(!entry.isIntersecting),
            { threshold: 0 }
        )
        observer.observe(el)
        return () => observer.disconnect()
    }, [productData])

    const wishlisted = productId ? isWishlisted(productId) : false

    // Build image gallery — use product images array if present, fallback to thumbnail
    const images: string[] = productData?.images?.length
        ? productData.images
        : productData?.thumbnail
            ? [productData.thumbnail]
            : []

    // When variant changes, adjust price / stock display
    const activeVariant = productData?.variant_groups
        ?.flatMap((g: any) => g.variants)
        ?.find((v: any) => v.id === selectedVariantId)

    const checkPincode = async () => {
        if (!pincode || pincode.length !== 6) {
            toast.error('Enter a valid 6-digit pincode')
            return
        }
        setPincodeLoading(true)
        try {
            const res = await pincodeApi.check(pincode)
            setDeliveryInfo(res.data.data)
        } catch {
            setDeliveryInfo({ available: false })
        } finally {
            setPincodeLoading(false)
        }
    }

    const handleAddToCart = () => {
        if (!productData.is_in_stock) {
            toast.error('Product is out of stock')
            return
        }

        addItem({
            product_id: productData.id,
            name: productData.name,
            price: productData.selling_price,
            image: productData.thumbnail,
            max_quantity: productData.quantity,
            quantity,
        })
        toast.success(`Added ${quantity} item(s) to cart`)
        setQuantity(1)
    }

    const handleShare = () => {
        if (navigator.share) {
            navigator.share({
                title: productData.name,
                text: `Check out ${productData.name}`,
                url: window.location.href,
            })
        } else {
            navigator.clipboard.writeText(window.location.href)
            toast.success('Link copied to clipboard')
        }
    }

    const handleWishlist = () => {
        if (!isAuthenticated) {
            toast.error('Please sign in to save to wishlist')
            return
        }
        if (productId) toggleWishlist(productId)
    }

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8 animate-fade-in">
                <div className="skeleton h-6 w-32 rounded-lg mb-8" />
                <div className="grid md:grid-cols-2 gap-8 lg:gap-12">
                    <div className="skeleton aspect-square rounded-2xl" />
                    <div className="space-y-4">
                        <div className="skeleton h-10 rounded-xl" />
                        <div className="skeleton h-6 w-3/4 rounded-lg" />
                        <div className="skeleton h-32 rounded-xl" />
                        <div className="skeleton h-16 rounded-xl" />
                        <div className="skeleton h-14 rounded-xl" />
                    </div>
                </div>
            </div>
        )
    }

    if (!productData) {
        return (
            <div className="container mx-auto px-4 py-16">
                <div className="empty-state">
                    <Package className="empty-state-icon" />
                    <h2 className="empty-state-title">Product not found</h2>
                    <p className="empty-state-description">This product may have been removed or doesn't exist.</p>
                    <Link to="/products" className="btn btn-primary">
                        <ArrowLeft className="h-4 w-4" />
                        Back to Products
                    </Link>
                </div>
            </div>
        )
    }

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-6 md:py-8">
                {/* Breadcrumb */}
                <nav className="mb-6">
                    <Link to="/products" className="inline-flex items-center gap-2 text-text-secondary hover:text-theme-primary transition-colors group">
                        <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
                        <span className="font-medium">Back to products</span>
                    </Link>
                </nav>

                <div className="card p-0 overflow-hidden">
                    <div className="grid md:grid-cols-2 gap-0">
                        {/* Product Images */}
                        <div className="p-6 md:p-8 bg-bg-tertiary/30">
                            {/* Main Image */}
                            <div className="aspect-square bg-bg-primary rounded-2xl overflow-hidden relative group shadow-lg border border-border-color">
                                {!view3D ? (
                                    <>
                                        {images.length > 0 ? (
                                            <img
                                                src={images[selectedImage]}
                                                alt={productData.name}
                                                className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
                                            />
                                        ) : (
                                            <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                                                <Package className="h-24 w-24" />
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="w-full h-full relative">
                                        <Suspense fallback={<Loader3D />}>
                                            <ProductCanvas 
                                                imageUrl={productData.thumbnail} 
                                                shape={productData.category_name?.toLowerCase().includes('shirt') ? 'box' : 'sphere'}
                                                color="#8B5CF6"
                                            />
                                        </Suspense>
                                        <div className="absolute bottom-4 left-4 right-4 text-center pointer-events-none">
                                            <p className="inline-block px-3 py-1 bg-black/50 backdrop-blur-md rounded-full text-[10px] text-white/80 uppercase tracking-widest">
                                                Interactive 3D Preview
                                            </p>
                                        </div>
                                    </div>
                                )}

                                {/* Preview Switcher */}
                                <div className="absolute bottom-4 right-4 flex gap-2">
                                    <button 
                                        onClick={() => setView3D(false)}
                                        className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-lg ${!view3D ? 'bg-theme-primary text-white' : 'bg-white/90 text-text-primary hover:bg-white'}`}
                                    >
                                        2D
                                    </button>
                                    <button 
                                        onClick={() => setView3D(true)}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all shadow-lg ${view3D ? 'bg-theme-primary text-white' : 'bg-white/90 text-text-primary hover:bg-white'}`}
                                    >
                                        <Sparkles className="h-3 w-3" />
                                        3D
                                    </button>
                                </div>

                                {/* Badges */}
                                <div className="absolute top-4 left-4 flex flex-col gap-2">
                                    {productData.discount_percent > 0 && (
                                        <span className="badge badge-danger shadow-lg">
                                            -{productData.discount_percent}% OFF
                                        </span>
                                    )}
                                    {!productData.is_in_stock && (
                                        <span className="badge bg-bg-tertiary/90 text-text-primary backdrop-blur-sm shadow-lg">
                                            Out of Stock
                                        </span>
                                    )}
                                </div>

                                {/* Action Buttons */}
                                <div className="absolute top-4 right-4 flex flex-col gap-2">
                                    <button
                                        onClick={handleWishlist}
                                        className={`p-3 rounded-full shadow-lg transition-all duration-300 ${wishlisted
                                            ? 'bg-red-500 text-white'
                                            : 'bg-bg-primary/90 text-text-secondary hover:bg-red-500 hover:text-white backdrop-blur-sm'
                                            }`}
                                        aria-label="Add to wishlist"
                                    >
                                        <Heart className={`h-5 w-5 ${wishlisted ? 'fill-current' : ''}`} />
                                    </button>
                                    <button
                                        onClick={handleShare}
                                        className="p-3 rounded-full bg-bg-primary/90 text-text-secondary hover:bg-theme-primary hover:text-white shadow-lg transition-all duration-300 backdrop-blur-sm"
                                        aria-label="Share product"
                                    >
                                        <Share2 className="h-5 w-5" />
                                    </button>
                                </div>
                            </div>

                            {/* Thumbnail Gallery */}
                            {images.length > 1 && (
                                <div className="grid grid-cols-4 gap-3 mt-4">
                                    {images.map((img, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => setSelectedImage(idx)}
                                            className={`aspect-square rounded-xl overflow-hidden border-2 transition-all ${selectedImage === idx
                                                ? 'border-theme-primary shadow-md ring-2 ring-theme-primary/20'
                                                : 'border-border-color hover:border-text-tertiary'
                                                }`}
                                        >
                                            <img src={img} alt={`${productData.name} ${idx + 1}`} className="w-full h-full object-cover" />
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Product Details */}
                        <div className="p-6 md:p-8 flex flex-col">
                            {/* Title */}
                            <h1 className="text-2xl md:text-3xl font-bold text-text-primary mb-4">{productData.name}</h1>

                            {/* Rating Placeholder */}
                            <div className="flex items-center gap-2 mb-6">
                                <div className="flex">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <Star key={star} className="h-5 w-5 text-yellow-400 fill-current" />
                                    ))}
                                </div>
                                <span className="text-text-secondary text-sm">(Reviews below)</span>
                            </div>

                            {/* Price */}
                            <div className="flex items-baseline flex-wrap gap-3 mb-6">
                                <span className="text-3xl md:text-4xl font-bold text-gradient">
                                    ₹{productData.selling_price.toFixed(2)}
                                </span>
                                {productData.discount_percent > 0 && (
                                    <>
                                        <span className="text-lg text-text-tertiary line-through">
                                            ₹{productData.mrp.toFixed(2)}
                                        </span>
                                        <span className="badge badge-success">
                                            Save ₹{(productData.mrp - productData.selling_price).toFixed(2)}
                                        </span>
                                    </>
                                )}
                            </div>

                            {/* Stock Status */}
                            <div className="mb-6 p-4 bg-bg-tertiary/50 rounded-xl border border-border-color">
                                {productData.is_in_stock ? (
                                    <div className="flex items-center gap-3">
                                        <div className="p-1.5 rounded-full bg-green-500/20">
                                            <Check className="h-4 w-4 text-green-600 dark:text-green-400" />
                                        </div>
                                        <div>
                                            <span className="font-semibold text-green-600 dark:text-green-400">In Stock</span>
                                            <span className="text-text-secondary ml-2">({productData.quantity} available)</span>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-3">
                                        <div className="h-3 w-3 bg-red-500 rounded-full" />
                                        <span className="font-semibold text-red-600 dark:text-red-400">Out of Stock</span>
                                    </div>
                                )}
                            </div>

                            {/* Variant Groups */}
                            {productData.variant_groups?.length > 0 && (
                                <div className="mb-6 space-y-4">
                                    {productData.variant_groups.map((group: any) => (
                                        <div key={group.id}>
                                            <label className="block text-sm font-semibold text-text-primary mb-2">
                                                {group.name}
                                                {selectedVariantId && activeVariant?.group_id === group.id && (
                                                    <span className="ml-2 font-normal text-text-secondary">
                                                        — {activeVariant.value}
                                                    </span>
                                                )}
                                            </label>
                                            <div className="flex flex-wrap gap-2">
                                                {group.variants.map((v: any) => (
                                                    <button
                                                        key={v.id}
                                                        onClick={() => setSelectedVariantId(
                                                            selectedVariantId === v.id ? null : v.id
                                                        )}
                                                        disabled={v.stock === 0}
                                                        title={v.stock === 0 ? 'Out of stock' : v.value}
                                                        className={`relative px-3 py-1.5 rounded-lg border-2 text-sm font-medium transition-all
                                                            ${selectedVariantId === v.id
                                                                ? 'border-theme-primary bg-theme-primary/10 text-theme-primary'
                                                                : v.stock === 0
                                                                    ? 'border-border-color text-text-tertiary bg-bg-tertiary/50 cursor-not-allowed line-through'
                                                                    : 'border-border-color hover:border-theme-primary text-text-primary'
                                                            }`}
                                                    >
                                                        {v.color_hex && (
                                                            <span
                                                                className="inline-block w-3 h-3 rounded-full mr-1.5 border border-border-color"
                                                                // @ts-ignore — dynamic color swatch
                                                                style={{ '--swatch': v.color_hex, backgroundColor: 'var(--swatch)' } as React.CSSProperties}
                                                            />
                                                        )}
                                                        {v.value}
                                                        {v.price_modifier !== 0 && (
                                                            <span className="ml-1 text-xs text-text-secondary">
                                                                {v.price_modifier > 0 ? `+₹${v.price_modifier}` : `-₹${Math.abs(v.price_modifier)}`}
                                                            </span>
                                                        )}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Pincode Delivery Estimator */}
                            <div className="mb-6 p-4 bg-bg-tertiary/50 rounded-xl border border-border-color">
                                <div className="flex items-center gap-2 mb-3">
                                    <MapPin className="h-4 w-4 text-theme-primary" />
                                    <span className="font-semibold text-text-primary text-sm">Check Delivery</span>
                                </div>
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        inputMode="numeric"
                                        maxLength={6}
                                        placeholder="Enter pincode"
                                        value={pincode}
                                        onChange={(e) => {
                                            setPincode(e.target.value.replace(/\D/g, ''))
                                            setDeliveryInfo(null)
                                        }}
                                        className="input flex-1 text-sm"
                                    />
                                    <button
                                        onClick={checkPincode}
                                        disabled={pincodeLoading}
                                        className="btn btn-outline btn-sm px-4"
                                    >
                                        {pincodeLoading ? 'Checking...' : 'Check'}
                                    </button>
                                </div>
                                {deliveryInfo && (
                                    <div className="mt-3 text-sm">
                                        {deliveryInfo.available === false ? (
                                            <p className="text-red-500">Delivery not available to this pincode</p>
                                        ) : (
                                            <div className="space-y-1">
                                                {deliveryInfo.standard_days && (
                                                    <p className="text-green-600 dark:text-green-400 flex items-center gap-1.5">
                                                        <Check className="h-3.5 w-3.5" />
                                                        Standard delivery in {deliveryInfo.standard_days} days
                                                    </p>
                                                )}
                                                {deliveryInfo.express_days && (
                                                    <p className="text-blue-600 dark:text-blue-400 flex items-center gap-1.5">
                                                        <Truck className="h-3.5 w-3.5" />
                                                        Express delivery in {deliveryInfo.express_days} days
                                                    </p>
                                                )}
                                                {deliveryInfo.same_day && (
                                                    <p className="text-purple-600 dark:text-purple-400 flex items-center gap-1.5">
                                                        <Check className="h-3.5 w-3.5" />
                                                        Same day delivery available
                                                    </p>
                                                )}
                                                {deliveryInfo.cod_available && (
                                                    <p className="text-text-secondary flex items-center gap-1.5 text-xs">
                                                        <Shield className="h-3.5 w-3.5" />
                                                        Cash on delivery available
                                                    </p>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Description */}
                            {productData.description && (
                                <div className="mb-6">
                                    <h2 className="text-lg font-semibold mb-3 text-text-primary">Description</h2>
                                    <p className="text-text-secondary leading-relaxed">{productData.description}</p>
                                </div>
                            )}

                            {/* Product Details */}
                            {(productData.sku || productData.unit) && (
                                <div className="bg-gradient-to-r from-theme-primary/5 to-theme-accent/5 rounded-xl p-4 mb-6 border border-theme-primary/10">
                                    <h2 className="text-lg font-semibold mb-3 text-text-primary">Product Details</h2>
                                    <dl className="space-y-2">
                                        {productData.sku && (
                                            <div className="flex">
                                                <dt className="w-24 text-text-secondary">SKU:</dt>
                                                <dd className="font-medium text-text-primary">{productData.sku}</dd>
                                            </div>
                                        )}
                                        {productData.unit && (
                                            <div className="flex">
                                                <dt className="w-24 text-text-secondary">Unit:</dt>
                                                <dd className="font-medium text-text-primary">{productData.unit}</dd>
                                            </div>
                                        )}
                                    </dl>
                                </div>
                            )}

                            {/* Features */}
                            <div className="grid grid-cols-3 gap-3 mb-6">
                                {[
                                    { icon: Truck, title: 'Free Delivery', desc: 'Orders over ₹499' },
                                    { icon: Shield, title: 'Secure', desc: '100% Protected' },
                                    { icon: RotateCcw, title: 'Easy Returns', desc: '7 day policy' },
                                ].map((feature, idx) => (
                                    <div key={idx} className="text-center p-3 rounded-xl bg-bg-tertiary/50 border border-border-color">
                                        <feature.icon className="h-5 w-5 mx-auto mb-1.5 text-theme-primary" />
                                        <p className="text-xs font-semibold text-text-primary">{feature.title}</p>
                                        <p className="text-[10px] text-text-tertiary">{feature.desc}</p>
                                    </div>
                                ))}
                            </div>

                            {/* Quantity & Add to Cart */}
                            <div className="mt-auto space-y-4">
                                {productData.is_in_stock ? (
                                    <>
                                        <div>
                                            <label className="block text-sm font-medium mb-3 text-text-primary">Quantity</label>
                                            <div className="flex items-center gap-4">
                                                <div className="flex items-center border-2 border-border-color rounded-xl overflow-hidden">
                                                    <button
                                                        onClick={() => setQuantity(Math.max(1, quantity - 1))}
                                                        className="p-3 hover:bg-bg-tertiary transition-colors"
                                                        aria-label="Decrease quantity"
                                                    >
                                                        <Minus className="h-5 w-5 text-text-primary" />
                                                    </button>
                                                    <span className="text-xl font-bold w-14 text-center text-text-primary">{quantity}</span>
                                                    <button
                                                        onClick={() => setQuantity(Math.min(productData.quantity, quantity + 1))}
                                                        className="p-3 hover:bg-bg-tertiary transition-colors"
                                                        aria-label="Increase quantity"
                                                    >
                                                        <Plus className="h-5 w-5 text-text-primary" />
                                                    </button>
                                                </div>
                                                <span className="text-text-secondary text-sm">
                                                    Max: {productData.quantity}
                                                </span>
                                            </div>
                                        </div>

                                        <button
                                            ref={cartButtonRef}
                                            onClick={handleAddToCart}
                                            className="w-full btn btn-primary btn-lg text-lg"
                                        >
                                            <ShoppingCart className="h-5 w-5" />
                                            <span>Add to Cart</span>
                                        </button>
                                    </>
                                ) : (
                                    <div className="space-y-3">
                                        <button
                                            disabled
                                            className="w-full btn btn-lg bg-bg-tertiary text-text-tertiary cursor-not-allowed"
                                        >
                                            <ShoppingCart className="h-5 w-5" />
                                            <span>Out of Stock</span>
                                        </button>
                                        {!notifySubmitted ? (
                                            <div className="rounded-xl bg-theme-primary/5 border border-theme-primary/20 p-4 space-y-3">
                                                <p className="text-sm font-semibold text-text-primary flex items-center gap-2">
                                                    <Bell className="h-4 w-4 text-theme-primary" />
                                                    Notify me when available
                                                </p>
                                                <div className="flex gap-2">
                                                    <input
                                                        type="email"
                                                        value={notifyEmail}
                                                        onChange={e => setNotifyEmail(e.target.value)}
                                                        placeholder="your@email.com"
                                                        className="input flex-1 text-sm"
                                                    />
                                                    <button
                                                        onClick={() => {
                                                            if (!notifyEmail) return
                                                            const stored = JSON.parse(localStorage.getItem('notify_me') || '[]')
                                                            stored.push({ productId, email: notifyEmail, product: productData.name, at: Date.now() })
                                                            localStorage.setItem('notify_me', JSON.stringify(stored))
                                                            setNotifySubmitted(true)
                                                            toast.success("We'll notify you when it's back in stock!")
                                                        }}
                                                        disabled={!notifyEmail}
                                                        className="btn btn-outline btn-sm flex-shrink-0"
                                                    >
                                                        Notify Me
                                                    </button>
                                                </div>
                                            </div>
                                        ) : (
                                            <div className="rounded-xl bg-green-500/10 border border-green-500/20 p-3 text-sm text-green-600 dark:text-green-400 font-medium flex items-center gap-2">
                                                <Check className="h-4 w-4" />
                                                You'll be notified when this item is restocked!
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* WhatsApp Button */}
                                <WhatsAppButton
                                    productName={productData.name}
                                    productUrl={`/products/${productId}`}
                                    price={productData.price}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                {/* Recently Viewed Products */}
                <div className="mt-8">
                    <RecentlyViewed exclude={productId} title="Recently Viewed" />
                </div>

                {/* Product Reviews */}
                <div className="mt-8">
                    <ProductReviews productId={productId!} />
                </div>
            </div>

            {/* Desktop sticky Add-to-Cart bar */}
            {productData.is_in_stock && showDesktopSticky && (
                <div className="hidden md:flex fixed bottom-0 inset-x-0 z-40 bg-bg-primary/95 backdrop-blur-sm border-t border-border-color shadow-2xl">
                    <div className="container mx-auto px-4 py-3 flex items-center gap-4">
                        {productData.thumbnail && (
                            <img src={productData.thumbnail} alt="" className="h-12 w-12 rounded-lg object-cover flex-shrink-0" />
                        )}
                        <div className="flex-1 min-w-0">
                            <p className="font-semibold text-text-primary truncate">{productData.name}</p>
                            <p className="text-theme-primary font-bold">₹{productData.selling_price?.toFixed(2)}</p>
                        </div>
                        <button
                            onClick={handleAddToCart}
                            className="btn btn-primary flex-shrink-0 shadow-lg"
                        >
                            <ShoppingCart className="h-4 w-4" />
                            Add to Cart
                        </button>
                    </div>
                </div>
            )}

            {/* Mobile sticky CTA bar */}
            {productData.is_in_stock && (
                <div className="fixed bottom-16 inset-x-0 z-40 md:hidden px-4 pb-2">
                    <div className="flex gap-3 bg-bg-primary/95 backdrop-blur-sm rounded-2xl border border-border-color p-3 shadow-xl">
                        <button
                            onClick={handleWishlist}
                            className={`p-3 rounded-xl border-2 transition-all ${wishlisted
                                ? 'border-red-500 bg-red-500/10 text-red-500'
                                : 'border-border-color text-text-secondary'}`}
                            aria-label="Wishlist"
                        >
                            <Heart className={`h-5 w-5 ${wishlisted ? 'fill-current' : ''}`} />
                        </button>
                        <button
                            onClick={handleAddToCart}
                            className="flex-1 btn btn-outline font-semibold"
                        >
                            <ShoppingCart className="h-4 w-4" />
                            Add to Cart
                        </button>
                        <button
                            onClick={() => {
                                handleAddToCart()
                                setTimeout(() => window.location.href = '/cart', 300)
                            }}
                            className="flex-1 btn btn-primary font-semibold"
                        >
                            Buy Now
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}

