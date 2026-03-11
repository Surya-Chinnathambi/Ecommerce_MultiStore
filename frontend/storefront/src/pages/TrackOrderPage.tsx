import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { orderApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import {
    Package, Search, MapPin, CheckCircle2, Clock,
    Truck, PackageOpen, XCircle, CalendarDays, IndianRupee, CreditCard,
} from 'lucide-react'

const trackFormSchema = z.object({
    order_number: z.string().min(1, 'Order number is required'),
    customer_phone: z
        .string()
        .trim()
        .optional()
        .or(z.literal(''))
        .refine((value) => !value || /^\+?[0-9]\d{9,14}$/.test(value), 'Invalid phone number'),
    email: z
        .string()
        .trim()
        .optional()
        .or(z.literal(''))
        .refine((value) => !value || z.string().email().safeParse(value).success, 'Invalid email address'),
}).refine(
    (data) => Boolean(data.customer_phone?.trim() || data.email?.trim()),
    { message: 'Provide phone number or email for verification', path: ['customer_phone'] }
)

type TrackForm = z.infer<typeof trackFormSchema>
type TrackedOrderHistory = {
    order_number: string
    customer_phone?: string
    email?: string
    order_status?: string
    tracked_at: string
}

const TRACK_HISTORY_KEY = 'track_order_history_v1'
const TRACK_HISTORY_LIMIT = 6

const loadTrackHistory = (): TrackedOrderHistory[] => {
    try {
        const raw = localStorage.getItem(TRACK_HISTORY_KEY)
        if (!raw) return []
        const parsed = JSON.parse(raw)
        return Array.isArray(parsed) ? parsed : []
    } catch {
        return []
    }
}

const saveTrackHistory = (history: TrackedOrderHistory[]) => {
    localStorage.setItem(TRACK_HISTORY_KEY, JSON.stringify(history.slice(0, TRACK_HISTORY_LIMIT)))
}

const upsertTrackHistory = (
    history: TrackedOrderHistory[],
    entry: TrackedOrderHistory
): TrackedOrderHistory[] => {
    const filtered = history.filter((it) => it.order_number.toUpperCase() !== entry.order_number.toUpperCase())
    return [entry, ...filtered].slice(0, TRACK_HISTORY_LIMIT)
}

// ── Order progress steps ───────────────────────────────────────────────────────

const ORDER_STEPS = [
    { key: 'pending', label: 'Placed', Icon: Clock },
    { key: 'confirmed', label: 'Confirmed', Icon: CheckCircle2 },
    { key: 'processing', label: 'Processing', Icon: PackageOpen },
    { key: 'shipped', label: 'Shipped', Icon: Truck },
    { key: 'delivered', label: 'Delivered', Icon: Package },
]

const STEP_IDX: Record<string, number> = {
    pending: 0, confirmed: 1, processing: 2, shipped: 3, delivered: 4,
}

const statusLabel = (value?: string) => {
    if (!value) return 'Unknown'
    return value.charAt(0).toUpperCase() + value.slice(1)
}

export default function TrackOrderPage() {
    const [searchParams] = useSearchParams()
    const [orderData, setOrderData] = useState<any>(null)
    const [history, setHistory] = useState<TrackedOrderHistory[]>([])

    const { register, handleSubmit, setValue, formState: { errors } } = useForm<TrackForm>({
        resolver: zodResolver(trackFormSchema),
        defaultValues: {
            order_number: searchParams.get('order_number') || '',
            customer_phone: '',
            email: '',
        },
    })

    useEffect(() => {
        setHistory(loadTrackHistory())
    }, [])

    const trackMutation = useMutation({
        mutationFn: ({ order_number, customer_phone, email }: TrackForm) =>
            orderApi.trackOrder(order_number, {
                customer_phone: customer_phone?.trim() || undefined,
                email: email?.trim() || undefined,
            }),
        onSuccess: (response, variables) => {
            setOrderData(response.data.data)

            const updated = upsertTrackHistory(history, {
                order_number: variables.order_number.trim(),
                customer_phone: variables.customer_phone?.trim() || undefined,
                email: variables.email?.trim() || undefined,
                order_status: response?.data?.data?.order_status,
                tracked_at: new Date().toISOString(),
            })
            setHistory(updated)
            saveTrackHistory(updated)
        },
        onError: (error: any) => {
            setOrderData(null)
            const detail = error?.response?.data?.detail
            if (typeof detail === 'string' && detail) {
                toast.error(detail)
                return
            }
            toast.error('Order not found. Please check the order number and verification details.')
        },
    })

    const onSubmit = (data: TrackForm) => trackMutation.mutate(data)
    const handleHistoryTrack = (entry: TrackedOrderHistory) => {
        setValue('order_number', entry.order_number)
        setValue('customer_phone', entry.customer_phone || '')
        setValue('email', entry.email || '')
        trackMutation.mutate({
            order_number: entry.order_number,
            customer_phone: entry.customer_phone || '',
            email: entry.email || '',
        })
    }

    const clearHistory = () => {
        setHistory([])
        localStorage.removeItem(TRACK_HISTORY_KEY)
        toast.success('Tracking history cleared')
    }

    const currentStep = orderData ? (orderData?.tracking?.current_step ?? STEP_IDX[orderData.order_status] ?? 0) : -1
    const isCancelled = orderData?.order_status === 'cancelled'
    const timeline = orderData?.tracking?.timeline ?? ORDER_STEPS.map((step, i) => ({
        key: step.key,
        label: step.label,
        completed: i < currentStep,
        active: i === currentStep,
        timestamp: null,
    }))

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            <div className="max-w-2xl mx-auto">

                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-theme-primary/10 mb-4">
                        <Package className="h-7 w-7 text-theme-primary" />
                    </div>
                    <h1 className="section-title">Track Your Order</h1>
                    <p className="section-subtitle">Enter your order number to see real-time status</p>
                </div>

                {/* Track Form */}
                <div className="card mb-6">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div className="grid sm:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Order Number *</label>
                                <input
                                    {...register('order_number')}
                                    className="input w-full"
                                    placeholder="ORD-20241209..."
                                />
                                {errors.order_number && (
                                    <p className="text-red-500 text-xs mt-1">{errors.order_number.message}</p>
                                )}
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-text-secondary mb-1">Phone Number</label>
                                <input
                                    {...register('customer_phone')}
                                    className="input w-full"
                                    placeholder="+919876543210"
                                />
                                {errors.customer_phone && (
                                    <p className="text-red-500 text-xs mt-1">{errors.customer_phone.message}</p>
                                )}
                            </div>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Email (optional)</label>
                            <input
                                {...register('email')}
                                className="input w-full"
                                placeholder="you@example.com"
                            />
                            {errors.email && (
                                <p className="text-red-500 text-xs mt-1">{errors.email.message}</p>
                            )}
                            {!errors.email && !errors.customer_phone && (
                                <p className="text-xs text-text-tertiary mt-1">Provide phone or email that was used during checkout.</p>
                            )}
                        </div>
                        <button
                            type="submit"
                            disabled={trackMutation.isPending}
                            className="w-full btn btn-primary"
                        >
                            <Search className="h-4 w-4" />
                            {trackMutation.isPending ? 'Searching…' : 'Track Order'}
                        </button>
                    </form>
                </div>

                {history.length > 0 && (
                    <div className="card mb-6">
                        <div className="flex items-center justify-between mb-3">
                            <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider">Recently Tracked</p>
                            <button
                                type="button"
                                onClick={clearHistory}
                                className="text-xs text-text-tertiary hover:text-red-500 transition-colors"
                            >
                                Clear
                            </button>
                        </div>
                        <div className="space-y-2">
                            {history.map((entry) => (
                                <button
                                    type="button"
                                    key={`${entry.order_number}-${entry.tracked_at}`}
                                    onClick={() => handleHistoryTrack(entry)}
                                    className="w-full text-left rounded-xl border border-border-color bg-bg-secondary/50 px-3 py-2 hover:border-theme-primary/40 hover:bg-theme-primary/5 transition-all"
                                >
                                    <div className="flex items-center justify-between gap-3">
                                        <p className="text-sm font-semibold text-text-primary truncate">{entry.order_number}</p>
                                        <span className="text-[11px] text-text-tertiary whitespace-nowrap">
                                            {new Date(entry.tracked_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                                        </span>
                                    </div>
                                    <p className="text-xs text-text-tertiary mt-1">
                                        {entry.order_status ? `Last status: ${statusLabel(entry.order_status)}` : 'Tap to track again'}
                                    </p>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {/* Empty hint */}
                {!orderData && !trackMutation.isPending && (
                    <div className="text-center py-10 text-text-tertiary">
                        <Package className="h-14 w-14 mx-auto mb-3 opacity-25" />
                        <p className="text-sm">Your order status will appear here</p>
                    </div>
                )}

                {/* ── Order Results ── */}
                {orderData && (
                    <div className="space-y-4 animate-fade-in">

                        {/* Status pill header */}
                        <div className="card flex items-center justify-between gap-4">
                            <div>
                                <p className="text-xs text-text-tertiary mb-0.5">Order</p>
                                <p className="font-bold text-text-primary">{orderData.order_number}</p>
                                {orderData.limited_details && (
                                    <p className="text-xs text-amber-600 mt-1">{orderData.verification_hint || 'Limited details shown. Verify to unlock full details.'}</p>
                                )}
                            </div>
                            <span className={`badge font-semibold px-3 py-1 ${isCancelled
                                ? 'bg-red-500/10 text-red-500'
                                : orderData.order_status === 'delivered'
                                    ? 'bg-green-500/10 text-green-600'
                                    : 'bg-theme-primary/10 text-theme-primary'
                                }`}>
                                {isCancelled
                                    ? <span className="flex items-center gap-1"><XCircle className="h-3.5 w-3.5" />Cancelled</span>
                                    : statusLabel(orderData.order_status)
                                }
                            </span>
                        </div>

                        {/* ── Progress stepper ── */}
                        {!isCancelled && (
                            <div className="card">
                                <p className="text-xs font-semibold text-text-secondary uppercase tracking-wider mb-6">Order Progress</p>
                                <div className="flex items-start">
                                    {timeline.map((step: any, i: number) => {
                                        const fallbackIcon = ORDER_STEPS.find((it) => it.key === step.key)?.Icon || Clock
                                        const Icon = fallbackIcon
                                        const done = Boolean(step.completed)
                                        const active = Boolean(step.active)
                                        return (
                                            <div key={step.key || i} className="flex items-start flex-1">
                                                {/* Step circle + label */}
                                                <div className="flex flex-col items-center gap-2 flex-none w-14">
                                                    <div className={`w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500 ${done ? 'bg-theme-primary text-white' :
                                                        active ? 'bg-theme-primary text-white ring-4 ring-theme-primary/20' :
                                                            'bg-bg-tertiary text-text-tertiary'
                                                        }`}>
                                                        {done
                                                            ? <CheckCircle2 className="h-5 w-5" />
                                                            : <Icon className="h-5 w-5" />
                                                        }
                                                    </div>
                                                    <span className={`text-xs font-medium text-center leading-tight ${active ? 'text-theme-primary' :
                                                        done ? 'text-text-primary' : 'text-text-tertiary'
                                                        }`}>
                                                        {step.label || statusLabel(step.key)}
                                                        {step.timestamp && (
                                                            <span className="block text-[10px] text-text-tertiary mt-0.5">
                                                                {new Date(step.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                                                            </span>
                                                        )}
                                                    </span>
                                                </div>
                                                {/* Connector line (between steps) */}
                                                {i < timeline.length - 1 && (
                                                    <div className={`flex-1 h-0.5 mt-5 mx-1 rounded-full transition-all duration-500 ${i < currentStep ? 'bg-theme-primary' : 'bg-bg-tertiary'
                                                        }`} />
                                                )}
                                            </div>
                                        )
                                    })}
                                </div>
                            </div>
                        )}

                        {/* ── Info grid ── */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="card flex items-center gap-3">
                                <CalendarDays className="h-5 w-5 text-theme-primary flex-shrink-0" />
                                <div>
                                    <p className="text-xs text-text-tertiary">Order Date</p>
                                    <p className="font-semibold text-text-primary text-sm">
                                        {orderData.created_at
                                            ? new Date(orderData.created_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                                            : 'N/A'}
                                    </p>
                                </div>
                            </div>
                            {!orderData.limited_details && (
                                <div className="card flex items-center gap-3">
                                    <IndianRupee className="h-5 w-5 text-green-500 flex-shrink-0" />
                                    <div>
                                        <p className="text-xs text-text-tertiary">Total Amount</p>
                                        <p className="font-semibold text-text-primary text-sm">₹{orderData.total_amount?.toFixed(2)}</p>
                                    </div>
                                </div>
                            )}
                            <div className="card flex items-center gap-3">
                                <CreditCard className="h-5 w-5 text-purple-500 flex-shrink-0" />
                                <div>
                                    <p className="text-xs text-text-tertiary">Payment</p>
                                    <p className="font-semibold text-text-primary text-sm capitalize">{statusLabel(orderData.payment_status)}</p>
                                </div>
                            </div>
                            <div className="card flex items-center gap-3">
                                <Clock className="h-5 w-5 text-cyan-500 flex-shrink-0" />
                                <div>
                                    <p className="text-xs text-text-tertiary">Tracking Updated</p>
                                    <p className="font-semibold text-text-primary text-sm">
                                        {orderData.updated_at
                                            ? new Date(orderData.updated_at).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
                                            : 'N/A'}
                                    </p>
                                </div>
                            </div>

                            {(orderData.expected_delivery_date || orderData.delivered_at) && (
                                <div className="card flex items-center gap-3">
                                    <MapPin className="h-5 w-5 text-orange-500 flex-shrink-0" />
                                    <div>
                                        <p className="text-xs text-text-tertiary">
                                            {orderData.delivered_at ? 'Delivered On' : 'Expected By'}
                                        </p>
                                        <p className="font-semibold text-text-primary text-sm">
                                            {new Date(orderData.delivered_at || orderData.expected_delivery_date)
                                                .toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>

                    </div>
                )}
            </div>
        </div>
    )
}
