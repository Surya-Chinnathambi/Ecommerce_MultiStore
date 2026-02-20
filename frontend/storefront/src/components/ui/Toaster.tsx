import { useEffect, useState } from 'react'
import { X, CheckCircle2, AlertCircle, Info, AlertTriangle } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info' | 'warning'

interface Toast {
    id: string
    type: ToastType
    title?: string
    message: string
    duration: number
}

let toasts: Toast[] = []
let listeners: ((toasts: Toast[]) => void)[] = []

function notify(listeners: ((t: Toast[]) => void)[], list: Toast[]) {
    listeners.forEach(l => l(list))
}

function addToast(type: ToastType, message: string, title?: string, duration = 5000) {
    const id = Math.random().toString(36).substring(2, 9)
    toasts = [...toasts, { id, type, message, title, duration }]
    notify(listeners, toasts)
    setTimeout(() => {
        toasts = toasts.filter(t => t.id !== id)
        notify(listeners, toasts)
    }, duration)
}

export const toast = {
    success: (message: string, title?: string) => addToast('success', message, title),
    error: (message: string, title?: string) => addToast('error', message, title, 7000),
    info: (message: string, title?: string) => addToast('info', message, title),
    warning: (message: string, title?: string) => addToast('warning', message, title, 6000),
}

// ── Individual toast item ──────────────────────────────────────────────────
function ToastItem({ toast: t, onRemove }: { toast: Toast; onRemove: (id: string) => void }) {
    const [progress, setProgress] = useState(100)
    const [exiting, setExiting] = useState(false)

    useEffect(() => {
        const start = Date.now()
        const interval = setInterval(() => {
            const elapsed = Date.now() - start
            const pct = 100 - (elapsed / t.duration) * 100
            setProgress(Math.max(0, pct))
            if (pct <= 0) clearInterval(interval)
        }, 50)
        return () => clearInterval(interval)
    }, [t.duration])

    const handleClose = () => {
        setExiting(true)
        setTimeout(() => onRemove(t.id), 220)
    }

    const config = {
        success: {
            icon: <CheckCircle2 className="h-5 w-5 flex-shrink-0" />,
            iconClass: 'text-emerald-500',
            bar: 'bg-emerald-500',
            title: t.title ?? 'Success',
        },
        error: {
            icon: <AlertCircle className="h-5 w-5 flex-shrink-0" />,
            iconClass: 'text-red-500',
            bar: 'bg-red-500',
            title: t.title ?? 'Error',
        },
        info: {
            icon: <Info className="h-5 w-5 flex-shrink-0" />,
            iconClass: 'text-blue-500',
            bar: 'bg-blue-500',
            title: t.title ?? 'Info',
        },
        warning: {
            icon: <AlertTriangle className="h-5 w-5 flex-shrink-0" />,
            iconClass: 'text-amber-500',
            bar: 'bg-amber-500',
            title: t.title ?? 'Warning',
        },
    }[t.type]

    return (
        <div
            className={`relative w-[360px] max-w-[90vw] overflow-hidden rounded-[var(--radius-xl)] border border-border-color bg-bg-primary shadow-xl transition-all duration-220
                ${exiting ? 'opacity-0 translate-x-full scale-95' : 'opacity-100 translate-x-0 scale-100 animate-slide-in-right'}`}
            role="alert"
            aria-live="polite"
        >
            {/* Content */}
            <div className="flex items-start gap-3 px-4 py-3.5 pr-10">
                <span className={config.iconClass}>{config.icon}</span>
                <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-text-primary">{config.title}</p>
                    <p className="text-sm text-text-secondary mt-0.5 leading-snug">{t.message}</p>
                </div>
            </div>

            {/* Close */}
            <button
                onClick={handleClose}
                aria-label="Dismiss"
                className="absolute top-3 right-3 btn btn-icon-sm btn-ghost text-text-tertiary hover:text-text-primary"
            >
                <X className="h-3.5 w-3.5" />
            </button>

            {/* Progress bar */}
            <div className="h-0.5 w-full bg-bg-tertiary">
                <div
                    className={`h-full ${config.bar} transition-all duration-50 ease-linear`}
                    style={{ width: `${progress}%` }}
                />
            </div>
        </div>
    )
}

// ── Toaster container ──────────────────────────────────────────────────────
export function Toaster() {
    const [currentToasts, setCurrentToasts] = useState<Toast[]>([])

    useEffect(() => {
        listeners.push(setCurrentToasts)
        return () => { listeners = listeners.filter(l => l !== setCurrentToasts) }
    }, [])

    const removeToast = (id: string) => {
        toasts = toasts.filter(t => t.id !== id)
        notify(listeners, toasts)
    }

    if (currentToasts.length === 0) return null

    return (
        <div
            className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-3 items-end"
            role="region"
            aria-label="Notifications"
        >
            {currentToasts.map(t => (
                <ToastItem key={t.id} toast={t} onRemove={removeToast} />
            ))}
        </div>
    )
}
