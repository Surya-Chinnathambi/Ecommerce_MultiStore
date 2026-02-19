import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/store/authStore'
import { toast } from '@/components/ui/Toaster'

export interface LiveOrderEvent {
    type: 'new_order' | 'order_update' | 'pong'
    order_number?: string
    customer_name?: string
    total_amount?: number
    order_status?: string
    timestamp?: string
}

export function useLiveOrders() {
    const [events, setEvents] = useState<LiveOrderEvent[]>([])
    const [connected, setConnected] = useState(false)
    const [newCount, setNewCount] = useState(0)
    const wsRef = useRef<WebSocket | null>(null)
    const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

    const { token } = useAuthStore()
    const storeId = localStorage.getItem('store_id')

    const resetNewCount = useCallback(() => setNewCount(0), [])

    useEffect(() => {
        if (!token || !storeId) return

        const wsBase = (import.meta.env.VITE_API_URL as string | undefined)
            ?.replace('/api/v1', '')
            .replace(/^http/, 'ws') ?? 'ws://localhost:8000'
        const url = `${wsBase}/api/v1/ws/store/${storeId}?token=${token}`

        function connect() {
            if (wsRef.current?.readyState === WebSocket.OPEN) return

            const ws = new WebSocket(url)
            wsRef.current = ws

            ws.onopen = () => {
                setConnected(true)
                ws.send(JSON.stringify({ type: 'ping' }))
            }

            ws.onmessage = (event) => {
                try {
                    const data: LiveOrderEvent = JSON.parse(event.data)
                    if (data.type === 'new_order') {
                        setEvents(prev => [data, ...prev].slice(0, 20))
                        setNewCount(n => n + 1)
                        toast.success(
                            `🛒 New order ${data.order_number} — ₹${Number(data.total_amount ?? 0).toLocaleString('en-IN')}`
                        )
                    } else if (data.type === 'order_update') {
                        setEvents(prev => [data, ...prev].slice(0, 20))
                    }
                } catch {
                    // ignore malformed frames
                }
            }

            ws.onerror = () => setConnected(false)

            ws.onclose = () => {
                setConnected(false)
                // Reconnect after 5 s
                reconnectRef.current = setTimeout(connect, 5000)
            }
        }

        connect()

        // Heartbeat every 30 s
        const heartbeat = setInterval(() => {
            if (wsRef.current?.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'ping' }))
            }
        }, 30_000)

        return () => {
            clearInterval(heartbeat)
            if (reconnectRef.current) clearTimeout(reconnectRef.current)
            wsRef.current?.close()
        }
    }, [token, storeId])

    return { events, connected, newCount, resetNewCount }
}
