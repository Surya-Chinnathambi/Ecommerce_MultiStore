import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { returnsApi } from '@/lib/api'
import { RotateCcw, CheckCircle, Clock, Truck, Package, XCircle, DollarSign } from 'lucide-react'

const STATUS_STEPS = [
    { key: 'requested', label: 'Requested', icon: RotateCcw },
    { key: 'approved', label: 'Approved', icon: CheckCircle },
    { key: 'picked_up', label: 'Picked Up', icon: Truck },
    { key: 'refunded', label: 'Refunded', icon: DollarSign },
]

const STATUS_ICONS: Record<string, any> = {
    requested: Clock,
    approved: CheckCircle,
    picked_up: Truck,
    refunded: DollarSign,
    rejected: XCircle,
    closed: CheckCircle,
}

const STATUS_COLORS: Record<string, string> = {
    requested: 'text-yellow-500 bg-yellow-100 dark:bg-yellow-900/30',
    approved: 'text-blue-500 bg-blue-100 dark:bg-blue-900/30',
    picked_up: 'text-purple-500 bg-purple-100 dark:bg-purple-900/30',
    refunded: 'text-green-500 bg-green-100 dark:bg-green-900/30',
    rejected: 'text-red-500 bg-red-100 dark:bg-red-900/30',
    closed: 'text-text-secondary bg-bg-tertiary',
}

export default function ReturnStatusPage() {
    const { returnId } = useParams()

    const { data, isLoading } = useQuery({
        queryKey: ['return-detail', returnId],
        queryFn: () => returnsApi.getReturn(returnId!).then((r) => r.data.data),
        enabled: !!returnId,
        refetchInterval: 30000,  // poll every 30s
    })

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="skeleton h-8 w-64 rounded-lg mb-6" />
                <div className="skeleton rounded-2xl h-64" />
            </div>
        )
    }

    if (!data) {
        return (
            <div className="container mx-auto px-4 py-16">
                <div className="empty-state">
                    <Package className="empty-state-icon" />
                    <h2 className="empty-state-title">Return request not found</h2>
                    <Link to="/my-orders" className="btn btn-primary">My Orders</Link>
                </div>
            </div>
        )
    }

    const currentStepIdx = STATUS_STEPS.findIndex((s) => s.key === data.status)
    const StatusIcon = STATUS_ICONS[data.status] ?? RotateCcw

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8 max-w-2xl">
                {/* Header */}
                <div className="card p-6 mb-6">
                    <div className="flex items-start justify-between mb-4">
                        <div>
                            <h1 className="text-xl font-bold text-text-primary">{data.return_number}</h1>
                            <p className="text-text-secondary text-sm mt-1">
                                Requested on {new Date(data.requested_at).toLocaleDateString('en-IN', {
                                    day: 'numeric', month: 'long', year: 'numeric'
                                })}
                            </p>
                        </div>
                        <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-semibold ${STATUS_COLORS[data.status] ?? ''}`}>
                            <StatusIcon className="h-4 w-4" />
                            {data.status.replace('_', ' ').toUpperCase()}
                        </div>
                    </div>

                    {/* Timeline */}
                    {data.status !== 'rejected' && (
                        <div className="flex items-center justify-between mt-6">
                            {STATUS_STEPS.map((step, idx) => {
                                const done = idx <= currentStepIdx
                                const active = idx === currentStepIdx
                                return (
                                    <div key={step.key} className={`flex-1 flex flex-col items-center ${idx < STATUS_STEPS.length - 1 ? 'relative' : ''}`}>
                                        {/* Connector line */}
                                        {idx < STATUS_STEPS.length - 1 && (
                                            <div className={`absolute top-4 left-1/2 w-full h-0.5 -z-10 ${idx < currentStepIdx ? 'bg-theme-primary' : 'bg-border-color'}`} />
                                        )}
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all
                                            ${done ? 'bg-theme-primary border-theme-primary text-white' : 'bg-bg-primary border-border-color text-text-tertiary'}`}>
                                            <step.icon className="h-4 w-4" />
                                        </div>
                                        <span className={`text-xs mt-1.5 text-center ${active ? 'font-bold text-theme-primary' : 'text-text-tertiary'}`}>
                                            {step.label}
                                        </span>
                                    </div>
                                )
                            })}
                        </div>
                    )}

                    {/* Rejection message */}
                    {data.status === 'rejected' && (
                        <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800">
                            <p className="font-semibold text-red-700 dark:text-red-300 text-sm mb-1">Return Request Rejected</p>
                            <p className="text-sm text-red-600 dark:text-red-400">{data.rejection_reason || 'Does not meet return criteria'}</p>
                        </div>
                    )}
                </div>

                {/* Refund Info */}
                {data.refund_amount && (
                    <div className="card p-6 mb-6 bg-green-50 dark:bg-green-900/10 border border-green-200 dark:border-green-800">
                        <div className="flex items-center gap-3">
                            <DollarSign className="h-6 w-6 text-green-600 dark:text-green-400" />
                            <div>
                                <p className="font-bold text-green-800 dark:text-green-200">
                                    Refund: ₹{data.refund_amount.toLocaleString()}
                                </p>
                                <p className="text-sm text-green-600 dark:text-green-400">
                                    Via {data.refund_method === 'original' ? 'original payment method' : data.refund_method}
                                    {data.refunded_at && ` · ${new Date(data.refunded_at).toLocaleDateString('en-IN')}`}
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Tracking */}
                {data.tracking_id && (
                    <div className="card p-4 mb-6 flex items-center gap-3">
                        <Truck className="h-5 w-5 text-theme-primary" />
                        <div>
                            <p className="font-semibold text-text-primary text-sm">Pickup Tracking</p>
                            <p className="text-text-secondary text-sm">{data.tracking_id}</p>
                        </div>
                    </div>
                )}

                {/* Items */}
                <div className="card p-6 mb-6">
                    <h2 className="text-lg font-bold text-text-primary mb-4">Items in Return</h2>
                    <div className="space-y-3">
                        {data.items?.map((item: any) => (
                            <div key={item.id} className="flex items-center justify-between py-2 border-b border-border-color last:border-0">
                                <div>
                                    <p className="font-medium text-text-primary">{item.product_name}</p>
                                    <p className="text-sm text-text-secondary">
                                        Qty: {item.quantity} × ₹{item.unit_price?.toLocaleString()}
                                    </p>
                                </div>
                                <span className="font-bold text-text-primary">
                                    ₹{item.refund_amount?.toLocaleString()}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Return reason */}
                <div className="card p-4 mb-6">
                    <p className="text-sm text-text-secondary mb-1">Return Reason</p>
                    <p className="text-text-primary font-medium">
                        {data.reason?.replace('_', ' ')}
                    </p>
                    {data.description && (
                        <p className="text-text-secondary text-sm mt-2">{data.description}</p>
                    )}
                </div>

                {/* Admin notes */}
                {data.admin_notes && (
                    <div className="card p-4 mb-6 border border-border-color">
                        <p className="text-sm font-semibold text-text-secondary mb-1">Notes from Support</p>
                        <p className="text-text-primary">{data.admin_notes}</p>
                    </div>
                )}

                <Link to="/my-orders" className="btn btn-ghost w-full">
                    ← Back to My Orders
                </Link>
            </div>
        </div>
    )
}
