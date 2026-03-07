/**
 * OfferSuggestions
 *
 * Analyses the live AnalyticsDashboard stats and produces actionable,
 * data-driven discount / promotion recommendations for shop owners.
 * No external API needed — all logic runs client-side on the existing data.
 */

import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
    Lightbulb, TrendingDown, Package, Users, ShoppingCart,
    Zap, Tag, Megaphone, Target, ChevronDown, ChevronUp, ExternalLink
} from 'lucide-react'

// ─── Types ────────────────────────────────────────────────────────────────────

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
    top_products: Array<{ id: string; name: string; sku: string; units_sold: number; revenue: number }>
    recent_orders: Array<{ id: string; order_number: string; customer_name: string; total_amount: number; status: string; created_at: string }>
    low_stock_products: number
    out_of_stock_products: number
}

interface Suggestion {
    id: string
    priority: 'high' | 'medium' | 'low'
    category: 'flash' | 'coupon' | 'bundle' | 'banner' | 'restock' | 'loyalty'
    icon: React.ElementType
    title: string
    reason: string
    action: string
    actionPath: string
    metric?: string
}

// ─── Priority colors ──────────────────────────────────────────────────────────

const PRIORITY_CFG = {
    high: { chip: 'bg-red-500/10 text-red-600 border border-red-500/20', dot: 'bg-red-500', label: 'High Priority' },
    medium: { chip: 'bg-yellow-500/10 text-yellow-600 border border-yellow-500/20', dot: 'bg-yellow-500', label: 'Medium Priority' },
    low: { chip: 'bg-green-500/10 text-green-600 border border-green-500/20', dot: 'bg-green-500', label: 'Low Priority' },
}

const CAT_COLORS: Record<Suggestion['category'], string> = {
    flash: 'bg-orange-500/10 text-orange-600',
    coupon: 'bg-theme-primary/10 text-theme-primary',
    bundle: 'bg-purple-500/10 text-purple-600',
    banner: 'bg-blue-500/10 text-blue-600',
    restock: 'bg-red-500/10 text-red-600',
    loyalty: 'bg-pink-500/10 text-pink-600',
}

// ─── Suggestion engine ────────────────────────────────────────────────────────

