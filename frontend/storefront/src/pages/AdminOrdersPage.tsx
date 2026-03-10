import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { api } from '../lib/api'
import { useLiveOrders } from '../hooks/useLiveOrders'
import {
    Wifi, WifiOff, Bell, SlidersHorizontal,
    ShoppingBag, TrendingUp, Clock, CheckCircle2, IndianRupee,
    Package, User,
} from 'lucide-react'
import StatusBadge from '@/components/ui/StatusBadge'
import EmptyState from '@/components/ui/EmptyState'
import PageHeader from '@/components/ui/PageHeader'
import FilterBar from '@/components/ui/FilterBar'
import PaginationControls from '@/components/ui/PaginationControls'
import DataGrid from '@/components/ui/DataGrid'
import RowActions, { RowActionButton } from '@/components/ui/RowActions'
import Modal, { ModalBody, ModalHeader } from '@/components/ui/Modal'

interface OrderItem {
    id: string
    product_name: string
    quantity: number
    unit_price: number
    total: number
}

interface Order {
    id: string
    order_number: string
    customer_name: string
    customer_email: string
    customer_phone: string
    order_status: string
    payment_status: string
    payment_method: string
    subtotal: number
    tax_amount: number
    delivery_charge: number
    total_amount: number
    items_count: number
    created_at: string
    updated_at: string
    items: OrderItem[]
}

interface OrderStats {
    status_counts: Record<string, number>
    total_revenue: number
    today_orders: number
}

const STATUS_OPTIONS = ['pending', 'confirmed', 'processing', 'shipped', 'delivered', 'cancelled']

const fmt = (amount: number) =>
    new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(amount)

const fmtDate = (d: string) =>
    new Date(d).toLocaleString('en-IN', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })

