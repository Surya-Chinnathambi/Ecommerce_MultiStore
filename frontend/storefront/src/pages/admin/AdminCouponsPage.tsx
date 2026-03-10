import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Tag, Plus, Edit2, Trash2, Check, Calendar, DollarSign, Users, Percent } from 'lucide-react'
import { couponsApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import DataGrid from '@/components/ui/DataGrid'
import EmptyState from '@/components/ui/EmptyState'
import RowActions, { RowActionButton } from '@/components/ui/RowActions'
import Modal, { ModalBody, ModalHeader } from '@/components/ui/Modal'

interface Coupon {
    id: string
    code: string
    discount_type: 'PERCENT' | 'FLAT' | 'FREE_SHIPPING' | 'BUY_X_GET_Y'
    discount_value: number
    min_order_amount: number
    max_discount_amount?: number
    usage_limit?: number
    per_user_limit: number
    used_count: number
    is_active: boolean
    valid_from?: string
    valid_until?: string
    description?: string
}

const DISCOUNT_TYPES = ['PERCENT', 'FLAT', 'FREE_SHIPPING', 'BUY_X_GET_Y'] as const

const emptyForm = {
    code: '',
    discount_type: 'PERCENT' as Coupon['discount_type'],
    discount_value: 10,
    min_order_amount: 0,
    max_discount_amount: '',
    usage_limit: '',
    per_user_limit: 1,
    valid_from: '',
    valid_until: '',
    description: '',
    is_active: true,
}

export default function AdminCouponsPage() {
    const qc = useQueryClient()
    const [showForm, setShowForm] = useState(false)
    const [editId, setEditId] = useState<string | null>(null)
    const [form, setForm] = useState({ ...emptyForm })

    const { data, isLoading } = useQuery({
        queryKey: ['admin-coupons'],
        queryFn: () => couponsApi.listCoupons(1).then((r) => r.data.data),
    })

    const coupons: Coupon[] = data?.coupons ?? data ?? []

    const saveMutation = useMutation({
        mutationFn: (payload: Record<string, unknown>) =>
            editId ? couponsApi.updateCoupon(editId, payload) : couponsApi.createCoupon(payload),
        onSuccess: () => {
            toast.success(editId ? 'Coupon updated' : 'Coupon created')
            qc.invalidateQueries({ queryKey: ['admin-coupons'] })
            setShowForm(false)
            setEditId(null)
            setForm({ ...emptyForm })
        },
        onError: (e: unknown) => {
            const err = e as { response?: { data?: { detail?: string } } }
            toast.error(err.response?.data?.detail ?? 'Failed to save coupon')
        },
    })

    const deactivateMutation = useMutation({
        mutationFn: (id: string) => couponsApi.deactivateCoupon(id),
        onSuccess: () => {
            toast.success('Coupon deactivated')
            qc.invalidateQueries({ queryKey: ['admin-coupons'] })
        },
    })

    const openCreate = () => {
        setEditId(null)
        setForm({ ...emptyForm })
        setShowForm(true)
    }

    const openEdit = (c: Coupon) => {
        setEditId(c.id)
        setForm({
            code: c.code,
            discount_type: c.discount_type,
            discount_value: c.discount_value,
            min_order_amount: c.min_order_amount,
            max_discount_amount: c.max_discount_amount?.toString() ?? '',
            usage_limit: c.usage_limit?.toString() ?? '',
            per_user_limit: c.per_user_limit,
            valid_from: c.valid_from ? c.valid_from.slice(0, 10) : '',
            valid_until: c.valid_until ? c.valid_until.slice(0, 10) : '',
            description: c.description ?? '',
            is_active: c.is_active,
        })
        setShowForm(true)
    }

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const payload: Record<string, unknown> = {
            code: form.code.toUpperCase(),
            discount_type: form.discount_type,
            discount_value: Number(form.discount_value),
            min_order_amount: Number(form.min_order_amount),
            per_user_limit: Number(form.per_user_limit),
            is_active: form.is_active,
            description: form.description || undefined,
        }
        if (form.max_discount_amount) payload.max_discount_amount = Number(form.max_discount_amount)
        if (form.usage_limit) payload.usage_limit = Number(form.usage_limit)
        if (form.valid_from) payload.valid_from = new Date(form.valid_from).toISOString()
        if (form.valid_until) payload.valid_until = new Date(form.valid_until).toISOString()
        saveMutation.mutate(payload)
    }

    const inputClass =
        'w-full px-3 py-2 bg-bg-secondary border border-border-color rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-theme-primary/40'

    const discountTypeBadge = (t: string) => {
        const map: Record<string, string> = {
            PERCENT: 'bg-blue-100 text-blue-700',
            FLAT: 'bg-green-100 text-green-700',
            FREE_SHIPPING: 'bg-purple-100 text-purple-700',
            BUY_X_GET_Y: 'bg-orange-100 text-orange-700',
        }
        return `px-2 py-0.5 rounded-full text-xs font-medium ${map[t] ?? 'bg-gray-100 text-gray-700'}`
    }

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <Tag className="h-6 w-6 text-theme-primary" />
                    <h1 className="text-2xl font-bold text-text-primary">Coupon Management</h1>
                    <span className="text-sm text-text-tertiary">({coupons.length} coupons)</span>
                </div>
                <button onClick={openCreate} className="btn btn-primary flex items-center gap-2">
                    <Plus className="h-4 w-4" /> Create Coupon
                </button>
            </div>

            {/* Form modal */}
            {showForm && (
                <Modal open={showForm} onClose={() => setShowForm(false)} maxWidthClassName="max-w-lg">
                    <ModalHeader
                        title={editId ? 'Edit Coupon' : 'Create New Coupon'}
                        onClose={() => setShowForm(false)}
                    />
                    <ModalBody className="p-5">
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div className="col-span-2">
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Coupon Code *</label>
                                    <input
                                        required
                                        className={inputClass + ' uppercase font-mono'}
                                        value={form.code}
                                        onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })}
                                        placeholder="SAVE20"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Discount Type *</label>
                                    <select title="Discount type" className={inputClass} value={form.discount_type}
                                        onChange={(e) => setForm({ ...form, discount_type: e.target.value as Coupon['discount_type'] })}>
                                        {DISCOUNT_TYPES.map((t) => <option key={t} value={t}>{t.replace('_', ' ')}</option>)}
                                    </select>
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">
                                        {form.discount_type === 'PERCENT' ? 'Discount %' : 'Discount ₹'} *
                                    </label>
                                    <input type="number" required min={0} title="Discount value" placeholder="0" className={inputClass} value={form.discount_value}
                                        onChange={(e) => setForm({ ...form, discount_value: Number(e.target.value) })} />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Min Order Amount (₹)</label>
                                    <input type="number" min={0} title="Minimum order amount" placeholder="0" className={inputClass} value={form.min_order_amount}
                                        onChange={(e) => setForm({ ...form, min_order_amount: Number(e.target.value) })} />
                                </div>
                                {form.discount_type === 'PERCENT' && (
                                    <div>
                                        <label className="block text-xs font-medium text-text-secondary mb-1">Max Discount Cap (₹)</label>
                                        <input type="number" min={0} className={inputClass} value={form.max_discount_amount}
                                            onChange={(e) => setForm({ ...form, max_discount_amount: e.target.value })} placeholder="No cap" />
                                    </div>
                                )}
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Total Usage Limit</label>
                                    <input type="number" min={1} className={inputClass} value={form.usage_limit}
                                        onChange={(e) => setForm({ ...form, usage_limit: e.target.value })} placeholder="Unlimited" />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Per User Limit</label>
                                    <input type="number" min={1} required title="Per user limit" placeholder="1" className={inputClass} value={form.per_user_limit}
                                        onChange={(e) => setForm({ ...form, per_user_limit: Number(e.target.value) })} />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Valid From</label>
                                    <input type="date" title="Valid from date" className={inputClass} value={form.valid_from}
                                        onChange={(e) => setForm({ ...form, valid_from: e.target.value })} />
                                </div>
                                <div>
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Valid Until</label>
                                    <input type="date" title="Valid until date" className={inputClass} value={form.valid_until}
                                        onChange={(e) => setForm({ ...form, valid_until: e.target.value })} />
                                </div>
                                <div className="col-span-2">
                                    <label className="block text-xs font-medium text-text-secondary mb-1">Description</label>
                                    <textarea rows={2} className={inputClass} value={form.description}
                                        onChange={(e) => setForm({ ...form, description: e.target.value })}
                                        placeholder="Internal note about this coupon..." />
                                </div>
                                <div className="col-span-2 flex items-center gap-2">
                                    <input type="checkbox" id="is_active" checked={form.is_active}
                                        onChange={(e) => setForm({ ...form, is_active: e.target.checked })}
                                        className="h-4 w-4 rounded accent-theme-primary" />
                                    <label htmlFor="is_active" className="text-sm text-text-primary">Active</label>
                                </div>
                            </div>
                            <div className="flex gap-3 pt-2">
                                <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary flex-1">Cancel</button>
                                <button type="submit" disabled={saveMutation.isPending} className="btn btn-primary flex-1 flex items-center justify-center gap-2">
                                    {saveMutation.isPending ? (
                                        <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                                    ) : (
                                        <Check className="h-4 w-4" />
                                    )}
                                    {editId ? 'Update' : 'Create'}
                                </button>
                            </div>
                        </form>
                    </ModalBody>
                </Modal>
            )}

            {/* Table */}
            <DataGrid
                className="bg-bg-primary border border-border-color rounded-xl overflow-hidden"
                loading={isLoading}
                isEmpty={coupons.length === 0}
                loadingState={
                    <div className="flex items-center justify-center h-40">
                        <div className="h-8 w-8 border-2 border-theme-primary border-t-transparent rounded-full animate-spin" />
                    </div>
                }
                emptyState={
                    <EmptyState
                        icon={<Tag className="h-12 w-12 opacity-30" />}
                        title="No coupons yet"
                        description="Create your first coupon to run promotions."
                    />
                }
            >
                <table className="w-full text-sm">
                    <thead>
                        <tr className="border-b border-border-color bg-bg-secondary/50">
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Code</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Type</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Value</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Min Order</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Usage</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Validity</th>
                            <th className="text-left px-4 py-3 text-text-secondary font-medium">Status</th>
                            <th className="text-right px-4 py-3 text-text-secondary font-medium">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border-color">
                        {coupons.map((c) => (
                            <tr key={c.id} className="hover:bg-bg-tertiary/40 transition-colors">
                                <td className="px-4 py-3">
                                    <span className="font-mono font-semibold text-theme-primary">{c.code}</span>
                                    {c.description && <p className="text-xs text-text-tertiary mt-0.5 truncate max-w-32">{c.description}</p>}
                                </td>
                                <td className="px-4 py-3">
                                    <span className={discountTypeBadge(c.discount_type)}>{c.discount_type.replace('_', ' ')}</span>
                                </td>
                                <td className="px-4 py-3 font-medium">
                                    {c.discount_type === 'PERCENT' ? (
                                        <span className="flex items-center gap-1"><Percent className="h-3 w-3" />{c.discount_value}%</span>
                                    ) : c.discount_type === 'FREE_SHIPPING' ? (
                                        <span className="text-purple-600">Free Ship</span>
                                    ) : (
                                        <span className="flex items-center gap-1"><DollarSign className="h-3 w-3" />₹{c.discount_value}</span>
                                    )}
                                </td>
                                <td className="px-4 py-3 text-text-secondary">
                                    {c.min_order_amount > 0 ? `₹${c.min_order_amount}` : '—'}
                                </td>
                                <td className="px-4 py-3">
                                    <div className="flex items-center gap-1 text-text-secondary">
                                        <Users className="h-3.5 w-3.5" />
                                        {c.used_count}/{c.usage_limit ?? '∞'}
                                    </div>
                                </td>
                                <td className="px-4 py-3 text-text-tertiary text-xs">
                                    {c.valid_from || c.valid_until ? (
                                        <div className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {c.valid_from ? new Date(c.valid_from).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) : '∞'}
                                            {' → '}
                                            {c.valid_until ? new Date(c.valid_until).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: '2-digit' }) : '∞'}
                                        </div>
                                    ) : '—'}
                                </td>
                                <td className="px-4 py-3">
                                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${c.is_active ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                                        {c.is_active ? 'Active' : 'Inactive'}
                                    </span>
                                </td>
                                <td className="px-4 py-3">
                                    <RowActions>
                                        <RowActionButton onClick={() => openEdit(c)} title="Edit" aria-label="Edit coupon" iconOnly icon={<Edit2 className="h-4 w-4" />} />
                                        {c.is_active && (
                                            <RowActionButton
                                                onClick={() => { if (confirm('Deactivate this coupon?')) deactivateMutation.mutate(c.id) }}
                                                tone="danger"
                                                title="Deactivate"
                                                aria-label="Deactivate coupon"
                                                iconOnly
                                                icon={<Trash2 className="h-4 w-4" />}
                                            />
                                        )}
                                    </RowActions>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </DataGrid>
        </div>
    )
}
