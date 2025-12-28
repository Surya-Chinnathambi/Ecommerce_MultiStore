import { useParams, Link } from 'react-router-dom'
import { CheckCircle, Package } from 'lucide-react'

export default function OrderSuccessPage() {
    const { orderNumber } = useParams()

    return (
        <div className="container mx-auto px-4 py-16 text-center">
            <div className="max-w-md mx-auto">
                <CheckCircle className="h-24 w-24 mx-auto text-green-500 mb-6" />

                <h1 className="text-3xl font-bold mb-4 text-text-primary">Order Placed Successfully!</h1>

                <p className="text-text-secondary mb-6">
                    Thank you for your order. We'll send you a confirmation message shortly.
                </p>

                <div className="bg-bg-tertiary rounded-lg p-6 mb-8 border border-border-color">
                    <p className="text-sm text-text-secondary mb-2">Order Number</p>
                    <p className="text-2xl font-bold text-text-primary">{orderNumber}</p>
                </div>

                <div className="space-y-3">
                    <Link to={`/track-order?order_number=${orderNumber}`} className="w-full btn btn-primary block">
                        <Package className="inline h-5 w-5 mr-2" />
                        Track Your Order
                    </Link>

                    <Link to="/products" className="w-full btn btn-secondary block">
                        Continue Shopping
                    </Link>
                </div>

                <div className="mt-8 text-sm text-text-secondary">
                    <p>We will call you to confirm your order.</p>
                    <p className="mt-2">Expected delivery: 1-2 business days</p>
                </div>
            </div>
        </div>
    )
}
