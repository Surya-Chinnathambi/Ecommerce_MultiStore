import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { AlertTriangle, CheckCircle, Plus, X, Package } from 'lucide-react'
import api from '@/lib/api'
import { toast } from '@/components/ui/Toaster'

interface InventoryAlert {
    id: string
    product_id: string
    product_name?: string
    alert_type: 'low_stock' | 'out_of_stock' | 'critical'
    current_quantity: number
    threshold_quantity: number
    message: string
    is_resolved: boolean
    resolved_at?: string
    created_at: string
}

interface Product {
    id: string
    name: string
    sku: string
    quantity: number
}

export default function AdminInventoryAlertsPage() {
    const queryClient = useQueryClient()
    const [filterResolved, setFilterResolved] = useState<'active' | 'resolved' | 'all'>('active')
    const [showCreateModal, setShowCreateModal] = useState(false)
    const [newAlert, setNewAlert] = useState({
        product_id: '',
        alert_type: 'low_stock' as 'low_stock' | 'out_of_stock' | 'critical',
        current_quantity: 0,
        threshold_quantity: 10,
        message: '',
    })

    // Fetch alerts
    const { data: alertsData, isLoading: alertsLoading } = useQuery({
        queryKey: ['inventory-alerts', filterResolved],
        queryFn: async () => {
            const params: any = {}
            if (filterResolved === 'active') params.is_resolved = false
            if (filterResolved === 'resolved') params.is_resolved = true

            const response = await api.get('/analytics/inventory/alerts', { params })
            return response.data.data as InventoryAlert[]
        },
    })

    // Fetch products for dropdown
    const { data: productsData } = useQuery({
        queryKey: ['products-list'],
        queryFn: async () => {
            const response = await api.get('/products/', { params: { per_page: 1000 } })
            return response.data.data.products as Product[]
        },
    })

    // Create alert mutation
    const createAlertMutation = useMutation({
        mutationFn: async (alertData: typeof newAlert) => {
            const response = await api.post('/analytics/inventory/alerts', alertData)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['inventory-alerts'] })
            setShowCreateModal(false)
            setNewAlert({
                product_id: '',
                alert_type: 'low_stock',
                current_quantity: 0,
                threshold_quantity: 10,
                message: '',
            })
            toast.success('Alert created successfully')
        },
        onError: () => {
            toast.error('Failed to create alert')
        },
    })

    // Resolve alert mutation
    const resolveAlertMutation = useMutation({
        mutationFn: async (alertId: string) => {
            const response = await api.put(`/analytics/inventory/alerts/${alertId}/resolve`)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['inventory-alerts'] })
            toast.success('Alert resolved')
        },
        onError: () => {
            toast.error('Failed to resolve alert')
        },
    })

    // Delete alert mutation
    const deleteAlertMutation = useMutation({
        mutationFn: async (alertId: string) => {
            const response = await api.delete(`/analytics/inventory/alerts/${alertId}`)
            return response.data
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['inventory-alerts'] })
            toast.success('Alert deleted')
        },
        onError: () => {
            toast.error('Failed to delete alert')
        },
    })

    const handleCreateAlert = () => {
        if (!newAlert.product_id) {
            toast.error('Please select a product')
            return
        }
        createAlertMutation.mutate(newAlert)
    }

    const getAlertColor = (type: string) => {
        switch (type) {
            case 'critical':
                return 'bg-red-100 text-red-700 border-red-300'
            case 'out_of_stock':
                return 'bg-orange-100 text-orange-700 border-orange-300'
            case 'low_stock':
                return 'bg-yellow-100 text-yellow-700 border-yellow-300'
            default:
                return 'bg-gray-100 text-gray-700 border-gray-300'
        }
    }

    const getAlertIcon = (type: string) => {
        if (type === 'critical') return <AlertTriangle className="h-6 w-6" />
        if (type === 'out_of_stock') return <X className="h-6 w-6" />
        return <Package className="h-6 w-6" />
    }

    const alerts = alertsData || []

    if (alertsLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="animate-pulse space-y-4">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-24 bg-bg-tertiary rounded-lg" />
                    ))}
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900">Inventory Alerts</h1>
                    <p className="text-gray-600 mt-2">Monitor and manage low stock alerts</p>
                </div>
                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors flex items-center gap-2"
                >
                    <Plus size={20} />
                    Create Alert
                </button>
            </div>

            {/* Filters */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                <div className="flex gap-4">
                    <select
                        value={filterResolved}
                        onChange={(e) => setFilterResolved(e.target.value as any)}
                        aria-label="Filter alerts by status"
                        className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                    >
                        <option value="active">Active Alerts</option>
                        <option value="resolved">Resolved Alerts</option>
                        <option value="all">All Alerts</option>
                    </select>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6 pt-6 border-t">
                    <div className="text-center">
                        <p className="text-2xl font-bold text-purple-600">{alerts.length}</p>
                        <p className="text-sm text-gray-600">Total Alerts</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-red-600">
                            {alerts.filter((a) => a.alert_type === 'critical' && !a.is_resolved).length}
                        </p>
                        <p className="text-sm text-gray-600">Critical</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-orange-600">
                            {alerts.filter((a) => a.alert_type === 'out_of_stock' && !a.is_resolved).length}
                        </p>
                        <p className="text-sm text-gray-600">Out of Stock</p>
                    </div>
                    <div className="text-center">
                        <p className="text-2xl font-bold text-green-600">
                            {alerts.filter((a) => a.is_resolved).length}
                        </p>
                        <p className="text-sm text-gray-600">Resolved</p>
                    </div>
                </div>
            </div>

            {/* Alerts List */}
            <div className="space-y-4">
                {alerts.length === 0 ? (
                    <div className="bg-white rounded-lg shadow-md p-12 text-center">
                        <Package className="mx-auto h-16 w-16 text-gray-300 mb-4" />
                        <p className="text-xl text-gray-600">No alerts found</p>
                        <p className="text-gray-500 mt-2">All inventory levels are healthy</p>
                    </div>
                ) : (
                    alerts.map((alert) => (
                        <div
                            key={alert.id}
                            className={`rounded-lg shadow-md p-6 border-l-4 ${getAlertColor(alert.alert_type)}`}
                        >
                            <div className="flex items-start justify-between">
                                <div className="flex items-start gap-4 flex-1">
                                    <div className="mt-1">{getAlertIcon(alert.alert_type)}</div>

                                    <div className="flex-1">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-lg font-semibold">
                                                {alert.product_name || `Product ${alert.product_id.slice(0, 8)}`}
                                            </h3>
                                            <span className="px-3 py-1 bg-white rounded-full text-sm font-medium">
                                                {alert.alert_type.replace('_', ' ').toUpperCase()}
                                            </span>
                                            {alert.is_resolved && (
                                                <span className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm font-medium flex items-center gap-1">
                                                    <CheckCircle size={14} />
                                                    Resolved
                                                </span>
                                            )}
                                        </div>

                                        <p className="text-gray-700 mb-3">{alert.message}</p>

                                        <div className="flex items-center gap-6 text-sm">
                                            <div>
                                                <span className="text-gray-600">Current Stock:</span>
                                                <span className="ml-2 font-semibold">{alert.current_quantity}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-600">Threshold:</span>
                                                <span className="ml-2 font-semibold">{alert.threshold_quantity}</span>
                                            </div>
                                            <div>
                                                <span className="text-gray-600">Created:</span>
                                                <span className="ml-2">
                                                    {new Date(alert.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                            {alert.resolved_at && (
                                                <div>
                                                    <span className="text-gray-600">Resolved:</span>
                                                    <span className="ml-2">
                                                        {new Date(alert.resolved_at).toLocaleDateString()}
                                                    </span>
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="flex gap-2 ml-4">
                                    {!alert.is_resolved && (
                                        <button
                                            onClick={() => resolveAlertMutation.mutate(alert.id)}
                                            aria-label="Resolve alert"
                                            className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                                        >
                                            <CheckCircle size={20} />
                                        </button>
                                    )}
                                    <button
                                        onClick={() => {
                                            if (window.confirm('Are you sure you want to delete this alert?')) {
                                                deleteAlertMutation.mutate(alert.id)
                                            }
                                        }}
                                        aria-label="Delete alert"
                                        className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 transition-colors"
                                    >
                                        <X size={20} />
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>

            {/* Create Alert Modal */}
            {showCreateModal && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white rounded-lg max-w-2xl w-full p-6">
                        <h2 className="text-2xl font-bold mb-4">Create Inventory Alert</h2>

                        <div className="space-y-4">
                            {/* Product Selection */}
                            <div>
                                <label className="block text-sm font-medium mb-2">Product</label>
                                <select
                                    value={newAlert.product_id}
                                    onChange={(e) => {
                                        const product = productsData?.find((p) => p.id === e.target.value)
                                        setNewAlert({
                                            ...newAlert,
                                            product_id: e.target.value,
                                            current_quantity: product?.quantity || 0,
                                        })
                                    }}
                                    aria-label="Select product"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="">Select a product</option>
                                    {productsData?.map((product) => (
                                        <option key={product.id} value={product.id}>
                                            {product.name} (SKU: {product.sku}) - Stock: {product.quantity}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Alert Type */}
                            <div>
                                <label className="block text-sm font-medium mb-2">Alert Type</label>
                                <select
                                    value={newAlert.alert_type}
                                    onChange={(e) =>
                                        setNewAlert({ ...newAlert, alert_type: e.target.value as any })
                                    }
                                    aria-label="Select alert type"
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                >
                                    <option value="low_stock">Low Stock</option>
                                    <option value="out_of_stock">Out of Stock</option>
                                    <option value="critical">Critical</option>
                                </select>
                            </div>

                            {/* Quantities */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium mb-2">Current Quantity</label>
                                    <input
                                        type="number"
                                        value={newAlert.current_quantity}
                                        onChange={(e) =>
                                            setNewAlert({ ...newAlert, current_quantity: parseInt(e.target.value) })
                                        }
                                        aria-label="Current quantity"
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium mb-2">Threshold Quantity</label>
                                    <input
                                        type="number"
                                        value={newAlert.threshold_quantity}
                                        onChange={(e) =>
                                            setNewAlert({ ...newAlert, threshold_quantity: parseInt(e.target.value) })
                                        }
                                        aria-label="Threshold quantity"
                                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    />
                                </div>
                            </div>

                            {/* Message */}
                            <div>
                                <label className="block text-sm font-medium mb-2">Message</label>
                                <textarea
                                    value={newAlert.message}
                                    onChange={(e) => setNewAlert({ ...newAlert, message: e.target.value })}
                                    rows={3}
                                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500"
                                    placeholder="Describe the alert..."
                                />
                            </div>
                        </div>

                        <div className="flex gap-3 mt-6">
                            <button
                                onClick={handleCreateAlert}
                                disabled={createAlertMutation.isPending}
                                className="flex-1 bg-purple-600 text-white py-3 rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
                            >
                                {createAlertMutation.isPending ? 'Creating...' : 'Create Alert'}
                            </button>
                            <button
                                onClick={() => setShowCreateModal(false)}
                                className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
