import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useMutation } from '@tanstack/react-query'
import { orderApi } from '@/lib/api'
import { Package, Search } from 'lucide-react'

const trackFormSchema = z.object({
    order_number: z.string().min(1, 'Order number is required'),
    customer_phone: z.string().regex(/^\+?[1-9]\d{9,14}$/, 'Invalid phone number'),
})

type TrackForm = z.infer<typeof trackFormSchema>

export default function TrackOrderPage() {
    const [searchParams] = useSearchParams()
    const [orderData, setOrderData] = useState<any>(null)

    const { register, handleSubmit, formState: { errors } } = useForm<TrackForm>({
        resolver: zodResolver(trackFormSchema),
        defaultValues: {
            order_number: searchParams.get('order_number') || '',
        },
    })

    const trackMutation = useMutation({
        mutationFn: ({ order_number }: TrackForm) =>
            orderApi.trackOrder(order_number),
        onSuccess: (response) => {
            setOrderData(response.data.data)
        },
        onError: () => {
            setOrderData(null)
            alert('Order not found. Please check your order number and phone number.')
        },
    })

    const onSubmit = (data: TrackForm) => {
        trackMutation.mutate(data)
    }

    const getStatusColor = (status: string) => {
        const colors: Record<string, string> = {
            pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400',
            confirmed: 'bg-theme-primary/10 text-theme-primary',
            processing: 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
            ready: 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400',
            delivered: 'bg-green-600 text-white',
            cancelled: 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
        }
        return colors[status] || 'bg-bg-tertiary text-text-primary'
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="max-w-2xl mx-auto">
                <h1 className="text-3xl font-bold mb-8 text-center">Track Your Order</h1>

                {/* Track Form */}
                <div className="card mb-8">
                    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium mb-1">Order Number</label>
                            <input {...register('order_number')} className="input" placeholder="ORD-20241209..." />
                            {errors.order_number && (
                                <p className="text-red-600 text-sm mt-1">{errors.order_number.message}</p>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium mb-1">Phone Number</label>
                            <input {...register('customer_phone')} className="input" placeholder="+919876543210" />
                            {errors.customer_phone && (
                                <p className="text-red-600 text-sm mt-1">{errors.customer_phone.message}</p>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={trackMutation.isPending}
                            className="w-full btn btn-primary flex items-center justify-center space-x-2"
                        >
                            <Search className="h-5 w-5" />
                            <span>{trackMutation.isPending ? 'Searching...' : 'Track Order'}</span>
                        </button>
                    </form>
                </div>

                {/* Order Details */}
                {orderData && (
                    <div className="card">
                        <div className="flex items-center justify-between mb-6">
                            <h2 className="text-xl font-bold">Order Details</h2>
                            <span className={`px-4 py-2 rounded-full font-medium ${getStatusColor(orderData.order_status)}`}>
                                {orderData.order_status.toUpperCase()}
                            </span>
                        </div>

                        <div className="space-y-4">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <p className="text-sm text-gray-600">Order Number</p>
                                    <p className="font-medium">{orderData.order_number}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Order Date</p>
                                    <p className="font-medium">
                                        {new Date(orderData.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Total Amount</p>
                                    <p className="font-medium">₹{orderData.total_amount.toFixed(2)}</p>
                                </div>
                                <div>
                                    <p className="text-sm text-gray-600">Payment Status</p>
                                    <p className="font-medium">{orderData.payment_status}</p>
                                </div>
                            </div>

                            {orderData.expected_delivery_date && (
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <p className="text-sm text-blue-800">
                                        <strong>Expected Delivery:</strong>{' '}
                                        {new Date(orderData.expected_delivery_date).toLocaleDateString()}
                                    </p>
                                </div>
                            )}

                            {orderData.delivered_at && (
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <p className="text-sm text-green-800">
                                        <strong>Delivered on:</strong>{' '}
                                        {new Date(orderData.delivered_at).toLocaleDateString()}
                                    </p>
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Empty State */}
                {!orderData && !trackMutation.isPending && (
                    <div className="text-center py-12">
                        <Package className="h-16 w-16 mx-auto text-gray-400 mb-4" />
                        <p className="text-gray-600">Enter your order details to track your order</p>
                    </div>
                )}
            </div>
        </div>
    )
}
