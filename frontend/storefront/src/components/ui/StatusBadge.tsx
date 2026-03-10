import { CheckCircle2, CircleDashed, Clock3, Package, Truck, XCircle, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

type Tone = 'default' | 'warning' | 'info' | 'primary' | 'success' | 'danger' | 'purple'

const toneClass: Record<Tone, string> = {
    default: 'badge badge-default',
    warning: 'badge badge-warning',
    info: 'badge badge-info',
    primary: 'badge badge-primary',
    success: 'badge badge-success',
    danger: 'badge badge-danger',
    purple: 'badge badge-purple',
}

const STATUS_META: Record<string, { tone: Tone; icon: JSX.Element }> = {
    pending: { tone: 'warning', icon: <Clock3 className="h-3 w-3" aria-hidden="true" /> },
    confirmed: { tone: 'info', icon: <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> },
    processing: { tone: 'purple', icon: <Package className="h-3 w-3" aria-hidden="true" /> },
    shipped: { tone: 'primary', icon: <Truck className="h-3 w-3" aria-hidden="true" /> },
    delivered: { tone: 'success', icon: <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> },
    cancelled: { tone: 'danger', icon: <XCircle className="h-3 w-3" aria-hidden="true" /> },
    paid: { tone: 'success', icon: <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> },
    failed: { tone: 'danger', icon: <XCircle className="h-3 w-3" aria-hidden="true" /> },
    cod: { tone: 'default', icon: <CircleDashed className="h-3 w-3" aria-hidden="true" /> },
    refunded: { tone: 'info', icon: <AlertTriangle className="h-3 w-3" aria-hidden="true" /> },
    approved: { tone: 'info', icon: <CheckCircle2 className="h-3 w-3" aria-hidden="true" /> },
    rejected: { tone: 'danger', icon: <XCircle className="h-3 w-3" aria-hidden="true" /> },
    picked_up: { tone: 'primary', icon: <Truck className="h-3 w-3" aria-hidden="true" /> },
}

interface StatusBadgeProps {
    status: string
    className?: string
    showIcon?: boolean
}

export default function StatusBadge({ status, className, showIcon = true }: StatusBadgeProps) {
    const key = status.toLowerCase()
    const meta = STATUS_META[key]
    const tone = meta?.tone ?? 'default'
    return (
        <span className={cn(toneClass[tone], className)}>
            {showIcon && meta?.icon}
            {status.replace(/_/g, ' ')}
        </span>
    )
}
