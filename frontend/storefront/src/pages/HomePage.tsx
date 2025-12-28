import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import { Link } from 'react-router-dom'
import { ArrowRight, Package } from 'lucide-react'
import PromotionalBanner from '@/components/marketing/PromotionalBanner'
import FlashSaleTimer from '@/components/marketing/FlashSaleTimer'

export default function HomePage() {
    useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    const { data: categoriesData } = useQuery({
        queryKey: ['categories'],
        queryFn: () => storeApi.getCategories().then(res => res.data.data),
    })

    const { data: featuredData } = useQuery({
        queryKey: ['featured-products'],
        queryFn: () => storeApi.getFeaturedProducts(8).then(res => res.data.data),
    })

    return (
        <div>
            {/* Promotional Banner */}
            <div className="mb-8">
                <PromotionalBanner />
            </div>

            {/* Flash Sales */}
            <FlashSaleTimer />

            <div className="container mx-auto px-4 py-12">
                {/* Categories */}
                {categoriesData && categoriesData.length > 0 && (
                    <section className="mb-12">
                        <h2 className="text-2xl font-bold text-text-primary mb-6">Shop by Category</h2>
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                            {categoriesData.slice(0, 6).map((category: any) => (
                                <Link
                                    key={category.id}
                                    to={`/products?category_id=${category.id}`}
                                    className="bg-bg-primary border border-border-color p-6 rounded-lg shadow-md hover:shadow-lg transition text-center"
                                >
                                    <Package className="h-12 w-12 mx-auto mb-3 text-theme-primary" />
                                    <h3 className="font-semibold text-text-primary">{category.name}</h3>
                                </Link>
                            ))}
                        </div>
                    </section>
                )}

                {/* Featured Products */}
                {featuredData && featuredData.length > 0 && (
                    <section className="mb-12">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-2xl font-bold text-text-primary">Featured Products</h2>
                            <Link
                                to="/products"
                                className="text-theme-primary hover:text-theme-primary-hover font-medium flex items-center space-x-1"
                            >
                                <span>View All</span>
                                <ArrowRight className="h-4 w-4" />
                            </Link>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
                            {featuredData.map((product: any) => (
                                <ProductCard key={product.id} product={product} viewMode="grid" />
                            ))}
                        </div>
                    </section>
                )}
            </div>
        </div>
    )
}
