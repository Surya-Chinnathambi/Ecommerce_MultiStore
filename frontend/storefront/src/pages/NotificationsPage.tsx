import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { notificationsApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import {
    Bell, BellOff, CheckCheck, Package, ShoppingBag, Tag, Star,
    AlertCircle, Info, ChevronLeft, ChevronRight, Loader2
} from 'lucide-react'

interface Notification {
    id: number
    notification_type: string
    subject: string
    body: string
    is_read: boolean
    created_at: string
    data?: Record<string, unknown>
}

interface NotifListResponse {
    notifications: Notification[]
    total: number
    unread_count: number
    page: number
    page_size: number
}

const PAGE_SIZE = 15

function typeIcon(type: string) {
    switch (type) {
        case 'order_placed':
        case 'order_confirmed':
        case 'order_shipped':
        case 'order_delivered':
            return <ShoppingBag className="h-5 w-5 text-blue-500" />
        case 'order_cancelled':
            return <Package className="h-5 w-5 text-red-500" />
        case 'promo':
        case 'coupon':
            return <Tag className="h-5 w-5 text-orange-500" />
        case 'review':
            return <Star className="h-5 w-5 text-yellow-500" />
        case 'alert':
            return <AlertCircle className="h-5 w-5 text-red-500" />
        default:
            return <Info className="h-5 w-5 text-theme-primary" />
    }
}

function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime()
    const mins = Math.floor(diff / 60000)
    if (mins < 1) return 'Just now'
    if (mins < 60) return `${mins}m ago`
    const hrs = Math.floor(mins / 60)
    if (hrs < 24) return `${hrs}h ago`
    const days = Math.floor(hrs / 24)
    if (days < 7) return `${days}d ago`
    return new Date(dateStr).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })
}

export default function NotificationsPage() {
    const [page, setPage] = useState(1)
    const [unreadOnly, setUnreadOnly] = useState(false)
    const qc = useQueryClient()

    const { data, isLoading } = useQuery<NotifListResponse>({
        queryKey: ['notifications', page, unreadOnly],
        queryFn: () =>
            notificationsApi.list({
                skip: (page - 1) * PAGE_SIZE,
                limit: PAGE_SIZE,
                unread_only: unreadOnly || undefined,
            }).then(r => r.data),
        placeholderData: (prev) => prev,
    })

    const notifications = data?.notifications ?? []
    const total = data?.total ?? 0
    const unreadCount = data?.unread_count ?? 0
    const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))

    const markReadMut = useMutation({
        mutationFn: (id: number) => notificationsApi.markRead(id),
        onSuccess: () => qc.invalidateQueries({ queryKey: ['notifications'] }),
    })

    const markAllMut = useMutation({
        mutationFn: () => notificationsApi.markAllRead(),
        onSuccess: () => {
            toast.success('All notifications marked as read')
            qc.invalidateQueries({ queryKey: ['notifications'] })
        },
        onError: () => toast.error('Failed to mark all as read'),
    })

    function handleNotifClick(n: Notification) {
        if (!n.is_read) markReadMut.mutate(n.id)
    }

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in max-w-3xl">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div>
                    <h1 className="section-title flex items-center gap-2">
                        <Bell className="h-6 w-6 text-theme-primary" />
                        Notifications
                        {unreadCount > 0 && (
                            <span className="ml-1 px-2 py-0.5 rounded-full bg-red-500 text-white text-xs font-bold">
                                {unreadCount}
                            </span>
                        )}
                    </h1>
                    <p className="section-subtitle">{total} total · {unreadCount} unread</p>
                </div>
                <div className="flex items-center gap-2">
                    {/* Unread filter toggle */}
                    <button
                        onClick={() => { setUnreadOnly(v => !v); setPage(1) }}
                        className={`btn btn-sm ${unreadOnly ? 'btn-primary' : 'btn-outline'} flex items-center gap-1`}
                        title="Show unread only"
                    >
                        <BellOff className="h-3.5 w-3.5" />
                        Unread only
                    </button>
                    {unreadCount > 0 && (
                        <button
                            onClick={() => markAllMut.mutate()}
                            disabled={markAllMut.isPending}
                            className="btn btn-sm btn-ghost flex items-center gap-1 text-theme-primary"
                            title="Mark all as read"
                        >
                            {markAllMut.isPending
                                ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                                : <CheckCheck className="h-3.5 w-3.5" />}
                            Mark all read
                        </button>
                    )}
                </div>
            </div>

            {/* List */}
            {isLoading ? (
                <div className="space-y-3">
                    {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-20 rounded-xl" />)}
                </div>
            ) : notifications.length === 0 ? (
                <div className="card text-center py-20">
                    <Bell className="h-14 w-14 mx-auto text-text-tertiary mb-4" />
                    <p className="text-text-secondary font-medium text-lg">
                        {unreadOnly ? 'No unread notifications' : 'No notifications yet'}
                    </p>
                    <p className="text-text-tertiary text-sm mt-1">
                        {unreadOnly ? 'All caught up!' : 'Order updates, offers and alerts will appear here.'}
                    </p>
                    {unreadOnly && (
                        <button
                            onClick={() => setUnreadOnly(false)}
                            className="btn btn-outline btn-sm mt-5"
                        >
                            Show all
                        </button>
                    )}
                </div>
            ) : (
                <div className="card p-0 overflow-hidden divide-y divide-border-color">
                    {notifications.map(n => (
                        <button
                            key={n.id}
                            onClick={() => handleNotifClick(n)}
                            className={`w-full text-left flex items-start gap-3 px-4 py-4 hover:bg-bg-tertiary/60 transition-colors
                                ${!n.is_read ? 'bg-theme-primary/5' : ''}`}
                        >
                            {/* Icon */}
                            <div className="flex-shrink-0 mt-0.5 w-9 h-9 rounded-full bg-bg-tertiary flex items-center justify-center">
                                {typeIcon(n.notification_type)}
                            </div>
                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <p className={`text-sm leading-snug ${!n.is_read ? 'font-semibold text-text-primary' : 'text-text-primary'}`}>
                                    {n.subject}
                                </p>
                                <p className="text-xs text-text-secondary mt-0.5 line-clamp-2">{n.body}</p>
                                <p className="text-[11px] text-text-tertiary mt-1">{timeAgo(n.created_at)}</p>
                            </div>
                            {/* Unread dot */}
                            {!n.is_read && (
                                <div className="flex-shrink-0 mt-2 w-2 h-2 rounded-full bg-theme-primary" />
                            )}
                        </button>
                    ))}
                </div>
            )}

            {/* Pagination */}
            {totalPages > 1 && (
                <div className="flex items-center justify-center gap-4 mt-6">
                    <button
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="btn btn-outline btn-sm btn-icon"
                        aria-label="Previous page"
                        title="Previous page"
                    >
                        <ChevronLeft className="h-4 w-4" />
                    </button>
                    <span className="text-sm text-text-secondary">Page {page} of {totalPages}</span>
                    <button
                        onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                        disabled={page === totalPages}
                        className="btn btn-outline btn-sm btn-icon"
                        aria-label="Next page"
                        title="Next page"
                    >
                        <ChevronRight className="h-4 w-4" />
                    </button>
                </div>
            )}
        </div>
    )
}
