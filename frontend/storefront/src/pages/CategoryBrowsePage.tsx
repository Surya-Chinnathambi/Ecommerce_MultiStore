import { useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { storeApi, productsApi } from '@/lib/api'
import ProductCard from '@/components/ProductCard'
import {
    ChevronRight, LayoutGrid, Layers, Search, X, SlidersHorizontal
} from 'lucide-react'

interface Category {
    id: string
    name: string
    slug: string
    description?: string
    parent_id?: string | null
    display_order: number
    is_active: boolean
}

// Palette of gradient pairs for category cards
const GRADIENTS = [
    'from-violet-500 to-purple-600',
    'from-blue-500 to-cyan-500',
    'from-emerald-500 to-teal-600',
    'from-orange-400 to-rose-500',
    'from-pink-500 to-fuchsia-600',
    'from-amber-400 to-orange-500',
    'from-sky-500 to-indigo-600',
    'from-lime-500 to-green-600',
]

function gradientFor(index: number) {
    return GRADIENTS[index % GRADIENTS.length]
}

// ── All-categories grid ───────────────────────────────────────────────────────
function CategoriesGrid({ categories }: { categories: Category[] }) {
    const [search, setSearch] = useState('')

    const filtered = useMemo(() => {
        if (!search.trim()) return categories
        const q = search.toLowerCase()
        return categories.filter(c => c.name.toLowerCase().includes(q))
    }, [categories, search])

    return (
        <div className="animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <div>
                    <h1 className="section-title flex items-center gap-2">
                        <LayoutGrid className="h-6 w-6 text-theme-primary" />
                        All Categories
                    </h1>
                    <p className="section-subtitle">{categories.length} categories available</p>
                </div>
                <div className="relative w-full sm:w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                    <input
                        className="input pl-9 pr-8 w-full"
                        placeholder="Search categories…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    {search && (
                        <button
                            onClick={() => setSearch('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                            aria-label="Clear search"
                            title="Clear search"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </div>

            {filtered.length === 0 ? (
                <div className="card text-center py-16">
                    <Layers className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                    <p className="text-text-secondary">No categories match &quot;{search}&quot;</p>
                    <button onClick={() => setSearch('')} className="btn btn-outline btn-sm mt-4">Clear</button>
                </div>
            ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                    {filtered.map((cat, i) => (
                        <Link
                            key={cat.id}
                            to={`/categories/${cat.slug}`}
                            className="card group p-0 overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
                        >
                            {/* Color band */}
                            <div className={`bg-gradient-to-br ${gradientFor(i)} h-24 flex items-center justify-center`}>
                                <Layers className="h-10 w-10 text-white/80" />
                            </div>
                            <div className="p-3">
                                <p className="font-semibold text-text-primary text-sm group-hover:text-theme-primary transition-colors">
                                    {cat.name}
                                </p>
                                {cat.description && (
                                    <p className="text-xs text-text-tertiary mt-0.5 line-clamp-2">{cat.description}</p>
                                )}
                            </div>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    )
}

// ── Single-category product listing ──────────────────────────────────────────
type SortKey = 'newest' | 'price_asc' | 'price_desc' | 'popular'

const SORT_OPTIONS: { label: string; value: SortKey }[] = [
    { label: 'Newest', value: 'newest' },
    { label: 'Price: Low → High', value: 'price_asc' },
    { label: 'Price: High → Low', value: 'price_desc' },
    { label: 'Popular', value: 'popular' },
]

function CategoryProducts({ slug, categories }: { slug: string; categories: Category[] }) {
    const [sort, setSort] = useState<SortKey>('newest')
    const [page, setPage] = useState(1)
    const [showFilters, setShowFilters] = useState(false)

    const category = categories.find(c => c.slug === slug)

    const sortParam: Record<SortKey, Record<string, string | number>> = {
        newest: { sort: 'created_at', order: 'desc' },
        price_asc: { sort: 'price', order: 'asc' },
        price_desc: { sort: 'price', order: 'desc' },
        popular: { sort: 'rating', order: 'desc' },
    }

    const { data: productsData, isLoading } = useQuery({
        queryKey: ['category-products', category?.id, sort, page],
        queryFn: () =>
            productsApi.getProducts({
                category_id: category?.id,
                page,
                per_page: 20,
                ...sortParam[sort],
            }).then(r => r.data),
        enabled: !!category,
    })

    const products = productsData?.data?.products ?? productsData?.products ?? []
    const total = productsData?.meta?.total ?? productsData?.total ?? 0
    const totalPages = Math.max(1, Math.ceil(total / 20))

    if (!category) {
        return (
            <div className="card text-center py-16 animate-fade-in">
                <Layers className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                <p className="text-text-secondary">Category not found.</p>
                <Link to="/categories" className="btn btn-outline btn-sm mt-4">Browse all categories</Link>
            </div>
        )
    }

    return (
        <div className="animate-fade-in">
            {/* Breadcrumb */}
            <nav className="flex items-center gap-1 text-sm text-text-tertiary mb-4">
                <Link to="/categories" className="hover:text-theme-primary transition-colors">Categories</Link>
                <ChevronRight className="h-3 w-3" />
                <span className="text-text-primary font-medium">{category.name}</span>
            </nav>

            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
                <div>
                    <h1 className="section-title">{category.name}</h1>
                    {category.description && <p className="section-subtitle">{category.description}</p>}
                    {!isLoading && <p className="text-sm text-text-tertiary mt-0.5">{total} products</p>}
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={() => setShowFilters(v => !v)}
                        className={`btn btn-sm ${showFilters ? 'btn-primary' : 'btn-outline'} flex items-center gap-1`}
                        title="Filters"
                    >
                        <SlidersHorizontal className="h-3.5 w-3.5" />
                        Sort
                    </button>
                </div>
            </div>

            {/* Sort bar */}
            {showFilters && (
                <div className="card mb-5">
                    <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-2">Sort by</p>
                    <div className="flex flex-wrap gap-2">
                        {SORT_OPTIONS.map(opt => (
                            <button
                                key={opt.value}
                                onClick={() => { setSort(opt.value); setPage(1) }}
                                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors border
                                    ${sort === opt.value
                                        ? 'bg-theme-primary text-white border-theme-primary'
                                        : 'border-border-color text-text-secondary hover:border-theme-primary hover:text-theme-primary'
                                    }`}
                            >
                                {opt.label}
                            </button>
                        ))}
                    </div>
                </div>
            )}

            {/* Products grid */}
            {isLoading ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                    {[...Array(8)].map((_, i) => <div key={i} className="skeleton aspect-[3/4] rounded-xl" />)}
                </div>
            ) : products.length === 0 ? (
                <div className="card text-center py-16">
                    <Layers className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                    <p className="text-text-secondary">No products in this category yet.</p>
                    <Link to="/products" className="btn btn-outline btn-sm mt-4">Browse all products</Link>
                </div>
            ) : (
                <>
                    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                        {products.map((p: any) => (
                            <ProductCard key={p.id} product={p} />
                        ))}
                    </div>

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="flex items-center justify-center gap-2 mt-8 flex-wrap">
                            <button
                                onClick={() => setPage(1)}
                                disabled={page === 1}
                                className="btn btn-outline btn-sm"
                            >
                                First
                            </button>
                            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                                const pg = Math.max(1, Math.min(page - 2 + i, totalPages - 4 + i))
                                return pg
                            }).filter((pg, idx, arr) => arr.indexOf(pg) === idx && pg >= 1 && pg <= totalPages).map(pg => (
                                <button
                                    key={pg}
                                    onClick={() => setPage(pg)}
                                    className={`btn btn-sm ${pg === page ? 'btn-primary' : 'btn-outline'}`}
                                >
                                    {pg}
                                </button>
                            ))}
                            <button
                                onClick={() => setPage(totalPages)}
                                disabled={page === totalPages}
                                className="btn btn-outline btn-sm"
                            >
                                Last
                            </button>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

// ── Route shell ───────────────────────────────────────────────────────────────
export default function CategoryBrowsePage() {
    const { slug } = useParams<{ slug?: string }>()

    const { data: categoriesData, isLoading } = useQuery({
        queryKey: ['categories'],
        queryFn: () => storeApi.getCategories().then(r => r.data.data as Category[]),
        staleTime: 5 * 60 * 1000,
    })

    const categories = categoriesData ?? []

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
                    {[...Array(8)].map((_, i) => <div key={i} className="skeleton aspect-[4/3] rounded-xl" />)}
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {slug
                ? <CategoryProducts slug={slug} categories={categories} />
                : <CategoriesGrid categories={categories} />
            }
        </div>
    )
}
