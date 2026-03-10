import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { sellerApi } from '@/lib/api'
import { Link } from 'react-router-dom'
import {
    ShoppingBag, Search, X,
    IndianRupee, Package
} from 'lucide-react'
import PaginationControls from '@/components/ui/PaginationControls'
import StatusBadge from '@/components/ui/StatusBadge'

interface SellerOrder {
    id: string
    order_number: string
    order_status: string
    payment_status: string
    payment_method: string
    customer_name: string
    delivery_city: string
    delivery_state: string
    created_at: string
    my_total: number
    my_items_count: number
    items: {
        product_name: string
        quantity: number
        unit_price: number
        total: number
    }[]
}

const STATUS_CHIPS = ['', 'PENDING', 'CONFIRMED', 'SHIPPED', 'DELIVERED', 'CANCELLED']

export default function SellerOrdersPage() {
    const [page, setPage] = useState(1)
    const [search, setSearch] = useState('')
    const [statusFilter, setStatusFilter] = useState('')
    const [expanded, setExpanded] = useState<string | null>(null)

    const { data, isLoading } = useQuery({
        queryKey: ['seller-orders', page, statusFilter],
        queryFn: () => sellerApi.getOrders({
            page,
            per_page: 20,
            ...(statusFilter ? { status_filter: statusFilter } : {}),
        }).then(r => r.data),
        placeholderData: (prev) => prev,
    })

    const allOrders: SellerOrder[] = data?.data ?? []
    const total: number = data?.meta?.total ?? 0
    const totalPages = Math.max(1, Math.ceil(total / 20))

    const filtered = search.trim()
        ? allOrders.filter(o =>
            o.order_number.toLowerCase().includes(search.toLowerCase()) ||
            o.customer_name.toLowerCase().includes(search.toLowerCase()))
        : allOrders

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
                <div>
                    <h1 className="section-title flex items-center gap-2">
                        <ShoppingBag className="h-6 w-6 text-theme-primary" />
                        My Orders
                    </h1>
                    <p className="section-subtitle">Orders containing your products</p>
                </div>
                <Link to="/seller/dashboard" className="btn btn-outline btn-sm self-start sm:self-auto">
                    ← Dashboard
                </Link>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-3 mb-5">
                {/* Search */}
                <div className="relative flex-1 max-w-sm">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                    <input
                        className="input pl-9 pr-8 w-full"
                        placeholder="Order # or customer…"
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                    />
                    {search && (
                        <button
                            onClick={() => setSearch('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                            aria-label="Clear search"
                            title="Clear"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
                {/* Status chips */}
                <div className="flex flex-wrap gap-2">
                    {STATUS_CHIPS.map(s => (
                        <button
                            key={s || 'all'}
                            onClick={() => { setStatusFilter(s); setPage(1) }}
                            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors
                                ${statusFilter === s
                                    ? 'bg-theme-primary text-white border-theme-primary'
                                    : 'border-border-color text-text-secondary hover:border-theme-primary'}`}
                        >
                            {s || 'All'}
                        </button>
                    ))}
                </div>
            </div>

            {/* List */}
            {isLoading ? (
                <div className="space-y-3">
                    {[...Array(5)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
                </div>
            ) : filtered.length === 0 ? (
                <div className="card text-center py-16">
                    <ShoppingBag className="h-12 w-12 mx-auto text-text-tertiary mb-3" />
                    <p className="text-text-secondary">No orders found</p>
                    {search && <button onClick={() => setSearch('')} className="btn btn-outline btn-sm mt-4">Clear search</button>}
                </div>
            ) : (
                <div className="space-y-3">
                    {filtered.map(order => (
                        <div key={order.id} className="card p-0 overflow-hidden">
                            {/* Summary row */}
                            <button
                                onClick={() => setExpanded(expanded === order.id ? null : order.id)}
                                className="w-full text-left px-4 py-3 hover:bg-bg-tertiary/50 transition-colors"
                            >
                                <div className="flex flex-wrap items-center gap-3">
                                    <span className="font-mono text-sm font-bold text-text-primary">
                                        {order.order_number}
                                    </span>
                                    <StatusBadge status={order.order_status} className="text-xs" />
                                    <span className="text-sm text-text-secondary">{order.customer_name}</span>
                                    {(order.delivery_city || order.delivery_state) && (
                                        <span className="text-xs text-text-tertiary">
                                            {[order.delivery_city, order.delivery_state].filter(Boolean).join(', ')}
                                        </span>
                                    )}
                                    <span className="ml-auto font-bold text-green-600 flex items-center gap-0.5">
                                        <IndianRupee className="h-3.5 w-3.5" />
                                        {order.my_total.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                    </span>
                                    <span className="text-xs text-text-tertiary">
                                        {order.my_items_count} item{order.my_items_count !== 1 ? 's' : ''}
                                    </span>
                                    <span className="text-xs text-text-tertiary">
                                        {new Date(order.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' })}
                                    </span>
                                </div>
                            </button>

                            {/* Expanded items */}
                            {expanded === order.id && (
                                <div className="border-t border-border-color px-4 py-3 bg-bg-tertiary/30">
                                    <table className="w-full text-sm">
                                        <thead>
                                            <tr className="text-xs text-text-tertiary uppercase tracking-wide">
                                                <th className="text-left pb-2">Product</th>
                                                <th className="text-right pb-2">Qty</th>
                                                <th className="text-right pb-2">Unit Price</th>
                                                <th className="text-right pb-2">Total</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-border-color">
                                            {order.items.map((item, i) => (
                                                <tr key={i}>
                                                    <td className="py-1.5 text-text-primary">{item.product_name}</td>
                                                    <td className="py-1.5 text-right text-text-secondary">×{item.quantity}</td>
                                                    <td className="py-1.5 text-right text-text-secondary">₹{item.unit_price.toLocaleString('en-IN')}</td>
                                                    <td className="py-1.5 text-right font-medium text-text-primary">₹{item.total.toLocaleString('en-IN')}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                    <div className="flex justify-between items-center mt-2 pt-2 border-t border-border-color">
                                        <span className="text-xs text-text-tertiary">Payment: {order.payment_method} · {order.payment_status}</span>
                                        <span className="font-bold text-green-600">
                                            Your earnings: ₹{order.my_total.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                        </span>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Pagination */}
            <PaginationControls
                className="mt-6"
                page={page}
                totalPages={totalPages}
                onPrev={() => setPage(p => Math.max(1, p - 1))}
                onNext={() => setPage(p => Math.min(totalPages, p + 1))}
            />
        </div>
    )
}
