import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { RefreshCw, CheckCircle, XCircle, Truck, Package, AlertCircle, ChevronDown } from 'lucide-react'
import { api } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'

interface ReturnItem {
    product_name: string
    quantity: number
    refund_amount: number
}

interface ReturnRequest {
    id: string
    return_number: string
    order_id: string
    order_number: string
    status: string
    reason: string
    description?: string
    total_refund_amount: number
    refund_method?: string
    tracking_id?: string
    admin_notes?: string
    created_at: string
    user: { full_name: string; email: string }
    items: ReturnItem[]
}

const STATUS_OPTIONS = ['all', 'pending', 'approved', 'rejected', 'picked_up', 'refunded'] as const
type AdminAction = 'approve' | 'reject' | 'schedule_pickup' | 'mark_picked_up' | 'refund'

const statusBadge = (s: string) => {
    const map: Record<string, string> = {
        pending: 'bg-yellow-100 text-yellow-700',
        approved: 'bg-blue-100 text-blue-700',
        rejected: 'bg-red-100 text-red-700',
        picked_up: 'bg-purple-100 text-purple-700',
        refunded: 'bg-green-100 text-green-700',
    }
    return `px-2 py-0.5 rounded-full text-xs font-medium capitalize ${map[s] ?? 'bg-gray-100 text-gray-600'}`
}

