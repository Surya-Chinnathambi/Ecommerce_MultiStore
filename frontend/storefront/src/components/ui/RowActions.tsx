import type { AnchorHTMLAttributes, ButtonHTMLAttributes, ReactNode } from 'react'
import { cn } from '@/lib/utils'

type RowActionTone = 'default' | 'primary' | 'danger'

interface RowActionsProps {
    children: ReactNode
    className?: string
    align?: 'start' | 'end'
}

interface RowActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    children?: ReactNode
    icon?: ReactNode
    tone?: RowActionTone
    iconOnly?: boolean
}

const toneClass: Record<RowActionTone, string> = {
    default: 'text-text-secondary hover:text-theme-primary hover:bg-bg-tertiary',
    primary: 'text-theme-primary hover:text-theme-primary hover:bg-theme-primary/10',
    danger: 'text-text-secondary hover:text-red-600 hover:bg-red-50',
}

export default function RowActions({ children, className, align = 'end' }: RowActionsProps) {
    return (
        <div
            className={cn(
                'flex items-center gap-2',
                align === 'end' ? 'justify-end' : 'justify-start',
                className,
            )}
        >
            {children}
        </div>
    )
}

export function RowActionButton({
    children,
    icon,
    tone = 'default',
    iconOnly = false,
    className,
    ...props
}: RowActionButtonProps) {
    return (
        <button
            className={cn(
                'rounded-lg transition-colors',
                iconOnly ? 'p-1.5' : 'btn btn-ghost btn-sm',
                toneClass[tone],
                className,
            )}
            {...props}
        >
            {icon}
            {!iconOnly && children}
        </button>
    )
}

interface RowActionLinkProps extends AnchorHTMLAttributes<HTMLAnchorElement> {
    children?: ReactNode
    icon?: ReactNode
    tone?: RowActionTone
    iconOnly?: boolean
}

export function RowActionLink({
    children,
    icon,
    tone = 'default',
    iconOnly = false,
    className,
    ...props
}: RowActionLinkProps) {
    return (
        <a
            className={cn(
                'rounded-lg transition-colors inline-flex items-center',
                iconOnly ? 'p-1.5' : 'btn btn-ghost btn-sm',
                toneClass[tone],
                className,
            )}
            {...props}
        >
            {icon}
            {!iconOnly && children}
        </a>
    )
}