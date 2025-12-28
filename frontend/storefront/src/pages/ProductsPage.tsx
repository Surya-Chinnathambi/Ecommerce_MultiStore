import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { productsApi, storeApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import SearchFilters, { SearchParams } from '@/components/SearchFilters'
import { ChevronLeft, ChevronRight, Grid, List } from 'lucide-react'

export default function ProductsPage() {
    const [page, setPage] = useState(1)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [filters, setFilters] = useState<SearchParams>({
        sort_by: 'newest',
        sort_order: 'desc',
    })

    const { data: categoriesData } = useQuery({
        queryKey: ['categories'],
        queryFn: () => storeApi.getCategories().then(res => res.data.data),
    })

    const { data: productsData, isLoading } = useQuery({
        queryKey: ['products', page, filters],
        queryFn: () => productsApi.getProducts({
            page,
            per_page: 20,
            ...filters,
        }).then(res => res.data.data),
    })

    const handleSearchChange = (newFilters: SearchParams) => {
        setFilters(newFilters)
        setPage(1)
    }

    return (
        <div className="container mx-auto px-4 py-6 md:py-8">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-6 md:mb-8">
                <h1 className="text-2xl md:text-3xl font-bold mb-4 md:mb-0">Our Products</h1>

                {/* View Mode Toggle - Desktop */}
                <div className="hidden md:flex items-center space-x-4">
                    <div className="flex items-center bg-bg-tertiary rounded-lg p-1">
                        <button
                            onClick={() => setViewMode('grid')}
                            aria-label="Grid view"
                            className={`p-2 rounded ${viewMode === 'grid'
                                ? 'bg-bg-primary text-theme-primary shadow-sm'
                                : 'text-text-secondary hover:text-text-primary'
                                }`}
                        >
                            <Grid className="h-5 w-5" />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            aria-label="List view"
                            className={`p-2 rounded ${viewMode === 'list'
                                ? 'bg-bg-primary text-theme-primary shadow-sm'
                                : 'text-text-secondary hover:text-text-primary'
                                }`}
                        >
                            <List className="h-5 w-5" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="mb-6">
                <SearchFilters
                    onSearchChange={handleSearchChange}
                    categories={categoriesData || []}
                />
            </div>

            <div className="grid lg:grid-cols-1 gap-6 lg:gap-8">

                {/* Products Grid */}
                <div>
                    {isLoading ? (
                        <div className={viewMode === 'grid' ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6" : "space-y-4"}>
                            {[...Array(8)].map((_, i) => (
                                <div key={i} className="bg-bg-tertiary animate-pulse rounded-xl h-80" />
                            ))}
                        </div>
                    ) : productsData?.products && productsData.products.length > 0 ? (
                        <>
                            <div className="mb-4 md:mb-6">
                                <p className="text-sm md:text-base text-text-secondary">
                                    Showing <span className="font-semibold">{productsData.products.length}</span> of <span className="font-semibold">{productsData.total}</span> products
                                </p>
                            </div>

                            <div className={viewMode === 'grid'
                                ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6"
                                : "space-y-4"
                            }>
                                {productsData.products.map((product: any) => (
                                    <ProductCard key={product.id} product={product} viewMode={viewMode} />
                                ))}
                            </div>

                            {/* Pagination */}
                            {productsData.total_pages > 1 && (
                                <div className="flex items-center justify-center space-x-4 mt-8">
                                    <button
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        aria-label="Previous page"
                                        className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronLeft className="h-5 w-5" />
                                    </button>

                                    <span className="text-text-primary">
                                        Page {page} of {productsData.total_pages}
                                    </span>

                                    <button
                                        onClick={() => setPage(p => Math.min(productsData.total_pages, p + 1))}
                                        disabled={page === productsData.total_pages}
                                        aria-label="Next page"
                                        className="btn btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        <ChevronRight className="h-5 w-5" />
                                    </button>
                                </div>
                            )}
                        </>
                    ) : (
                        <div className="text-center py-12">
                            <p className="text-gray-600 text-lg">No products found</p>
                            <p className="text-gray-500 mt-2">Try adjusting your filters</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