export default function AdminReturnsPage() {
    const qc = useQueryClient()
    const [statusFilter, setStatusFilter] = useState<string>('all')
    const [expanded, setExpanded] = useState<string | null>(null)
    const [actionPayload, setActionPayload] = useState<Record<string, string>>({})

    const { data, isLoading } = useQuery({
        queryKey: ['admin-returns', statusFilter],
        queryFn: () =>
            api.get('/returns/admin/list', {
                params: { status: statusFilter === 'all' ? undefined : statusFilter, page: 1, per_page: 50 },
            }).then((r) => r.data.data),
    })

    const returns: ReturnRequest[] = data?.returns ?? data ?? []

    const actionMutation = useMutation({
        mutationFn: ({ id, action, payload }: { id: string; action: string; payload: Record<string, string> }) =>
            api.post(`/returns/admin/${id}/process`, { action, ...payload }),
        onSuccess: (_, vars) => {
            toast.success(`Return ${vars.action.replace('_', ' ')} successfully`)
            qc.invalidateQueries({ queryKey: ['admin-returns'] })
            setActionPayload({})
        },
        onError: (e: unknown) => {
            const err = e as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail ?? 'Action failed')
        },
    })

    const doAction = (id: string, action: AdminAction) => {
        actionMutation.mutate({ id, action, payload: actionPayload })
    }

    const nextActions = (status: string): { label: string; action: AdminAction; color: string }[] => {
        const actionMap: Record<string, { label: string; action: AdminAction; color: string }[]> = {
            pending: [
                { label: 'Approve', action: 'approve', color: 'btn-primary' },
                { label: 'Reject', action: 'reject', color: 'btn-danger' },
            ],
            approved: [
                { label: 'Schedule Pickup', action: 'schedule_pickup', color: 'btn-secondary' },
            ],
            picked_up: [
                { label: 'Mark Received', action: 'mark_picked_up', color: 'btn-secondary' },
            ],
            mark_picked_up: [
                { label: 'Issue Refund', action: 'refund', color: 'btn-primary' },
            ],
        }
        return actionMap[status] ?? []
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <RefreshCw className="h-6 w-6 text-theme-primary" />
                    <h1 className="text-2xl font-bold text-text-primary">Return Requests</h1>
                    <span className="text-sm text-text-tertiary">({returns.length} shown)</span>
                </div>
                {/* Status filter */}
                <div className="flex gap-2 flex-wrap">
                    {STATUS_OPTIONS.map((s) => (
                        <button
                            key={s}
                            onClick={() => setStatusFilter(s)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors capitalize
                                ${statusFilter === s ? 'bg-theme-primary text-white border-theme-primary' : 'bg-bg-primary text-text-secondary border-border-color hover:border-theme-primary/40'}`}
                        >
                            {s === 'all' ? 'All' : s.replace('_', ' ')}
                        </button>
                    ))}
                </div>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center h-40">
                    <div className="h-8 w-8 border-2 border-theme-primary border-t-transparent rounded-full animate-spin" />
                </div>
            ) : returns.length === 0 ? (
                <div className="text-center py-16 text-text-tertiary">
                    <Package className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>No return requests found for this filter.</p>
                </div>
            ) : (
                <div className="space-y-3">
                    {returns.map((r) => (
                        <div key={r.id} className="bg-bg-primary border border-border-color rounded-xl overflow-hidden">
                            {/* Summary row */}
                            <button
                                onClick={() => setExpanded(expanded === r.id ? null : r.id)}
                                className="w-full flex items-center gap-4 px-5 py-4 text-left hover:bg-bg-tertiary/30 transition-colors"
                            >
                                <div className="flex-1 grid grid-cols-2 md:grid-cols-5 gap-3 text-sm">
                                    <div>
                                        <p className="font-semibold text-text-primary">{r.return_number}</p>
                                        <p className="text-xs text-text-tertiary">{new Date(r.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary text-xs">Order</p>
                                        <p className="font-medium">{r.order_number}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary text-xs">Customer</p>
                                        <p className="font-medium truncate">{r.user?.full_name}</p>
                                    </div>
                                    <div>
                                        <p className="text-text-secondary text-xs">Refund</p>
                                        <p className="font-semibold text-green-600">₹{r.total_refund_amount?.toLocaleString()}</p>
                                    </div>
                                    <div className="flex items-center">
                                        <span className={statusBadge(r.status)}>{r.status.replace('_', ' ')}</span>
                                    </div>
                                </div>
                                <ChevronDown className={`h-4 w-4 text-text-tertiary flex-shrink-0 transition-transform ${expanded === r.id ? 'rotate-180' : ''}`} />
                            </button>

                            {/* Expanded detail */}
                            {expanded === r.id && (
                                <div className="border-t border-border-color px-5 py-4 bg-bg-secondary/30">
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                        {/* Items */}
                                        <div>
                                            <h4 className="text-sm font-semibold text-text-primary mb-2">Return Items</h4>
                                            <table className="w-full text-xs">
                                                <thead>
                                                    <tr className="text-text-tertiary">
                                                        <th className="text-left pb-1">Product</th>
                                                        <th className="text-center pb-1">Qty</th>
                                                        <th className="text-right pb-1">Refund</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-border-color">
                                                    {r.items.map((item, i) => (
                                                        <tr key={i}>
                                                            <td className="py-1.5 text-text-primary">{item.product_name}</td>
                                                            <td className="py-1.5 text-center text-text-secondary">{item.quantity}</td>
                                                            <td className="py-1.5 text-right font-medium text-green-600">₹{item.refund_amount?.toLocaleString()}</td>
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                            {r.description && (
                                                <div className="mt-3 p-3 bg-bg-tertiary rounded-lg text-xs text-text-secondary">
                                                    <p className="font-medium mb-1">Customer note:</p>
                                                    <p>{r.description}</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* Actions panel */}
                                        <div>
                                            <h4 className="text-sm font-semibold text-text-primary mb-3">Admin Actions</h4>

                                            {/* Admin notes */}
                                            <div className="mb-3">
                                                <label className="block text-xs text-text-secondary mb-1">Admin Notes</label>
                                                <textarea
                                                    rows={2}
                                                    className="w-full px-3 py-2 bg-bg-secondary border border-border-color rounded-lg text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-theme-primary/40"
                                                    placeholder="Notes visible to customer..."
                                                    value={actionPayload.admin_notes ?? r.admin_notes ?? ''}
                                                    onChange={(e) => setActionPayload({ ...actionPayload, admin_notes: e.target.value })}
                                                />
                                            </div>

                                            {/* Tracking ID for pickup */}
                                            {(r.status === 'approved') && (
                                                <div className="mb-3">
                                                    <label className="block text-xs text-text-secondary mb-1">Tracking ID (for pickup)</label>
                                                    <input
                                                        className="w-full px-3 py-2 bg-bg-secondary border border-border-color rounded-lg text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-theme-primary/40"
                                                        placeholder="AWB / tracking number..."
                                                        value={actionPayload.tracking_id ?? ''}
                                                        onChange={(e) => setActionPayload({ ...actionPayload, tracking_id: e.target.value })}
                                                    />
                                                </div>
                                            )}

                                            {/* Refund method */}
                                            {(r.status === 'picked_up' || r.status === 'mark_picked_up') && (
                                                <div className="mb-3">
                                                    <label className="block text-xs text-text-secondary mb-1">Refund Method</label>
                                                    <select
                                                        title="Refund method"
                                                        className="w-full px-3 py-2 bg-bg-secondary border border-border-color rounded-lg text-xs text-text-primary focus:outline-none"
                                                        value={actionPayload.refund_method ?? 'original_payment'}
                                                        onChange={(e) => setActionPayload({ ...actionPayload, refund_method: e.target.value })}
                                                    >
                                                        <option value="original_payment">Original Payment Method</option>
                                                        <option value="store_credit">Store Credit</option>
                                                        <option value="bank_transfer">Bank Transfer</option>
                                                        <option value="upi">UPI</option>
                                                    </select>
                                                </div>
                                            )}

                                            {/* Action buttons */}
                                            <div className="flex gap-2 flex-wrap">
                                                {nextActions(r.status).map(({ label, action, color }) => (
                                                    <button
                                                        key={action}
                                                        disabled={actionMutation.isPending}
                                                        onClick={() => doAction(r.id, action)}
                                                        className={`btn ${color} text-xs px-4 py-2 flex items-center gap-1.5`}
                                                    >
                                                        {action === 'approve' && <CheckCircle className="h-3.5 w-3.5" />}
                                                        {action === 'reject' && <XCircle className="h-3.5 w-3.5" />}
                                                        {(action === 'schedule_pickup' || action === 'mark_picked_up') && <Truck className="h-3.5 w-3.5" />}
                                                        {action === 'refund' && <CheckCircle className="h-3.5 w-3.5" />}
                                                        {label}
                                                    </button>
                                                ))}
                                            </div>

                                            {r.status === 'refunded' && (
                                                <div className="flex items-center gap-2 text-green-600 text-sm mt-2">
                                                    <CheckCircle className="h-4 w-4" />
                                                    Refund issued via {r.refund_method ?? 'original payment'}
                                                </div>
                                            )}

                                            {r.status === 'rejected' && r.admin_notes && (
                                                <div className="flex items-start gap-2 text-red-600 text-xs mt-2 p-2 bg-red-50 rounded-lg">
                                                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                                                    {r.admin_notes}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}
