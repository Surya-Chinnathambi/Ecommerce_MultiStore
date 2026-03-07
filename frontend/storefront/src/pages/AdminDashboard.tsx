import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Package, ShoppingBag, Users, RefreshCw, AlertCircle, ArrowRight, Activity, TrendingUp, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { clsx } from 'clsx'
import { useEffect, useState } from 'react'

const MotionLink = motion(Link)

// --- Gamified Sync Node Visualizer Component ---
const SyncVisualizer = () => {
    const [progress, setProgress] = useState(0)

    useEffect(() => {
        const interval = setInterval(() => {
            setProgress(prev => (prev >= 100 ? 0 : prev + 1.5))
        }, 100)
        return () => clearInterval(interval)
    }, [])

    return (
        <div className="relative h-[250px] w-full rounded-3xl bg-gradient-to-br from-bg-secondary via-theme-primary/5 to-theme-accent/5 flex items-center justify-center overflow-hidden border border-border-color shadow-inner">
            {/* Background animated rings */}
            <motion.div 
                animate={{ rotate: 360, scale: [1, 1.1, 1] }} 
                transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
                className="absolute w-[200%] h-[200%] rounded-full border border-theme-primary/10 opacity-30 border-dashed"
            />
            
            <div className="flex items-center gap-8 relative z-10 w-full max-w-sm justify-between">
                {/* Local Store Node */}
                <motion.div 
                    whileHover={{ scale: 1.1, rotate: 5 }}
                    className="flex flex-col items-center gap-2"
                >
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-purple-500/20 to-blue-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(139,92,246,0.2)] border border-theme-primary/30 backdrop-blur-md">
                        <Package className="h-8 w-8 text-theme-primary" />
                    </div>
                    <span className="text-xs font-bold text-text-secondary">Platform POS</span>
                </motion.div>

                {/* Progress Node */}
                <div className="flex-1 relative mx-4">
                    <div className="h-2 rounded-full bg-bg-tertiary overflow-hidden flex items-center shadow-inner relative">
                        <motion.div 
                            className="h-full bg-gradient-to-r from-theme-primary to-theme-accent drop-shadow-[0_0_10px_rgba(139,92,246,0.8)]"
                            style={{ width: `${progress}%` }}
                        />
                        {/* Gamified packet animation */}
                        <motion.div 
                            initial={{ x: "-100%" }}
                            animate={{ x: "400%" }}
                            transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
                            className="absolute h-4 w-4 rounded-full bg-white shadow-[0_0_15px_#fff] top-1/2 -translate-y-1/2"
                        />
                    </div>
                    {progress >= 100 ? (
                        <p className="text-center text-[10px] font-bold text-emerald-500 mt-2 uppercase tracking-wide flex items-center justify-center gap-1">
                            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" /> Sync Complete
                        </p>
                    ) : (
                        <p className="text-center text-[10px] font-bold text-theme-primary mt-2 uppercase tracking-wide flex items-center justify-center gap-1">
                            <RefreshCw className="h-3 w-3 animate-spin text-theme-primary" /> Syncing ({Math.floor(progress)}%)
                        </p>
                    )}
                </div>

                {/* Cloud Node */}
                <motion.div 
                    whileHover={{ scale: 1.1, rotate: -5 }}
                    className="flex flex-col items-center gap-2"
                >
                    <div className="h-16 w-16 rounded-2xl bg-gradient-to-br from-theme-accent/20 to-pink-500/20 flex items-center justify-center shadow-[0_0_30px_rgba(236,72,153,0.2)] border border-theme-accent/30 backdrop-blur-md">
                        <Cpu className="h-8 w-8 text-theme-accent" />
                    </div>
                    <span className="text-xs font-bold text-text-secondary">Cloud DB</span>
                </motion.div>
            </div>
            
            {/* Gamification Level Badge */}
            <div className="absolute top-4 left-4 flex items-center gap-2 bg-bg-primary/80 backdrop-blur-sm px-3 py-1.5 rounded-full border border-border-color shadow-sm">
                <span className="text-[10px] font-extrabold text-theme-primary uppercase tracking-wider">Level 12</span>
                <div className="w-16 h-1.5 bg-bg-tertiary rounded-full overflow-hidden">
                    <div className="h-full w-3/4 bg-theme-primary" />
                </div>
            </div>
        </div>
    )
}

