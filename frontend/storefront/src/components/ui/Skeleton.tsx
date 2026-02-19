import { cn } from '@/lib/utils'

// ── Core primitive ─────────────────────────────────────────────────────────────
interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> { }

export function Skeleton({ className, ...props }: SkeletonProps) {
    return (
        <div
            className={cn('animate-pulse rounded-md bg-muted', className)}
            {...props}
        />
    )
}

// ── Product card skeleton ──────────────────────────────────────────────────────
export function ProductCardSkeleton() {
    return (
        <div className="rounded-lg border bg-card overflow-hidden shadow-sm">
            {/* Image area */}
            <Skeleton className="h-48 w-full rounded-none" />
            <div className="p-4 space-y-3">
                {/* Category tag */}
                <Skeleton className="h-4 w-16" />
                {/* Title */}
                <Skeleton className="h-5 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                {/* Stars */}
                <div className="flex gap-1">
                    {[...Array(5)].map((_, i) => (
                        <Skeleton key={i} className="h-4 w-4 rounded-full" />
                    ))}
                    <Skeleton className="h-4 w-8 ml-1" />
                </div>
                {/* Price + button row */}
                <div className="flex items-center justify-between pt-1">
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-9 w-28 rounded-md" />
                </div>
            </div>
        </div>
    )
}

// ── Stat / KPI card skeleton ───────────────────────────────────────────────────
export function StatCardSkeleton() {
    return (
        <div className="rounded-lg border bg-card p-6 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
                <Skeleton className="h-4 w-24" />
                <Skeleton className="h-8 w-8 rounded-md" />
            </div>
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-3 w-20" />
        </div>
    )
}

// ── Table row skeleton ─────────────────────────────────────────────────────────
interface TableRowSkeletonProps {
    /** Number of columns to render (default: 5) */
    cols?: number
    /** Number of rows to render (default: 8) */
    rows?: number
}

export function TableRowSkeleton({ cols = 5, rows = 8 }: TableRowSkeletonProps) {
    return (
        <>
            {[...Array(rows)].map((_, ri) => (
                <tr key={ri} className="border-b last:border-0">
                    {[...Array(cols)].map((_, ci) => (
                        <td key={ci} className="px-4 py-3">
                            <Skeleton
                                className="h-4"
                                style={{ width: `${60 + ((ri * 13 + ci * 17) % 35)}%` }}
                            />
                        </td>
                    ))}
                </tr>
            ))}
        </>
    )
}

// ── Full-page skeleton (Suspense fallback) ─────────────────────────────────────
export function PageSkeleton() {
    return (
        <div className="min-h-screen bg-background">
            {/* Navbar placeholder */}
            <div className="h-16 border-b bg-card px-6 flex items-center gap-4">
                <Skeleton className="h-8 w-32" />
                <div className="flex-1" />
                <Skeleton className="h-8 w-24" />
                <Skeleton className="h-8 w-8 rounded-full" />
            </div>

            <div className="container mx-auto px-4 py-8 space-y-6">
                {/* Page title */}
                <Skeleton className="h-8 w-48" />

                {/* Content grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                    {[...Array(4)].map((_, i) => (
                        <StatCardSkeleton key={i} />
                    ))}
                </div>

                {/* Main content area */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="lg:col-span-2 rounded-lg border bg-card p-6 space-y-4">
                        <Skeleton className="h-6 w-32" />
                        <Skeleton className="h-48 w-full" />
                    </div>
                    <div className="rounded-lg border bg-card p-6 space-y-4">
                        <Skeleton className="h-6 w-28" />
                        {[...Array(5)].map((_, i) => (
                            <div key={i} className="flex gap-3 items-center">
                                <Skeleton className="h-10 w-10 rounded-md flex-shrink-0" />
                                <div className="flex-1 space-y-2">
                                    <Skeleton className="h-4 w-full" />
                                    <Skeleton className="h-3 w-2/3" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
