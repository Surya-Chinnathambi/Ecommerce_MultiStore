import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { productsApi, storeApi } from '@/lib/api'
import ProductCard3D from '@/components/ui/ProductCard3D'
import SearchFilters, { SearchParams } from '@/components/SearchFilters'
import { ChevronLeft, ChevronRight, Grid, List, Package, SlidersHorizontal, X } from 'lucide-react'

export default function ProductsPage() {
    const [page, setPage] = useState(1)
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid')
    const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false)
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

    const total = productsData?.total ?? 0
    const shown = productsData?.products?.length ?? 0

    const setQuickSort = (sort_by: string, sort_order: string) => {
        handleSearchChange({ ...filters, sort_by, sort_order })
    }

    const isSortActive = (sort_by: string, sort_order: string) => {
        return filters.sort_by === sort_by && filters.sort_order === sort_order
    }

    const closeMobileFilters = () => setMobileFiltersOpen(false)

    return (
        <div className="container mx-auto px-4 py-6 md:py-8 animate-fade-in">
            <div className="mb-6 md:mb-8">
                <h1 className="section-title">Our Products</h1>
                <p className="section-subtitle">Discover our amazing collection</p>
            </div>

            {/* Mobile utility bar */}
            <div className="xl:hidden mb-4 sticky top-[72px] z-20 bg-bg-secondary/95 backdrop-blur py-2 border-y border-border-color">
                <div className="flex items-center justify-between gap-3">
                    <button
                        onClick={() => setMobileFiltersOpen(true)}
                        className="btn btn-secondary btn-sm"
                    >
                        <SlidersHorizontal className="h-4 w-4" />
                        Filters
                    </button>
                    <p className="text-xs text-text-secondary">
                        <span className="font-semibold text-text-primary">{total}</span> items
                    </p>
                    <div className="flex items-center bg-bg-tertiary rounded-lg p-1">
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
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-[320px_minmax(0,1fr)] gap-6 xl:gap-8 items-start">
                {/* Desktop filters */}
                <aside className="hidden xl:block sticky top-24">
                    <div className="flex items-center gap-2 mb-3">
                        <SlidersHorizontal className="h-5 w-5 text-theme-primary" />
                        <h2 className="font-semibold text-text-primary">Filters</h2>
                    </div>
                    <SearchFilters
                        onSearchChange={handleSearchChange}
                        categories={categoriesData || []}
                    />
                </aside>

                <section className="min-w-0">
                    {/* Desktop top controls */}
                    <div className="hidden xl:flex items-center justify-between gap-4 mb-4">
                        <p className="text-text-secondary text-sm">
                            Showing <span className="font-semibold text-text-primary">{shown}</span> of{' '}
                            <span className="font-semibold text-text-primary">{total}</span> products
                        </p>
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

                    {/* Quick sort chips */}
                    <div className="flex items-center gap-2 mb-5 overflow-x-auto pb-1 -mx-1 px-1">
                        {([
                            { label: '🆕 Newest', sort_by: 'newest', sort_order: 'desc' },
                            { label: '🔥 Popular', sort_by: 'popularity', sort_order: 'desc' },
                            { label: '⬆️ Price: Low', sort_by: 'price', sort_order: 'asc' },
                            { label: '⬇️ Price: High', sort_by: 'price', sort_order: 'desc' },
                            { label: '⭐ Top Rated', sort_by: 'rating', sort_order: 'desc' },
                            { label: '💥 On Sale', sort_by: 'discount', sort_order: 'desc' },
                        ] as const).map(chip => {
                            const active = isSortActive(chip.sort_by, chip.sort_order)
                            return (
                                <button
                                    key={chip.label}
                                    onClick={() => setQuickSort(chip.sort_by, chip.sort_order)}
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

                    {/* Products */}
                    {isLoading ? (
                        <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 2xl:grid-cols-4 gap-4 md:gap-6' : 'space-y-4'}>
                            {[...Array(8)].map((_, i) => (
                                <div key={i} className="skeleton h-80 rounded-2xl" />
                            ))}
                        </div>
                    ) : productsData?.products && productsData.products.length > 0 ? (
                        <>
                            <div className="xl:hidden mb-4">
                                <p className="text-sm text-text-secondary">
                                    Showing <span className="font-semibold text-text-primary">{shown}</span> of{' '}
                                    <span className="font-semibold text-text-primary">{total}</span> products
                                </p>
                            </div>

                            <div className={viewMode === 'grid' ? 'grid grid-cols-2 md:grid-cols-3 2xl:grid-cols-4 gap-4 md:gap-6' : 'space-y-4'}>
                                {productsData.products.map((product: any) => (
                                    <ProductCard3D key={product.id} product={product} viewMode={viewMode} />
                                ))}
                            </div>

                            {/* Pagination */}
                            {productsData.total_pages > 1 && (
                                <div className="flex flex-wrap items-center justify-center gap-2 mt-10 md:mt-12">
                                    <button
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        aria-label="Previous page"
                                        className="btn btn-secondary btn-icon"
                                    >
                                        <ChevronLeft className="h-5 w-5" />
                                    </button>

                                    <div className="hidden sm:flex items-center gap-1">
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

                                    <p className="sm:hidden text-sm text-text-secondary px-2">
                                        Page <span className="font-semibold text-text-primary">{page}</span> of{' '}
                                        <span className="font-semibold text-text-primary">{productsData.total_pages}</span>
                                    </p>

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
                </section>
            </div>

            {/* Mobile filters drawer */}
            {mobileFiltersOpen && (
                <div className="xl:hidden fixed inset-0 z-[130]">
                    <button
                        aria-label="Close filters"
                        className="absolute inset-0 bg-black/45"
                        onClick={closeMobileFilters}
                    />
                    <div className="absolute inset-x-0 bottom-0 max-h-[84vh] overflow-y-auto bg-bg-secondary border-t border-border-color rounded-t-2xl p-4 pb-8">
                        <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-2">
                                <SlidersHorizontal className="h-5 w-5 text-theme-primary" />
                                <h2 className="font-semibold text-text-primary">Filters</h2>
                            </div>
                            <button
                                onClick={closeMobileFilters}
                                className="btn btn-ghost btn-icon-sm"
                                aria-label="Close"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        </div>
                        <SearchFilters
                            onSearchChange={handleSearchChange}
                            categories={categoriesData || []}
                        />
                    </div>
                </div>
            )}
        </div>
    )
}