export default function AdminDashboard() {
    const { data: stats, isLoading } = useQuery({
        queryKey: ['admin-stats'],
        queryFn: () => adminApi.getDashboardStats().then(res => res.data.data),
    })

    const metricCards = [
        { title: 'Total Revenue', value: stats?.total_revenue ? `₹${stats.total_revenue.toLocaleString('en-IN')}` : '₹0', icon: TrendingUp, color: 'text-emerald-500', bg: 'from-emerald-500/10 to-emerald-500/5', border: 'hover:border-emerald-500/50' },
        { title: 'Total Orders', value: stats?.total_orders?.toLocaleString() || '0', icon: ShoppingBag, color: 'text-blue-500', bg: 'from-blue-500/10 to-blue-500/5', border: 'hover:border-blue-500/50' },
        { title: 'Total Products', value: stats?.total_products?.toLocaleString() || '0', icon: Package, color: 'text-theme-primary', bg: 'from-theme-primary/10 to-theme-primary/5', border: 'hover:border-theme-primary/50' },
        { title: 'Total Users', value: stats?.total_users?.toLocaleString() || '0', icon: Users, color: 'text-theme-accent', bg: 'from-theme-accent/10 to-theme-accent/5', border: 'hover:border-theme-accent/50' },
    ]

    return (
        <div className="animate-fade-in p-6 max-w-7xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-extrabold text-text-primary tracking-tight">Admin Headquarters</h1>
                    <p className="text-text-secondary text-sm mt-1">Manage infrastructure, track syncing, and grow revenue.</p>
                </div>
                <div className="hidden sm:flex items-center gap-3">
                    <span className="flex items-center gap-2 text-xs font-semibold px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
                        <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                        System Healthy
                    </span>
                    <button className="btn btn-primary btn-sm rounded-full shadow-lg shadow-theme-primary/30 hover:-translate-y-0.5 transition-transform">
                        <RefreshCw className="h-3.5 w-3.5" /> Force Global Sync
                    </button>
                </div>
            </div>

            {/* Top Metrics - 3D Hover Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                <AnimatePresence>
                    {metricCards.map((card, i) => (
                        <motion.div
                            key={card.title}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ delay: i * 0.1, type: "spring" }}
                            whileHover={{ y: -8, scale: 1.02 }}
                            className={clsx(
                                "relative overflow-hidden p-6 rounded-[2rem] border border-border-color bg-bg-primary shadow-sm hover:shadow-xl transition-all duration-300",
                                card.border
                            )}
                        >
                            <div className={clsx("absolute inset-0 bg-gradient-to-br opacity-50", card.bg)} />
                            <div className="relative z-10 flex items-start justify-between">
                                <div>
                                    <p className="text-text-tertiary text-sm font-semibold mb-2">{card.title}</p>
                                    {isLoading ? (
                                        <div className="skeleton h-8 w-24 mb-1" />
                                    ) : (
                                        <h3 className="text-3xl font-black text-text-primary tracking-tight">{card.value}</h3>
                                    )}
                                </div>
                                <div className={clsx("p-3 rounded-2xl bg-bg-primary shadow-sm border border-border-color", card.color)}>
                                    <card.icon className="h-6 w-6" />
                                </div>
                            </div>
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Sync Engine Gamification Panel */}
                <motion.div 
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    className="lg:col-span-2 card p-1 flex flex-col justify-between bg-bg-primary/50 backdrop-blur-xl border border-white/10 overflow-hidden"
                >
                    <div className="p-5 flex items-center justify-between border-b border-border-color/50">
                        <h2 className="text-xl font-bold flex items-center gap-2">
                            <Activity className="h-5 w-5 text-theme-primary" />
                            Live Sync Engine
                        </h2>
                        <span className="text-xs font-semibold text-theme-accent bg-theme-accent/10 px-2 py-1 rounded-md">Tier 1 Performance</span>
                    </div>
                    <div className="p-4">
                        <SyncVisualizer />
                    </div>
                    <div className="grid grid-cols-3 gap-4 p-5 bg-bg-secondary/50 rounded-b-2xl border-t border-border-color/50">
                        <div className="text-center">
                            <p className="text-text-secondary text-xs font-semibold mb-1">Queue Size</p>
                            <p className="text-lg font-bold">128</p>
                        </div>
                        <div className="text-center border-l border-r border-border-color/50">
                            <p className="text-text-secondary text-xs font-semibold mb-1">Success Rate</p>
                            <p className="text-lg font-bold text-emerald-500">99.9%</p>
                        </div>
                        <div className="text-center">
                            <p className="text-text-secondary text-xs font-semibold mb-1">Avg Latency</p>
                            <p className="text-lg font-bold text-theme-primary">42ms</p>
                        </div>
                    </div>
                </motion.div>

                {/* Quick Actions / Recent Activity */}
                <motion.div 
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.2 }}
                    className="card p-6 flex flex-col gap-6"
                >
                    <div>
                        <h2 className="text-lg font-bold mb-4">Command Center</h2>
                        <div className="grid grid-cols-2 gap-3">
                            <MotionLink whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} to="/admin/products" className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl bg-bg-secondary hover:bg-theme-primary/10 hover:text-theme-primary transition-colors border border-border-color hover:border-theme-primary/30">
                                <Package className="h-5 w-5" />
                                <span className="text-xs font-bold text-center">Manage<br/>Products</span>
                            </MotionLink>
                            <MotionLink whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} to="/admin/orders" className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl bg-bg-secondary hover:bg-blue-500/10 hover:text-blue-500 transition-colors border border-border-color hover:border-blue-500/30">
                                <ShoppingBag className="h-5 w-5" />
                                <span className="text-xs font-bold text-center">View<br/>Orders</span>
                            </MotionLink>
                            <MotionLink whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} to="/admin/customers" className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl bg-bg-secondary hover:bg-theme-accent/10 hover:text-theme-accent transition-colors border border-border-color hover:border-theme-accent/30">
                                <Users className="h-5 w-5" />
                                <span className="text-xs font-bold text-center">User<br/>Roles</span>
                            </MotionLink>
                            <MotionLink whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }} to="/admin/analytics" className="flex flex-col items-center justify-center gap-2 p-4 rounded-2xl bg-bg-secondary hover:bg-pink-500/10 hover:text-pink-500 transition-colors border border-border-color hover:border-pink-500/30">
                                <TrendingUp className="h-5 w-5" />
                                <span className="text-xs font-bold text-center">Deep<br/>Analytics</span>
                            </MotionLink>
                        </div>
                    </div>

                    <div className="flex-1 bg-gradient-to-br from-theme-primary/10 to-theme-accent/10 rounded-3xl p-5 border border-theme-primary/20 flex flex-col justify-center items-center text-center relative overflow-hidden">
                        <div className="absolute top-0 right-0 p-4 opacity-10">
                            <AlertCircle className="h-24 w-24" />
                        </div>
                        <h3 className="font-bold text-theme-primary mb-2 relative z-10">Inventory Alerts</h3>
                        <p className="text-xs text-text-secondary mb-4 relative z-10">12 items are running low across 3 stores. Replenish soon.</p>
                        <MotionLink whileHover={{ x: 5 }} to="/admin/inventory-alerts" className="text-xs font-black text-theme-accent flex items-center gap-1 uppercase tracking-wider relative z-10 cursor-pointer">
                            Review Alerts <ArrowRight className="h-3 w-3" />
                        </MotionLink>
                    </div>
                </motion.div>
            </div>
        </div>
    )
}
