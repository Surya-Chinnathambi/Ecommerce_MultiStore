import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { sellerApi } from '@/lib/api'
import { Store, Package, TrendingUp, DollarSign, Clock, AlertCircle, Plus, ShoppingBag } from 'lucide-react'

export default function SellerDashboardPage() {
    const { data: profileRes, isLoading: profileLoading } = useQuery({
        queryKey: ['seller-profile'],
        queryFn: () => sellerApi.getProfile().then((r) => r.data.data),
        retry: false,
    })

    const { data: dashRes } = useQuery({
        queryKey: ['seller-dashboard'],
        queryFn: () => sellerApi.getDashboard().then((r) => r.data.data),
        enabled: !!profileRes,
    })

    const { data: payoutsRes } = useQuery({
        queryKey: ['seller-payouts'],
        queryFn: () => sellerApi.getPayouts().then((r) => r.data.data),
        enabled: !!profileRes,
    })

    if (profileLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="skeleton h-8 w-48 rounded-lg mb-6" />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[...Array(4)].map((_, i) => <div key={i} className="skeleton rounded-2xl h-28" />)}
                </div>
            </div>
        )
    }

    // Not registered yet
    if (!profileRes) {
        return (
            <div className="container mx-auto px-4 py-16">
                <div className="empty-state">
                    <Store className="empty-state-icon" />
                    <h2 className="empty-state-title">Start Selling Today</h2>
                    <p className="empty-state-description">
                        Register as a seller to list your products and reach millions of customers.
                    </p>
                    <Link to="/seller/register" className="btn btn-primary">
                        <Plus className="h-4 w-4" />
                        Register as Seller
                    </Link>
                </div>
            </div>
        )
    }

    const statusColors: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400',
        approved: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
        rejected: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
        suspended: 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400',
    }

    const stats = [
        { label: 'Monthly Revenue', value: `₹${(dashRes?.monthly_revenue || 0).toLocaleString()}`, icon: DollarSign, color: 'text-green-500' },
        { label: 'Monthly Orders', value: dashRes?.monthly_orders ?? 0, icon: Package, color: 'text-blue-500' },
        { label: 'Active Listings', value: dashRes?.active_listings ?? 0, icon: TrendingUp, color: 'text-purple-500' },
        { label: 'Pending Payout', value: `₹${(dashRes?.pending_payout || 0).toLocaleString()}`, icon: Clock, color: 'text-orange-500' },
    ]

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8">
                {/* Header */}
                <div className="flex items-center justify-between mb-8">
                    <div>
                        <h1 className="text-2xl md:text-3xl font-bold text-text-primary">
                            Seller Dashboard
                        </h1>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="text-text-secondary">{profileRes.display_name}</span>
                            <span className={`badge text-xs ${statusColors[profileRes.status] || ''}`}>
                                {profileRes.status?.toUpperCase()}
                            </span>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        <Link to="/seller/orders" className="btn btn-outline flex items-center gap-1.5">
                            <ShoppingBag className="h-4 w-4" />
                            My Orders
                        </Link>
                        <Link to="/seller/products" className="btn btn-primary">
                            <Plus className="h-4 w-4" />
                            List Product
                        </Link>
                    </div>
                </div>

                {/* Pending warning */}
                {profileRes.status === 'pending' && (
                    <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl border border-yellow-200 dark:border-yellow-800 p-4 mb-6 flex gap-3">
                        <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5 flex-shrink-0" />
                        <div>
                            <p className="font-semibold text-yellow-800 dark:text-yellow-200">Application Under Review</p>
                            <p className="text-sm text-yellow-600 dark:text-yellow-400">
                                Your seller application is being reviewed. This typically takes 24 hours.
                            </p>
                        </div>
                    </div>
                )}

                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    {stats.map((stat) => (
                        <div key={stat.label} className="card p-5">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-sm text-text-secondary">{stat.label}</span>
                                <stat.icon className={`h-5 w-5 ${stat.color}`} />
                            </div>
                            <p className="text-2xl font-bold text-text-primary">{stat.value}</p>
                        </div>
                    ))}
                </div>

                <div className="grid md:grid-cols-2 gap-6">
                    {/* Recent Payouts */}
                    <div className="card p-6">
                        <h2 className="text-lg font-bold text-text-primary mb-4">Recent Payouts</h2>
                        {(payoutsRes?.length ?? 0) === 0 ? (
                            <p className="text-text-tertiary text-sm">No payouts yet.</p>
                        ) : (
                            <div className="space-y-3">
                                {(payoutsRes as any[]).slice(0, 5).map((p: any) => (
                                    <div key={p.id} className="flex items-center justify-between py-2 border-b border-border-color last:border-0">
                                        <div>
                                            <p className="font-medium text-text-primary text-sm">₹{p.amount?.toLocaleString()}</p>
                                            <p className="text-xs text-text-tertiary">{p.utr_number || 'Pending'}</p>
                                        </div>
                                        <span className={`badge text-xs ${p.status === 'paid' ? 'badge-success' :
                                            p.status === 'processing' ? 'bg-blue-100 text-blue-700' :
                                                'bg-bg-tertiary text-text-secondary'
                                            }`}>
                                            {p.status}
                                        </span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Quick Actions */}
                    <div className="card p-6">
                        <h2 className="text-lg font-bold text-text-primary mb-4">Quick Actions</h2>
                        <div className="space-y-3">
                            {[
                                { label: 'Manage Product Listings', to: '/seller/products', icon: Package },
                                { label: 'View Payouts', to: '/seller/dashboard', icon: DollarSign },
                                { label: 'Edit Profile', to: '/seller/dashboard', icon: Store },
                            ].map((action) => (
                                <Link
                                    key={action.label}
                                    to={action.to}
                                    className="flex items-center gap-3 p-3 rounded-xl hover:bg-bg-tertiary/60 transition-colors"
                                >
                                    <action.icon className="h-5 w-5 text-theme-primary" />
                                    <span className="text-text-primary font-medium">{action.label}</span>
                                </Link>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
