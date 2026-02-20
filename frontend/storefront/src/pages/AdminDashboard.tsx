import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { adminApi } from '@/lib/api'
import {
  Package, ShoppingBag, Users, Tag, Megaphone, RotateCcw,
  Star, Upload, BarChart2, Settings, Activity, Bell,
  TrendingUp, AlertTriangle, IndianRupee, Clock, ChevronRight,
  ArrowUpRight,
} from 'lucide-react'

const ADMIN_SECTIONS = [
  { to: '/admin/analytics', Icon: BarChart2, label: 'Analytics', color: 'text-blue-500', bg: 'bg-blue-50 dark:bg-blue-950/40', border: 'border-blue-100 dark:border-blue-900/40' },
  { to: '/admin/orders', Icon: ShoppingBag, label: 'Orders', color: 'text-violet-500', bg: 'bg-violet-50 dark:bg-violet-950/40', border: 'border-violet-100 dark:border-violet-900/40' },
  { to: '/admin/products', Icon: Package, label: 'Products', color: 'text-emerald-500', bg: 'bg-emerald-50 dark:bg-emerald-950/40', border: 'border-emerald-100 dark:border-emerald-900/40' },
  { to: '/admin/customers', Icon: Users, label: 'Customers', color: 'text-cyan-500', bg: 'bg-cyan-50 dark:bg-cyan-950/40', border: 'border-cyan-100 dark:border-cyan-900/40' },
  { to: '/admin/coupons', Icon: Tag, label: 'Coupons', color: 'text-amber-500', bg: 'bg-amber-50 dark:bg-amber-950/40', border: 'border-amber-100 dark:border-amber-900/40' },
  { to: '/admin/ads', Icon: Megaphone, label: 'Ads & Promos', color: 'text-orange-500', bg: 'bg-orange-50 dark:bg-orange-950/40', border: 'border-orange-100 dark:border-orange-900/40' },
  { to: '/admin/returns', Icon: RotateCcw, label: 'Returns', color: 'text-red-500', bg: 'bg-red-50 dark:bg-red-950/40', border: 'border-red-100 dark:border-red-900/40' },
  { to: '/admin/reviews', Icon: Star, label: 'Reviews', color: 'text-yellow-500', bg: 'bg-yellow-50 dark:bg-yellow-950/40', border: 'border-yellow-100 dark:border-yellow-900/40' },
  { to: '/admin/inventory-alerts', Icon: Bell, label: 'Stock Alerts', color: 'text-rose-500', bg: 'bg-rose-50 dark:bg-rose-950/40', border: 'border-rose-100 dark:border-rose-900/40' },
  { to: '/admin/product-import', Icon: Upload, label: 'Import Products', color: 'text-indigo-500', bg: 'bg-indigo-50 dark:bg-indigo-950/40', border: 'border-indigo-100 dark:border-indigo-900/40' },
  { to: '/monitoring', Icon: Activity, label: 'System Monitor', color: 'text-teal-500', bg: 'bg-teal-50 dark:bg-teal-950/40', border: 'border-teal-100 dark:border-teal-900/40' },
  { to: '/admin/settings', Icon: Settings, label: 'Store Settings', color: 'text-slate-500', bg: 'bg-slate-50 dark:bg-slate-950/40', border: 'border-slate-100 dark:border-slate-900/40' },
]

