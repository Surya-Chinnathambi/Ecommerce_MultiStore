import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
    icon?: ReactNode
    title: string
    description?: string
    action?: ReactNode
    className?: string
}

export default function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
    return (
        <div className={cn('empty-state', className)}>
            {icon ? <div className="empty-state-icon">{icon}</div> : null}
            <h3 className="empty-state-title">{title}</h3>
            {description ? <p className="empty-state-description">{description}</p> : null}
            {action}
        </div>
    )
}
