import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { productsApi, storeApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import SearchFilters, { SearchParams } from '@/components/SearchFilters'
import { ChevronLeft, ChevronRight, Grid, List, Package, SlidersHorizontal } from 'lucide-react'

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
        <div className="container mx-auto px-4 py-6 md:py-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
                <div>
                    <h1 className="section-title">Our Products</h1>
                    <p className="section-subtitle">Discover our amazing collection</p>
                </div>

                {/* View Mode Toggle - Desktop */}
                <div className="hidden md:flex items-center gap-4 mt-4 md:mt-0">
                    <div className="flex items-center bg-bg-tertiary rounded-xl p-1">
                        <button
                            onClick={() => setViewMode('grid')}
                            aria-label="Grid view"
                            className={`p-2.5 rounded-lg transition-all duration-200 ${viewMode === 'grid'
                                ? 'bg-bg-primary text-theme-primary shadow-sm'
                                : 'text-text-secondary hover:text-text-primary'
                                }`}
                        >
                            <Grid className="h-5 w-5" />
                        </button>
                        <button
                            onClick={() => setViewMode('list')}
                            aria-label="List view"
                            className={`p-2.5 rounded-lg transition-all duration-200 ${viewMode === 'list'
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
            <div className="card mb-8">
                <div className="flex items-center gap-2 mb-4">
                    <SlidersHorizontal className="h-5 w-5 text-theme-primary" />
                    <h2 className="font-semibold text-text-primary">Filters</h2>
                </div>
                <SearchFilters
                    onSearchChange={handleSearchChange}
                    categories={categoriesData || []}
                />
            </div>

            {/* Quick Sort Chips */}
            <div className="flex items-center gap-2 mb-5 overflow-x-auto pb-1 -mx-1 px-1">
                {([
                    { label: '🆕 Newest', sort_by: 'newest', sort_order: 'desc' },
                    { label: '🔥 Popular', sort_by: 'popularity', sort_order: 'desc' },
                    { label: '⬆️ Price: Low', sort_by: 'price', sort_order: 'asc' },
                    { label: '⬇️ Price: High', sort_by: 'price', sort_order: 'desc' },
                    { label: '⭐ Top Rated', sort_by: 'rating', sort_order: 'desc' },
                    { label: '💥 On Sale', sort_by: 'discount', sort_order: 'desc' },
                ] as const).map(chip => {
                    const active = filters.sort_by === chip.sort_by && filters.sort_order === chip.sort_order
                    return (
                        <button
                            key={chip.label}
                            onClick={() => handleSearchChange({ ...filters, sort_by: chip.sort_by as string, sort_order: chip.sort_order as string })}
                            className={`flex-shrink-0 px-4 py-1.5 rounded-full text-sm font-medium transition-all ${active
                                    ? 'bg-theme-primary text-white shadow-md'
                                    : 'bg-bg-tertiary text-text-secondary hover:text-text-primary border border-border-color'
                                }`}
                        >
                            {chip.label}
                        </button>
                    )
                })}
            </div>

            {/* Products Grid */}
            <div>
                {isLoading ? (
                    <div className={viewMode === 'grid' ? "grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 md:gap-6" : "space-y-4"}>
                        {[...Array(8)].map((_, i) => (
                            <div key={i} className="skeleton h-80 rounded-2xl" />
                        ))}
                    </div>
                ) : productsData?.products && productsData.products.length > 0 ? (
                    <>
                        {/* Results count */}
                        <div className="flex items-center justify-between mb-6">
                            <p className="text-text-secondary">
                                Showing <span className="font-semibold text-text-primary">{productsData.products.length}</span> of{' '}
                                <span className="font-semibold text-text-primary">{productsData.total}</span> products
                            </p>
                            {/* Mobile view toggle */}
                            <div className="flex md:hidden items-center bg-bg-tertiary rounded-lg p-1">
                                <button
                                    onClick={() => setViewMode('grid')}
                                    aria-label="Grid view"
                                    className={`p-2 rounded ${viewMode === 'grid' ? 'bg-bg-primary text-theme-primary shadow-sm' : 'text-text-secondary'}`}
                                >
                                    <Grid className="h-4 w-4" />
                                </button>
                                <button
                                    onClick={() => setViewMode('list')}
                                    aria-label="List view"
                                    className={`p-2 rounded ${viewMode === 'list' ? 'bg-bg-primary text-theme-primary shadow-sm' : 'text-text-secondary'}`}
                                >
                                    <List className="h-4 w-4" />
                                </button>
                            </div>
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
                            <div className="flex items-center justify-center gap-2 mt-12">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    aria-label="Previous page"
                                    className="btn btn-secondary btn-icon"
                                >
                                    <ChevronLeft className="h-5 w-5" />
                                </button>

                                <div className="flex items-center gap-1">
                                    {Array.from({ length: Math.min(5, productsData.total_pages) }, (_, i) => {
                                        let pageNum = i + 1
                                        if (productsData.total_pages > 5) {
                                            if (page > 3) {
                                                pageNum = page - 2 + i
                                            }
                                            if (page > productsData.total_pages - 2) {
                                                pageNum = productsData.total_pages - 4 + i
                                            }
                                        }
                                        return pageNum <= productsData.total_pages ? (
                                            <button
                                                key={pageNum}
                                                onClick={() => setPage(pageNum)}
                                                className={`min-w-[40px] h-10 rounded-xl font-medium transition-all ${page === pageNum
                                                    ? 'bg-theme-primary text-white shadow-md'
                                                    : 'bg-bg-tertiary text-text-secondary hover:bg-bg-tertiary/80'
                                                    }`}
                                            >
                                                {pageNum}
                                            </button>
                                        ) : null
                                    })}
                                </div>

                                <button
                                    onClick={() => setPage(p => Math.min(productsData.total_pages, p + 1))}
                                    disabled={page === productsData.total_pages}
                                    aria-label="Next page"
                                    className="btn btn-secondary btn-icon"
                                >
                                    <ChevronRight className="h-5 w-5" />
                                </button>
                            </div>
                        )}
                    </>
                ) : (
                    <div className="empty-state">
                        <Package className="empty-state-icon" />
                        <h2 className="empty-state-title">No products found</h2>
                        <p className="empty-state-description">Try adjusting your filters or search terms</p>
                        <button
                            onClick={() => handleSearchChange({ sort_by: 'newest', sort_order: 'desc' })}
                            className="btn btn-primary"
                        >
                            Clear Filters
                        </button>
                    </div>
                )}
            </div>
        </div>
    )
}