function buildSuggestions(stats: DashboardStats): Suggestion[] {
    const suggestions: Suggestion[] = []

    const avg_order =
        stats.today_orders > 0 ? stats.today_revenue / stats.today_orders : 0

    const week_aov =
        stats.week_orders > 0 ? stats.week_revenue / stats.week_orders : 0

    // 1. Revenue drop → flash sale
    if (stats.revenue_change < -10) {
        suggestions.push({
            id: 'rev-drop-flash',
            priority: 'high',
            category: 'flash',
            icon: Zap,
            title: 'Launch a Flash Sale to recover revenue',
            reason: `Today's revenue is down ${Math.abs(stats.revenue_change).toFixed(1)}% vs yesterday. A time-limited flash sale can quickly spike orders.`,
            action: 'Create Flash Sale',
            actionPath: '/admin/ads',
            metric: `${stats.revenue_change.toFixed(1)}% revenue change`,
        })
    }

    // 2. Orders drop → coupon push
    if (stats.orders_change < -15) {
        suggestions.push({
            id: 'orders-drop-coupon',
            priority: 'high',
            category: 'coupon',
            icon: Tag,
            title: 'Issue a discount coupon to boost order count',
            reason: `Orders are down ${Math.abs(stats.orders_change).toFixed(1)}% today. A 10-15% coupon pushed via WhatsApp/email typically converts 8-12% of browsers.`,
            action: 'Create Coupon',
            actionPath: '/admin/coupons',
            metric: `${stats.orders_change.toFixed(1)}% order change`,
        })
    }

    // 3. Low stock — urgency opportunity
    if (stats.low_stock_products > 0) {
        suggestions.push({
            id: 'low-stock-flash',
            priority: stats.low_stock_products > 10 ? 'high' : 'medium',
            category: 'flash',
            icon: Package,
            title: `Run a "Last Few Left" flash sale on ${stats.low_stock_products} low-stock item${stats.low_stock_products > 1 ? 's' : ''}`,
            reason: 'Low-stock products with urgency messaging convert 3× better. A flash sale clears inventory while maximising revenue.',
            action: 'Create Flash Sale',
            actionPath: '/admin/ads',
            metric: `${stats.low_stock_products} products low on stock`,
        })
    }

    // 4. Out-of-stock alert
    if (stats.out_of_stock_products > 0) {
        suggestions.push({
            id: 'oos-restock',
            priority: 'high',
            category: 'restock',
            icon: Package,
            title: `Restock ${stats.out_of_stock_products} out-of-stock product${stats.out_of_stock_products > 1 ? 's' : ''} — you're losing sales`,
            reason: `${stats.out_of_stock_products} products are completely out of stock. Each OOS product is an invisible revenue leak. Prioritise restocking best-sellers.`,
            action: 'View Inventory Alerts',
            actionPath: '/admin/inventory-alerts',
            metric: `${stats.out_of_stock_products} out of stock`,
        })
    }

    // 5. Low AOV → bundle / minimum discount
    if (avg_order > 0 && avg_order < 350) {
        suggestions.push({
            id: 'low-aov-bundle',
            priority: 'medium',
            category: 'bundle',
            icon: ShoppingCart,
            title: 'Offer a "Spend ₹499 & save ₹50" deal to raise AOV',
            reason: `Today's avg order is only ₹${avg_order.toFixed(0)}. A minimum-spend coupon (e.g. SAVE50 for orders ≥₹499) nudges customers to add one more item.`,
            action: 'Create Coupon',
            actionPath: '/admin/coupons',
            metric: `₹${avg_order.toFixed(0)} avg order today`,
        })
    }

    // 6. Healthy AOV but little volume → acquisition banner
    if (week_aov > 500 && stats.week_orders < 20) {
        suggestions.push({
            id: 'low-volume-banner',
            priority: 'medium',
            category: 'banner',
            icon: Megaphone,
            title: 'Set up an acquisition banner — good AOV but low traffic',
            reason: `Weekly AOV is healthy (₹${week_aov.toFixed(0)}) but only ${stats.week_orders} orders this week. A high-visibility banner or referral push could drive more top-of-funnel traffic.`,
            action: 'Create Banner',
            actionPath: '/admin/ads',
            metric: `${stats.week_orders} orders this week`,
        })
    }

    // 7. New customers down → referral / loyalty push
    if (stats.customers_change < -5) {
        suggestions.push({
            id: 'cust-drop-loyalty',
            priority: 'medium',
            category: 'loyalty',
            icon: Users,
            title: 'Activate loyalty points & referral to win back customers',
            reason: `New customer acquisition is down ${Math.abs(stats.customers_change).toFixed(1)}% today. Loyalty rewards and referral codes are proven re-engagement tools.`,
            action: 'View Coupons & Codes',
            actionPath: '/admin/coupons',
            metric: `${stats.customers_change.toFixed(1)}% customer change`,
        })
    }

    // 8. Top seller → promote it via banner
    if (stats.top_products?.length > 0) {
        const top = stats.top_products[0]
        suggestions.push({
            id: 'top-product-banner',
            priority: 'low',
            category: 'banner',
            icon: Target,
            title: `Spotlight your #1 seller "${top.name}" in a banner`,
            reason: `"${top.name}" has generated ₹${top.revenue.toLocaleString()} — featuring it prominently in a hero banner can compound its success.`,
            action: 'Create Banner',
            actionPath: '/admin/ads',
            metric: `₹${top.revenue.toLocaleString()} revenue`,
        })
    }

    // 9. Cancelled orders spike — free-shipping coupon
    const cancelled = stats.recent_orders?.filter(o => o.status === 'cancelled').length ?? 0
    const cancelRate = stats.recent_orders?.length > 0 ? cancelled / stats.recent_orders.length : 0
    if (cancelRate > 0.2) {
        suggestions.push({
            id: 'cancellations-freeship',
            priority: 'high',
            category: 'coupon',
            icon: Tag,
            title: 'High cancellation rate — offer Free Shipping to reduce drop-offs',
            reason: `${(cancelRate * 100).toFixed(0)}% of recent orders were cancelled. A free-shipping coupon at checkout is the #1 reducer of cart abandonment globally.`,
            action: 'Create Free-Shipping Coupon',
            actionPath: '/admin/coupons',
            metric: `${(cancelRate * 100).toFixed(0)}% cancellation rate`,
        })
    }

    // 10. Good week, month worse — sustain momentum
    if (stats.week_revenue > 0 && stats.month_revenue > 0) {
        const weekDaily = stats.week_revenue / 7
        const monthDaily = stats.month_revenue / 30
        if (weekDaily > monthDaily * 1.3) {
            suggestions.push({
                id: 'good-week-sustain',
                priority: 'low',
                category: 'loyalty',
                icon: TrendingDown,
                title: 'Momentum is strong — launch a loyalty reward to sustain it',
                reason: `This week is outperforming the 30-day average by ${(((weekDaily / monthDaily) - 1) * 100).toFixed(0)}%. A time-limited double-points event will lock in repeat purchases.`,
                action: 'View Coupons',
                actionPath: '/admin/coupons',
                metric: `+${(((weekDaily / monthDaily) - 1) * 100).toFixed(0)}% vs monthly avg`,
            })
        }
    }

    // Sort: high → medium → low
    const order = { high: 0, medium: 1, low: 2 }
    return suggestions.sort((a, b) => order[a.priority] - order[b.priority])
}

