import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Search, SlidersHorizontal, X, ChevronDown } from 'lucide-react'
import { typesenseSearchApi, productsApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'

const SORT_OPTIONS = [
    { value: 'relevance', label: 'Most Relevant' },
    { value: 'price_asc', label: 'Price: Low to High' },
    { value: 'price_desc', label: 'Price: High to Low' },
    { value: 'newest', label: 'Newest First' },
    { value: 'discount', label: 'Biggest Discount' },
]

interface SearchResult {
    id: string
    name: string
    selling_price: number
    mrp: number
    discount_percent: number
    thumbnail?: string
    is_in_stock: boolean
    category_id?: string
}

export default function SearchResultsPage() {
    const [searchParams] = useSearchParams()
    const q = searchParams.get('q') || searchParams.get('search') || ''
    const [page, setPage] = useState(1)
    const [sort, setSort] = useState('relevance')
    const [minPrice, setMinPrice] = useState('')
    const [maxPrice, setMaxPrice] = useState('')
    const [inStockOnly, setInStockOnly] = useState(false)
    const [filterOpen, setFilterOpen] = useState(false)
    const [useTypesense, setUseTypesense] = useState(true)

    // Reset page when query changes
    useEffect(() => {
        setPage(1)
    }, [q])

    // Typesense search
    const tsQuery = useQuery({
        queryKey: ['ts-search', q, page, sort, minPrice, maxPrice, inStockOnly],
        queryFn: () =>
            typesenseSearchApi
                .search({
                    q,
                    page,
                    per_page: 24,
                    sort,
                    min_price: minPrice ? Number(minPrice) : undefined,
                    max_price: maxPrice ? Number(maxPrice) : undefined,
                    in_stock: inStockOnly || undefined,
                })
                .then((r) => r.data.data),
        enabled: !!q && useTypesense,
        retry: 0,
    })

    // Fall back to basic search if Typesense errors
    useEffect(() => {
        if (tsQuery.isError) setUseTypesense(false)
    }, [tsQuery.isError])

    // Fallback: regular products search
    const fallbackQuery = useQuery({
        queryKey: ['products-search-fallback', q, page],
        queryFn: () =>
            productsApi.getProducts({ page, limit: 24, search: q }).then((r) => r.data.data),
        enabled: !!q && !useTypesense,
    })

    const isLoading = useTypesense ? tsQuery.isLoading : fallbackQuery.isLoading
    const rawData = useTypesense ? tsQuery.data : fallbackQuery.data

    // Normalize results — Typesense returns { results, total, page } or similar
    const results: SearchResult[] = rawData?.results ?? rawData?.products ?? rawData ?? []
    const total: number = rawData?.total ?? rawData?.found ?? results.length
    const totalPages = Math.ceil(total / 24)

    const clearFilters = () => {
        setMinPrice('')
        setMaxPrice('')
        setInStockOnly(false)
        setSort('relevance')
    }

    const hasActiveFilters = minPrice || maxPrice || inStockOnly || sort !== 'relevance'

    return (
        <div className="container mx-auto px-4 py-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-5 flex-wrap gap-3">
                <div>
                    <h1 className="text-xl font-bold text-text-primary flex items-center gap-2">
                        <Search className="h-5 w-5 text-theme-primary" />
                        {q ? (
                            <>Results for "<span className="text-theme-primary">{q}</span>"</>
                        ) : (
                            'Browse Products'
                        )}
                    </h1>
                    {!isLoading && (
                        <p className="text-sm text-text-tertiary mt-0.5">
                            {total.toLocaleString()} product{total !== 1 ? 's' : ''} found
                            {!useTypesense && <span className="ml-2 text-xs text-amber-500">(using basic search)</span>}
                        </p>
                    )}
                </div>
                <div className="flex items-center gap-3">
                    {/* Sort */}
                    <div className="relative">
                        <select
                            title="Sort results"
                            value={sort}
                            onChange={(e) => { setSort(e.target.value); setPage(1) }}
                            className="appearance-none pl-3 pr-8 py-2 text-sm bg-bg-primary border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary/40 cursor-pointer"
                        >
                            {SORT_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                        </select>
                        <ChevronDown className="absolute right-2 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                    </div>
                    {/* Filter toggle (mobile) */}
                    <button
                        onClick={() => setFilterOpen(!filterOpen)}
                        aria-label="Toggle filters"
                        className={`flex items-center gap-2 px-3 py-2 text-sm rounded-lg border transition-colors
                            ${hasActiveFilters ? 'bg-theme-primary text-white border-theme-primary' : 'bg-bg-primary text-text-secondary border-border-color hover:border-theme-primary/40'}`}
                    >
                        <SlidersHorizontal className="h-4 w-4" />
                        Filters
                        {hasActiveFilters && (
                            <span className="bg-white/20 text-white rounded-full px-1.5 text-xs">•</span>
                        )}
                    </button>
                    {hasActiveFilters && (
                        <button
                            onClick={clearFilters}
                            aria-label="Clear filters"
                            className="text-xs text-text-tertiary hover:text-red-500 flex items-center gap-1"
                        >
                            <X className="h-3 w-3" /> Clear
                        </button>
                    )}
                </div>
            </div>

            <div className="flex gap-6">
                {/* Sidebar filters */}
                <aside className={`${filterOpen ? 'block' : 'hidden'} md:block w-full md:w-56 flex-shrink-0`}>
                    <div className="bg-bg-primary border border-border-color rounded-xl p-4 space-y-5 sticky top-20">
                        <h3 className="font-semibold text-text-primary text-sm">Filters</h3>

                        {/* Price range */}
                        <div>
                            <p className="text-xs font-medium text-text-secondary mb-2">Price Range (₹)</p>
                            <div className="flex gap-2">
                                <input
                                    type="number"
                                    min={0}
                                    placeholder="Min"
                                    title="Minimum price"
                                    value={minPrice}
                                    onChange={(e) => { setMinPrice(e.target.value); setPage(1) }}
                                    className="w-full px-2 py-1.5 text-xs bg-bg-secondary border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-theme-primary/40"
                                />
                                <input
                                    type="number"
                                    min={0}
                                    placeholder="Max"
                                    title="Maximum price"
                                    value={maxPrice}
                                    onChange={(e) => { setMaxPrice(e.target.value); setPage(1) }}
                                    className="w-full px-2 py-1.5 text-xs bg-bg-secondary border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-1 focus:ring-theme-primary/40"
                                />
                            </div>
                        </div>

                        {/* Availability */}
                        <div>
                            <p className="text-xs font-medium text-text-secondary mb-2">Availability</p>
                            <label className="flex items-center gap-2 cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={inStockOnly}
                                    onChange={(e) => { setInStockOnly(e.target.checked); setPage(1) }}
                                    className="h-4 w-4 rounded accent-theme-primary"
                                />
                                <span className="text-sm text-text-primary">In Stock Only</span>
                            </label>
                        </div>

                        {/* SearchFilters component omitted — price/stock filters handled inline above */}
                    </div>
                </aside>

                {/* Results grid */}
                <div className="flex-1 min-w-0">
                    {!q && !isLoading && (
                        <div className="text-center py-20 text-text-tertiary">
                            <Search className="h-14 w-14 mx-auto mb-4 opacity-20" />
                            <p className="text-lg font-medium">Start searching</p>
                            <p className="text-sm mt-1">Type in the search bar above to find products</p>
                        </div>
                    )}

                    {isLoading && (
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                            {Array.from({ length: 12 }).map((_, i) => (
                                <div key={i} className="bg-bg-secondary rounded-xl h-64 animate-pulse" />
                            ))}
                        </div>
                    )}

                    {!isLoading && q && results.length === 0 && (
                        <div className="text-center py-20 text-text-tertiary">
                            <Search className="h-14 w-14 mx-auto mb-4 opacity-20" />
                            <p className="text-lg font-medium">No results found</p>
                            <p className="text-sm mt-1">Try different keywords or clear filters</p>
                            {hasActiveFilters && (
                                <button onClick={clearFilters} className="mt-4 btn btn-secondary text-sm">
                                    Clear all filters
                                </button>
                            )}
                        </div>
                    )}

                    {!isLoading && results.length > 0 && (
                        <>
                            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                                {results.map((product: SearchResult) => (
                                    <ProductCard key={product.id} product={product as any} />
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-center gap-2 mt-8">
                                    <button
                                        disabled={page === 1}
                                        onClick={() => setPage((p) => p - 1)}
                                        className="px-4 py-2 text-sm rounded-lg border border-border-color text-text-secondary hover:border-theme-primary/40 disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        Previous
                                    </button>
                                    <span className="text-sm text-text-secondary">
                                        Page {page} of {totalPages}
                                    </span>
                                    <button
                                        disabled={page >= totalPages}
                                        onClick={() => setPage((p) => p + 1)}
                                        className="px-4 py-2 text-sm rounded-lg border border-border-color text-text-secondary hover:border-theme-primary/40 disabled:opacity-40 disabled:cursor-not-allowed"
                                    >
                                        Next
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>
        </div>
    )
}
