import type { ReactNode } from 'react'
import { Search, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface FilterBarProps {
    searchValue: string
    onSearchChange: (value: string) => void
    searchPlaceholder?: string
    rightSlot?: ReactNode
    className?: string
    searchWidthClassName?: string
}

export default function FilterBar({
    searchValue,
    onSearchChange,
    searchPlaceholder = 'Search…',
    rightSlot,
    className,
    searchWidthClassName = 'w-full sm:w-80',
}: FilterBarProps) {
    return (
        <div className={cn('card p-4', className)}>
            <div className="flex flex-col sm:flex-row gap-3 sm:items-center sm:justify-between">
                <div className={cn('relative', searchWidthClassName)}>
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                    <input
                        type="text"
                        value={searchValue}
                        onChange={(e) => onSearchChange(e.target.value)}
                        placeholder={searchPlaceholder}
                        className="input w-full pl-9 pr-8 text-sm"
                    />
                    {searchValue && (
                        <button
                            type="button"
                            onClick={() => onSearchChange('')}
                            className="absolute right-2 top-1/2 -translate-y-1/2 text-text-tertiary hover:text-text-primary"
                            aria-label="Clear search"
                        >
                            <X className="h-4 w-4" />
                        </button>
                    )}
                </div>
                {rightSlot ? <div className="flex items-center gap-2">{rightSlot}</div> : null}
            </div>
        </div>
    )
}
