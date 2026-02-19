import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useCartStore } from '@/store/cartStore'
import { useAuthStore } from '@/store/authStore'
import { useMutation, useQuery } from '@tanstack/react-query'
import { orderApi, authApi, couponsApi, pincodeApi } from '@/lib/api'
import { useNavigate } from 'react-router-dom'
import { toast } from '@/components/ui/Toaster'
import { useEffect, useState, useRef } from 'react'
import { MapPin, Tag, X, Check, Loader2, Truck } from 'lucide-react'

const checkoutSchema = z.object({
    customer_name: z.string().min(2, 'Name must be at least 2 characters'),
    customer_phone: z.string().regex(/^\+?[1-9]\d{9,14}$/, 'Invalid phone number'),
    customer_email: z.string().email('Invalid email').optional().or(z.literal('')),
    delivery_address: z.string().min(10, 'Address must be at least 10 characters'),
    delivery_city: z.string().min(2, 'City is required'),
    delivery_state: z.string().min(2, 'State is required'),
    delivery_pincode: z.string().regex(/^\d{6}$/, 'Invalid pincode'),
    delivery_landmark: z.string().optional(),
    notes: z.string().optional(),
    payment_method: z.enum(['COD', 'ONLINE']),
})

type CheckoutForm = z.infer<typeof checkoutSchema>

