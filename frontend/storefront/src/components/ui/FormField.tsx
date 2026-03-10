import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface FormFieldProps {
    id: string
    label: string
    required?: boolean
    hint?: string
    error?: string
    className?: string
    children: ReactNode
}

export default function FormField({ id, label, required = false, hint, error, className, children }: FormFieldProps) {
    const hintId = hint ? `${id}-hint` : undefined
    const errorId = error ? `${id}-error` : undefined
    return (
        <div className={cn('space-y-1.5', className)}>
            <label htmlFor={id} className="form-label mb-0">
                {label}
                {required ? ' *' : ''}
            </label>
            {children}
            {hint && !error && (
                <p id={hintId} className="form-hint mt-0">
                    {hint}
                </p>
            )}
            {error && (
                <p id={errorId} className="form-error mt-0" role="alert" aria-live="polite">
                    {error}
                </p>
            )}
        </div>
    )
}

export function getFieldAria({ hint, error }: { hint?: string; error?: string }, id: string) {
    const describedBy = [hint ? `${id}-hint` : null, error ? `${id}-error` : null].filter(Boolean).join(' ')
    return {
        'aria-invalid': !!error,
        'aria-describedby': describedBy || undefined,
    }
}
