import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { api } from '../lib/api'
import { useLiveOrders } from '../hooks/useLiveOrders'
import { Wifi, WifiOff, Bell } from 'lucide-react'

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

const STATUS_COLORS: Record<string, string> = {
    pending: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-300 border-yellow-500/20',
    confirmed: 'bg-blue-500/10 text-blue-700 dark:text-blue-300 border-blue-500/20',
    processing: 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20',
    shipped: 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/20',
    delivered: 'bg-green-500/10 text-green-700 dark:text-green-300 border-green-500/20',
    cancelled: 'bg-red-500/10 text-red-700 dark:text-red-300 border-red-500/20'
}

const STATUS_OPTIONS = [
    'pending',
    'confirmed',
    'processing',
    'shipped',
    'delivered',
    'cancelled'
]

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

    // For admins, always prefer the store_id assigned to their account.
    // Fallback to localStorage only for super_admin or edge cases.
    const storeId = user?.store_id || localStorage.getItem('store_id')

    // Check admin access
    useEffect(() => {
        if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) {
            navigate('/login')
        }
    }, [user, navigate])

    // Fetch stats
    useEffect(() => {
        if (!storeId) return
        fetchStats()
    }, [storeId])

    // Fetch orders
    useEffect(() => {
        if (!storeId) return
        fetchOrders()
    }, [storeId, page, selectedStatus, searchQuery])

    const fetchStats = async () => {
        if (!storeId) return
        try {
            const response = await api.get(
                '/orders/admin/stats',
                {
                    params: { store_id: storeId }
                }
            )
            if (response.data.success) {
                setStats(response.data.data)
            }
        } catch (error) {
            console.error('Failed to fetch stats:', error)
        }
    }

    const fetchOrders = async () => {
        if (!storeId) return
        setLoading(true)
        try {
            const params: any = {
                store_id: storeId,
                page,
                per_page: 20
            }
            if (selectedStatus) params.status_filter = selectedStatus
            if (searchQuery) params.search = searchQuery

            const response = await api.get(
                '/orders/admin',
                {
                    params
                }
            )

            if (response.data.success) {
                setOrders(response.data.data)
                setTotalPages(response.data.meta.total_pages)
            }
        } catch (error) {
            console.error('Failed to fetch orders:', error)
        } finally {
            setLoading(false)
        }
    }

    const updateOrderStatus = async (orderId: string, newStatus: string) => {
        setUpdatingStatus(true)
        try {
            const response = await api.put(
                `/orders/admin/${orderId}/status`,
                null,
                {
                    params: { order_status: newStatus }
                }
            )

            if (response.data.success) {
                // Refresh orders
                await fetchOrders()
                await fetchStats()
                setSelectedOrder(null)
                alert('Order status updated successfully!')
            }
        } catch (error) {
            console.error('Failed to update status:', error)
            alert('Failed to update order status')
        } finally {
            setUpdatingStatus(false)
        }
    }

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('en-IN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    if (!user || (user.role !== 'admin' && user.role !== 'super_admin')) {
        return null
    }

    return (
        <div className="min-h-screen bg-bg-secondary py-8">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8 flex items-start justify-between gap-4">
                    <div>
                        <h1 className="text-3xl font-bold text-text-primary">Order Management</h1>
                        <p className="mt-2 text-text-secondary">Manage all customer orders like Flipkart/Amazon</p>
                    </div>
                    {/* Live indicator */}
                    <div className="flex items-center gap-2">
                        {newCount > 0 && (
                            <button
                                onClick={() => { resetNewCount(); fetchOrders() }}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-orange-500 text-white text-sm font-semibold animate-pulse"
                                title="New orders received — click to refresh"
                            >
                                <Bell className="h-4 w-4" />
                                {newCount} new
                            </button>
                        )}
                        <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                            connected ? 'bg-green-500/10 text-green-600' : 'bg-bg-tertiary text-text-tertiary'
                        }`}>
                            {connected
                                ? <><Wifi className="h-3.5 w-3.5" />Live</>
                                : <><WifiOff className="h-3.5 w-3.5" />Offline</>}
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                {stats && (
                    <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                        <div className="card">
                            <h3 className="text-sm font-medium text-text-tertiary">Today's Orders</h3>
                            <p className="mt-2 text-3xl font-bold text-text-primary">{stats.today_orders}</p>
                        </div>
                        <div className="card">
                            <h3 className="text-sm font-medium text-text-tertiary">Total Revenue</h3>
                            <p className="mt-2 text-3xl font-bold text-text-primary">
                                {formatCurrency(stats.total_revenue)}
                            </p>
                        </div>
                        <div className="card">
                            <h3 className="text-sm font-medium text-text-tertiary">Pending Orders</h3>
                            <p className="mt-2 text-3xl font-bold text-text-primary">
                                {stats.status_counts['pending'] || 0}
                            </p>
                        </div>
                        <div className="card">
                            <h3 className="text-sm font-medium text-text-tertiary">Delivered</h3>
                            <p className="mt-2 text-3xl font-bold text-text-primary">
                                {stats.status_counts['delivered'] || 0}
                            </p>
                        </div>
                    </div>
                )}

                {/* Filters */}
                <div className="card mb-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-text-primary mb-2">
                                Filter by Status
                            </label>
                            <select
                                value={selectedStatus}
                                onChange={(e) => {
                                    setSelectedStatus(e.target.value)
                                    setPage(1)
                                }}
                                className="input"
                                aria-label="Filter orders by status"
                            >
                                <option value="">All Orders</option>
                                {STATUS_OPTIONS.map(status => (
                                    <option key={status} value={status}>
                                        {status.charAt(0).toUpperCase() + status.slice(1)}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div className="md:col-span-2">
                            <label className="block text-sm font-medium text-text-primary mb-2">
                                Search Orders
                            </label>
                            <input
                                type="text"
                                value={searchQuery}
                                onChange={(e) => {
                                    setSearchQuery(e.target.value)
                                    setPage(1)
                                }}
                                placeholder="Search by order number, customer name, email, or phone"
                                className="input"
                            />
                        </div>
                    </div>
                </div>

                {/* Orders Table */}
                <div className="bg-bg-primary rounded-lg shadow overflow-hidden border border-border-color">
                    {loading ? (
                        <div className="p-8 text-center">
                            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary mx-auto"></div>
                            <p className="mt-4 text-text-secondary">Loading orders...</p>
                        </div>
                    ) : orders.length === 0 ? (
                        <div className="p-8 text-center text-text-tertiary">
                            No orders found
                        </div>
                    ) : (
                        <>
                            <div className="overflow-x-auto">
                                <table className="table min-w-full">
                                    <thead>
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Order Details
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Customer
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Status
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Amount
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Date
                                            </th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-text-tertiary uppercase tracking-wider">
                                                Actions
                                            </th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-bg-primary">
                                        {orders.map((order) => (
                                            <tr key={order.id} className="hover:bg-bg-tertiary">
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div>
                                                        <div className="text-sm font-medium text-text-primary">
                                                            {order.order_number}
                                                        </div>
                                                        <div className="text-sm text-text-tertiary">
                                                            {order.items_count} item(s)
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4">
                                                    <div>
                                                        <div className="text-sm font-medium text-text-primary">
                                                            {order.customer_name}
                                                        </div>
                                                        <div className="text-sm text-text-secondary">
                                                            {order.customer_email}
                                                        </div>
                                                        <div className="text-sm text-text-secondary">
                                                            {order.customer_phone}
                                                        </div>
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <span className={`badge ${STATUS_COLORS[order.order_status] || 'bg-bg-tertiary/50 text-text-secondary'}`}>
                                                        {order.order_status}
                                                    </span>
                                                    <div className="text-xs text-text-tertiary mt-1">
                                                        Payment: {order.payment_status}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap">
                                                    <div className="text-sm font-medium text-text-primary">
                                                        {formatCurrency(order.total_amount)}
                                                    </div>
                                                    <div className="text-xs text-text-tertiary">
                                                        {order.payment_method}
                                                    </div>
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-text-secondary">
                                                    {formatDate(order.created_at)}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                    <button
                                                        onClick={() => setSelectedOrder(order)}
                                                        className="text-theme-primary hover:text-theme-primary-hover font-medium"
                                                    >
                                                        Manage
                                                    </button>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="px-6 py-4 border-t border-border-color flex items-center justify-between bg-bg-primary">
                                    <button
                                        onClick={() => setPage(p => Math.max(1, p - 1))}
                                        disabled={page === 1}
                                        className="px-4 py-2 border border-border-color rounded-md text-sm font-medium text-text-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Previous
                                    </button>
                                    <span className="text-sm text-text-primary">
                                        Page {page} of {totalPages}
                                    </span>
                                    <button
                                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                        disabled={page === totalPages}
                                        className="px-4 py-2 border border-border-color rounded-md text-sm font-medium text-text-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed"
                                    >
                                        Next
                                    </button>
                                </div>
                            )}
                        </>
                    )}
                </div>
            </div>

            {/* Order Details Modal */}
            {selectedOrder && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-bg-primary rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-border-color">
                        <div className="p-6 border-b border-border-color">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h2 className="text-2xl font-bold text-text-primary">
                                        Order {selectedOrder.order_number}
                                    </h2>
                                    <p className="text-sm text-text-tertiary mt-1">
                                        Placed on {formatDate(selectedOrder.created_at)}
                                    </p>
                                </div>
                                <button
                                    onClick={() => setSelectedOrder(null)}
                                    className="text-text-tertiary hover:text-text-secondary"
                                    aria-label="Close order details"
                                >
                                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                    </svg>
                                </button>
                            </div>
                        </div>

                        <div className="p-6 space-y-6">
                            {/* Customer Info */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Customer Information</h3>
                                <div className="bg-bg-tertiary rounded-lg p-4 space-y-2">
                                    <p className="text-sm text-text-primary"><span className="font-medium">Name:</span> {selectedOrder.customer_name}</p>
                                    <p className="text-sm text-text-primary"><span className="font-medium">Email:</span> {selectedOrder.customer_email}</p>
                                    <p className="text-sm text-text-primary"><span className="font-medium">Phone:</span> {selectedOrder.customer_phone}</p>
                                </div>
                            </div>

                            {/* Order Items */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Order Items</h3>
                                <div className="space-y-3">
                                    {selectedOrder.items.map((item) => (
                                        <div key={item.id} className="flex justify-between items-center bg-bg-tertiary rounded-lg p-4">
                                            <div>
                                                <p className="font-medium text-text-primary">{item.product_name}</p>
                                                <p className="text-sm text-text-secondary">Quantity: {item.quantity}</p>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-medium text-text-primary">{formatCurrency(item.total)}</p>
                                                <p className="text-sm text-text-tertiary">{formatCurrency(item.unit_price)} each</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Order Summary */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Order Summary</h3>
                                <div className="bg-bg-tertiary rounded-lg p-4 space-y-2">
                                    <div className="flex justify-between text-sm text-text-primary">
                                        <span>Subtotal:</span>
                                        <span>{formatCurrency(selectedOrder.subtotal)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm text-text-primary">
                                        <span>Tax (GST):</span>
                                        <span>{formatCurrency(selectedOrder.tax_amount)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm text-text-primary">
                                        <span>Delivery Charge:</span>
                                        <span>{formatCurrency(selectedOrder.delivery_charge)}</span>
                                    </div>
                                    <div className="flex justify-between text-lg font-bold border-t border-border-color pt-2 mt-2 text-text-primary">
                                        <span>Total Amount:</span>
                                        <span className="text-green-600">{formatCurrency(selectedOrder.total_amount)}</span>
                                    </div>
                                </div>
                            </div>

                            {/* Update Status */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Update Order Status</h3>
                                <div className="flex items-center space-x-4">
                                    <span className={`px-3 py-1 rounded-full text-sm font-semibold ${STATUS_COLORS[selectedOrder.order_status]}`}>
                                        Current: {selectedOrder.order_status}
                                    </span>
                                    <select
                                        onChange={(e) => {
                                            if (e.target.value && confirm(`Update order status to "${e.target.value}"?`)) {
                                                updateOrderStatus(selectedOrder.id, e.target.value)
                                            }
                                        }}
                                        disabled={updatingStatus}
                                        className="flex-1 px-3 py-2 border border-border-color rounded-md focus:outline-none focus:ring-2 focus:ring-theme-primary bg-bg-primary text-text-primary"
                                        aria-label="Change order status"
                                    >
                                        <option value="">Change status...</option>
                                        {STATUS_OPTIONS.filter(s => s !== selectedOrder.order_status).map(status => (
                                            <option key={status} value={status}>
                                                {status.charAt(0).toUpperCase() + status.slice(1)}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                                {updatingStatus && (
                                    <p className="text-sm text-text-tertiary mt-2">Updating status...</p>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