// ─── Component ────────────────────────────────────────────────────────────────

interface Props {
    stats: DashboardStats
}

export default function OfferSuggestions({ stats }: Props) {
    const navigate = useNavigate()
    const suggestions = useMemo(() => buildSuggestions(stats), [stats])
    const [expanded, setExpanded] = useState<string | null>(null)
    const [dismissed, setDismissed] = useState<Set<string>>(new Set<string>())

    const visible = suggestions.filter((s: Suggestion) => !dismissed.has(s.id))
    const highCount = visible.filter(s => s.priority === 'high').length

    if (visible.length === 0) return null

    return (
        <div className="mb-8">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold text-text-primary flex items-center gap-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500" />
                    AI Offer Suggestions
                    {highCount > 0 && (
                        <span className="badge bg-red-500/10 text-red-600 border border-red-500/20 text-xs">
                            {highCount} urgent
                        </span>
                    )}
                </h2>
                <span className="text-sm text-text-tertiary">{visible.length} recommendation{visible.length !== 1 ? 's' : ''} based on your sales data</span>
            </div>

            <div className="space-y-3">
                {visible.map((s: Suggestion) => {
                    const p = PRIORITY_CFG[s.priority]
                    const Icon: any = s.icon
                    const open = expanded === s.id
                    return (
                        <div
                            key={s.id}
                            className={`card border transition-all duration-200 ${s.priority === 'high' ? 'border-red-500/20' : 'border-border-color'
                                }`}
                        >
                            <div className="flex items-start gap-3">
                                {/* Icon */}
                                <div className={`flex-shrink-0 p-2.5 rounded-xl ${CAT_COLORS[s.category]}`}>
                                    <Icon className={"h-5 w-5" as any} />
                                </div>

                                {/* Body */}
                                <div className="flex-1 min-w-0">
                                    <div className="flex items-start justify-between gap-2">
                                        <div>
                                            <div className="flex items-center gap-2 flex-wrap mb-1">
                                                <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${p.chip}`}>
                                                    <span className={`h-1.5 w-1.5 rounded-full ${p.dot}`} />
                                                    {p.label}
                                                </span>
                                                {s.metric && (
                                                    <span className="text-xs text-text-tertiary bg-bg-tertiary rounded-full px-2 py-0.5 border border-border-color">
                                                        {s.metric}
                                                    </span>
                                                )}
                                            </div>
                                            <p className="font-semibold text-text-primary text-sm">{s.title}</p>
                                        </div>
                                        <button
                                            onClick={() => setExpanded(open ? null : s.id)}
                                            className="text-text-tertiary hover:text-text-secondary flex-shrink-0 mt-0.5"
                                            aria-label={open ? 'Collapse' : 'Expand'}
                                        >
                                            {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                        </button>
                                    </div>

                                    {/* Expanded reason + actions */}
                                    {open && (
                                        <div className="mt-3 space-y-3 animate-fade-in">
                                            <p className="text-sm text-text-secondary leading-relaxed">{s.reason}</p>
                                            <div className="flex items-center gap-2 flex-wrap">
                                                <button
                                                    onClick={() => navigate(s.actionPath)}
                                                    className="btn btn-sm btn-primary gap-1.5"
                                                >
                                                    <ExternalLink className="h-3.5 w-3.5" />
                                                    {s.action}
                                                </button>
                                                <button
                                                    onClick={() => setDismissed(d => new Set([...d, s.id]))}
                                                    className="btn btn-sm btn-ghost text-text-tertiary"
                                                >
                                                    Dismiss
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Collapsed quick action */}
                                    {!open && (
                                        <div className="flex items-center gap-2 mt-2">
                                            <button
                                                onClick={() => navigate(s.actionPath)}
                                                className="text-sm text-theme-primary font-medium hover:underline flex items-center gap-1"
                                            >
                                                {s.action} →
                                            </button>
                                            <span className="text-text-tertiary text-xs">·</span>
                                            <button
                                                onClick={() => setDismissed(d => new Set([...d, s.id]))}
                                                className="text-xs text-text-tertiary hover:text-text-secondary"
                                            >
                                                Dismiss
                                            </button>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}
