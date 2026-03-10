import { Gift, Tag, X } from 'lucide-react'
import Button from '@/components/ui/Button'

interface CouponFieldProps {
    code: string
    onCodeChange: (value: string) => void
    onApply: () => void
    onRemove: () => void
    loading?: boolean
    appliedCode?: string | null
    placeholder?: string
    className?: string
}

export default function CouponField({
    code,
    onCodeChange,
    onApply,
    onRemove,
    loading = false,
    appliedCode,
    placeholder = 'Enter coupon code',
    className,
}: CouponFieldProps) {
    return (
        <div className={className ?? 'space-y-2'}>
            <label className="text-sm font-semibold text-text-primary flex items-center gap-1.5">
                <Gift className="h-4 w-4 text-theme-primary" />
                Coupon Code
            </label>
            {appliedCode ? (
                <div className="flex items-center justify-between rounded-xl bg-green-500/10 border border-green-500/20 px-3 py-2.5">
                    <span className="text-sm font-semibold text-green-600 dark:text-green-400 flex items-center gap-1.5">
                        <Tag className="h-3.5 w-3.5" />{appliedCode}
                    </span>
                    <button
                        type="button"
                        onClick={onRemove}
                        className="text-text-tertiary hover:text-red-500 transition-colors"
                        aria-label="Remove coupon"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            ) : (
                <div className="flex gap-2">
                    <input
                        type="text"
                        value={code}
                        onChange={e => onCodeChange(e.target.value.toUpperCase())}
                        onKeyDown={e => e.key === 'Enter' && onApply()}
                        placeholder={placeholder}
                        className="input flex-1 text-sm uppercase tracking-wider"
                    />
                    <Button
                        type="button"
                        onClick={onApply}
                        disabled={loading || !code.trim()}
                        variant="outline"
                        size="sm"
                        className="flex-shrink-0"
                    >
                        {loading ? '...' : 'Apply'}
                    </Button>
                </div>
            )}
        </div>
    )
}
