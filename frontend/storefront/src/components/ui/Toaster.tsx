import { useEffect, useState } from 'react'
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react'

interface Toast {
    id: string
    type: 'success' | 'error' | 'info'
    message: string
}

let toasts: Toast[] = []
let listeners: ((toasts: Toast[]) => void)[] = []

export const toast = {
    success: (message: string) => addToast('success', message),
    error: (message: string) => addToast('error', message),
    info: (message: string) => addToast('info', message),
}

function addToast(type: Toast['type'], message: string) {
    const id = Math.random().toString(36).substring(7)
    toasts = [...toasts, { id, type, message }]
    listeners.forEach(listener => listener(toasts))

    setTimeout(() => {
        toasts = toasts.filter(t => t.id !== id)
        listeners.forEach(listener => listener(toasts))
    }, 5000)
}

export function Toaster() {
    const [currentToasts, setCurrentToasts] = useState<Toast[]>([])

    useEffect(() => {
        listeners.push(setCurrentToasts)
        return () => {
            listeners = listeners.filter(l => l !== setCurrentToasts)
        }
    }, [])

    const removeToast = (id: string) => {
        toasts = toasts.filter(t => t.id !== id)
        listeners.forEach(listener => listener(toasts))
    }

    const icons = {
        success: <CheckCircle className="h-5 w-5" />,
        error: <AlertCircle className="h-5 w-5" />,
        info: <Info className="h-5 w-5" />,
    }

    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-theme-primary',
    }

    return (
        <div className="fixed bottom-4 right-4 z-50 space-y-2">
            {currentToasts.map(toast => (
                <div
                    key={toast.id}
                    className={`${colors[toast.type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center space-x-3 min-w-[300px] animate-slide-up`}
                >
                    {icons[toast.type]}
                    <span className="flex-1">{toast.message}</span>
                    <button
                        onClick={() => removeToast(toast.id)}
                        aria-label="Close notification"
                        className="hover:bg-white/20 rounded p-1"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            ))}
        </div>
    )
}
