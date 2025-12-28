import { Link } from 'react-router-dom'
import { ShoppingCart } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { toast } from '@/components/ui/Toaster'

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

export default function ProductCard({ product }: ProductCardProps) {
    const addItem = useCartStore((state) => state.addItem)

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
        toast.success('Added to cart')
    }

    return (
        <div className="bg-bg-primary rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200 border border-border-color">
            <Link to={`/products/${product.id}`}>
                <div className="aspect-square bg-bg-tertiary relative">
                    {product.thumbnail ? (
                        <img
                            src={product.thumbnail}
                            alt={product.name}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                            No Image
                        </div>
                    )}
                    {product.discount_percent > 0 && (
                        <div className="absolute top-2 right-2 bg-red-500 text-white px-2 py-1 rounded text-sm font-bold">
                            {product.discount_percent}% OFF
                        </div>
                    )}
                    {!product.is_in_stock && (
                        <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                            <span className="text-white font-bold text-lg">Out of Stock</span>
                        </div>
                    )}
                </div>
            </Link>

            <div className="p-4">
                <Link to={`/products/${product.id}`}>
                    <h3 className="font-semibold text-text-primary mb-2 line-clamp-2 hover:text-theme-primary">
                        {product.name}
                    </h3>
                </Link>

                <div className="flex items-baseline space-x-2 mb-3">
                    <span className="text-xl font-bold text-text-primary">
                        ₹{product.selling_price.toFixed(2)}
                    </span>
                    {product.discount_percent > 0 && (
                        <span className="text-sm text-text-tertiary line-through">
                            ₹{product.mrp.toFixed(2)}
                        </span>
                    )}
                </div>

                <button
                    onClick={handleAddToCart}
                    disabled={!product.is_in_stock}
                    className={`w-full flex items-center justify-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${product.is_in_stock
                        ? 'bg-theme-primary text-white hover:bg-theme-primary-hover'
                        : 'bg-bg-tertiary text-text-tertiary cursor-not-allowed'
                        }`}
                    aria-label={product.is_in_stock ? 'Add to cart' : 'Out of stock'}
                >
                    <ShoppingCart className="h-4 w-4" />
                    <span>{product.is_in_stock ? 'Add to Cart' : 'Out of Stock'}</span>
                </button>
            </div>
        </div>
    )
}
