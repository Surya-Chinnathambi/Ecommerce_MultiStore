import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { productsApi } from '@/lib/api'
import { ShoppingCart, Package, Minus, Plus, ArrowLeft } from 'lucide-react'
import { useState } from 'react'
import { useCartStore } from '@/store/cartStore'
import { toast } from '@/components/ui/Toaster'

export default function ProductDetailPage() {
    const { productId } = useParams()
    const [quantity, setQuantity] = useState(1)
    const addItem = useCartStore((state) => state.addItem)

    const { data: productData, isLoading } = useQuery({
        queryKey: ['product', productId],
        queryFn: () => productsApi.getProduct(productId!).then(res => res.data.data),
        enabled: !!productId,
    })

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

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse">
                    <div className="h-8 w-32 bg-gray-200 rounded mb-8" />
                    <div className="grid md:grid-cols-2 gap-8">
                        <div className="aspect-square bg-gray-200 rounded-lg" />
                        <div className="space-y-4">
                            <div className="h-8 bg-gray-200 rounded" />
                            <div className="h-6 bg-gray-200 rounded w-3/4" />
                            <div className="h-20 bg-gray-200 rounded" />
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    if (!productData) {
        return (
            <div className="container mx-auto px-4 py-8 text-center">
                <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                <h2 className="text-2xl font-bold mb-2">Product not found</h2>
                <Link to="/products" className="text-primary-600 hover:underline">
                    Back to products
                </Link>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <Link to="/products" className="inline-flex items-center space-x-2 text-primary-600 hover:text-primary-700 mb-6">
                <ArrowLeft className="h-4 w-4" />
                <span>Back to products</span>
            </Link>

            <div className="grid md:grid-cols-2 gap-8">
                {/* Product Image */}
                <div className="bg-gray-100 rounded-lg overflow-hidden">
                    {productData.thumbnail ? (
                        <img
                            src={productData.thumbnail}
                            alt={productData.name}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="aspect-square flex items-center justify-center text-gray-400">
                            <Package className="h-24 w-24" />
                        </div>
                    )}
                </div>

                {/* Product Details */}
                <div>
                    <h1 className="text-3xl font-bold mb-4">{productData.name}</h1>

                    {/* Price */}
                    <div className="flex items-baseline space-x-3 mb-6">
                        <span className="text-4xl font-bold text-gray-900">
                            ₹{productData.selling_price.toFixed(2)}
                        </span>
                        {productData.discount_percent > 0 && (
                            <>
                                <span className="text-xl text-gray-500 line-through">
                                    ₹{productData.mrp.toFixed(2)}
                                </span>
                                <span className="bg-red-500 text-white px-2 py-1 rounded text-sm font-bold">
                                    {productData.discount_percent}% OFF
                                </span>
                            </>
                        )}
                    </div>

                    {/* Stock Status */}
                    <div className="mb-6">
                        {productData.is_in_stock ? (
                            <span className="inline-flex items-center space-x-2 text-green-600">
                                <div className="h-2 w-2 bg-green-600 rounded-full" />
                                <span className="font-medium">In Stock ({productData.quantity} available)</span>
                            </span>
                        ) : (
                            <span className="inline-flex items-center space-x-2 text-red-600">
                                <div className="h-2 w-2 bg-red-600 rounded-full" />
                                <span className="font-medium">Out of Stock</span>
                            </span>
                        )}
                    </div>

                    {/* Description */}
                    {productData.description && (
                        <div className="mb-6">
                            <h2 className="text-lg font-semibold mb-2">Description</h2>
                            <p className="text-gray-700">{productData.description}</p>
                        </div>
                    )}

                    {/* Product Details */}
                    <div className="bg-gray-50 rounded-lg p-4 mb-6">
                        <h2 className="text-lg font-semibold mb-3">Product Details</h2>
                        <dl className="space-y-2">
                            {productData.sku && (
                                <div className="flex">
                                    <dt className="w-32 text-gray-600">SKU:</dt>
                                    <dd className="font-medium">{productData.sku}</dd>
                                </div>
                            )}
                            {productData.unit && (
                                <div className="flex">
                                    <dt className="w-32 text-gray-600">Unit:</dt>
                                    <dd className="font-medium">{productData.unit}</dd>
                                </div>
                            )}
                        </dl>
                    </div>

                    {/* Quantity Selector */}
                    {productData.is_in_stock && (
                        <div className="mb-6">
                            <label className="block text-sm font-medium mb-2">Quantity</label>
                            <div className="flex items-center space-x-4">
                                <button
                                    onClick={() => setQuantity(Math.max(1, quantity - 1))}
                                    className="btn btn-secondary"
                                >
                                    <Minus className="h-4 w-4" />
                                </button>
                                <span className="text-xl font-semibold w-12 text-center">{quantity}</span>
                                <button
                                    onClick={() => setQuantity(Math.min(productData.quantity, quantity + 1))}
                                    className="btn btn-secondary"
                                >
                                    <Plus className="h-4 w-4" />
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Add to Cart */}
                    <button
                        onClick={handleAddToCart}
                        disabled={!productData.is_in_stock}
                        className="w-full btn btn-primary flex items-center justify-center space-x-2 text-lg py-4 disabled:bg-gray-300 disabled:cursor-not-allowed"
                    >
                        <ShoppingCart className="h-5 w-5" />
                        <span>{productData.is_in_stock ? 'Add to Cart' : 'Out of Stock'}</span>
                    </button>
                </div>
            </div>
        </div>
    )
}
