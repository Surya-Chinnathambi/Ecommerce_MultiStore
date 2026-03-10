import type { ReactNode } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ModalProps {
    open: boolean
    onClose: () => void
    children: ReactNode
    className?: string
    panelClassName?: string
    maxWidthClassName?: string
}

interface ModalHeaderProps {
    title: ReactNode
    subtitle?: ReactNode
    onClose?: () => void
    className?: string
}

interface ModalSectionProps {
    children: ReactNode
    className?: string
}

export default function Modal({
    open,
    onClose,
    children,
    className,
    panelClassName,
    maxWidthClassName = 'max-w-2xl',
}: ModalProps) {
    if (!open) return null

    return (
        <div
            className={cn('fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in', className)}
            onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
            role="dialog"
            aria-modal="true"
        >
            <div className={cn('bg-bg-primary border border-border-color rounded-[var(--radius-2xl)] w-full max-h-[90vh] overflow-y-auto shadow-2xl animate-scale-in', maxWidthClassName, panelClassName)}>
                {children}
            </div>
        </div>
    )
}

export function ModalHeader({ title, subtitle, onClose, className }: ModalHeaderProps) {
    return (
        <div className={cn('sticky top-0 bg-bg-primary border-b border-border-color px-6 py-4 flex items-start justify-between z-10 rounded-t-[var(--radius-2xl)]', className)}>
            <div>
                <h2 className="text-lg font-bold text-text-primary">{title}</h2>
                {subtitle ? <p className="text-sm text-text-tertiary mt-0.5">{subtitle}</p> : null}
            </div>
            {onClose ? (
                <button
                    onClick={onClose}
                    aria-label="Close"
                    className="btn btn-icon btn-ghost text-text-tertiary"
                    type="button"
                >
                    <X className="h-5 w-5" />
                </button>
            ) : null}
        </div>
    )
}

export function ModalBody({ children, className }: ModalSectionProps) {
    return <div className={cn('p-6', className)}>{children}</div>
}

export function ModalFooter({ children, className }: ModalSectionProps) {
    return <div className={cn('sticky bottom-0 bg-bg-primary border-t border-border-color px-6 py-4', className)}>{children}</div>
}