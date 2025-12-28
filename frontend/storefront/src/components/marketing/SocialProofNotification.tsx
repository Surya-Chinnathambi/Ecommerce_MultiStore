import { useEffect, useState } from 'react'
import { ShoppingBag, Eye, ShoppingCart, X } from 'lucide-react'
import { marketingApi } from '@/lib/marketing-api'

interface Activity {
    id: string
    user_name: string
    activity_type: 'purchase' | 'viewing' | 'added_to_cart'
    product_name?: string
    city?: string
    created_at: string
}

const activityIcons = {
    purchase: ShoppingBag,
    viewing: Eye,
    added_to_cart: ShoppingCart,
}

const activityMessages = {
    purchase: 'just purchased',
    viewing: 'is viewing',
    added_to_cart: 'added to cart',
}

export default function SocialProofNotification() {
    const [activities, setActivities] = useState<Activity[]>([])
    const [currentActivity, setCurrentActivity] = useState<Activity | null>(null)
    const [isVisible, setIsVisible] = useState(false)

    useEffect(() => {
        fetchActivities()
        const interval = setInterval(fetchActivities, 30000) // Fetch every 30 seconds
        return () => clearInterval(interval)
    }, [])

    useEffect(() => {
        if (activities.length > 0 && !isVisible) {
            showNextActivity()
        }
    }, [activities])

    const fetchActivities = async () => {
        try {
            const response = await marketingApi.getRecentActivities(10)
            if (response.data.activities) {
                setActivities(response.data.activities)
            }
        } catch (error) {
            console.error('Error fetching activities:', error)
        }
    }

    const showNextActivity = () => {
        if (activities.length === 0) return

        const randomActivity = activities[Math.floor(Math.random() * activities.length)]
        setCurrentActivity(randomActivity)
        setIsVisible(true)

        // Auto-hide after 5 seconds
        setTimeout(() => {
            setIsVisible(false)
        }, 5000)
    }

    const handleClose = () => {
        setIsVisible(false)
    }

    if (!currentActivity || !isVisible) {
        return null
    }

    const Icon = activityIcons[currentActivity.activity_type]
    const message = activityMessages[currentActivity.activity_type]

    return (
        <div className="fixed bottom-6 left-6 z-50 animate-slide-in-left">
            <div className="bg-bg-primary rounded-lg shadow-2xl p-4 max-w-sm border-l-4 border-theme-primary flex items-start gap-3">
                {/* Icon */}
                <div className="bg-gradient-to-br from-theme-primary to-theme-accent p-2 rounded-full flex-shrink-0">
                    <Icon className="w-5 h-5 text-white" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                    <p className="text-sm text-text-primary">
                        <span className="font-semibold">{currentActivity.user_name}</span>
                        {currentActivity.city && (
                            <span className="text-text-secondary"> from {currentActivity.city}</span>
                        )}
                    </p>
                    <p className="text-sm text-text-secondary">
                        {message}
                        {currentActivity.product_name && (
                            <span className="font-medium text-text-primary">
                                {' '}{currentActivity.product_name}
                            </span>
                        )}
                    </p>
                    <p className="text-xs text-text-tertiary mt-1">
                        {getTimeAgo(currentActivity.created_at)}
                    </p>
                </div>

                {/* Close Button */}
                <button
                    onClick={handleClose}
                    className="text-text-tertiary hover:text-text-secondary transition-colors flex-shrink-0"
                    aria-label="Close notification"
                >
                    <X className="w-4 h-4" />
                </button>
            </div>
        </div>
    )
}

function getTimeAgo(timestamp: string): string {
    const seconds = Math.floor((new Date().getTime() - new Date(timestamp).getTime()) / 1000)

    if (seconds < 60) return 'just now'
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
    return `${Math.floor(seconds / 86400)} days ago`
}
