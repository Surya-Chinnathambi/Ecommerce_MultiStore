import { useState, useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { Users, IndianRupee, ShoppingBag, Phone, Mail, CalendarDays } from 'lucide-react'
import PageHeader from '@/components/ui/PageHeader'
import FilterBar from '@/components/ui/FilterBar'
import DataGrid from '@/components/ui/DataGrid'
import EmptyState from '@/components/ui/EmptyState'
import Button from '@/components/ui/Button'

interface CustomerSummary {
    name: string
    phone: string
    email: string
    orderCount: number
    totalSpent: number
    lastOrderDate: string
}

function buildCustomers(orders: any[]): CustomerSummary[] {
    const map = new Map<string, CustomerSummary>()
    for (const o of orders) {
        const key = o.customer_phone || o.customer_email || o.customer_name
        if (!key) continue
        const existing = map.get(key)
        if (existing) {
            existing.orderCount++
            existing.totalSpent += o.total_amount ?? 0
            if (o.created_at > existing.lastOrderDate) existing.lastOrderDate = o.created_at
        } else {
            map.set(key, {
                name: o.customer_name || '—',
                phone: o.customer_phone || '—',
                email: o.customer_email || '—',
                orderCount: 1,
                totalSpent: o.total_amount ?? 0,
                lastOrderDate: o.created_at,
            })
        }
    }
    return Array.from(map.values()).sort((a, b) => b.totalSpent - a.totalSpent)
}

const storeId = () => localStorage.getItem('store_id') ?? ''

export default function AdminCustomersPage() {
    const [search, setSearch] = useState('')

    const { data: ordersData, isLoading } = useQuery({
        queryKey: ['admin-customers-orders'],
        queryFn: () =>
            adminApi.getAdminOrders({ store_id: storeId(), per_page: 500, page: 1 })
                .then(r => r.data.data?.orders ?? []),
    })

    const customers = useMemo(() => buildCustomers(ordersData ?? []), [ordersData])

    const filtered = useMemo(() => {
        if (!search.trim()) return customers
        const q = search.toLowerCase()
        return customers.filter(c =>
            c.name.toLowerCase().includes(q) ||
            c.phone.includes(q) ||
            c.email.toLowerCase().includes(q)
        )
    }, [customers, search])

    const totalRevenue = customers.reduce((s, c) => s + c.totalSpent, 0)

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            {/* Header */}
            <PageHeader
                title="Customers"
                subtitle={`${customers.length} unique customers · ₹${totalRevenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })} total revenue`}
            />
            <FilterBar
                className="mb-6"
                searchValue={search}
                onSearchChange={setSearch}
                searchPlaceholder="Name, phone or email…"
                searchWidthClassName="w-full"
            />

            {/* Summary strip */}
            <div className="grid grid-cols-3 gap-4 mb-6">
                {[
                    { label: 'Total Customers', value: customers.length, Icon: Users, color: 'text-cyan-500', bg: 'bg-cyan-500/10' },
                    { label: 'Total Revenue', value: `₹${totalRevenue.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`, Icon: IndianRupee, color: 'text-green-500', bg: 'bg-green-500/10' },
                    {
                        label: 'Avg. Order Value', value: customers.length
                            ? `₹${Math.round(totalRevenue / customers.reduce((s, c) => s + c.orderCount, 0)).toLocaleString('en-IN')}`
                            : '—', Icon: ShoppingBag, color: 'text-purple-500', bg: 'bg-purple-500/10'
                    },
                ].map(({ label, value, Icon, color, bg }) => (
                    <div key={label} className="card text-center py-4">
                        <div className={`inline-flex items-center justify-center w-10 h-10 rounded-xl ${bg} mb-2 mx-auto`}>
                            <Icon className={`h-5 w-5 ${color}`} />
                        </div>
                        <div className={`text-xl font-black ${color}`}>{value}</div>
                        <div className="text-xs text-text-tertiary mt-0.5">{label}</div>
                    </div>
                ))}
            </div>

            {/* Customer list */}
            <DataGrid
                loading={isLoading}
                isEmpty={filtered.length === 0}
                loadingState={
                    <div className="space-y-3 p-4">
                        {[...Array(8)].map((_, i) => <div key={i} className="skeleton h-16 rounded-xl" />)}
                    </div>
                }
                emptyState={
                    <EmptyState
                        icon={<Users className="h-12 w-12" />}
                        title={search ? 'No customers match your search' : 'No customer data yet'}
                        action={search ? <Button type="button" variant="outline" size="sm" onClick={() => setSearch('')}>Clear Search</Button> : undefined}
                    />
                }
            >
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-border-color bg-bg-tertiary text-text-secondary text-xs uppercase tracking-wider">
                            <th className="text-left pl-4 py-3">Customer</th>
                            <th className="text-left px-3 py-3">Contact</th>
                            <th className="text-right px-3 py-3">Orders</th>
                            <th className="text-right px-3 py-3">Total Spent</th>
                            <th className="text-right px-3 py-3">Avg. Order</th>
                            <th className="text-right px-3 pr-4 py-3">Last Order</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border-color">
                        {filtered.map((c, i) => (
                            <tr key={`${c.phone}-${i}`} className="hover:bg-bg-tertiary/50 transition-colors">
                                <td className="pl-4 py-3">
                                    <div className="flex items-center gap-3">
                                        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-theme-primary to-theme-accent flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                                            {c.name.charAt(0).toUpperCase()}
                                        </div>
                                        <span className="font-medium text-text-primary">{c.name}</span>
                                    </div>
                                </td>
                                <td className="px-3 py-3">
                                    <div className="space-y-0.5">
                                        {c.phone !== '—' && (
                                            <div className="flex items-center gap-1 text-text-secondary">
                                                <Phone className="h-3 w-3 flex-shrink-0" />
                                                <span className="text-xs">{c.phone}</span>
                                            </div>
                                        )}
                                        {c.email !== '—' && (
                                            <div className="flex items-center gap-1 text-text-tertiary">
                                                <Mail className="h-3 w-3 flex-shrink-0" />
                                                <span className="text-xs truncate max-w-[160px]">{c.email}</span>
                                            </div>
                                        )}
                                    </div>
                                </td>
                                <td className="px-3 py-3 text-right">
                                    <span className="font-semibold text-text-primary">{c.orderCount}</span>
                                </td>
                                <td className="px-3 py-3 text-right font-bold text-green-600">
                                    ₹{c.totalSpent.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                                </td>
                                <td className="px-3 py-3 text-right text-text-secondary">
                                    ₹{Math.round(c.totalSpent / c.orderCount).toLocaleString('en-IN')}
                                </td>
                                <td className="px-3 pr-4 py-3 text-right">
                                    <div className="flex items-center justify-end gap-1 text-text-tertiary">
                                        <CalendarDays className="h-3 w-3" />
                                        <span className="text-xs">
                                            {new Date(c.lastOrderDate).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}
                                        </span>
                                    </div>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </DataGrid>
        </div>
    )
}
