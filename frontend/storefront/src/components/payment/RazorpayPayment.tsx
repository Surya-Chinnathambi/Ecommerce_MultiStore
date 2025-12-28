import React, { useState, useEffect } from 'react';
import { api } from '../../lib/api';

interface RazorpayPaymentProps {
    orderId: string;
    amount: number;
    currency: string;
    customerName: string;
    customerEmail: string;
    customerPhone: string;
    onSuccess: (paymentId: string) => void;
    onError: (error: string) => void;
}

declare global {
    interface Window {
        Razorpay: any;
    }
}

const RazorpayPayment: React.FC<RazorpayPaymentProps> = ({
    orderId,
    amount,
    currency,
    customerName,
    customerEmail,
    customerPhone,
    onSuccess,
    onError
}) => {
    const [loading, setLoading] = useState(false);
    const [razorpayLoaded, setRazorpayLoaded] = useState(false);

    useEffect(() => {
        // Load Razorpay script
        const script = document.createElement('script');
        script.src = 'https://checkout.razorpay.com/v1/checkout.js';
        script.async = true;
        script.onload = () => setRazorpayLoaded(true);
        document.body.appendChild(script);

        return () => {
            document.body.removeChild(script);
        };
    }, []);

    const handlePayment = async () => {
        if (!razorpayLoaded) {
            onError('Razorpay SDK not loaded');
            return;
        }

        setLoading(true);

        try {
            // Create payment intent
            const response = await api.post('/payments/intent', {
                order_id: orderId,
                payment_gateway: 'razorpay',
                payment_method: 'card'
            });

            const { razorpay_order_id, razorpay_key_id, payment_id } = response.data;

            // Configure Razorpay options
            const options = {
                key: razorpay_key_id,
                amount: amount * 100, // Convert to paise
                currency: currency,
                name: 'Your Store Name',
                description: `Order #${orderId}`,
                order_id: razorpay_order_id,
                handler: async function (response: any) {
                    try {
                        // Verify payment with our backend
                        await api.post('/payments/confirm', {
                            payment_id: payment_id,
                            gateway_payment_id: response.razorpay_payment_id,
                            gateway_signature: response.razorpay_signature
                        });

                        onSuccess(payment_id);
                    } catch (error: any) {
                        onError(error.response?.data?.detail || 'Payment verification failed');
                    }
                },
                prefill: {
                    name: customerName,
                    email: customerEmail,
                    contact: customerPhone
                },
                theme: {
                    color: '#3B82F6'
                },
                modal: {
                    ondismiss: function () {
                        setLoading(false);
                        onError('Payment cancelled');
                    }
                }
            };

            // Open Razorpay checkout
            const razorpay = new window.Razorpay(options);
            razorpay.open();

            razorpay.on('payment.failed', function (response: any) {
                onError(response.error.description || 'Payment failed');
                setLoading(false);
            });

        } catch (error: any) {
            onError(error.response?.data?.detail || 'Failed to initialize payment');
            setLoading(false);
        }
    };

    return (
        <div className="space-y-4">
            <div className="bg-bg-primary p-6 rounded-lg border border-border-color">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-semibold text-text-primary">Razorpay Payment</h3>
                        <p className="text-sm text-text-secondary">
                            Pay securely with Card, UPI, Net Banking, or Wallets
                        </p>
                    </div>
                    <img
                        src="/razorpay-logo.png"
                        alt="Razorpay"
                        className="h-8"
                    />
                </div>

                <div className="bg-bg-tertiary p-4 rounded-lg mb-4">
                    <div className="flex justify-between items-center">
                        <span className="text-sm text-text-secondary">Total Amount</span>
                        <span className="text-lg font-semibold text-text-primary">
                            ₹{amount.toFixed(2)}
                        </span>
                    </div>
                </div>

                <div className="space-y-2 mb-4">
                    <div className="flex items-center text-sm text-text-secondary">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Supports all major payment methods
                    </div>
                    <div className="flex items-center text-sm text-text-secondary">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        Instant payment confirmation
                    </div>
                    <div className="flex items-center text-sm text-text-secondary">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        100% secure and encrypted
                    </div>
                </div>

                <button
                    onClick={handlePayment}
                    disabled={loading || !razorpayLoaded}
                    className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${loading || !razorpayLoaded
                        ? 'bg-gray-400 cursor-not-allowed'
                        : 'bg-theme-primary hover:bg-theme-primary-hover'
                        }`}
                >
                    {loading ? (
                        <span className="flex items-center justify-center">
                            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Processing...
                        </span>
                    ) : !razorpayLoaded ? (
                        'Loading...'
                    ) : (
                        `Pay ₹${amount.toFixed(2)}`
                    )}
                </button>

                <p className="text-xs text-text-tertiary text-center mt-3">
                    🔒 Secured by Razorpay. Your payment information is safe.
                </p>
            </div>
        </div>
    );
};

export default RazorpayPayment;
