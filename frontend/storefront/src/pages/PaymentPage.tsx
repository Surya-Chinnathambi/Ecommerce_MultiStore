import { useEffect, useState } from 'react'
import { useParams, useNavigate, useSearchParams } from 'react-router-dom'
import { orderApi } from '@/lib/api'
import PaymentGateway from '@/components/payment/PaymentGateway'
import { toast } from '@/components/ui/Toaster'
import { ArrowLeft } from 'lucide-react'

export default function PaymentPage() {
    const { orderNumber } = useParams<{ orderNumber: string }>()
    const [searchParams] = useSearchParams()
    const navigate = useNavigate()
    const [order, setOrder] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        if (orderNumber) {
            fetchOrderDetails()
        }
    }, [orderNumber])

    const fetchOrderDetails = async () => {
        try {
            const response = await orderApi.trackOrder(orderNumber!)
            const orderData = response.data.data

            // Check if payment is already completed
            if (orderData.payment_status === 'paid') {
                toast.info('Payment already completed')
                navigate(`/order-success/${orderNumber}`)
                return
            }

            // Check if payment method is COD
            if (orderData.payment_method === 'COD') {
                toast.info('This order uses Cash on Delivery')
                navigate(`/order-success/${orderNumber}`)
                return
            }

            setOrder(orderData)
        } catch (error: any) {
            toast.error('Failed to load order details')
            navigate('/orders')
        } finally {
            setLoading(false)
        }
    }

    const handlePaymentSuccess = (paymentId: string) => {
        toast.success('Payment successful!')
        navigate(`/order-success/${orderNumber}`)
    }

    const handlePaymentError = (error: string) => {
        toast.error(error)
    }

    const handleBackToOrders = () => {
        navigate('/orders')
    }

    if (loading) {
        return (
            <div className="min-h-screen bg-bg-secondary flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-16 w-16 border-b-4 border-theme-primary mx-auto mb-4"></div>
                    <p className="text-text-secondary">Loading payment details...</p>
                </div>
            </div>
        )
    }

    if (!order) {
        return (
            <div className="min-h-screen bg-bg-secondary flex items-center justify-center">
                <div className="text-center">
                    <p className="text-text-primary text-xl mb-4">Order not found</p>
                    <button
                        onClick={handleBackToOrders}
                        className="btn btn-primary"
                    >
                        Back to Orders
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className="min-h-screen bg-bg-secondary py-8">
            <div className="container mx-auto px-4">
                {/* Header */}
                <div className="mb-6">
                    <button
                        onClick={handleBackToOrders}
                        className="flex items-center text-theme-primary hover:text-theme-primary-hover mb-4"
                    >
                        <ArrowLeft className="h-4 w-4 mr-2" />
                        Back to Orders
                    </button>
                    <h1 className="text-3xl font-bold text-text-primary">Complete Your Payment</h1>
                    <p className="text-text-secondary mt-2">
                        Order #{order.order_number}
                    </p>
                </div>

                <div className="grid lg:grid-cols-3 gap-8">
                    {/* Payment Section */}
                    <div className="lg:col-span-2">
                        <PaymentGateway
                            orderId={order.id}
                            amount={order.total_amount}
                            currency="INR"
                            customerName={order.customer_name}
                            customerEmail={order.customer_email || ''}
                            customerPhone={order.customer_phone}
                            onSuccess={handlePaymentSuccess}
                            onError={handlePaymentError}
                        />
                    </div>

                    {/* Order Summary */}
                    <div className="lg:col-span-1">
                        <div className="bg-bg-primary rounded-lg shadow-md p-6 border border-border-color sticky top-24">
                            <h2 className="text-xl font-bold text-text-primary mb-4">Order Summary</h2>

                            <div className="space-y-3 mb-4">
                                {order.items?.map((item: any) => (
                                    <div key={item.id} className="flex justify-between text-sm">
                                        <span className="text-text-secondary">
                                            {item.product_name} x {item.quantity}
                                        </span>
                                        <span className="font-medium text-text-primary">
                                            ₹{item.total.toFixed(2)}
                                        </span>
                                    </div>
                                ))}
                            </div>

                            <div className="border-t border-border-color pt-4 space-y-2 mb-4">
                                <div className="flex justify-between text-sm">
                                    <span className="text-text-secondary">Subtotal</span>
                                    <span className="text-text-primary">₹{order.subtotal.toFixed(2)}</span>
                                </div>
                                {order.tax_amount > 0 && (
                                    <div className="flex justify-between text-sm">
                                        <span className="text-text-secondary">Tax</span>
                                        <span className="text-text-primary">₹{order.tax_amount.toFixed(2)}</span>
                                    </div>
                                )}
                                <div className="flex justify-between text-sm">
                                    <span className="text-text-secondary">Delivery</span>
                                    <span className="text-text-primary">
                                        {order.delivery_charge === 0 ? 'FREE' : `₹${order.delivery_charge.toFixed(2)}`}
                                    </span>
                                </div>
                            </div>

                            <div className="border-t border-border-color pt-4">
                                <div className="flex justify-between text-lg font-bold">
                                    <span className="text-text-primary">Total</span>
                                    <span className="text-theme-primary">₹{order.total_amount.toFixed(2)}</span>
                                </div>
                            </div>

                            {/* Delivery Address */}
                            <div className="mt-6 pt-6 border-t border-border-color">
                                <h3 className="font-semibold text-text-primary mb-2">Delivery Address</h3>
                                <p className="text-sm text-text-secondary">
                                    {order.shipping_address?.address || order.delivery_address}
                                </p>
                                <p className="text-sm text-text-secondary">
                                    {order.shipping_address?.city || order.delivery_city}, {order.shipping_address?.state || order.delivery_state} - {order.shipping_address?.postal_code || order.delivery_pincode}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}
