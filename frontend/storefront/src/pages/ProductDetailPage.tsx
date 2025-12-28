import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productsApi } from '@/lib/api'
import { ShoppingCart, Package, Minus, Plus, ArrowLeft, Heart, Share2, Truck, Shield, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import { useCartStore } from '@/store/cartStore'
import WhatsAppButton from '@/components/marketing/WhatsAppButton'
import ProductReviews from '@/components/ProductReviews'
import { toast } from '@/components/ui/Toaster'

export default function ProductDetailPage() {
    const { productId } = useParams()
    const [quantity, setQuantity] = useState(1)
    const [selectedImage, setSelectedImage] = useState(0)
    const addItem = useCartStore((state) => state.addItem)

    const { data: productData, isLoading } = useQuery({
        queryKey: ['product', productId],
        queryFn: () => productsApi.getProduct(productId!).then(res => res.data.data),
        enabled: !!productId,
    })

    // Mock image gallery - in real app, product would have multiple images
    const images = productData?.thumbnail ? [productData.thumbnail] : []

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

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse">
                    <div className="h-8 w-32 bg-bg-tertiary rounded mb-8" />
                    <div className="grid md:grid-cols-2 gap-8">
                        <div className="aspect-square bg-bg-tertiary rounded-xl" />
                        <div className="space-y-4">
                            <div className="h-10 bg-bg-tertiary rounded" />
                            <div className="h-6 bg-bg-tertiary rounded w-3/4" />
                            <div className="h-24 bg-bg-tertiary rounded" />
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    if (!productData) {
        return (
            <div className="container mx-auto px-4 py-8 text-center">
                <Package className="h-20 w-20 mx-auto text-text-tertiary mb-4" />
                <h2 className="text-2xl font-bold mb-4 text-text-primary">Product not found</h2>
                <Link to="/products" className="text-theme-primary hover:underline font-medium">
                    Back to products
                </Link>
            </div>
        )
    }

    return (
        <div className="bg-bg-secondary min-h-screen">
            <div className="container mx-auto px-4 py-6 md:py-8">
                {/* Breadcrumb */}
                <Link to="/products" className="inline-flex items-center space-x-2 text-theme-primary hover:opacity-80 mb-6 group">
                    <ArrowLeft className="h-4 w-4 transition-transform group-hover:-translate-x-1" />
                    <span className="font-medium">Back to products</span>
                </Link>

                <div className="bg-bg-primary rounded-2xl shadow-sm overflow-hidden border border-border-color">
                    <div className="grid md:grid-cols-2 gap-8 p-6 md:p-8">
                        {/* Product Images */}
                        <div className="space-y-4">
                            {/* Main Image */}
                            <div className="aspect-square bg-bg-tertiary rounded-xl overflow-hidden relative group">
                                {images.length > 0 ? (
                                    <img
                                        src={images[selectedImage]}
                                        alt={productData.name}
                                        className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                                    />
                                ) : (
                                    <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                                        <Package className="h-24 w-24" />
                                    </div>
                                )}
                                {productData.discount_percent > 0 && (
                                    <div className="absolute top-4 right-4 bg-gradient-to-r from-red-500 to-pink-500 text-white px-4 py-2 rounded-full text-sm font-bold shadow-lg">
                                        -{productData.discount_percent}% OFF
                                    </div>
                                )}
                            </div>

                            {/* Thumbnail Gallery - shown if multiple images */}
                            {images.length > 1 && (
                                <div className="grid grid-cols-4 gap-4">
                                    {images.map((img, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => setSelectedImage(idx)}
                                            className={`aspect-square rounded-lg overflow-hidden border-2 transition-all ${selectedImage === idx
                                                ? 'border-theme-primary shadow-md'
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
                        <div className="flex flex-col">
                            {/* Header Actions */}
                            <div className="flex items-start justify-between mb-4">
                                <h1 className="text-2xl md:text-3xl font-bold text-text-primary flex-1">{productData.name}</h1>
                                <div className="flex space-x-2 ml-4">
                                    <button
                                        onClick={handleShare}
                                        className="p-2 rounded-full hover:bg-bg-tertiary transition-colors"
                                        aria-label="Share product"
                                    >
                                        <Share2 className="h-5 w-5 text-text-secondary" />
                                    </button>
                                    <button
                                        className="p-2 rounded-full hover:bg-bg-tertiary transition-colors"
                                        aria-label="Add to wishlist"
                                    >
                                        <Heart className="h-5 w-5 text-text-secondary" />
                                    </button>
                                </div>
                            </div>

                            {/* Price */}
                            <div className="flex items-baseline space-x-3 mb-6">
                                <span className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                                    ?{productData.selling_price.toFixed(2)}
                                </span>
                                {productData.discount_percent > 0 && (
                                    <>
                                        <span className="text-lg md:text-xl text-gray-500 line-through">
                                            ?{productData.mrp.toFixed(2)}
                                        </span>
                                        <span className="text-green-600 font-semibold">
                                            Save ?{(productData.mrp - productData.selling_price).toFixed(2)}
                                        </span>
                                    </>
                                )}
                            </div>

                            {/* Stock Status */}
                            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                                {productData.is_in_stock ? (
                                    <div className="flex items-center space-x-2">
                                        <div className="h-3 w-3 bg-green-500 rounded-full animate-pulse" />
                                        <span className="font-semibold text-green-700">
                                            In Stock ({productData.quantity} available)
                                        </span>
                                    </div>
                                ) : (
                                    <div className="flex items-center space-x-2">
                                        <div className="h-3 w-3 bg-red-500 rounded-full" />
                                        <span className="font-semibold text-red-700">Out of Stock</span>
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
                            <div className="bg-gradient-to-r from-theme-primary/10 to-theme-accent/10 rounded-xl p-4 mb-6">
                                <h2 className="text-lg font-semibold mb-3 text-text-primary">Product Details</h2>
                                <dl className="space-y-2">
                                    {productData.sku && (
                                        <div className="flex">
                                            <dt className="w-32 text-text-secondary font-medium">SKU:</dt>
                                            <dd className="font-semibold text-text-primary">{productData.sku}</dd>
                                        </div>
                                    )}
                                    {productData.unit && (
                                        <div className="flex">
                                            <dt className="w-32 text-text-secondary font-medium">Unit:</dt>
                                            <dd className="font-semibold text-text-primary">{productData.unit}</dd>
                                        </div>
                                    )}
                                </dl>
                            </div>

                            {/* Features */}
                            <div className="grid grid-cols-3 gap-4 mb-6">
                                <div className="text-center p-3 rounded-lg bg-bg-tertiary">
                                    <Truck className="h-6 w-6 mx-auto mb-2 text-theme-primary" />
                                    <p className="text-xs text-text-secondary font-medium">Free Delivery</p>
                                </div>
                                <div className="text-center p-3 rounded-lg bg-bg-tertiary">
                                    <Shield className="h-6 w-6 mx-auto mb-2 text-theme-primary" />
                                    <p className="text-xs text-text-secondary font-medium">Secure Payment</p>
                                </div>
                                <div className="text-center p-3 rounded-lg bg-bg-tertiary">
                                    <RotateCcw className="h-6 w-6 mx-auto mb-2 text-theme-primary" />
                                    <p className="text-xs text-text-secondary font-medium">Easy Returns</p>
                                </div>
                            </div>

                            {/* Quantity Selector & Add to Cart */}
                            {productData.is_in_stock && (
                                <div className="space-y-4 mt-auto">
                                    <div>
                                        <label className="block text-sm font-medium mb-3 text-text-primary">Quantity</label>
                                        <div className="flex items-center space-x-4">
                                            <button
                                                onClick={() => setQuantity(Math.max(1, quantity - 1))}
                                                className="p-3 rounded-lg border-2 border-gray-300 hover:border-purple-600 hover:bg-purple-50 transition-all"
                                                aria-label="Decrease quantity"
                                            >
                                                <Minus className="h-5 w-5" />
                                            </button>
                                            <span className="text-2xl font-bold w-16 text-center">{quantity}</span>
                                            <button
                                                onClick={() => setQuantity(Math.min(productData.quantity, quantity + 1))}
                                                className="p-3 rounded-lg border-2 border-gray-300 hover:border-purple-600 hover:bg-purple-50 transition-all"
                                                aria-label="Increase quantity"
                                            >
                                                <Plus className="h-5 w-5" />
                                            </button>
                                        </div>
                                    </div>

                                    <button
                                        onClick={handleAddToCart}
                                        className="w-full bg-gradient-to-r from-purple-600 to-pink-600 text-white flex items-center justify-center space-x-3 text-lg font-semibold py-4 rounded-xl hover:shadow-lg transform hover:-translate-y-0.5 transition-all"
                                    >
                                        <ShoppingCart className="h-6 w-6" />
                                        <span>Add to Cart</span>
                                    </button>
                                </div>
                            )}

                            {/* Share on WhatsApp */}
                            <div className="mt-4">
                                <WhatsAppButton
                                    productName={productData.name}
                                    productUrl={`/products/${productId}`}
                                    price={productData.price}
                                />
                            </div>

                            {!productData.is_in_stock && (
                                <button
                                    disabled
                                    className="w-full bg-gray-200 text-gray-500 flex items-center justify-center space-x-3 text-lg font-semibold py-4 rounded-xl cursor-not-allowed"
                                >
                                    <ShoppingCart className="h-6 w-6" />
                                    <span>Out of Stock</span>
                                </button>
                            )}
                        </div>
                    </div>
                </div>

                {/* Product Reviews */}
                <div className="mt-8">
                    <ProductReviews productId={productId!} />
                </div>
            </div>
        </div>
    )
}

