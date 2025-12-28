import { useQuery } from '@tanstack/react-query'
import { TrendingUp, TrendingDown, ShoppingCart, Users, AlertTriangle, DollarSign, MessageSquare, Bell, Upload } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface DashboardStats {
    today_orders: number
    today_revenue: number
    today_customers: number
    orders_change: number
    revenue_change: number
    customers_change: number
    week_orders: number
    week_revenue: number
    week_customers: number
    month_orders: number
    month_revenue: number
    month_customers: number
    top_products: Array<{
        id: string
        name: string
        sku: string
        units_sold: number
        revenue: number
    }>
    recent_orders: Array<{
        id: string
        order_number: string
        customer_name: string
        total_amount: number
        status: string
        created_at: string
    }>
    low_stock_products: number
    out_of_stock_products: number
}

interface SalesChartData {
    dates: string[]
    revenue: number[]
    orders: number[]
    customers: number[]
}

interface InventoryAlert {
    id: string
    product_name: string
    product_sku: string
    alert_type: string
    current_quantity: number
    threshold_quantity: number
    created_at: string
}

export default function AnalyticsDashboard() {
    // Fetch dashboard stats
    const { data: stats, isLoading: statsLoading } = useQuery<DashboardStats>({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            const response = await api.get('/api/v1/analytics/dashboard')
            return response.data
        },
        refetchInterval: 60000, // Refetch every minute
    })

    // Fetch sales chart data
    const { data: chartData } = useQuery<SalesChartData>({
        queryKey: ['sales-chart'],
        queryFn: async () => {
            const response = await api.get('/api/v1/analytics/sales-chart?days=30')
            return response.data
        },
    })

    // Fetch inventory alerts
    const { data: alerts } = useQuery<InventoryAlert[]>({
        queryKey: ['inventory-alerts'],
        queryFn: async () => {
            const response = await api.get('/api/v1/analytics/inventory-alerts?resolved=false')
            return response.data
        },
    })

    // Format chart data
    const formattedChartData = chartData
        ? chartData.dates.map((date, index) => ({
            date: new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
            revenue: chartData.revenue[index],
            orders: chartData.orders[index],
            customers: chartData.customers[index],
        }))
        : []

    const StatCard = ({
        title,
        value,
        change,
        icon: Icon,
        color,
    }: {
        title: string
        value: string | number
        change?: number
        icon: any
        color: string
    }) => {
        const isPositive = change ? change > 0 : false
        const isNegative = change ? change < 0 : false

        return (
            <div className="bg-white p-6 rounded-lg shadow-md">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-gray-500 text-sm font-medium">{title}</p>
                        <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
                        {change !== undefined && (
                            <div className="flex items-center mt-2">
                                {isPositive && <TrendingUp className="text-green-600 mr-1" size={16} />}
                                {isNegative && <TrendingDown className="text-red-600 mr-1" size={16} />}
                                <span
                                    className={`text-sm font-medium ${isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-600'
                                        }`}
                                >
                                    {change > 0 ? '+' : ''}
                                    {change.toFixed(1)}% vs yesterday
                                </span>
                            </div>
                        )}
                    </div>
                    <div className={`${color} rounded-full p-3`}>
                        <Icon className="h-6 w-6 text-white" />
                    </div>
                </div>
            </div>
        )
    }

    if (statsLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="text-center">Loading dashboard...</div>
            </div>
        )
    }

    if (!stats) return null

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex items-center justify-between mb-8">
                <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>

                {/* Quick Actions */}
                <div className="flex gap-3">
                    <Link
                        to="/admin/product-import"
                        className="flex items-center gap-2 px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                    >
                        <Upload size={18} />
                        Import Products
                    </Link>
                    <Link
                        to="/admin/reviews"
                        className="flex items-center gap-2 px-4 py-2 bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
                    >
                        <MessageSquare size={18} />
                        Manage Reviews
                    </Link>
                    <Link
                        to="/admin/inventory-alerts"
                        className="flex items-center gap-2 px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors"
                    >
                        <Bell size={18} />
                        Inventory Alerts
                    </Link>
                </div>
            </div>

            {/* Today's Stats */}
            <div className="mb-8">
                <h2 className="text-xl font-semibold mb-4">Today's Performance</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <StatCard
                        title="Orders"
                        value={stats.today_orders}
                        change={stats.orders_change}
                        icon={ShoppingCart}
                        color="bg-blue-600"
                    />
                    <StatCard
                        title="Revenue"
                        value={`₹${stats.today_revenue.toLocaleString()}`}
                        change={stats.revenue_change}
                        icon={DollarSign}
                        color="bg-green-600"
                    />
                    <StatCard
                        title="Customers"
                        value={stats.today_customers}
                        change={stats.customers_change}
                        icon={Users}
                        color="bg-purple-600"
                    />
                </div>
            </div>

            {/* Weekly & Monthly Stats */}
            <div className="mb-8">
                <h2 className="text-xl font-semibold mb-4">Period Overview</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-white p-6 rounded-lg shadow-md">
                        <h3 className="text-lg font-semibold mb-4">Last 7 Days</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Orders:</span>
                                <span className="font-semibold">{stats.week_orders}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Revenue:</span>
                                <span className="font-semibold">₹{stats.week_revenue.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Customers:</span>
                                <span className="font-semibold">{stats.week_customers}</span>
                            </div>
                        </div>
                    </div>

                    <div className="bg-white p-6 rounded-lg shadow-md">
                        <h3 className="text-lg font-semibold mb-4">Last 30 Days</h3>
                        <div className="space-y-3">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Orders:</span>
                                <span className="font-semibold">{stats.month_orders}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Revenue:</span>
                                <span className="font-semibold">₹{stats.month_revenue.toLocaleString()}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Customers:</span>
                                <span className="font-semibold">{stats.month_customers}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Sales Chart */}
            {formattedChartData.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">Sales Trend (30 Days)</h2>
                    <div className="bg-white p-6 rounded-lg shadow-md">
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={formattedChartData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="date" />
                                <YAxis yAxisId="left" />
                                <YAxis yAxisId="right" orientation="right" />
                                <Tooltip />
                                <Legend />
                                <Line
                                    yAxisId="left"
                                    type="monotone"
                                    dataKey="revenue"
                                    stroke="#10b981"
                                    name="Revenue (₹)"
                                />
                                <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#3b82f6" name="Orders" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

            {/* Inventory Alerts */}
            {alerts && alerts.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="text-orange-600" />
                        Inventory Alerts ({alerts.length})
                    </h2>
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Product
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        SKU
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Alert
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Stock
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {alerts.slice(0, 10).map((alert) => (
                                    <tr key={alert.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {alert.product_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {alert.product_sku}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span
                                                className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${alert.alert_type === 'out_of_stock'
                                                    ? 'bg-red-100 text-red-800'
                                                    : alert.alert_type === 'critical'
                                                        ? 'bg-orange-100 text-orange-800'
                                                        : 'bg-yellow-100 text-yellow-800'
                                                    }`}
                                            >
                                                {alert.alert_type.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {alert.current_quantity} units
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Top Products */}
            {stats.top_products.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4">Top Selling Products</h2>
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Product
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        SKU
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Units Sold
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Revenue
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {stats.top_products.map((product) => (
                                    <tr key={product.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {product.name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {product.sku}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {product.units_sold}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            ₹{product.revenue.toLocaleString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Recent Orders */}
            {stats.recent_orders.length > 0 && (
                <div>
                    <h2 className="text-xl font-semibold mb-4">Recent Orders</h2>
                    <div className="bg-white rounded-lg shadow-md overflow-hidden">
                        <table className="min-w-full divide-y divide-gray-200">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Order #
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Customer
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Amount
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Status
                                    </th>
                                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                                        Date
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-white divide-y divide-gray-200">
                                {stats.recent_orders.map((order) => (
                                    <tr key={order.id}>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                            {order.order_number}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {order.customer_name}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            ₹{order.total_amount.toLocaleString()}
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap">
                                            <span
                                                className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${order.status === 'delivered'
                                                    ? 'bg-green-100 text-green-800'
                                                    : order.status === 'cancelled'
                                                        ? 'bg-red-100 text-red-800'
                                                        : 'bg-yellow-100 text-yellow-800'
                                                    }`}
                                            >
                                                {order.status}
                                            </span>
                                        </td>
                                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                            {new Date(order.created_at).toLocaleDateString()}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}
