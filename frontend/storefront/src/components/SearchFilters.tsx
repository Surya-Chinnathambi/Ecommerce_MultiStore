import { useState, useEffect } from 'react'
import { Search, SlidersHorizontal, X } from 'lucide-react'

interface SearchFiltersProps {
    onSearchChange: (params: SearchParams) => void
    categories: Array<{ id: string; name: string }>
}

export interface SearchParams {
    q?: string
    category_id?: string
    min_price?: number
    max_price?: number
    in_stock?: boolean
    min_rating?: number
    sort_by?: string
    sort_order?: string
}

export default function SearchFilters({ onSearchChange, categories }: SearchFiltersProps) {
    const [showFilters, setShowFilters] = useState(false)
    const [searchTerm, setSearchTerm] = useState('')
    const [filters, setFilters] = useState<SearchParams>({
        sort_by: 'newest',
        sort_order: 'desc',
    })

    useEffect(() => {
        const debounce = setTimeout(() => {
            if (searchTerm) {
                onSearchChange({ ...filters, q: searchTerm })
            } else {
                const { q, ...rest } = filters
                onSearchChange(rest)
            }
        }, 500)

        return () => clearTimeout(debounce)
    }, [searchTerm])

    const handleFilterChange = (key: string, value: any) => {
        const newFilters = { ...filters, [key]: value }
        setFilters(newFilters)

        if (searchTerm) {
            onSearchChange({ ...newFilters, q: searchTerm })
        } else {
            onSearchChange(newFilters)
        }
    }

    const clearFilters = () => {
        setSearchTerm('')
        setFilters({
            sort_by: 'newest',
            sort_order: 'desc',
        })
        onSearchChange({
            sort_by: 'newest',
            sort_order: 'desc',
        })
    }

    const hasActiveFilters = () => {
        return (
            searchTerm ||
            filters.category_id ||
            filters.min_price ||
            filters.max_price ||
            filters.in_stock !== undefined ||
            filters.min_rating
        )
    }

    return (
        <div className="bg-bg-primary p-4 rounded-lg shadow-md mb-6 border border-border-color">
            {/* Search Bar */}
            <div className="flex gap-2 mb-4">
                <div className="flex-1 relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-text-tertiary" size={20} />
                    <input
                        type="text"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        placeholder="Search products..."
                        className="w-full pl-10 pr-4 py-2 border border-border-color rounded-lg focus:outline-none focus:ring-2 focus:ring-theme-primary bg-bg-primary text-text-primary"
                    />
                </div>
                <button
                    onClick={() => setShowFilters(!showFilters)}
                    className="px-4 py-2 border border-border-color rounded-lg hover:bg-bg-tertiary flex items-center gap-2 text-text-primary"
                >
                    <SlidersHorizontal size={20} />
                    Filters
                    {hasActiveFilters() && (
                        <span className="bg-theme-primary text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                            !
                        </span>
                    )}
                </button>
                {hasActiveFilters() && (
                    <button
                        onClick={clearFilters}
                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg flex items-center gap-2"
                    >
                        <X size={20} />
                        Clear
                    </button>
                )}
            </div>

            {/* Advanced Filters */}
            {showFilters && (
                <div className="border-t pt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {/* Category Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Category</label>
                        <select
                            value={filters.category_id || ''}
                            onChange={(e) => handleFilterChange('category_id', e.target.value || undefined)}
                            aria-label="Filter by category"
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="">All Categories</option>
                            {categories.map((cat) => (
                                <option key={cat.id} value={cat.id}>
                                    {cat.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Price Range */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Min Price</label>
                        <input
                            type="number"
                            value={filters.min_price || ''}
                            onChange={(e) =>
                                handleFilterChange('min_price', e.target.value ? Number(e.target.value) : undefined)
                            }
                            placeholder="₹0"
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium mb-2">Max Price</label>
                        <input
                            type="number"
                            value={filters.max_price || ''}
                            onChange={(e) =>
                                handleFilterChange('max_price', e.target.value ? Number(e.target.value) : undefined)
                            }
                            placeholder="₹10000"
                            className="w-full px-3 py-2 border rounded-lg"
                        />
                    </div>

                    {/* Rating Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Min Rating</label>
                        <select
                            value={filters.min_rating || ''}
                            onChange={(e) =>
                                handleFilterChange('min_rating', e.target.value ? Number(e.target.value) : undefined)
                            }
                            aria-label="Filter by minimum rating"
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="">All Ratings</option>
                            <option value="4">4+ Stars</option>
                            <option value="3">3+ Stars</option>
                            <option value="2">2+ Stars</option>
                            <option value="1">1+ Stars</option>
                        </select>
                    </div>

                    {/* Stock Filter */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Availability</label>
                        <select
                            value={filters.in_stock === undefined ? '' : filters.in_stock ? 'true' : 'false'}
                            onChange={(e) =>
                                handleFilterChange(
                                    'in_stock',
                                    e.target.value === '' ? undefined : e.target.value === 'true'
                                )
                            }
                            aria-label="Filter by stock availability"
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="">All Products</option>
                            <option value="true">In Stock</option>
                            <option value="false">Out of Stock</option>
                        </select>
                    </div>

                    {/* Sort By */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Sort By</label>
                        <select
                            value={filters.sort_by || 'newest'}
                            onChange={(e) => handleFilterChange('sort_by', e.target.value)}
                            aria-label="Sort products by"
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="newest">Newest</option>
                            <option value="name">Name</option>
                            <option value="price">Price</option>
                        </select>
                    </div>

                    {/* Sort Order */}
                    <div>
                        <label className="block text-sm font-medium mb-2">Order</label>
                        <select
                            value={filters.sort_order || 'desc'}
                            onChange={(e) => handleFilterChange('sort_order', e.target.value)}
                            aria-label="Sort order"
                            className="w-full px-3 py-2 border rounded-lg"
                        >
                            <option value="desc">Descending</option>
                            <option value="asc">Ascending</option>
                        </select>
                    </div>
                </div>
            )}
        </div>
    )
}
