import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { storeApi } from '@/lib/api'
import {
    Package, Search, X, Star, AlertTriangle, CheckCircle,
    XCircle, ExternalLink,
} from 'lucide-react'
import DataGrid from '@/components/ui/DataGrid'
import PaginationControls from '@/components/ui/PaginationControls'
import RowActions, { RowActionLink } from '@/components/ui/RowActions'

export default function AdminProductsPage() {
    const [page, setPage] = useState(1)
    const [search, setSearch] = useState('')
    const [categoryId, setCategoryId] = useState('')
    const [inStock, setInStock] = useState<boolean | undefined>(undefined)
    const [isFeatured, setIsFeatured] = useState<boolean | undefined>(undefined)

    const { data: categoriesData } = useQuery({
        queryKey: ['categories'],
        queryFn: () => storeApi.getCategories().then(r => r.data.data),
    })

    const { data, isLoading } = useQuery({
        queryKey: ['admin-products', page, search, categoryId, inStock, isFeatured],
        queryFn: () => adminApi.getAdminProducts({
            page,
            search: search || undefined,
            category_id: categoryId || undefined,
            in_stock: inStock,
            is_featured: isFeatured,
        }).then(r => r.data.data),
    })

    const products = data?.products ?? []
    const totalPages = data?.total_pages ?? 1
    const total = data?.total ?? 0

    const resetFilters = () => {
        setSearch('')
        setCategoryId('')
        setInStock(undefined)
        setIsFeatured(undefined)
        setPage(1)
    }

    const hasFilters = search || categoryId || inStock !== undefined || isFeatured !== undefined

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="section-title flex items-center gap-2">
                        <Package className="h-6 w-6 text-theme-primary" />
                        Products
                    </h1>
                    <p className="section-subtitle">{total} total products (including inactive)</p>
                </div>
            </div>

            {/* Filter bar */}
            <div className="card mb-6 space-y-3">
                <div className="flex flex-col sm:flex-row gap-3">
                    {/* Search */}
                    <div className="relative flex-1">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                        <input
                            className="input pl-9 w-full"
                            placeholder="Search by name, SKU, barcode…"
                            value={search}
                            onChange={e => { setSearch(e.target.value); setPage(1) }}
                        />
                        {search && (
                            <button
                                onClick={() => setSearch('')}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                                aria-label="Clear search"
                            >
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    </div>

                    {/* Category */}
                    <select
                        title="Filter by category"
                        className="input sm:w-48"
                        value={categoryId}
                        onChange={e => { setCategoryId(e.target.value); setPage(1) }}
                    >
                        <option value="">All Categories</option>
                        {(categoriesData || []).map((c: any) => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                        ))}
                    </select>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                    {/* In stock toggle chips */}
                    {([
                        { label: 'In Stock', val: true },
                        { label: 'Out of Stock', val: false },
                    ] as const).map(chip => (
                        <button
                            key={String(chip.val)}
                            onClick={() => { setInStock(inStock === chip.val ? undefined : chip.val); setPage(1) }}
                            className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${inStock === chip.val
                                ? 'bg-theme-primary text-white border-theme-primary'
                                : 'bg-bg-primary text-text-secondary border-border-color hover:border-theme-primary/50'
                                }`}
                        >
                            {chip.label}
                        </button>
                    ))}
                    <button
                        onClick={() => { setIsFeatured(isFeatured === true ? undefined : true); setPage(1) }}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${isFeatured === true
                            ? 'bg-amber-500 text-white border-amber-500'
                            : 'bg-bg-primary text-text-secondary border-border-color hover:border-amber-500/50'
                            }`}
                    >
                        ⭐ Featured
                    </button>
                    {hasFilters && (
                        <button onClick={resetFilters} className="text-xs text-text-tertiary hover:text-red-500 underline ml-1">
                            Clear all
                        </button>
                    )}
                </div>
            </div>

            {/* Product table */}
            {isLoading ? (
                <div className="space-y-3">
                    {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
                </div>
            ) : products.length === 0 ? (
                <div className="card text-center py-16">
                    <Package className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                    <p className="text-text-secondary">No products found</p>
                    {hasFilters && (
                        <button onClick={resetFilters} className="btn btn-outline btn-sm mt-4">Clear Filters</button>
                    )}
                </div>
            ) : (
                <>
                    <DataGrid className="card p-0 overflow-hidden">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b border-border-color bg-bg-tertiary text-text-secondary text-xs uppercase tracking-wider">
                                    <th className="text-left pl-4 py-3 w-12"></th>
                                    <th className="text-left px-3 py-3">Product</th>
                                    <th className="text-left px-3 py-3">SKU</th>
                                    <th className="text-right px-3 py-3">Price</th>
                                    <th className="text-right px-3 py-3">MRP</th>
                                    <th className="text-right px-3 py-3">Stock</th>
                                    <th className="text-center px-3 py-3">Status</th>
                                    <th className="text-center px-3 py-3">Featured</th>
                                    <th className="text-center px-3 py-3">Rating</th>
                                    <th className="py-3 pr-4"></th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border-color">
                                {products.map((p: any) => (
                                    <tr key={p.id} className={`hover:bg-bg-tertiary/50 transition-colors ${!p.is_active ? 'opacity-50' : ''}`}>
                                        <td className="pl-4 py-3">
                                            {p.thumbnail ? (
                                                <img src={p.thumbnail} alt="" className="w-10 h-10 object-cover rounded-lg flex-shrink-0" />
                                            ) : (
                                                <div className="w-10 h-10 bg-bg-tertiary rounded-lg flex items-center justify-center flex-shrink-0">
                                                    <Package className="h-4 w-4 text-text-tertiary" />
                                                </div>
                                            )}
                                        </td>
                                        <td className="px-3 py-3 max-w-[200px]">
                                            <p className="font-medium text-text-primary truncate">{p.name}</p>
                                            {p.category_name && (
                                                <p className="text-xs text-text-tertiary truncate">{p.category_name}</p>
                                            )}
                                        </td>
                                        <td className="px-3 py-3 font-mono text-xs text-text-secondary">{p.sku || '—'}</td>
                                        <td className="px-3 py-3 text-right font-semibold text-text-primary">
                                            ₹{p.selling_price?.toLocaleString()}
                                        </td>
                                        <td className="px-3 py-3 text-right text-xs text-text-tertiary line-through">
                                            {p.mrp ? `₹${p.mrp.toLocaleString()}` : '—'}
                                        </td>
                                        <td className="px-3 py-3 text-right">
                                            <span className={`font-semibold ${p.quantity === 0 ? 'text-red-500' :
                                                p.quantity <= (p.low_stock_threshold ?? 5) ? 'text-orange-500' :
                                                    'text-text-primary'
                                                }`}>
                                                {p.quantity}
                                                {p.quantity > 0 && p.quantity <= (p.low_stock_threshold ?? 5) && (
                                                    <AlertTriangle className="inline h-3 w-3 ml-1 text-orange-500" />
                                                )}
                                            </span>
                                        </td>
                                        <td className="px-3 py-3 text-center">
                                            {p.is_active
                                                ? <CheckCircle className="h-4 w-4 text-green-500 mx-auto" />
                                                : <XCircle className="h-4 w-4 text-red-500 mx-auto" />
                                            }
                                        </td>
                                        <td className="px-3 py-3 text-center">
                                            {p.is_featured && <Star className="h-4 w-4 text-amber-400 fill-amber-400 mx-auto" />}
                                        </td>
                                        <td className="px-3 py-3 text-center text-xs text-text-secondary">
                                            {p.average_rating > 0 ? (
                                                <span className="flex items-center justify-center gap-0.5">
                                                    <Star className="h-3 w-3 text-amber-400 fill-amber-400" />
                                                    {Number(p.average_rating).toFixed(1)}
                                                </span>
                                            ) : '—'}
                                        </td>
                                        <td className="pr-4 py-3">
                                            <RowActions>
                                                <RowActionLink
                                                    href={`/products/${p.id}`}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    title="View product"
                                                    aria-label="View product"
                                                    tone="primary"
                                                    iconOnly
                                                    icon={<ExternalLink className="h-4 w-4" />}
                                                />
                                            </RowActions>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </DataGrid>

                    {/* Pagination */}
                    <PaginationControls
                        className="mt-6"
                        page={page}
                        totalPages={totalPages}
                        onPrev={() => setPage(p => Math.max(1, p - 1))}
                        onNext={() => setPage(p => Math.min(totalPages, p + 1))}
                    />
                </>
            )}
        </div>
    )
}
