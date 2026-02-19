import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import {
  Package, ShoppingBag, Users, Tag, Megaphone, RotateCcw,
  Star, Upload, BarChart2, Settings, Activity, Bell,
  TrendingUp, AlertTriangle, IndianRupee, Clock,
} from 'lucide-react'

const ADMIN_SECTIONS = [
  { to: '/admin/analytics', Icon: BarChart2, label: 'Analytics', color: 'text-blue-500', bg: 'bg-blue-500/10' },
  { to: '/admin/orders', Icon: ShoppingBag, label: 'Orders', color: 'text-purple-500', bg: 'bg-purple-500/10' },
  { to: '/admin/products', Icon: Package, label: 'Products', color: 'text-green-500', bg: 'bg-green-500/10' },
  { to: '/admin/customers', Icon: Users, label: 'Customers', color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
  { to: '/admin/coupons', Icon: Tag, label: 'Coupons', color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
  { to: '/admin/ads', Icon: Megaphone, label: 'Ads & Promotions', color: 'text-orange-500', bg: 'bg-orange-500/10' },
  { to: '/admin/returns', Icon: RotateCcw, label: 'Returns', color: 'text-red-500', bg: 'bg-red-500/10' },
  { to: '/admin/reviews', Icon: Star, label: 'Reviews', color: 'text-amber-500', bg: 'bg-amber-500/10' },
  { to: '/admin/inventory-alerts', Icon: Bell, label: 'Inventory Alerts', color: 'text-rose-500', bg: 'bg-rose-500/10' },
  { to: '/admin/product-import', Icon: Upload, label: 'Import Products', color: 'text-indigo-500', bg: 'bg-indigo-500/10' },
  { to: '/monitoring', Icon: Activity, label: 'System Monitor', color: 'text-teal-500', bg: 'bg-teal-500/10' },
  { to: '/admin/settings', Icon: Settings, label: 'Store Settings', color: 'text-slate-500', bg: 'bg-slate-500/10' },
]

export default function AdminDashboard() {
  const { data: stats } = useQuery({
    queryKey: ['store-dashboard-stats'],
    queryFn: () => adminApi.getDashboardStats(30).then(r => r.data.data),
  })

  const STAT_CARDS = [
    { label: 'Orders (30d)', value: stats?.orders?.total ?? '—', Icon: ShoppingBag, color: 'text-purple-500', bg: 'bg-purple-500/10' },
    { label: 'Revenue (30d)', value: stats ? `₹${(stats.orders.revenue as number).toLocaleString('en-IN', { maximumFractionDigits: 0 })}` : '—', Icon: IndianRupee, color: 'text-green-500', bg: 'bg-green-500/10' },
    { label: 'Total Products', value: stats?.products?.total ?? '—', Icon: Package, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { label: 'Pending Orders', value: stats?.orders?.pending ?? '—', Icon: Clock, color: 'text-yellow-500', bg: 'bg-yellow-500/10' },
    { label: 'Low Stock', value: stats?.products?.low_stock ?? '—', Icon: AlertTriangle, color: 'text-orange-500', bg: 'bg-orange-500/10' },
    { label: 'Out of Stock', value: stats?.products?.out_of_stock ?? '—', Icon: TrendingUp, color: 'text-red-500', bg: 'bg-red-500/10' },
  ]

  return (
    <div className="container mx-auto px-4 py-8 animate-fade-in">
      <div className="mb-8">
        <h1 className="section-title">Admin Dashboard</h1>
        <p className="section-subtitle">Manage your entire store from one place</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4 mb-10">
        {STAT_CARDS.map(({ label, value, Icon, color, bg }) => (
          <div key={label} className="card text-center py-5">
            <div className={`inline-flex items-center justify-center w-11 h-11 rounded-xl ${bg} mb-3 mx-auto`}>
              <Icon className={`h-5 w-5 ${color}`} />
            </div>
            <div className={`text-2xl font-black ${color}`}>{value}</div>
            <div className="text-xs text-text-tertiary mt-1 leading-tight">{label}</div>
          </div>
        ))}
      </div>

      {/* Section grid */}
      <div>
        <h2 className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-4">Manage</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {ADMIN_SECTIONS.map(({ to, Icon, label, color, bg }) => (
            <Link
              key={to}
              to={to}
              className="card card-hover text-center group py-6 px-4"
            >
              <div className={`inline-flex items-center justify-center w-12 h-12 rounded-2xl ${bg} mb-3 mx-auto group-hover:scale-110 transition-transform duration-200`}>
                <Icon className={`h-6 w-6 ${color}`} />
              </div>
              <p className="text-sm font-medium text-text-primary leading-tight">{label}</p>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
