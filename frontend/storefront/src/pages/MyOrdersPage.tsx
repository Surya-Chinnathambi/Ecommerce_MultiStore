import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { api } from '../lib/api'

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
    items: OrderItem[]
    shipping_address: {
        address: string
        city: string
        state: string
        postal_code: string
    }
}

const STATUS_COLORS: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 border-yellow-300',
    confirmed: 'bg-blue-100 text-blue-800 border-blue-300',
    processing: 'bg-purple-100 text-purple-800 border-purple-300',
    shipped: 'bg-indigo-100 text-indigo-800 border-indigo-300',
    delivered: 'bg-green-100 text-green-800 border-green-300',
    cancelled: 'bg-red-100 text-red-800 border-red-300'
}

const STATUS_ICONS: Record<string, string> = {
    pending: '⏱️',
    confirmed: '✅',
    processing: '📦',
    shipped: '🚚',
    delivered: '🎉',
    cancelled: '❌'
}

export default function MyOrdersPage() {
    const navigate = useNavigate()
    const { user } = useAuthStore()
    const [orders, setOrders] = useState<Order[]>([])
    const [loading, setLoading] = useState(true)
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [selectedOrder, setSelectedOrder] = useState<Order | null>(null)

    useEffect(() => {
        if (!user) {
            navigate('/login')
            return
        }
        fetchOrders()
    }, [user, navigate, page])

    const fetchOrders = async () => {
        setLoading(true)
        try {
            const response = await api.get(
                '/orders/customer',
                {
                    params: { page, per_page: 10 }
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

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR'
        }).format(amount)
    }

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-IN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        })
    }

    const getStatusMessage = (status: string) => {
        const messages: Record<string, string> = {
            pending: 'Your order has been placed and is awaiting confirmation',
            confirmed: 'Your order has been confirmed and will be processed soon',
            processing: 'Your order is being prepared for shipment',
            shipped: 'Your order is on the way!',
            delivered: 'Your order has been delivered successfully',
            cancelled: 'This order has been cancelled'
        }
        return messages[status] || status
    }

    if (!user) {
        return null
    }

    return (
        <div className="min-h-screen bg-bg-secondary py-8">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
                {/* Header */}
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-text-primary">My Orders</h1>
                    <p className="mt-2 text-text-secondary">Track and manage your orders</p>
                </div>

                {loading ? (
                    <div className="bg-bg-primary rounded-lg shadow p-12 text-center border border-border-color">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary mx-auto"></div>
                        <p className="mt-4 text-text-secondary">Loading your orders...</p>
                    </div>
                ) : orders.length === 0 ? (
                    <div className="bg-bg-primary rounded-lg shadow p-12 text-center border border-border-color">
                        <div className="text-6xl mb-4">📦</div>
                        <h2 className="text-2xl font-semibold text-text-primary mb-2">No orders yet</h2>
                        <p className="text-text-secondary mb-6">Start shopping to see your orders here</p>
                        <button
                            onClick={() => navigate('/products')}
                            className="bg-theme-primary text-white px-6 py-3 rounded-lg hover:bg-theme-primary-hover transition-colors"
                        >
                            Browse Products
                        </button>
                    </div>
                ) : (
                    <>
                        {/* Orders List */}
                        <div className="space-y-6">
                            {orders.map((order) => (
                                <div key={order.id} className="bg-bg-primary rounded-lg shadow overflow-hidden border border-border-color">
                                    {/* Order Header */}
                                    <div className="bg-bg-tertiary px-6 py-4 border-b border-border-color">
                                        <div className="flex flex-wrap items-center justify-between gap-4">
                                            <div>
                                                <h3 className="text-lg font-semibold text-text-primary">
                                                    Order #{order.order_number}
                                                </h3>
                                                <p className="text-sm text-text-tertiary mt-1">
                                                    Placed on {formatDate(order.created_at)}
                                                </p>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-lg font-bold text-text-primary">
                                                    {formatCurrency(order.total_amount)}
                                                </div>
                                                <div className="text-sm text-text-tertiary">
                                                    {order.items.length} item(s)
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Order Status */}
                                    <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-white">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center space-x-3">
                                                <span className="text-3xl">{STATUS_ICONS[order.order_status]}</span>
                                                <div>
                                                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-semibold border ${STATUS_COLORS[order.order_status]}`}>
                                                        {order.order_status.toUpperCase()}
                                                    </div>
                                                    <p className="text-sm text-text-secondary mt-1">
                                                        {getStatusMessage(order.order_status)}
                                                    </p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => setSelectedOrder(order)}
                                                className="bg-theme-primary text-white px-4 py-2 rounded-lg hover:bg-theme-primary-hover transition-colors text-sm font-medium"
                                            >
                                                View Details
                                            </button>
                                        </div>
                                    </div>

                                    {/* Order Items Preview */}
                                    <div className="px-6 py-4">
                                        <div className="space-y-3">
                                            {order.items.slice(0, 2).map((item) => (
                                                <div key={item.id} className="flex items-center justify-between">
                                                    <div className="flex items-center space-x-4">
                                                        {item.product?.image_url ? (
                                                            <img
                                                                src={item.product.image_url}
                                                                alt={item.product_name}
                                                                className="w-16 h-16 object-cover rounded"
                                                            />
                                                        ) : (
                                                            <div className="w-16 h-16 bg-bg-tertiary rounded flex items-center justify-center">
                                                                <span className="text-text-tertiary text-2xl">📦</span>
                                                            </div>
                                                        )}
                                                        <div>
                                                            <p className="font-medium text-text-primary">{item.product_name}</p>
                                                            <p className="text-sm text-text-tertiary">Qty: {item.quantity}</p>
                                                        </div>
                                                    </div>
                                                    <div className="text-right">
                                                        <p className="font-semibold text-text-primary">{formatCurrency(item.total)}</p>
                                                    </div>
                                                </div>
                                            ))}
                                            {order.items.length > 2 && (
                                                <p className="text-sm text-text-tertiary text-center py-2">
                                                    + {order.items.length - 2} more item(s)
                                                </p>
                                            )}
                                        </div>
                                    </div>

                                    {/* Order Actions */}
                                    <div className="px-6 py-4 bg-bg-tertiary border-t border-border-color">
                                        <div className="flex items-center justify-between">
                                            <div className="text-sm text-text-secondary">
                                                Payment: <span className="font-medium">{order.payment_method}</span>
                                                {' • '}
                                                <span className={order.payment_status === 'completed' ? 'text-green-600 font-medium' : 'text-yellow-600 font-medium'}>
                                                    {order.payment_status}
                                                </span>
                                            </div>
                                            <button
                                                onClick={() => navigate(`/track-order?order=${order.order_number}`)}
                                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                                            >
                                                Track Order →
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>

                        {/* Pagination */}
                        {totalPages > 1 && (
                            <div className="mt-8 flex items-center justify-center space-x-4">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="px-4 py-2 border border-border-color rounded-lg text-sm font-medium text-text-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    ← Previous
                                </button>
                                <span className="text-sm text-text-primary">
                                    Page {page} of {totalPages}
                                </span>
                                <button
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                    className="px-4 py-2 border border-border-color rounded-lg text-sm font-medium text-text-primary hover:bg-bg-tertiary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    Next →
                                </button>
                            </div>
                        )}
                    </>
                )}
            </div>

            {/* Order Details Modal */}
            {selectedOrder && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
                    <div className="bg-bg-primary rounded-lg max-w-3xl w-full max-h-[90vh] overflow-y-auto border border-border-color">
                        <div className="sticky top-0 bg-bg-primary border-b border-border-color p-6 z-10">
                            <div className="flex justify-between items-start">
                                <div>
                                    <h2 className="text-2xl font-bold text-text-primary">
                                        Order Details
                                    </h2>
                                    <p className="text-sm text-text-tertiary mt-1">
                                        #{selectedOrder.order_number}
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
                            {/* Status Timeline */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-4">Order Status</h3>
                                <div className={`p-4 rounded-lg border-2 ${STATUS_COLORS[selectedOrder.order_status]}`}>
                                    <div className="flex items-center space-x-3 mb-2">
                                        <span className="text-3xl">{STATUS_ICONS[selectedOrder.order_status]}</span>
                                        <div>
                                            <div className="font-bold text-lg">{selectedOrder.order_status.toUpperCase()}</div>
                                            <div className="text-sm">{getStatusMessage(selectedOrder.order_status)}</div>
                                        </div>
                                    </div>
                                    <div className="text-sm mt-2">
                                        Order placed on {formatDate(selectedOrder.created_at)}
                                    </div>
                                </div>
                            </div>

                            {/* All Order Items */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-4">Items in Your Order</h3>
                                <div className="space-y-4">
                                    {selectedOrder.items.map((item) => (
                                        <div key={item.id} className="flex items-start space-x-4 border border-border-color rounded-lg p-4">
                                            {item.product?.image_url ? (
                                                <img
                                                    src={item.product.image_url}
                                                    alt={item.product_name}
                                                    className="w-20 h-20 object-cover rounded"
                                                />
                                            ) : (
                                                <div className="w-20 h-20 bg-bg-tertiary rounded flex items-center justify-center">
                                                    <span className="text-text-tertiary text-3xl">📦</span>
                                                </div>
                                            )}
                                            <div className="flex-1">
                                                <h4 className="font-medium text-text-primary">{item.product_name}</h4>
                                                <div className="mt-2 space-y-1 text-sm text-text-secondary">
                                                    <p>Quantity: {item.quantity}</p>
                                                    <p>Price per item: {formatCurrency(item.unit_price)}</p>
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                <p className="font-bold text-lg text-text-primary">{formatCurrency(item.total)}</p>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            {/* Delivery Address */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Delivery Address</h3>
                                <div className="bg-bg-tertiary rounded-lg p-4">
                                    <p className="text-sm text-text-primary">{selectedOrder.shipping_address.address}</p>
                                    <p className="text-sm text-text-primary mt-1">
                                        {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.state} {selectedOrder.shipping_address.postal_code}
                                    </p>
                                </div>
                            </div>

                            {/* Price Breakdown */}
                            <div>
                                <h3 className="text-lg font-semibold text-text-primary mb-3">Payment Summary</h3>
                                <div className="bg-bg-tertiary rounded-lg p-4 space-y-3">
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-secondary">Subtotal:</span>
                                        <span className="font-medium">{formatCurrency(selectedOrder.subtotal)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-secondary">Tax (GST):</span>
                                        <span className="font-medium">{formatCurrency(selectedOrder.tax_amount)}</span>
                                    </div>
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-secondary">Delivery Charge:</span>
                                        <span className="font-medium">
                                            {selectedOrder.delivery_charge === 0 ? 'FREE' : formatCurrency(selectedOrder.delivery_charge)}
                                        </span>
                                    </div>
                                    <div className="border-t border-border-color pt-3 mt-3">
                                        <div className="flex justify-between">
                                            <span className="text-lg font-bold text-text-primary">Total Paid:</span>
                                            <span className="text-lg font-bold text-green-600">{formatCurrency(selectedOrder.total_amount)}</span>
                                        </div>
                                        <div className="flex justify-between text-sm mt-2">
                                            <span className="text-text-secondary">Payment Method:</span>
                                            <span className="font-medium">{selectedOrder.payment_method}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex space-x-4">
                                <button
                                    onClick={() => {
                                        setSelectedOrder(null)
                                        navigate(`/track-order?order=${selectedOrder.order_number}`)
                                    }}
                                    className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
                                >
                                    Track Order
                                </button>
                                <button
                                    onClick={() => setSelectedOrder(null)}
                                    className="flex-1 bg-gray-200 text-gray-700 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
