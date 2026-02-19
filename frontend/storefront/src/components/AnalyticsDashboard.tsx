import { useQuery } from '@tanstack/react-query'
import { useState, useEffect } from 'react'
import { TrendingUp, TrendingDown, ShoppingCart, Users, AlertTriangle, DollarSign, MessageSquare, Bell, Upload, Download, RefreshCw, Target, BarChart2, LineChartIcon, AreaChartIcon, Megaphone } from 'lucide-react'
import { Link } from 'react-router-dom'
import api from '@/lib/api'
import {
    LineChart, Line, BarChart, Bar, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    PieChart, Pie, Cell
} from 'recharts'
import OfferSuggestions from '@/components/OfferSuggestions'

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

const DAILY_GOAL = 10000 // ₹10k default daily revenue target
const PIE_COLORS: Record<string, string> = {
    delivered: '#22c55e', processing: '#3b82f6', shipped: '#8b5cf6',
    pending: '#eab308', cancelled: '#ef4444', confirmed: '#06b6d4'
}
const FALLBACK_COLORS = ['#6366f1', '#ec4899', '#f97316', '#14b8a6', '#f59e0b', '#64748b']

export default function AnalyticsDashboard() {
    const [dateRange, setDateRange] = useState<7 | 30 | 90>(30)
    const [chartMode, setChartMode] = useState<'line' | 'bar' | 'area'>('area')
    const [lastUpdated, setLastUpdated] = useState<Date>(new Date())
    const [countdown, setCountdown] = useState(60)

    // Fetch dashboard stats
    const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery<DashboardStats>({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            const response = await api.get('/api/v1/analytics/dashboard')
            return response.data
        },
        refetchInterval: 60000,
    })

    // Fetch sales chart data
    const { data: chartData } = useQuery<SalesChartData>({
        queryKey: ['sales-chart', dateRange],
        queryFn: async () => {
            const response = await api.get(`/api/v1/analytics/sales-chart?days=${dateRange}`)
            return response.data
        },
    })

    // Update last-updated timestamp whenever data arrives
    useEffect(() => { setLastUpdated(new Date()) }, [stats, chartData])

    // Auto-refresh countdown badge
    useEffect(() => {
        setCountdown(60)
        const interval = setInterval(() => setCountdown(c => c <= 1 ? (refetchStats(), 60) : c - 1), 1000)
        return () => clearInterval(interval)
    }, [lastUpdated])

    // CSV export
    const exportCSV = () => {
        if (!stats) return
        const rows: (string | number)[][] = [
            ['Metric', 'Today', 'Last 7 Days', 'Last 30 Days'],
            ['Orders', stats.today_orders, stats.week_orders, stats.month_orders],
            ['Revenue (INR)', stats.today_revenue.toFixed(2), stats.week_revenue.toFixed(2), stats.month_revenue.toFixed(2)],
            ['Customers', stats.today_customers, stats.week_customers, stats.month_customers],
            ['Avg Order Value', stats.today_orders > 0 ? (stats.today_revenue / stats.today_orders).toFixed(2) : 0, '', ''],
        ]
        const csv = rows.map(r => r.join(',')).join('\n')
        const blob = new Blob([csv], { type: 'text/csv' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `analytics-${new Date().toISOString().split('T')[0]}.csv`
        a.click()
        URL.revokeObjectURL(url)
    }

    // Build order-status distribution from recent_orders
    const statusCounts = (stats?.recent_orders ?? []).reduce((acc, o) => {
        acc[o.status] = (acc[o.status] || 0) + 1
        return acc
    }, {} as Record<string, number>)
    const statusPieData = Object.entries(statusCounts).map(([name, value]) => ({ name, value }))

    // Avg Order Value
    const aov = stats && stats.today_orders > 0
        ? stats.today_revenue / stats.today_orders
        : 0

    // KPI progress
    const kpiProgress = stats ? Math.min(100, (stats.today_revenue / DAILY_GOAL) * 100) : 0

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
            <div className="card">
                <div className="flex items-center justify-between">
                    <div>
                        <p className="text-text-tertiary text-sm font-medium">{title}</p>
                        <p className="text-3xl font-bold text-text-primary mt-2">{value}</p>
                        {change !== undefined && (
                            <div className="flex items-center mt-2">
                                {isPositive && <TrendingUp className="text-green-600 mr-1" size={16} />}
                                {isNegative && <TrendingDown className="text-red-600 mr-1" size={16} />}
                                <span
                                    className={`text-sm font-medium ${isPositive ? 'text-green-500' : isNegative ? 'text-red-500' : 'text-text-secondary'
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
            <div className="container mx-auto px-4 py-8 animate-fade-in">
                <div className="skeleton h-10 w-64 rounded-xl mb-8" />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="skeleton h-32 rounded-2xl" />
                    ))}
                </div>
                <div className="skeleton h-80 rounded-2xl" />
            </div>
        )
    }

    if (!stats) return null

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 mb-6">
                <div>
                    <h1 className="section-title">Analytics Dashboard</h1>
                    <p className="section-subtitle flex items-center gap-2">
                        Monitor your store's performance
                        <span className="inline-flex items-center gap-1.5 text-xs text-text-tertiary bg-bg-tertiary rounded-full px-2.5 py-0.5 border border-border-color">
                            <span className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse" />
                            Refreshes in {countdown}s
                        </span>
                    </p>
                </div>

                {/* Quick Actions */}
                <div className="flex flex-wrap gap-2">
                    <button
                        onClick={exportCSV}
                        className="btn btn-sm btn-outline gap-1.5"
                        title="Export CSV"
                    >
                        <Download size={14} />
                        <span className="hidden sm:inline">Export</span>
                    </button>
                    <button
                        onClick={() => refetchStats()}
                        className="btn btn-sm btn-outline gap-1.5"
                        title="Refresh now"
                    >
                        <RefreshCw size={14} />
                        <span className="hidden sm:inline">Refresh</span>
                    </button>
                    <Link
                        to="/admin/ads"
                        className="btn btn-sm bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20 hover:bg-orange-500/20"
                    >
                        <Megaphone size={16} />
                        <span className="hidden sm:inline">Ads</span>
                    </Link>
                    <Link
                        to="/admin/product-import"
                        className="btn btn-sm bg-green-500/10 text-green-600 dark:text-green-400 border border-green-500/20 hover:bg-green-500/20"
                    >
                        <Upload size={16} />
                        <span className="hidden sm:inline">Import</span>
                    </Link>
                    <Link
                        to="/admin/reviews"
                        className="btn btn-sm bg-theme-primary/10 text-theme-primary border border-theme-primary/20 hover:bg-theme-primary/20"
                    >
                        <MessageSquare size={16} />
                        <span className="hidden sm:inline">Reviews</span>
                    </Link>
                    <Link
                        to="/admin/inventory-alerts"
                        className="btn btn-sm bg-yellow-500/10 text-yellow-600 dark:text-yellow-400 border border-yellow-500/20 hover:bg-yellow-500/20"
                    >
                        <Bell size={16} />
                        <span className="hidden sm:inline">Alerts</span>
                    </Link>
                </div>
            </div>

            {/* ── Daily Revenue KPI Progress Bar ─────────────────────────────── */}
            <div className="card mb-6 p-4">
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                        <Target className="h-4 w-4 text-theme-primary" />
                        Daily Revenue Goal
                    </div>
                    <div className="text-right">
                        <span className="text-lg font-bold text-gradient">₹{stats.today_revenue.toLocaleString()}</span>
                        <span className="text-text-tertiary text-sm"> / ₹{DAILY_GOAL.toLocaleString()}</span>
                    </div>
                </div>
                <div className="h-3 bg-bg-tertiary rounded-full overflow-hidden">
                    <style dangerouslySetInnerHTML={{ __html: `.kpi-bar{width:${kpiProgress}%}` }} />
                    <div className={`kpi-bar h-full rounded-full transition-all duration-700 ${kpiProgress >= 100 ? 'bg-green-500' : kpiProgress >= 60 ? 'bg-theme-primary' : 'bg-yellow-500'
                        }`} />
                </div>
                <p className="text-xs text-text-tertiary mt-1.5">
                    {kpiProgress >= 100 ? '🎉 Daily goal achieved!' : `${kpiProgress.toFixed(1)}% of daily target`}
                </p>
            </div>

            {/* ── AI-Driven Offer Suggestions ──────────────────────────────────── */}
            <OfferSuggestions stats={stats} />

            {/* Today's Stats */}
            <div className="mb-8">
                <h2 className="text-xl font-semibold mb-4 text-text-primary">Today's Performance</h2>
                <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
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
                    <StatCard
                        title="Avg Order Value"
                        value={`₹${aov.toFixed(0)}`}
                        icon={Target}
                        color="bg-orange-600"
                    />
                </div>
            </div>

            {/* Sales Chart */}
            <div className="mb-8">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
                    <h2 className="text-xl font-semibold text-text-primary">Sales Trend</h2>
                    <div className="flex items-center gap-2 flex-wrap">
                        {/* Date range tabs */}
                        <div className="flex rounded-xl overflow-hidden border border-border-color">
                            {([7, 30, 90] as const).map(d => (
                                <button
                                    key={d}
                                    onClick={() => setDateRange(d)}
                                    className={`px-3 py-1.5 text-xs font-semibold transition-colors ${dateRange === d
                                        ? 'bg-theme-primary text-white'
                                        : 'text-text-secondary hover:bg-bg-tertiary'
                                        }`}
                                >
                                    {d}d
                                </button>
                            ))}
                        </div>
                        {/* Chart mode toggle */}
                        <div className="flex rounded-xl overflow-hidden border border-border-color">
                            {([
                                { mode: 'area' as const, icon: AreaChartIcon },
                                { mode: 'line' as const, icon: LineChartIcon },
                                { mode: 'bar' as const, icon: BarChart2 },
                            ]).map(({ mode, icon: Icon }) => (
                                <button
                                    key={mode}
                                    onClick={() => setChartMode(mode)}
                                    title={mode}
                                    className={`px-2.5 py-1.5 transition-colors ${chartMode === mode
                                        ? 'bg-theme-primary text-white'
                                        : 'text-text-secondary hover:bg-bg-tertiary'
                                        }`}
                                >
                                    <Icon size={14} />
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
                {formattedChartData.length > 0 ? (
                    <div className="card">
                        <ResponsiveContainer width="100%" height={300}>
                            {chartMode === 'bar' ? (
                                <BarChart data={formattedChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                                    <Tooltip />
                                    <Legend />
                                    <Bar yAxisId="left" dataKey="revenue" fill="#10b981" name="Revenue (₹)" radius={[3, 3, 0, 0]} />
                                    <Bar yAxisId="right" dataKey="orders" fill="#3b82f6" name="Orders" radius={[3, 3, 0, 0]} />
                                </BarChart>
                            ) : chartMode === 'area' ? (
                                <AreaChart data={formattedChartData}>
                                    <defs>
                                        <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                        </linearGradient>
                                        <linearGradient id="ordGrad" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                                    <Tooltip />
                                    <Legend />
                                    <Area yAxisId="left" type="monotone" dataKey="revenue" stroke="#10b981" fill="url(#revGrad)" name="Revenue (₹)" />
                                    <Area yAxisId="right" type="monotone" dataKey="orders" stroke="#3b82f6" fill="url(#ordGrad)" name="Orders" />
                                </AreaChart>
                            ) : (
                                <LineChart data={formattedChartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border-color)" />
                                    <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="left" tick={{ fontSize: 11 }} />
                                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                                    <Tooltip />
                                    <Legend />
                                    <Line yAxisId="left" type="monotone" dataKey="revenue" stroke="#10b981" name="Revenue (₹)" dot={false} strokeWidth={2} />
                                    <Line yAxisId="right" type="monotone" dataKey="orders" stroke="#3b82f6" name="Orders" dot={false} strokeWidth={2} />
                                </LineChart>
                            )}
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="card flex items-center justify-center h-48 text-text-tertiary">No chart data yet</div>
                )}
            </div>

            {/* ── Order Status Distribution + Period Overview side-by-side ─── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
                {/* Period Overview */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4 text-text-primary">Period Overview</h3>
                    <div className="space-y-4">
                        {[{ label: 'Last 7 Days', o: stats.week_orders, r: stats.week_revenue, c: stats.week_customers },
                        { label: 'Last 30 Days', o: stats.month_orders, r: stats.month_revenue, c: stats.month_customers }].map(p => (
                            <div key={p.label} className="rounded-xl bg-bg-tertiary/50 border border-border-color p-3 space-y-2">
                                <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider">{p.label}</p>
                                <div className="grid grid-cols-3 gap-2 text-center">
                                    <div><p className="text-lg font-bold text-text-primary">{p.o}</p><p className="text-xs text-text-tertiary">Orders</p></div>
                                    <div><p className="text-lg font-bold text-gradient">₹{(p.r / 1000).toFixed(1)}k</p><p className="text-xs text-text-tertiary">Revenue</p></div>
                                    <div><p className="text-lg font-bold text-text-primary">{p.c}</p><p className="text-xs text-text-tertiary">Customers</p></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Order Status Donut */}
                <div className="card">
                    <h3 className="text-lg font-semibold mb-4 text-text-primary">Order Status Distribution</h3>
                    {statusPieData.length > 0 ? (
                        <div className="flex items-center gap-4">
                            <ResponsiveContainer width={160} height={160}>
                                <PieChart>
                                    <Pie
                                        data={statusPieData}
                                        innerRadius={45}
                                        outerRadius={72}
                                        paddingAngle={3}
                                        dataKey="value"
                                    >
                                        {statusPieData.map((entry, idx) => (
                                            <Cell
                                                key={entry.name}
                                                fill={PIE_COLORS[entry.name] ?? FALLBACK_COLORS[idx % FALLBACK_COLORS.length]}
                                            />
                                        ))}
                                    </Pie>
                                    <Tooltip formatter={(value: number) => [`${value} orders`, '']} />
                                </PieChart>
                            </ResponsiveContainer>
                            <div className="flex-1 space-y-2">
                                <style dangerouslySetInnerHTML={{
                                    __html: statusPieData.map((e, i) =>
                                        `.sd-${i}{background:${PIE_COLORS[e.name] ?? FALLBACK_COLORS[i % FALLBACK_COLORS.length]}}`).join('')
                                }} />
                                {statusPieData.map((entry, idx) => (
                                    <div key={entry.name} className="flex items-center justify-between text-sm">
                                        <div className="flex items-center gap-2">
                                            <span className={`sd-${idx} h-2.5 w-2.5 rounded-full flex-shrink-0`} />
                                            <span className="capitalize text-text-secondary">{entry.name}</span>
                                        </div>
                                        <span className="font-semibold text-text-primary">{entry.value}</span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="flex items-center justify-center h-32 text-text-tertiary text-sm">No order data</div>
                    )}
                </div>
            </div>

            {/* Inventory Alerts */}
            {alerts && alerts.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <AlertTriangle className="text-yellow-500" />
                        Inventory Alerts ({alerts.length})
                    </h2>
                    <div className="card p-0 overflow-hidden">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>
                                        Product
                                    </th>
                                    <th>
                                        SKU
                                    </th>
                                    <th>
                                        Alert
                                    </th>
                                    <th>
                                        Stock
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="bg-bg-primary">
                                {alerts.slice(0, 10).map((alert) => (
                                    <tr key={alert.id}>
                                        <td className="text-text-primary font-medium">
                                            {alert.product_name}
                                        </td>
                                        <td>
                                            {alert.product_sku}
                                        </td>
                                        <td>
                                            <span
                                                className={`badge ${alert.alert_type === 'out_of_stock'
                                                    ? 'bg-red-500/10 text-red-500'
                                                    : alert.alert_type === 'critical'
                                                        ? 'bg-yellow-500/10 text-yellow-500'
                                                        : 'bg-theme-primary/10 text-theme-primary'
                                                    }`}
                                            >
                                                {alert.alert_type.replace('_', ' ')}
                                            </span>
                                        </td>
                                        <td>
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
                    <h2 className="text-xl font-semibold mb-4 text-text-primary">Top Selling Products</h2>
                    <div className="card space-y-3">
                        {(() => {
                            const maxRev = Math.max(...stats.top_products.map(p => p.revenue), 1)
                            return stats.top_products.map((product, idx) => (
                                <div key={product.id} className="flex items-center gap-3">
                                    <span className="w-6 text-sm font-bold text-text-tertiary text-center flex-shrink-0">#{idx + 1}</span>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center justify-between mb-1">
                                            <span className="text-sm font-semibold text-text-primary truncate mr-2">{product.name}</span>
                                            <span className="text-xs text-text-tertiary flex-shrink-0">{product.units_sold} units</span>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <div className="flex-1 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                                                <style dangerouslySetInnerHTML={{ __html: `.tp-${idx}{width:${((product.revenue / maxRev) * 100).toFixed(1)}%}` }} />
                                                <div className={`tp-${idx} h-full rounded-full bg-gradient-to-r from-theme-primary to-theme-accent`} />
                                            </div>
                                            <span className="text-xs font-semibold text-gradient flex-shrink-0">₹{product.revenue.toLocaleString()}</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        })()}
                    </div>
                </div>
            )}

            {stats.recent_orders.length > 0 && (
                <div className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 text-text-primary">Recent Orders</h2>
                    <div className="card p-0 overflow-hidden">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Order #</th>
                                    <th>Customer</th>
                                    <th>Amount</th>
                                    <th>Status</th>
                                    <th>Date</th>
                                </tr>
                            </thead>
                            <tbody className="bg-bg-primary">
                                {stats.recent_orders.map((order) => (
                                    <tr key={order.id}>
                                        <td className="text-text-primary font-medium">{order.order_number}</td>
                                        <td>{order.customer_name}</td>
                                        <td>₹{order.total_amount.toLocaleString()}</td>
                                        <td>
                                            <span className={`badge ${order.status === 'delivered' ? 'bg-green-500/10 text-green-500'
                                                : order.status === 'cancelled' ? 'bg-red-500/10 text-red-500'
                                                    : 'bg-yellow-500/10 text-yellow-500'
                                                }`}>
                                                {order.status}
                                            </span>
                                        </td>
                                        <td>{new Date(order.created_at).toLocaleDateString()}</td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {/* Last Updated Footer */}
            <div className="flex items-center justify-between text-xs text-text-tertiary pt-4 border-t border-border-color">
                <span>Data auto-refreshes every 60 seconds</span>
                <span>Last updated: {lastUpdated.toLocaleTimeString()}</span>
            </div>
        </div>
    )
}