export default function AdminDashboard() {
  const { data: stats } = useQuery({
    queryKey: ['store-dashboard-stats'],
    queryFn: () => adminApi.getDashboardStats(30).then(r => r.data.data),
  })

  const fmt = (n: number) => n.toLocaleString('en-IN', { maximumFractionDigits: 0 })

  const STAT_CARDS = [
    {
      label: 'Orders',
      sublabel: 'Last 30 days',
      value: stats?.orders?.total ?? '—',
      Icon: ShoppingBag,
      color: 'text-violet-600',
      bg: 'bg-violet-50 dark:bg-violet-950/40',
      href: '/admin/orders',
    },
    {
      label: 'Revenue',
      sublabel: 'Last 30 days',
      value: stats ? `?${fmt(stats.orders.revenue)}` : '—',
      Icon: IndianRupee,
      color: 'text-emerald-600',
      bg: 'bg-emerald-50 dark:bg-emerald-950/40',
      href: '/admin/analytics',
    },
    {
      label: 'Total Products',
      sublabel: 'In catalogue',
      value: stats?.products?.total ?? '—',
      Icon: Package,
      color: 'text-blue-600',
      bg: 'bg-blue-50 dark:bg-blue-950/40',
      href: '/admin/products',
    },
    {
      label: 'Pending Orders',
      sublabel: 'Needs attention',
      value: stats?.orders?.pending ?? '—',
      Icon: Clock,
      color: 'text-amber-600',
      bg: 'bg-amber-50 dark:bg-amber-950/40',
      href: '/admin/orders',
    },
    {
      label: 'Low Stock',
      sublabel: 'Items running low',
      value: stats?.products?.low_stock ?? '—',
      Icon: AlertTriangle,
      color: 'text-orange-600',
      bg: 'bg-orange-50 dark:bg-orange-950/40',
      href: '/admin/inventory-alerts',
    },
    {
      label: 'Out of Stock',
      sublabel: 'Needs restocking',
      value: stats?.products?.out_of_stock ?? '—',
      Icon: TrendingUp,
      color: 'text-red-600',
      bg: 'bg-red-50 dark:bg-red-950/40',
      href: '/admin/products',
    },
  ]

  return (
    <div className="container-wide py-8 animate-fade-in">
      {/* -- Page header -------------------------------------- */}
      <div className="page-header mb-10">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="page-subtitle">Welcome back. Here's what's happening with your store today.</p>
        </div>
        <Link to="/admin/settings" className="btn btn-secondary btn-sm gap-1.5">
          <Settings className="h-4 w-4" />
          Store Settings
        </Link>
      </div>

      {/* -- Stat cards --------------------------------------- */}
      <div className="grid grid-cols-2 sm:grid-cols-3 xl:grid-cols-6 gap-4 mb-10">
        {STAT_CARDS.map(({ label, sublabel, value, Icon, color, bg, href }) => (
          <Link
            key={label}
            to={href}
            className="card card-hover group flex flex-col gap-3 p-5"
          >
            <div className="flex items-center justify-between">
              <div className={`h-10 w-10 rounded-[var(--radius-lg)] ${bg} flex items-center justify-center`}>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
              <ArrowUpRight className="h-4 w-4 text-text-quaternary opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            <div>
              <div className={`text-2xl font-black ${color} tabular-nums`}>{value}</div>
              <div className="text-sm font-medium text-text-primary mt-0.5">{label}</div>
              <div className="text-xs text-text-tertiary">{sublabel}</div>
            </div>
          </Link>
        ))}
      </div>

      {/* -- Section grid ------------------------------------- */}
      <div>
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-sm font-semibold text-text-tertiary uppercase tracking-wider">Management</h2>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
          {ADMIN_SECTIONS.map(({ to, Icon, label, color, bg, border }) => (
            <Link
              key={to}
              to={to}
              className={`group flex flex-col items-center text-center gap-3 rounded-[var(--radius-xl)] border ${border} ${bg} p-5 transition-all duration-200 hover:-translate-y-0.5 hover:shadow-md`}
            >
              <div className={`h-11 w-11 rounded-[var(--radius-lg)] bg-bg-primary/80 border border-white/50 flex items-center justify-center shadow-xs group-hover:scale-110 transition-transform duration-200`}>
                <Icon className={`h-5 w-5 ${color}`} />
              </div>
              <div className="flex items-center gap-1">
                <p className="text-sm font-medium text-text-primary leading-tight">{label}</p>
                <ChevronRight className="h-3.5 w-3.5 text-text-quaternary opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
