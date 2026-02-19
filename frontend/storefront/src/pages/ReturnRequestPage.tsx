import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { orderApi, returnsApi } from '@/lib/api'
import { RotateCcw, Package, ChevronRight, AlertCircle } from 'lucide-react'
import { toast } from '@/components/ui/Toaster'

const RETURN_REASONS = [
    { value: 'defective', label: 'Product is defective / damaged' },
    { value: 'wrong_item', label: 'Wrong item received' },
    { value: 'not_as_described', label: 'Not as described' },
    { value: 'missing_parts', label: 'Missing parts / accessories' },
    { value: 'quality_issue', label: 'Quality not satisfactory' },
    { value: 'changed_mind', label: 'Changed my mind' },
    { value: 'other', label: 'Other reason' },
]

export default function ReturnRequestPage() {
    const { orderId } = useParams()
    const navigate = useNavigate()

    const [step, setStep] = useState(1)
    const [reason, setReason] = useState('')
    const [description, setDescription] = useState('')
    const [selectedItems, setSelectedItems] = useState<Record<string, number>>({})
    const [submitting, setSubmitting] = useState(false)

    const { data: orderData, isLoading } = useQuery({
        queryKey: ['order-for-return', orderId],
        queryFn: () => orderApi.getOrder(orderId!).then((r) => r.data.data),
        enabled: !!orderId,
    })

    const toggleItem = (itemId: string, qty: number) => {
        setSelectedItems((prev) => {
            const n = { ...prev }
            if (n[itemId]) delete n[itemId]
            else n[itemId] = qty
            return n
        })
    }

    const handleSubmit = async () => {
        if (!reason) { toast.error('Please select a reason'); return }
        const items = Object.entries(selectedItems).map(([id, q]) => ({
            order_item_id: id,
            quantity: q,
        }))
        setSubmitting(true)
        try {
            const res = await returnsApi.createReturn({
                order_id: orderId!,
                reason,
                description,
                items: items.length > 0 ? items : undefined,
            })
            const ret = res.data.data
            toast.success(`Return #${ret.return_number} created successfully`)
            navigate(`/returns/${ret.id}`)
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Failed to create return request')
        } finally {
            setSubmitting(false)
        }
    }

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="skeleton h-8 w-48 rounded-lg mb-6" />
                <div className="skeleton rounded-2xl h-64" />
            </div>
        )
    }

    if (!orderData) {
        return (
            <div className="container mx-auto px-4 py-16">
                <div className="empty-state">
                    <Package className="empty-state-icon" />
                    <h2 className="empty-state-title">Order not found</h2>
                    <Link to="/my-orders" className="btn btn-primary">Back to Orders</Link>
                </div>
            </div>
        )
    }

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8 max-w-2xl">
                {/* Header */}
                <div className="flex items-center gap-3 mb-8">
                    <div className="p-3 rounded-2xl bg-orange-100 dark:bg-orange-900/20">
                        <RotateCcw className="h-6 w-6 text-orange-500" />
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-text-primary">Return Request</h1>
                        <p className="text-text-secondary text-sm">Order #{orderData.order_number}</p>
                    </div>
                </div>

                {/* Step 1: Select items */}
                {step === 1 && (
                    <div className="card p-6">
                        <h2 className="text-lg font-bold text-text-primary mb-4">Select Items to Return</h2>
                        <p className="text-sm text-text-secondary mb-4">
                            All items are selected by default. Deselect any you are keeping.
                        </p>
                        <div className="space-y-3">
                            {orderData.items?.map((item: any) => {
                                const checked = !!selectedItems[item.id] || Object.keys(selectedItems).length === 0
                                return (
                                    <label key={item.id}
                                        className={`flex items-center gap-4 p-4 rounded-xl border-2 cursor-pointer transition-all
                                            ${checked ? 'border-theme-primary bg-theme-primary/5' : 'border-border-color'}`}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={selectedItems[item.id] !== undefined
                                                ? !!selectedItems[item.id]
                                                : true}
                                            onChange={() => toggleItem(item.id, item.quantity)}
                                            className="accent-theme-primary w-4 h-4"
                                        />
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium text-text-primary truncate">{item.product_name}</p>
                                            <p className="text-sm text-text-secondary">
                                                Qty: {item.quantity} × ₹{item.unit_price?.toLocaleString()}
                                            </p>
                                        </div>
                                        <span className="font-bold text-text-primary">
                                            ₹{(item.unit_price * item.quantity).toLocaleString()}
                                        </span>
                                    </label>
                                )
                            })}
                        </div>
                        <button onClick={() => setStep(2)} className="w-full btn btn-primary mt-6">
                            Continue
                            <ChevronRight className="h-4 w-4" />
                        </button>
                    </div>
                )}

                {/* Step 2: Reason */}
                {step === 2 && (
                    <div className="card p-6">
                        <h2 className="text-lg font-bold text-text-primary mb-4">Why are you returning?</h2>
                        <div className="space-y-2 mb-6">
                            {RETURN_REASONS.map((r) => (
                                <label key={r.value}
                                    className={`flex items-center gap-3 p-4 rounded-xl border-2 cursor-pointer transition-all
                                        ${reason === r.value ? 'border-theme-primary bg-theme-primary/5' : 'border-border-color hover:border-theme-primary/50'}`}
                                >
                                    <input type="radio" name="reason" value={r.value}
                                        checked={reason === r.value}
                                        onChange={() => setReason(r.value)}
                                        className="accent-theme-primary" />
                                    <span className="text-text-primary">{r.label}</span>
                                </label>
                            ))}
                        </div>

                        <div className="mb-6">
                            <label className="label">Additional Details (optional)</label>
                            <textarea
                                className="input resize-none h-24"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe the issue in more detail..."
                            />
                        </div>

                        <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 mb-6 border border-blue-200 dark:border-blue-800">
                            <div className="flex gap-2">
                                <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5" />
                                <p className="text-xs text-blue-700 dark:text-blue-300">
                                    Once approved, a pickup will be scheduled. Refund will be processed within 5-7 business days after pickup.
                                </p>
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <button onClick={() => setStep(1)} className="btn btn-ghost flex-1">Back</button>
                            <button
                                onClick={handleSubmit}
                                disabled={!reason || submitting}
                                className="btn btn-primary flex-1"
                            >
                                {submitting ? 'Submitting...' : 'Submit Return Request'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