export default function CheckoutPage() {
    const navigate = useNavigate()
    const { items, getTotalPrice, clearCart } = useCartStore()
    const { user, isAuthenticated } = useAuthStore()
    const [showAddresses, setShowAddresses] = useState(false)
    const [couponCode, setCouponCode] = useState('')
    const [couponData, setCouponData] = useState<any>(null)
    const [couponLoading, setCouponLoading] = useState(false)
    const [pincodeInfo, setPincodeInfo] = useState<{ serviceable: boolean; standard_days?: number; city?: string; state?: string } | null>(null)
    const [pincodeLoading, setPincodeLoading] = useState(false)
    const pincodeDebounce = useRef<ReturnType<typeof setTimeout> | null>(null)

    const subtotal = getTotalPrice()
    const discount = couponData?.discount_amount ?? 0
    const freeShipping = couponData?.free_shipping ?? false
    const finalTotal = Math.max(subtotal - discount, 0)

    const applyCoupon = async () => {
        if (!couponCode.trim()) return
        setCouponLoading(true)
        try {
            const res = await couponsApi.validate({
                code: couponCode.trim(),
                order_amount: subtotal,
                item_count: items.length,
            })
            setCouponData(res.data.data)
            toast.success(`Coupon applied! You save ₹${res.data.data.discount_amount.toFixed(2)}`)
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Invalid coupon code')
            setCouponData(null)
        } finally {
            setCouponLoading(false)
        }
    }

    const removeCoupon = () => {
        setCouponData(null)
        setCouponCode('')
    }

    const { register, handleSubmit, formState: { errors }, setValue, watch } = useForm<CheckoutForm>({
        resolver: zodResolver(checkoutSchema),
        defaultValues: {
            payment_method: 'COD',
        },
    })

    // Pincode autofill
    const watchedPincode = watch('delivery_pincode', '')
    useEffect(() => {
        const raw = (watchedPincode ?? '').replace(/\D/g, '')
        if (raw.length !== 6) { setPincodeInfo(null); return }
        if (pincodeDebounce.current) clearTimeout(pincodeDebounce.current)
        pincodeDebounce.current = setTimeout(async () => {
            setPincodeLoading(true)
            try {
                const res = await pincodeApi.check(raw)
                const info = res.data?.data ?? res.data
                setPincodeInfo(info)
                if (info?.city) setValue('delivery_city', info.city)
                if (info?.state) setValue('delivery_state', info.state)
            } catch {
                setPincodeInfo({ serviceable: false })
            } finally {
                setPincodeLoading(false)
            }
        }, 400)
        return () => { if (pincodeDebounce.current) clearTimeout(pincodeDebounce.current) }
    }, [watchedPincode, setValue])

    // Fetch saved addresses if user is logged in
    const { data: addressesData } = useQuery({
        queryKey: ['addresses'],
        queryFn: () => authApi.getAddresses(),
        enabled: isAuthenticated,
    })

    const addresses = addressesData?.data || []
    const defaultAddress = addresses.find((addr: any) => addr.is_default)

    // Auto-fill user data on mount
    useEffect(() => {
        if (isAuthenticated && user) {
            setValue('customer_name', user.full_name)
            setValue('customer_phone', user.phone || '')
            setValue('customer_email', user.email)

            // Auto-fill default address
            if (defaultAddress) {
                const addressText = `${defaultAddress.address_line1}${defaultAddress.address_line2 ? ', ' + defaultAddress.address_line2 : ''}`
                setValue('delivery_address', addressText)
                setValue('delivery_city', defaultAddress.city)
                setValue('delivery_state', defaultAddress.state)
                setValue('delivery_pincode', defaultAddress.pincode)
                setValue('delivery_landmark', defaultAddress.landmark || '')
            }
        }
    }, [isAuthenticated, user, defaultAddress, setValue])

    const createOrderMutation = useMutation({
        mutationFn: (data: any) => orderApi.createOrder(data),
        onSuccess: (response, variables) => {
            const orderNumber = response.data.data.order_number
            const paymentMethod = variables.payment_method

            clearCart()

            // Redirect to payment page for online payments
            if (paymentMethod === 'ONLINE') {
                toast.success('Order created! Please complete payment.')
                navigate(`/payment/${orderNumber}`)
            } else {
                // COD orders go directly to success page
                toast.success('Order placed successfully!')
                navigate(`/order-success/${orderNumber}`)
            }
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to place order')
        },
    })

    const onSubmit = (data: CheckoutForm) => {
        const orderData = {
            ...data,
            // Ensure email is always included for logged-in users
            customer_email: data.customer_email || user?.email || '',
            items: items.map(item => ({
                product_id: item.product_id,
                quantity: item.quantity,
            })),
            coupon_code: couponData?.code,
            coupon_id: couponData?.coupon_id,
        }
        createOrderMutation.mutate(orderData)
    }

    const useAddress = (address: any) => {
        const addressText = `${address.address_line1}${address.address_line2 ? ', ' + address.address_line2 : ''}`
        setValue('customer_name', address.full_name)
        setValue('customer_phone', address.phone)
        setValue('delivery_address', addressText)
        setValue('delivery_city', address.city)
        setValue('delivery_state', address.state)
        setValue('delivery_pincode', address.pincode)
        setValue('delivery_landmark', address.landmark || '')
        setShowAddresses(false)
        toast.success('Address filled successfully!')
    }

    if (items.length === 0) {
        navigate('/cart')
        return null
    }

    const STEPS = [
        { id: 1, label: 'Delivery Details', icon: '📍' },
        { id: 2, label: 'Payment Method', icon: '💳' },
        { id: 3, label: 'Review & Place', icon: '✅' },
    ]

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold mb-6 text-text-primary">Checkout</h1>

            {/* ── Progress stepper ── */}
            <div className="card mb-8 py-4">
                <div className="flex items-center">
                    {STEPS.map((step, i) => (
                        <div key={step.id} className="flex items-center flex-1">
                            <div className="flex flex-col items-center gap-1 flex-none">
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold transition-all ${step.id <= 2
                                        ? 'bg-theme-primary text-white shadow-md shadow-theme-primary/30'
                                        : 'bg-bg-tertiary text-text-tertiary'
                                    }`}>
                                    {step.icon}
                                </div>
                                <span className={`text-xs font-medium text-center leading-tight hidden sm:block ${step.id <= 2 ? 'text-theme-primary' : 'text-text-tertiary'
                                    }`}>
                                    {step.label}
                                </span>
                            </div>
                            {i < STEPS.length - 1 && (
                                <div className={`flex-1 h-0.5 mx-2 rounded-full ${step.id < 2 ? 'bg-theme-primary' : 'bg-bg-tertiary'
                                    }`} />
                            )}
                        </div>
                    ))}
                </div>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} className="grid lg:grid-cols-3 gap-8">
                {/* Delivery Details */}
                <div className="lg:col-span-2 space-y-6">
                    <div className="card">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-bold text-text-primary">Delivery Details</h2>
                            {isAuthenticated && addresses.length > 0 && (
                                <button
                                    type="button"
                                    onClick={() => setShowAddresses(!showAddresses)}
                                    className="text-sm text-theme-primary hover:text-theme-primary-hover font-medium"
                                >
                                    {showAddresses ? 'Hide Addresses' : 'Choose Saved Address'}
                                </button>
                            )}
                        </div>

                        {/* Saved Addresses */}
                        {isAuthenticated && showAddresses && addresses.length > 0 && (
                            <div className="mb-6 grid md:grid-cols-2 gap-4">
                                {addresses.map((address: any) => (
                                    <div
                                        key={address.id}
                                        onClick={() => useAddress(address)}
                                        className="border border-border-color rounded-lg p-4 cursor-pointer hover:border-theme-primary hover:bg-bg-tertiary transition-colors relative"
                                    >
                                        {address.is_default && (
                                            <span className="absolute top-2 right-2 px-2 py-1 bg-theme-primary bg-opacity-10 text-theme-primary text-xs rounded">
                                                Default
                                            </span>
                                        )}
                                        <div className="flex items-start space-x-3">
                                            <MapPin className="h-5 w-5 text-text-tertiary mt-1 flex-shrink-0" />
                                            <div>
                                                <p className="font-semibold text-text-primary">{address.full_name}</p>
                                                <p className="text-sm text-text-secondary">{address.phone}</p>
                                                <p className="text-sm text-text-secondary mt-1">
                                                    {address.address_line1}
                                                    {address.address_line2 && `, ${address.address_line2}`}
                                                </p>
                                                <p className="text-sm text-text-secondary">
                                                    {address.city}, {address.state} - {address.pincode}
                                                </p>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        <div className="grid md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium mb-1">Full Name *</label>
                                <input {...register('customer_name')} className="input" />
                                {errors.customer_name && (
                                    <p className="text-red-600 text-sm mt-1">{errors.customer_name.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Phone Number *</label>
                                <input {...register('customer_phone')} placeholder="+919876543210" className="input" />
                                {errors.customer_phone && (
                                    <p className="text-red-600 text-sm mt-1">{errors.customer_phone.message}</p>
                                )}
                            </div>

                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium mb-1">Email (Optional)</label>
                                <input {...register('customer_email')} type="email" className="input" />
                                {errors.customer_email && (
                                    <p className="text-red-600 text-sm mt-1">{errors.customer_email.message}</p>
                                )}
                            </div>

                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium mb-1">Address *</label>
                                <textarea {...register('delivery_address')} rows={3} className="input" />
                                {errors.delivery_address && (
                                    <p className="text-red-600 text-sm mt-1">{errors.delivery_address.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">City *</label>
                                <input {...register('delivery_city')} className="input" />
                                {errors.delivery_city && (
                                    <p className="text-red-600 text-sm mt-1">{errors.delivery_city.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">State *</label>
                                <input {...register('delivery_state')} className="input" />
                                {errors.delivery_state && (
                                    <p className="text-red-600 text-sm mt-1">{errors.delivery_state.message}</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Pincode *</label>
                                <div className="relative">
                                    <input {...register('delivery_pincode')} placeholder="400001" className="input pr-9" maxLength={6} />
                                    {pincodeLoading && (
                                        <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 animate-spin text-text-tertiary" />
                                    )}
                                    {!pincodeLoading && pincodeInfo && (
                                        pincodeInfo.serviceable
                                            ? <Check className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-green-500" />
                                            : <X className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-red-500" />
                                    )}
                                </div>
                                {errors.delivery_pincode && (
                                    <p className="text-red-600 text-sm mt-1">{errors.delivery_pincode.message}</p>
                                )}
                                {pincodeInfo?.serviceable && pincodeInfo.standard_days != null && (
                                    <p className="text-xs text-green-600 mt-1 flex items-center gap-1">
                                        <Truck className="h-3 w-3" />
                                        Delivery available · Est. {pincodeInfo.standard_days} day{pincodeInfo.standard_days !== 1 ? 's' : ''}
                                    </p>
                                )}
                                {pincodeInfo && !pincodeInfo.serviceable && (
                                    <p className="text-xs text-red-600 mt-1">Delivery not available to this pincode</p>
                                )}
                            </div>

                            <div>
                                <label className="block text-sm font-medium mb-1">Landmark (Optional)</label>
                                <input {...register('delivery_landmark')} className="input" />
                            </div>

                            <div className="md:col-span-2">
                                <label className="block text-sm font-medium mb-1">Order Notes (Optional)</label>
                                <textarea {...register('notes')} rows={2} className="input" />
                            </div>
                        </div>
                    </div>

                    {/* Payment Method */}
                    <div className="card">
                        <h2 className="text-xl font-bold mb-4 text-text-primary">Payment Method</h2>

                        <div className="space-y-3">
                            <label className="flex items-center space-x-3 p-4 border border-border-color rounded-lg cursor-pointer hover:bg-bg-tertiary">
                                <input {...register('payment_method')} type="radio" value="COD" className="text-theme-primary" />
                                <div>
                                    <p className="font-medium">Cash on Delivery</p>
                                    <p className="text-sm text-text-secondary">Pay when you receive your order</p>
                                </div>
                            </label>

                            <label className="flex items-center space-x-3 p-4 border border-border-color rounded-lg cursor-pointer hover:bg-bg-tertiary">
                                <input {...register('payment_method')} type="radio" value="ONLINE" className="text-theme-primary" />
                                <div>
                                    <p className="font-medium">Online Payment</p>
                                    <p className="text-sm text-text-secondary">Pay with Card, UPI, or Net Banking</p>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>

                {/* Order Summary */}
                <div className="lg:col-span-1">
                    <div className="card sticky top-24">
                        <h2 className="text-xl font-bold mb-4 text-text-primary">Order Summary</h2>

                        <div className="space-y-3 mb-4">
                            {items.map(item => (
                                <div key={item.product_id} className="flex justify-between text-sm">
                                    <span className="text-text-secondary">{item.name} x {item.quantity}</span>
                                    <span className="font-medium text-text-primary">₹{(item.price * item.quantity).toFixed(2)}</span>
                                </div>
                            ))}
                        </div>

                        <div className="border-t border-border-color pt-4 space-y-2 mb-4">
                            <div className="flex justify-between">
                                <span className="text-text-secondary">Subtotal</span>
                                <span className="font-medium text-text-primary">₹{subtotal.toFixed(2)}</span>
                            </div>
                            {discount > 0 && (
                                <div className="flex justify-between text-green-600 dark:text-green-400">
                                    <span>Coupon ({couponData?.code})</span>
                                    <span className="font-medium">-₹{discount.toFixed(2)}</span>
                                </div>
                            )}
                            <div className="flex justify-between">
                                <span className="text-text-secondary">Delivery</span>
                                <span className={`font-medium ${freeShipping ? 'text-green-600' : 'text-text-primary'}`}>
                                    {freeShipping ? 'FREE (Coupon)' : 'FREE'}
                                </span>
                            </div>
                        </div>

                        {/* Coupon Input */}
                        <div className="mb-4">
                            {couponData ? (
                                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
                                    <div className="flex items-center gap-2">
                                        <Check className="h-4 w-4 text-green-600" />
                                        <span className="text-sm font-semibold text-green-700 dark:text-green-300">
                                            {couponData.code} applied
                                        </span>
                                    </div>
                                    <button aria-label="Remove coupon" onClick={removeCoupon} className="text-text-tertiary hover:text-red-500">
                                        <X className="h-4 w-4" />
                                    </button>
                                </div>
                            ) : (
                                <div className="flex gap-2">
                                    <div className="relative flex-1">
                                        <Tag className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary" />
                                        <input
                                            type="text"
                                            value={couponCode}
                                            onChange={(e) => setCouponCode(e.target.value.toUpperCase())}
                                            onKeyDown={(e) => e.key === 'Enter' && applyCoupon()}
                                            placeholder="Coupon code"
                                            className="input pl-9 text-sm"
                                        />
                                    </div>
                                    <button
                                        type="button"
                                        onClick={applyCoupon}
                                        disabled={couponLoading || !couponCode}
                                        className="btn btn-outline btn-sm px-4 whitespace-nowrap"
                                    >
                                        {couponLoading ? '...' : 'Apply'}
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="border-t border-border-color pt-4 mb-6">
                            <div className="flex justify-between text-lg font-bold">
                                <span className="text-text-primary">Total</span>
                                <span className="text-text-primary">₹{finalTotal.toFixed(2)}</span>
                            </div>
                            {discount > 0 && (
                                <p className="text-xs text-green-600 dark:text-green-400 text-right mt-1">
                                    You save ₹{discount.toFixed(2)} with coupon
                                </p>
                            )}
                        </div>

                        <button
                            type="submit"
                            disabled={createOrderMutation.isPending}
                            className="w-full btn btn-primary disabled:opacity-50"
                        >
                            {createOrderMutation.isPending ? 'Placing Order...' : 'Place Order'}
                        </button>

                        {!isAuthenticated && (
                            <p className="text-sm text-text-secondary mt-4 text-center">
                                Want to save your addresses?{' '}
                                <a href="/login" className="text-theme-primary hover:text-theme-primary-hover font-medium">
                                    Login
                                </a>
                            </p>
                        )}
                    </div>
                </div>
            </form>
        </div>
    )
}
