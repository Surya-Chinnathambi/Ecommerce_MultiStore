import { ChevronLeft, ChevronRight } from 'lucide-react'
import Button from '@/components/ui/Button'

interface PaginationControlsProps {
    page: number
    totalPages: number
    onPrev: () => void
    onNext: () => void
    className?: string
}

export default function PaginationControls({ page, totalPages, onPrev, onNext, className }: PaginationControlsProps) {
    if (totalPages <= 1) return null
    return (
        <div className={className ?? 'flex items-center justify-between px-5 py-3.5 border-t border-border-color bg-bg-secondary/50'}>
            <span className="text-sm text-text-tertiary">Page {page} of {totalPages}</span>
            <div className="flex items-center gap-2">
                <Button type="button" variant="secondary" size="sm" onClick={onPrev} disabled={page === 1} leftIcon={<ChevronLeft className="h-4 w-4" />}>
                    Prev
                </Button>
                <Button type="button" variant="secondary" size="sm" onClick={onNext} disabled={page === totalPages} rightIcon={<ChevronRight className="h-4 w-4" />}>
                    Next
                </Button>
            </div>
        </div>
    )
}
