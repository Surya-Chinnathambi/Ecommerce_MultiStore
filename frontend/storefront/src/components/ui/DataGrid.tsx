import type { ReactNode } from 'react'

interface DataGridProps {
    loading?: boolean
    isEmpty?: boolean
    loadingState?: ReactNode
    emptyState?: ReactNode
    footer?: ReactNode
    className?: string
    children: ReactNode
}

export default function DataGrid({
    loading = false,
    isEmpty = false,
    loadingState,
    emptyState,
    footer,
    className,
    children,
}: DataGridProps) {
    return (
        <div className={className ?? 'card p-0 overflow-hidden'}>
            {loading ? (
                loadingState ?? (
                    <div className="flex flex-col items-center justify-center py-20 gap-3">
                        <div className="h-8 w-8 rounded-full border-2 border-theme-primary border-t-transparent animate-spin" />
                        <p className="text-sm text-text-tertiary">Loading…</p>
                    </div>
                )
            ) : isEmpty ? (
                emptyState ?? null
            ) : (
                <>
                    <div className="overflow-x-auto">{children}</div>
                    {footer}
                </>
            )}
        </div>
    )
}
