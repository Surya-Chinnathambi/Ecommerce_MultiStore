import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { marketingApi } from '@/lib/marketing-api'

interface Banner {
    id: string
    title: string
    subtitle?: string
    image_url: string
    link_url?: string
    banner_type: string
    display_order: number
}

export default function PromotionalBanner() {
    const [banners, setBanners] = useState<Banner[]>([])
    const [currentIndex, setCurrentIndex] = useState(0)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        fetchBanners()
    }, [])

    const fetchBanners = async () => {
        try {
            const response = await marketingApi.getBanners({ banner_type: 'hero' })
            if (response.data.banners && response.data.banners.length > 0) {
                setBanners(response.data.banners)
            }
        } catch (error) {
            console.error('Error fetching banners:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleBannerClick = async (banner: Banner) => {
        try {
            await marketingApi.trackBannerClick(banner.id)
            if (banner.link_url) {
                window.location.href = banner.link_url
            }
        } catch (error) {
            console.error('Error tracking banner click:', error)
        }
    }

    const nextBanner = () => {
        setCurrentIndex((prev) => (prev + 1) % banners.length)
    }

    const prevBanner = () => {
        setCurrentIndex((prev) => (prev - 1 + banners.length) % banners.length)
    }

    // Auto-advance banners every 5 seconds
    useEffect(() => {
        if (banners.length > 1) {
            const interval = setInterval(nextBanner, 5000)
            return () => clearInterval(interval)
        }
    }, [banners.length])

    if (isLoading || banners.length === 0) {
        return null
    }

    const currentBanner = banners[currentIndex]

    return (
        <div className="relative w-full h-[400px] md:h-[500px] overflow-hidden rounded-xl">
            {/* Banner Image */}
            <div
                className="absolute inset-0 bg-cover bg-center transition-all duration-500 cursor-pointer"
                style={{ backgroundImage: `url(${currentBanner.image_url})` }}
                onClick={() => handleBannerClick(currentBanner)}
            >
                {/* Gradient Overlay */}
                <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/50 to-transparent" />

                {/* Content */}
                <div className="relative h-full flex items-center px-8 md:px-16">
                    <div className="max-w-2xl text-white">
                        <h1 className="text-4xl md:text-6xl font-bold mb-4 animate-fade-in">
                            {currentBanner.title}
                        </h1>
                        {currentBanner.subtitle && (
                            <p className="text-xl md:text-2xl mb-6 text-gray-200">
                                {currentBanner.subtitle}
                            </p>
                        )}
                        {currentBanner.link_url && (
                            <button className="px-8 py-3 bg-gradient-to-r from-pink-500 to-purple-600 text-white font-semibold rounded-full hover:from-pink-600 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg">
                                Shop Now
                            </button>
                        )}
                    </div>
                </div>
            </div>

            {/* Navigation Arrows */}
            {banners.length > 1 && (
                <>
                    <button
                        onClick={prevBanner}
                        className="absolute left-4 top-1/2 -translate-y-1/2 bg-white/30 hover:bg-white/50 backdrop-blur-sm text-white p-2 rounded-full transition-all duration-300"
                        aria-label="Previous banner"
                    >
                        <ChevronLeft className="w-6 h-6" />
                    </button>
                    <button
                        onClick={nextBanner}
                        className="absolute right-4 top-1/2 -translate-y-1/2 bg-white/30 hover:bg-white/50 backdrop-blur-sm text-white p-2 rounded-full transition-all duration-300"
                        aria-label="Next banner"
                    >
                        <ChevronRight className="w-6 h-6" />
                    </button>
                </>
            )}

            {/* Dots Indicator */}
            {banners.length > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex gap-2">
                    {banners.map((_, index) => (
                        <button
                            key={index}
                            onClick={() => setCurrentIndex(index)}
                            className={`h-2 rounded-full transition-all duration-300 ${index === currentIndex
                                ? 'w-8 bg-white'
                                : 'w-2 bg-white/50 hover:bg-white/75'
                                }`}
                            aria-label={`Go to banner ${index + 1}`}
                        />
                    ))}
                </div>
            )}
        </div>
    )
}
