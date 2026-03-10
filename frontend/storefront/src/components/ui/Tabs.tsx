import { cn } from '@/lib/utils'

interface TabItem {
    key: string
    label: string
}

interface TabsProps {
    tabs: TabItem[]
    active: string
    onChange: (key: string) => void
    className?: string
}

export default function Tabs({ tabs, active, onChange, className }: TabsProps) {
    return (
        <div className={cn('flex flex-wrap gap-2', className)} aria-label="Sections">
            {tabs.map((tab) => {
                const isActive = tab.key === active
                return (
                    <button
                        key={tab.key}
                        type="button"
                        onClick={() => onChange(tab.key)}
                        className={cn(
                            'chip',
                            isActive && 'chip-active'
                        )}
                    >
                        {tab.label}
                    </button>
                )
            })}
        </div>
    )
}
