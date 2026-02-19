import { useParams, Link } from 'react-router-dom'
import { CheckCircle, Package, ArrowRight, Truck, Clock, CreditCard, MapPin } from 'lucide-react'

// ── Pure-CSS confetti particles ───────────────────────────────────────────────
const CONFETTI_COLORS = [
    '#a855f7', '#8b5cf6', '#ec4899', '#f97316', '#22c55e', '#3b82f6', '#eab308',
]
const CONFETTI_COUNT = 28

function Confetti() {
    // Inject per-particle CSS via <style> to avoid inline-style lint warnings.
    // CSS custom properties cannot be set any other way in React.
    const particleCSS = Array.from({ length: CONFETTI_COUNT }).map((_, i) => {
        const color = CONFETTI_COLORS[i % CONFETTI_COLORS.length]
        const left = `${(i * 3.7 + 2) % 100}%`
        const delay = `${(i * 0.13) % 3.5}s`
        const size = `${6 + (i % 5) * 2}px`
        const shape = i % 3 === 0 ? '50%' : i % 3 === 1 ? '2px' : '0%'
        const duration = `${2.8 + (i % 6) * 0.4}s`
        return `.cp-${i}{left:${left};width:${size};height:${size};background-color:${color};border-radius:${shape};animation-delay:${delay};animation-duration:${duration}}`
    }).join('')

    return (
        <>
            {/* eslint-disable-next-line react/no-danger */}
            <style dangerouslySetInnerHTML={{ __html: particleCSS }} />
            <div className="pointer-events-none fixed inset-x-0 top-0 overflow-hidden z-[100]">
                {Array.from({ length: CONFETTI_COUNT }).map((_, i) => (
                    <div key={i} className={`confetti-particle cp-${i}`} />
                ))}
            </div>
        </>
    )
}

// ── Order progress timeline ───────────────────────────────────────────────────
const TIMELINE = [
    { icon: CreditCard, label: 'Payment Confirmed', desc: 'Your payment was successful', done: true },
    { icon: Package, label: 'Order Processing', desc: 'We are preparing your items', done: true },
    { icon: Truck, label: 'Out for Delivery', desc: '1-2 business days', done: false },
    { icon: MapPin, label: 'Delivered', desc: 'Enjoy your order!', done: false },
]

export default function OrderSuccessPage() {
    const { orderNumber } = useParams()

    return (
        <div className="container mx-auto px-4 py-12 animate-fade-in">
            <Confetti />

            <div className="max-w-xl mx-auto">
                {/* Animated success icon */}
                <div className="relative mb-8 flex items-center justify-center">
                    <div className="absolute h-40 w-40 rounded-full bg-green-500/10 animate-ping [animation-duration:2s]" />
                    <div className="absolute h-28 w-28 rounded-full bg-green-500/15" />
                    <CheckCircle className="relative z-10 h-20 w-20 text-green-500 animate-bounce-in" />
                </div>

                <div className="text-center mb-4">
                    <h1 className="text-3xl md:text-4xl font-extrabold text-text-primary mb-2">
                        Order Placed! 🎉
                    </h1>
                    <p className="text-text-secondary">
                        Thank you — we’ll start packing right away.
                    </p>
                </div>

                {/* Order number badge */}
                <div className="card text-center mb-8 bg-gradient-to-br from-theme-primary/5 to-theme-accent/5 border-theme-primary/20">
                    <p className="text-xs text-text-tertiary uppercase tracking-widest mb-1">Order Reference</p>
                    <p className="text-3xl font-bold text-gradient tracking-wide">{orderNumber}</p>
                </div>

                {/* Progress timeline */}
                <div className="card mb-8 p-6">
                    <h2 className="text-base font-semibold text-text-primary mb-5">Order Progress</h2>
                    <ol className="space-y-0">
                        {TIMELINE.map((step, idx) => (
                            <li key={step.label} className="flex gap-4">
                                {/* Connector */}
                                <div className="flex flex-col items-center">
                                    <div className={`flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border-2 transition-colors ${step.done
                                        ? 'border-green-500 bg-green-500/10 text-green-500'
                                        : 'border-border-color bg-bg-tertiary text-text-tertiary'
                                        }`}>
                                        <step.icon className="h-4 w-4" />
                                    </div>
                                    {idx < TIMELINE.length - 1 && (
                                        <div className={`my-1 w-0.5 flex-1 min-h-[20px] rounded-full ${step.done ? 'bg-green-500/40' : 'bg-border-color'
                                            }`} />
                                    )}
                                </div>
                                {/* Text */}
                                <div className="pb-4">
                                    <p className={`text-sm font-semibold ${step.done ? 'text-text-primary' : 'text-text-tertiary'
                                        }`}>{step.label}</p>
                                    <p className="text-xs text-text-tertiary mt-0.5">{step.desc}</p>
                                </div>
                            </li>
                        ))}
                    </ol>
                </div>

                {/* Estimated delivery */}
                <div className="flex items-center gap-3 rounded-xl bg-blue-500/10 border border-blue-500/20 px-4 py-3 mb-8">
                    <Clock className="h-5 w-5 text-blue-500 flex-shrink-0" />
                    <div>
                        <p className="text-sm font-semibold text-text-primary">Estimated Delivery</p>
                        <p className="text-xs text-text-secondary">1–2 business days from now</p>
                    </div>
                </div>

                {/* Actions */}
                <div className="space-y-3">
                    <Link to={`/track-order?order_number=${orderNumber}`} className="btn btn-primary btn-lg w-full shadow-lg shadow-theme-primary/20">
                        <Package className="h-5 w-5" />
                        <span>Track Your Order</span>
                        <ArrowRight className="h-5 w-5 ml-auto" />
                    </Link>
                    <Link to="/products" className="btn btn-secondary w-full">
                        Continue Shopping
                    </Link>
                </div>

                <p className="mt-6 text-center text-xs text-text-tertiary">
                    A confirmation has been sent to your registered email address.
                </p>
            </div>
        </div>
    )
}