export default function AdminOrdersPage() {
    const navigate = useNavigate()
    const { user } = useAuthStore()
    const [orders, setOrders] = useState<Order[]>([])
    const [stats, setStats] = useState<OrderStats | null>(null)
    const [loading, setLoading] = useState(true)
    const [selectedStatus, setSelectedStatus] = useState<string>('')
    const [searchQuery, setSearchQuery] = useState('')
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)
    const [updatingStatus, setUpdatingStatus] = useState(false)

    const { connected, newCount, resetNewCount } = useLiveOrders()
    const storeId = user?.store_id || localStorage.getItem('store_id')

    useEffect(() => {
        if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) navigate('/login')
    }, [user, navigate])

    useEffect(() => { if (storeId) fetchStats() }, [storeId])
    useEffect(() => { if (storeId) fetchOrders() }, [storeId, page, selectedStatus, searchQuery])

    const fetchStats = async () => {
        if (!storeId) return
        try {
            const r = await api.get('/orders/admin/stats', { params: { store_id: storeId } })
            if (r.data.success) setStats(r.data.data)
        } catch { /* noop */ }
    }

    const fetchOrders = async () => {
        if (!storeId) return
        setLoading(true)
        try {
            const params: any = { store_id: storeId, page, per_page: 20 }
            if (selectedStatus) params.status_filter = selectedStatus
            if (searchQuery) params.search = searchQuery
            const r = await api.get('/orders/admin', { params })
            if (r.data.success) {
                setOrders(r.data.data)
                setTotalPages(r.data.meta.total_pages)
            }
        } catch { /* noop */ } finally { setLoading(false) }
    }

    const updateOrderStatus = async (orderId: string, newStatus: string) => {
        setUpdatingStatus(true)
        try {
            const r = await api.put(`/orders/admin/${orderId}/status`, null, { params: { order_status: newStatus } })
            if (r.data.success) {
                await fetchOrders()
                await fetchStats()
                setSelectedOrder(null)
            }
        } catch (e) {
            console.error('Failed to update status:', e)
        } finally { setUpdatingStatus(false) }
    }

    if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) return null

    const statCards = [
        { label: "Today's Orders", value: stats?.today_orders ?? '—', Icon: ShoppingBag, color: 'text-violet-600', bg: 'bg-violet-50 dark:bg-violet-950/40' },
        { label: 'Total Revenue', value: stats ? fmt(stats.total_revenue) : '—', Icon: IndianRupee, color: 'text-emerald-600', bg: 'bg-emerald-50 dark:bg-emerald-950/40' },
        { label: 'Pending', value: stats?.status_counts['pending'] ?? 0, Icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50 dark:bg-amber-950/40' },
        { label: 'Delivered', value: stats?.status_counts['delivered'] ?? 0, Icon: CheckCircle2, color: 'text-teal-600', bg: 'bg-teal-50 dark:bg-teal-950/40' },
    ]

    return (
        <div className="min-h-screen bg-bg-secondary">
            <div className="container-wide py-8 animate-fade-in">

                {/* ── Page Header ──────────────────────────────────── */}
                <PageHeader
                    title="Order Management"
                    subtitle="Monitor and manage all customer orders in real time"
                    actions={
                        <>
                            {newCount > 0 && (
                                <button
                                    onClick={() => { resetNewCount(); fetchOrders() }}
                                    className="flex items-center gap-1.5 rounded-full bg-orange-500 px-3 py-1.5 text-sm font-semibold text-white animate-pulse shadow-glow-sm"
                                >
                                    <Bell className="h-4 w-4" />
                                    {newCount} new order{newCount > 1 ? 's' : ''}
                                </button>
                            )}
                            <div className={`flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-semibold ${connected
                                ? 'bg-emerald-50 border-emerald-200 text-emerald-700 dark:bg-emerald-950/50 dark:border-emerald-900/50 dark:text-emerald-400'
                                : 'bg-bg-tertiary border-border-color text-text-tertiary'
                                }`}>
                                {connected ? <Wifi className="h-3.5 w-3.5" /> : <WifiOff className="h-3.5 w-3.5" />}
                                {connected ? 'Live' : 'Offline'}
                            </div>
                        </>
                    }
                />

                {/* ── Stats ────────────────────────────────────────── */}
                {stats && (
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
                        {statCards.map(({ label, value, Icon, color, bg }) => (
                            <div key={label} className="card flex items-center gap-4 p-5">
                                <div className={`h-11 w-11 rounded-[var(--radius-lg)] flex-shrink-0 flex items-center justify-center ${bg}`}>
                                    <Icon className={`h-5 w-5 ${color}`} />
                                </div>
                                <div>
                                    <div className={`text-2xl font-black tabular-nums ${color}`}>{value}</div>
                                    <div className="text-sm text-text-tertiary mt-0.5">{label}</div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}

                {/* ── Filters ──────────────────────────────────────── */}
                <FilterBar
                    className="mb-5"
                    searchValue={searchQuery}
                    onSearchChange={(value) => { setSearchQuery(value); setPage(1) }}
                    searchPlaceholder="Search order number, customer name, email…"
                    rightSlot={
                        <>
                            <SlidersHorizontal className="h-4 w-4 text-text-tertiary flex-shrink-0" />
                            <select
                                value={selectedStatus}
                                onChange={e => { setSelectedStatus(e.target.value); setPage(1) }}
                                className="input w-40"
                                aria-label="Filter by status"
                            >
                                <option value="">All statuses</option>
                                {STATUS_OPTIONS.map(s => (
                                    <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                                ))}
                            </select>
                        </>
                    }
                />

                {/* ── Table ────────────────────────────────────────── */}
                <DataGrid
                    loading={loading}
                    isEmpty={orders.length === 0}
                    loadingState={
                        <div className="flex flex-col items-center justify-center py-20 gap-3">
                            <div className="h-8 w-8 rounded-full border-2 border-theme-primary border-t-transparent animate-spin" />
                            <p className="text-sm text-text-tertiary">Loading orders…</p>
                        </div>
                    }
                    emptyState={
                        <EmptyState
                            icon={<Package className="h-12 w-12" />}
                            title="No orders found"
                            description="Try adjusting your filters or search query."
                        />
                    }
                    footer={
                        <PaginationControls
                            page={page}
                            totalPages={totalPages}
                            onPrev={() => setPage(p => Math.max(1, p - 1))}
                            onNext={() => setPage(p => Math.min(totalPages, p + 1))}
                        />
                    }
                >
                    <table className="table">
                        <thead>
                            <tr>
                                <th>Order</th>
                                <th>Customer</th>
                                <th>Status</th>
                                <th className="text-right">Amount</th>
                                <th>Date</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody>
                            {orders.map(order => (
                                <tr key={order.id}>
                                    <td>
                                        <div className="font-semibold text-text-primary">{order.order_number}</div>
                                        <div className="text-xs text-text-tertiary mt-0.5">{order.items_count} item{order.items_count !== 1 ? 's' : ''}</div>
                                    </td>
                                    <td>
                                        <div className="font-medium text-text-primary">{order.customer_name}</div>
                                        <div className="text-xs text-text-tertiary mt-0.5">{order.customer_email}</div>
                                        {order.customer_phone && (
                                            <div className="text-xs text-text-tertiary">{order.customer_phone}</div>
                                        )}
                                    </td>
                                    <td>
                                        <StatusBadge status={order.order_status} />
                                        <div className="mt-1.5">
                                            <StatusBadge status={order.payment_status} className="text-[10px]" />
                                        </div>
                                    </td>
                                    <td className="text-right">
                                        <div className="font-bold text-text-primary tabular-nums">{fmt(order.total_amount)}</div>
                                        <div className="text-xs text-text-tertiary mt-0.5">{order.payment_method}</div>
                                    </td>
                                    <td className="text-xs text-text-tertiary whitespace-nowrap">{fmtDate(order.created_at)}</td>
                                    <td>
                                        <RowActions align="start">
                                            <RowActionButton tone="primary" onClick={() => setSelectedOrder(order)}>
                                                Manage →
                                            </RowActionButton>
                                        </RowActions>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </DataGrid>
            </div>

            {/* ── Order Detail Modal ────────────────────────────── */}
            {selectedOrder && (
                <Modal open={!!selectedOrder} onClose={() => setSelectedOrder(null)} maxWidthClassName="max-w-2xl">
                    <ModalHeader
                        title={`Order ${selectedOrder.order_number}`}
                        subtitle={`Placed ${fmtDate(selectedOrder.created_at)}`}
                        onClose={() => setSelectedOrder(null)}
                    />

                    <ModalBody className="space-y-6">
                        {/* Customer */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <User className="h-4 w-4 text-text-tertiary" />
                                <h3 className="text-sm font-semibold text-text-primary">Customer</h3>
                            </div>
                            <div className="card-inset space-y-1.5">
                                <p className="text-sm text-text-primary font-medium">{selectedOrder.customer_name}</p>
                                <p className="text-sm text-text-secondary">{selectedOrder.customer_email}</p>
                                {selectedOrder.customer_phone && <p className="text-sm text-text-secondary">{selectedOrder.customer_phone}</p>}
                            </div>
                        </section>

                        {/* Items */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <Package className="h-4 w-4 text-text-tertiary" />
                                <h3 className="text-sm font-semibold text-text-primary">Items</h3>
                            </div>
                            <div className="space-y-2">
                                {selectedOrder.items.map(item => (
                                    <div key={item.id} className="card-inset flex items-center justify-between gap-3">
                                        <div>
                                            <p className="text-sm font-medium text-text-primary">{item.product_name}</p>
                                            <p className="text-xs text-text-tertiary">Qty: {item.quantity} × {fmt(item.unit_price)}</p>
                                        </div>
                                        <p className="text-sm font-bold text-text-primary tabular-nums">{fmt(item.total)}</p>
                                    </div>
                                ))}
                            </div>
                        </section>

                        {/* Summary */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <IndianRupee className="h-4 w-4 text-text-tertiary" />
                                <h3 className="text-sm font-semibold text-text-primary">Summary</h3>
                            </div>
                            <div className="card-inset space-y-2 text-sm">
                                {[
                                    { label: 'Subtotal', value: fmt(selectedOrder.subtotal) },
                                    { label: 'Tax (GST)', value: fmt(selectedOrder.tax_amount) },
                                    { label: 'Delivery', value: fmt(selectedOrder.delivery_charge) },
                                ].map(row => (
                                    <div key={row.label} className="flex justify-between text-text-secondary">
                                        <span>{row.label}</span>
                                        <span className="tabular-nums">{row.value}</span>
                                    </div>
                                ))}
                                <div className="flex justify-between font-bold text-text-primary border-t border-border-color pt-2 mt-1">
                                    <span>Total</span>
                                    <span className="text-emerald-600 tabular-nums">{fmt(selectedOrder.total_amount)}</span>
                                </div>
                            </div>
                        </section>

                        {/* Update Status */}
                        <section>
                            <div className="flex items-center gap-2 mb-3">
                                <TrendingUp className="h-4 w-4 text-text-tertiary" />
                                <h3 className="text-sm font-semibold text-text-primary">Update Status</h3>
                            </div>
                            <div className="flex items-center gap-3">
                                <StatusBadge status={selectedOrder.order_status} />
                                <select
                                    onChange={e => {
                                        if (e.target.value && confirm(`Update status to "${e.target.value}"?`)) {
                                            updateOrderStatus(selectedOrder.id, e.target.value)
                                        }
                                    }}
                                    disabled={updatingStatus}
                                    className="input flex-1"
                                    aria-label="Change status"
                                >
                                    <option value="">Change status…</option>
                                    {STATUS_OPTIONS.filter(s => s !== selectedOrder.order_status).map(s => (
                                        <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                                    ))}
                                </select>
                                {updatingStatus && <div className="h-4 w-4 rounded-full border-2 border-theme-primary border-t-transparent animate-spin flex-shrink-0" />}
                            </div>
                        </section>
                    </ModalBody>
                </Modal>
            )}
        </div>
    )
}

