import { useEffect, useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { useCartStore } from '../store/cartStore'
import { api } from '../lib/api'
import { toast } from '../components/ui/Toaster'
import StatusBadge from '@/components/ui/StatusBadge'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'
import PageHeader from '@/components/ui/PageHeader'
import FilterBar from '@/components/ui/FilterBar'
import PaginationControls from '@/components/ui/PaginationControls'
import { CalendarDays, Clock3, CreditCard, IndianRupee, Package, RefreshCw, Truck } from 'lucide-react'

interface OrderItem {
    id: string
    product_name: string
    quantity: number
    unit_price: number
    total: number
    product?: {
        id: string
        image_url: string | null
    }
}

interface Order {
    id: string
    order_number: string
    order_status: string
    payment_status: string
    payment_method: string
    subtotal: number
    tax_amount: number
    delivery_charge: number
    total_amount: number
    created_at: string
    updated_at?: string
    expected_delivery_date?: string | null
    delivered_at?: string | null
    items: OrderItem[]
    shipping_address: {
        address: string
        city: string
        state: string
        postal_code: string
    }
}

const STATUS_CHIPS = [
    { key: 'all', label: 'All Orders' },
    { key: 'pending', label: 'Pending' },
    { key: 'confirmed', label: 'Confirmed' },
    { key: 'processing', label: 'Processing' },
    { key: 'shipped', label: 'Shipped' },
    { key: 'delivered', label: 'Delivered' },
    { key: 'cancelled', label: 'Cancelled' },
]

const ORDER_STEPS = ['pending', 'confirmed', 'processing', 'shipped', 'delivered']

const statusDescription: Record<string, string> = {
    pending: 'Order is placed and waiting for confirmation.',
    confirmed: 'Order confirmed and queued for packing.',
    processing: 'Warehouse is preparing your items.',
    shipped: 'Package has left the warehouse.',
    delivered: 'Order delivered successfully.',
    cancelled: 'Order was cancelled.',
}

const humanize = (value: string) => `${value.charAt(0).toUpperCase()}${value.slice(1)}`

export default function MyOrdersPage() {
    const navigate = useNavigate()
    const { user } = useAuthStore()

    const [orders, setOrders] = useState<Order[]>([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [searchQuery, setSearchQuery] = useState('')
    const [statusFilter, setStatusFilter] = useState('all')
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)

    useEffect(() => {
        if (!user) {
            navigate('/login')
            return
        }
        fetchOrders()
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user, page, statusFilter])

    useEffect(() => {
        const timeout = setTimeout(() => {
            if (!user) return
            setPage(1)
            fetchOrders(1)
        }, 350)
        return () => clearTimeout(timeout)
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [searchQuery])

    const fetchOrders = async (nextPage?: number) => {
        setLoading(true)
        try {
            const response = await api.get('/orders/customer', {
                params: {
                    page: nextPage ?? page,
                    per_page: 10,
                    status_filter: statusFilter === 'all' ? undefined : statusFilter,
                    search: searchQuery.trim() || undefined,
                },
            })

            if (response.data?.success) {
                setOrders(response.data.data ?? [])
                setTotalPages(response.data.meta?.total_pages ?? 1)
            }
        } catch (error: any) {
            const detail = error?.response?.data?.detail
            toast.error(typeof detail === 'string' ? detail : 'Failed to load your orders')
            setOrders([])
        } finally {
            setLoading(false)
        }
    }

    const stats = useMemo(() => {
        const totalSpend = orders.reduce((acc, order) => acc + (order.total_amount || 0), 0)
        const activeCount = orders.filter((o) => !['delivered', 'cancelled'].includes(o.order_status)).length
        const deliveredCount = orders.filter((o) => o.order_status === 'delivered').length
        return {
            totalSpend,
            activeCount,
            deliveredCount,
            count: orders.length,
        }
    }, [orders])

    const formatCurrency = (amount: number) => new Intl.NumberFormat('en-IN', {
        style: 'currency',
        currency: 'INR',
    }).format(amount)

    const formatDate = (dateString?: string | null) => {
        if (!dateString) return 'N/A'
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: '2-digit',
        })
    }

    const currentStep = (status: string) => {
        const idx = ORDER_STEPS.indexOf(status)
        return idx >= 0 ? idx : 0
    }

    const handleReorder = (order: Order) => {
        const addItem = useCartStore.getState().addItem
        let count = 0

        order.items.forEach((item) => {
            if (!item.product?.id) return
            addItem({
                product_id: item.product.id,
                name: item.product_name,
                price: item.unit_price,
                image: item.product.image_url ?? undefined,
                max_quantity: 99,
                quantity: item.quantity,
            })
            count += 1
        })

        if (count > 0) {
            toast.success(`${count} item${count > 1 ? 's' : ''} added to cart`)
            navigate('/cart')
        } else {
            toast.error('No items available to reorder')
        }
    }

    if (!user) return null

    return (
        <div className="min-h-screen bg-bg-secondary py-8">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-6">
                <PageHeader
                    title="My Orders"
                    subtitle="Track, manage, and reorder from one dashboard"
                />

                <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                    <div className="card">
                        <p className="text-xs uppercase tracking-wider text-text-tertiary">This Page</p>
                        <p className="text-2xl font-bold text-text-primary mt-1">{stats.count}</p>
                        <p className="text-xs text-text-tertiary mt-1">Visible orders</p>
                    </div>
                    <div className="card">
                        <p className="text-xs uppercase tracking-wider text-text-tertiary">Active</p>
                        <p className="text-2xl font-bold text-amber-500 mt-1">{stats.activeCount}</p>
                        <p className="text-xs text-text-tertiary mt-1">In progress</p>
                    </div>
                    <div className="card">
                        <p className="text-xs uppercase tracking-wider text-text-tertiary">Delivered</p>
                        <p className="text-2xl font-bold text-emerald-500 mt-1">{stats.deliveredCount}</p>
                        <p className="text-xs text-text-tertiary mt-1">Completed</p>
                    </div>
                    <div className="card">
                        <p className="text-xs uppercase tracking-wider text-text-tertiary">Total Spend</p>
                        <p className="text-xl font-bold text-theme-primary mt-1">{formatCurrency(stats.totalSpend)}</p>
                        <p className="text-xs text-text-tertiary mt-1">This page scope</p>
                    </div>
                </div>

                <div className="card">
                    <div className="flex flex-col gap-4">
                        <FilterBar
                            searchValue={searchQuery}
                            onSearchChange={setSearchQuery}
                            searchPlaceholder="Search by order number or product name"
                            searchWidthClassName="w-full"
                        />
                        <div className="flex flex-wrap gap-2 items-center justify-between">
                            <div className="flex flex-wrap gap-2">
                                {STATUS_CHIPS.map((chip) => (
                                    <button
                                        key={chip.key}
                                        onClick={() => {
                                            setStatusFilter(chip.key)
                                            setPage(1)
                                        }}
                                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border transition-all ${statusFilter === chip.key
                                            ? 'bg-theme-primary text-white border-theme-primary'
                                            : 'bg-bg-primary text-text-secondary border-border-color hover:border-theme-primary/50'
                                            }`}
                                    >
                                        {chip.label}
                                    </button>
                                ))}
                            </div>
                            <button
                                type="button"
                                onClick={() => fetchOrders()}
                                className="inline-flex items-center gap-1.5 text-sm text-text-secondary hover:text-theme-primary transition-colors"
                            >
                                <RefreshCw className="h-4 w-4" />
                                Refresh
                            </button>
                        </div>
                    </div>
                </div>

                {loading ? (
                    <div className="card text-center py-16">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary mx-auto" />
                        <p className="mt-4 text-text-secondary">Loading your latest orders...</p>
                    </div>
                ) : orders.length === 0 ? (
                    <div className="card">
                        <EmptyState
                            icon={<Package className="h-16 w-16 text-text-tertiary" />}
                            title="No orders found"
                            description={searchQuery || statusFilter !== 'all'
                                ? 'Try a different filter or search term.'
                                : 'Place your first order and it will appear here instantly.'}
                            action={searchQuery || statusFilter !== 'all' ? (
                                <Button
                                    type="button"
                                    variant="outline"
                                    onClick={() => {
                                        setSearchQuery('')
                                        setStatusFilter('all')
                                    }}
                                >
                                    Clear Filters
                                </Button>
                            ) : (
                                <Button type="button" onClick={() => navigate('/products')}>
                                    Browse Products
                                </Button>
                            )}
                        />
                    </div>
                ) : (
                    <div className="space-y-4">
                        {orders.map((order) => {
                            const step = currentStep(order.order_status)
                            const isCancelled = order.order_status === 'cancelled'
                            return (
                                <div key={order.id} className="card overflow-hidden p-0">
                                    <div className="px-5 py-4 border-b border-border-color bg-bg-tertiary/40 flex flex-wrap gap-4 items-center justify-between">
                                        <div>
                                            <p className="text-xs text-text-tertiary">Order Number</p>
                                            <p className="text-lg font-bold text-text-primary">#{order.order_number}</p>
                                            <p className="text-xs text-text-tertiary mt-1">Placed {formatDate(order.created_at)}</p>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-text-tertiary">Total</p>
                                            <p className="text-lg font-bold text-theme-primary">{formatCurrency(order.total_amount)}</p>
                                            <p className="text-xs text-text-tertiary mt-1">{order.items.length} item(s)</p>
                                        </div>
                                    </div>

                                    <div className="px-5 py-4 border-b border-border-color">
                                        <div className="flex items-center justify-between gap-3">
                                            <div>
                                                <StatusBadge status={order.order_status.toUpperCase()} className="text-sm" />
                                                <p className="text-sm text-text-secondary mt-1">{statusDescription[order.order_status] || humanize(order.order_status)}</p>
                                            </div>
                                            <button
                                                onClick={() => setSelectedOrder(order)}
                                                className="text-sm font-medium text-theme-primary hover:text-theme-accent"
                                            >
                                                View Details
                                            </button>
                                        </div>

                                        {!isCancelled && (
                                            <div className="mt-4 flex items-center">
                                                {ORDER_STEPS.map((label, idx) => (
                                                    <div key={label} className="flex items-center flex-1">
                                                        <div className={`h-2.5 w-2.5 rounded-full ${idx <= step ? 'bg-theme-primary' : 'bg-bg-tertiary'}`} />
                                                        {idx < ORDER_STEPS.length - 1 && (
                                                            <div className={`h-0.5 flex-1 mx-1 ${idx < step ? 'bg-theme-primary' : 'bg-bg-tertiary'}`} />
                                                        )}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>

                                    <div className="px-5 py-4 space-y-3">
                                        {order.items.slice(0, 2).map((item) => (
                                            <div key={item.id} className="flex items-center justify-between gap-3">
                                                <div className="flex items-center gap-3 min-w-0">
                                                    {item.product?.image_url ? (
                                                        <img src={item.product.image_url} alt={item.product_name} className="h-14 w-14 rounded-lg object-cover" />
                                                    ) : (
                                                        <div className="h-14 w-14 rounded-lg bg-bg-tertiary flex items-center justify-center">
                                                            <Package className="h-6 w-6 text-text-tertiary" />
                                                        </div>
                                                    )}
                                                    <div className="min-w-0">
                                                        <p className="font-medium text-text-primary truncate">{item.product_name}</p>
                                                        <p className="text-xs text-text-tertiary">Qty {item.quantity}</p>
                                                    </div>
                                                </div>
                                                <p className="text-sm font-semibold text-text-primary">{formatCurrency(item.total)}</p>
                                            </div>
                                        ))}
                                        {order.items.length > 2 && (
                                            <p className="text-xs text-text-tertiary">+ {order.items.length - 2} more item(s)</p>
                                        )}
                                    </div>

                                    <div className="px-5 py-4 border-t border-border-color bg-bg-tertiary/30 flex flex-wrap gap-3 items-center justify-between">
                                        <div className="text-sm text-text-secondary">
                                            Payment: <span className="font-semibold text-text-primary">{order.payment_method}</span>
                                            {' · '}
                                            <span className="capitalize">{order.payment_status}</span>
                                        </div>
                                        <div className="flex items-center gap-3 text-sm">
                                            <button onClick={() => handleReorder(order)} className="text-theme-primary hover:text-theme-accent font-medium">Reorder</button>
                                            <button
                                                onClick={() => navigate(`/track-order?order_number=${encodeURIComponent(order.order_number)}`)}
                                                className="text-blue-500 hover:text-blue-600 font-medium"
                                            >
                                                Track
                                            </button>
                                            {order.order_status === 'delivered' && (
                                                <button
                                                    onClick={() => navigate(`/returns/new/${order.id}`)}
                                                    className="text-orange-500 hover:text-orange-600 font-medium"
                                                >
                                                    Return
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )
                        })}

                        <PaginationControls
                            className="mt-6 flex items-center justify-center gap-4"
                            page={page}
                            totalPages={totalPages}
                            onPrev={() => setPage((p) => Math.max(1, p - 1))}
                            onNext={() => setPage((p) => Math.min(totalPages, p + 1))}
                        />
                    </div>
                )}
            </div>

            {selectedOrder && (
                <div className="fixed inset-0 bg-black/55 z-50 flex items-center justify-center p-4">
                    <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl border border-border-color bg-bg-primary">
                        <div className="sticky top-0 bg-bg-primary border-b border-border-color px-6 py-4 flex items-center justify-between">
                            <div>
                                <h2 className="text-xl font-bold text-text-primary">Order Details</h2>
                                <p className="text-sm text-text-tertiary">#{selectedOrder.order_number}</p>
                            </div>
                            <button onClick={() => setSelectedOrder(null)} className="text-text-tertiary hover:text-text-primary text-xl">x</button>
                        </div>

                        <div className="p-6 space-y-6">
                            <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-3">
                                <div className="card p-3">
                                    <div className="flex items-center gap-2 text-text-tertiary text-xs"><CalendarDays className="h-4 w-4" />Placed</div>
                                    <p className="font-semibold mt-1">{formatDate(selectedOrder.created_at)}</p>
                                </div>
                                <div className="card p-3">
                                    <div className="flex items-center gap-2 text-text-tertiary text-xs"><Clock3 className="h-4 w-4" />Updated</div>
                                    <p className="font-semibold mt-1">{formatDate(selectedOrder.updated_at)}</p>
                                </div>
                                <div className="card p-3">
                                    <div className="flex items-center gap-2 text-text-tertiary text-xs"><IndianRupee className="h-4 w-4" />Amount</div>
                                    <p className="font-semibold mt-1">{formatCurrency(selectedOrder.total_amount)}</p>
                                </div>
                                <div className="card p-3">
                                    <div className="flex items-center gap-2 text-text-tertiary text-xs"><CreditCard className="h-4 w-4" />Payment</div>
                                    <p className="font-semibold mt-1 capitalize">{selectedOrder.payment_status}</p>
                                </div>
                            </div>

                            {(selectedOrder.expected_delivery_date || selectedOrder.delivered_at) && (
                                <div className="card p-4">
                                    <div className="flex items-center gap-2 text-sm font-semibold text-text-primary mb-1">
                                        <Truck className="h-4 w-4 text-theme-primary" />
                                        Delivery Timeline
                                    </div>
                                    <p className="text-sm text-text-secondary">
                                        {selectedOrder.delivered_at
                                            ? `Delivered on ${formatDate(selectedOrder.delivered_at)}`
                                            : `Expected by ${formatDate(selectedOrder.expected_delivery_date)}`}
                                    </p>
                                </div>
                            )}

                            <div>
                                <h3 className="text-lg font-semibold mb-3">Items</h3>
                                <div className="space-y-3">
                                    {selectedOrder.items.map((item) => (
                                        <div key={item.id} className="card p-3 flex items-center justify-between">
                                            <div>
                                                <p className="font-medium">{item.product_name}</p>
                                                <p className="text-xs text-text-tertiary">Qty {item.quantity} · Unit {formatCurrency(item.unit_price)}</p>
                                            </div>
                                            <p className="font-semibold">{formatCurrency(item.total)}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="card p-4">
                                <h3 className="font-semibold mb-2">Shipping Address</h3>
                                <p className="text-sm text-text-secondary leading-relaxed">
                                    {selectedOrder.shipping_address.address}, {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
