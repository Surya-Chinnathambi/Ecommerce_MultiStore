import { useEffect, useState } from 'react'
import { Clock, Flame } from 'lucide-react'
import { marketingApi } from '@/lib/marketing-api'
import { Link } from 'react-router-dom'

interface FlashSale {
    id: string
    product_id: string
    product: {
        id: string
        name: string
        image_url: string
        price: number
    }
    sale_price: number
    discount_percent: number
    start_time: string
    end_time: string
    max_quantity: number
    sold_quantity: number
}

interface TimeLeft {
    days: number
    hours: number
    minutes: number
    seconds: number
}

export default function FlashSaleTimer() {
    const [flashSales, setFlashSales] = useState<FlashSale[]>([])
    const [timeLeft, setTimeLeft] = useState<{ [key: string]: TimeLeft }>({})

    useEffect(() => {
        fetchFlashSales()
        const interval = setInterval(updateTimers, 1000)
        return () => clearInterval(interval)
    }, [])

    const fetchFlashSales = async () => {
        try {
            const response = await marketingApi.getFlashSales({ active_only: true })
            if (response.data.flash_sales) {
                setFlashSales(response.data.flash_sales)
            }
        } catch (error) {
            console.error('Error fetching flash sales:', error)
        }
    }

    const calculateTimeLeft = (endTime: string): TimeLeft => {
        const difference = new Date(endTime).getTime() - new Date().getTime()

        if (difference <= 0) {
            return { days: 0, hours: 0, minutes: 0, seconds: 0 }
        }

        return {
            days: Math.floor(difference / (1000 * 60 * 60 * 24)),
            hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
            minutes: Math.floor((difference / 1000 / 60) % 60),
            seconds: Math.floor((difference / 1000) % 60),
        }
    }

    const updateTimers = () => {
        const newTimeLeft: { [key: string]: TimeLeft } = {}
        flashSales.forEach((sale) => {
            newTimeLeft[sale.id] = calculateTimeLeft(sale.end_time)
        })
        setTimeLeft(newTimeLeft)
    }

    if (flashSales.length === 0) {
        return null
    }

    return (
        <div className="py-12 bg-gradient-to-r from-red-50 to-pink-50">
            <div className="max-w-7xl mx-auto px-4">
                <div className="flex items-center justify-center gap-3 mb-8">
                    <Flame className="w-8 h-8 text-red-500 animate-pulse" />
                    <h2 className="text-3xl font-bold bg-gradient-to-r from-red-600 to-pink-600 bg-clip-text text-transparent">
                        Flash Sales
                    </h2>
                    <Flame className="w-8 h-8 text-red-500 animate-pulse" />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {flashSales.map((sale) => {
                        const time = timeLeft[sale.id] || { days: 0, hours: 0, minutes: 0, seconds: 0 }
                        const isUrgent = time.days === 0 && time.hours < 1
                        const soldPercentage = (sale.sold_quantity / sale.max_quantity) * 100

                        return (
                            <Link
                                key={sale.id}
                                to={`/products/${sale.product_id}`}
                                className="bg-white rounded-xl shadow-lg overflow-hidden hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1"
                            >
                                {/* Product Image */}
                                <div className="relative">
                                    <img
                                        src={sale.product.image_url}
                                        alt={sale.product.name}
                                        className="w-full h-48 object-cover"
                                    />
                                    <div className="absolute top-2 right-2 bg-gradient-to-r from-red-500 to-pink-500 text-white px-3 py-1 rounded-full font-bold text-sm">
                                        -{sale.discount_percent}%
                                    </div>
                                </div>

                                {/* Product Info */}
                                <div className="p-4">
                                    <h3 className="font-semibold text-lg mb-2 line-clamp-2">
                                        {sale.product.name}
                                    </h3>

                                    {/* Prices */}
                                    <div className="flex items-center gap-3 mb-3">
                                        <span className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-pink-600 bg-clip-text text-transparent">
                                            ₹{sale.sale_price.toFixed(2)}
                                        </span>
                                        <span className="text-gray-400 line-through">
                                            ₹{sale.product.price.toFixed(2)}
                                        </span>
                                    </div>

                                    {/* Stock Progress */}
                                    <div className="mb-3">
                                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                                            <span>Sold: {sale.sold_quantity}/{sale.max_quantity}</span>
                                            <span>{soldPercentage.toFixed(0)}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                                            <div
                                                className={`bg-gradient-to-r from-theme-primary to-theme-accent h-full rounded-full transition-all duration-300`}
                                                style={{ width: `${Math.min(100, soldPercentage)}%` }}
                                            />
                                        </div>
                                    </div>

                                    {/* Countdown Timer */}
                                    <div className={`flex items-center gap-2 p-3 rounded-lg ${isUrgent ? 'bg-red-50' : 'bg-gray-50'
                                        }`}>
                                        <Clock className={`w-5 h-5 ${isUrgent ? 'text-red-500' : 'text-gray-600'}`} />
                                        <div className="flex gap-2 text-sm font-semibold">
                                            {time.days > 0 && (
                                                <div className={isUrgent ? 'text-red-600' : 'text-gray-800'}>
                                                    {time.days}d
                                                </div>
                                            )}
                                            <div className={isUrgent ? 'text-red-600' : 'text-gray-800'}>
                                                {String(time.hours).padStart(2, '0')}:
                                                {String(time.minutes).padStart(2, '0')}:
                                                {String(time.seconds).padStart(2, '0')}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Link>
                        )
                    })}
                </div>
            </div>
        </div>
    )
}
