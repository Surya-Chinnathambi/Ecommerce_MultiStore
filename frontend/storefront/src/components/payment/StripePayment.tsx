import React, { useState, useEffect } from 'react';
import { loadStripe, Stripe } from '@stripe/stripe-js';
import { Elements, CardElement, useStripe, useElements } from '@stripe/react-stripe-js';
import { api } from '../../lib/api';

// Initialize Stripe (will be set from payment intent response)
let stripePromise: Promise<Stripe | null> | null = null;

interface StripePaymentFormProps {
    orderId: string;
    amount: number;
    currency: string;
    onSuccess: (paymentId: string) => void;
    onError: (error: string) => void;
}

const StripePaymentForm: React.FC<StripePaymentFormProps> = ({
    orderId,
    amount,
    currency,
    onSuccess,
    onError
}) => {
    const stripe = useStripe();
    const elements = useElements();
    const [processing, setProcessing] = useState(false);
    const [clientSecret, setClientSecret] = useState<string>('');
    const [paymentId, setPaymentId] = useState<string>('');

    useEffect(() => {
        // Create payment intent when component mounts
        const createPaymentIntent = async () => {
            try {
                const response = await api.post('/payments/intent', {
                    order_id: orderId,
                    payment_gateway: 'stripe',
                    payment_method: 'card'
                });

                setClientSecret(response.data.client_secret);
                setPaymentId(response.data.payment_id);
            } catch (error: any) {
                onError(error.response?.data?.detail || 'Failed to initialize payment');
            }
        };

        createPaymentIntent();
    }, [orderId]);

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();

        if (!stripe || !elements || !clientSecret) {
            return;
        }

        setProcessing(true);

        const cardElement = elements.getElement(CardElement);

        if (!cardElement) {
            onError('Card element not found');
            setProcessing(false);
            return;
        }

        try {
            // Confirm the payment with Stripe
            const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
                payment_method: {
                    card: cardElement,
                },
            });

            if (error) {
                onError(error.message || 'Payment failed');
                setProcessing(false);
            } else if (paymentIntent.status === 'succeeded') {
                // Confirm payment with our backend
                await api.post('/payments/confirm', {
                    payment_id: paymentId,
                    gateway_payment_id: paymentIntent.id
                });

                onSuccess(paymentId);
            }
        } catch (error: any) {
            onError(error.response?.data?.detail || 'Payment processing failed');
            setProcessing(false);
        }
    };

    const cardElementOptions = {
        style: {
            base: {
                fontSize: '16px',
                color: '#424770',
                '::placeholder': {
                    color: '#aab7c4',
                },
            },
            invalid: {
                color: '#9e2146',
            },
        },
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div className="bg-bg-primary p-4 rounded-lg border border-border-color">
                <label className="block text-sm font-medium text-text-primary mb-2">
                    Card Details
                </label>
                <CardElement options={cardElementOptions} />
            </div>

            <div className="bg-bg-tertiary p-4 rounded-lg">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-text-secondary">Amount</span>
                    <span className="text-lg font-semibold text-text-primary">
                        {currency} {amount.toFixed(2)}
                    </span>
                </div>
            </div>

            <button
                type="submit"
                disabled={!stripe || processing || !clientSecret}
                className={`w-full py-3 px-4 rounded-lg font-medium text-white transition-colors ${processing || !stripe || !clientSecret
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-theme-primary hover:bg-theme-primary-hover'
                    }`}
            >
                {processing ? (
                    <span className="flex items-center justify-center">
                        <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Processing...
                    </span>
                ) : (
                    `Pay ${currency} ${amount.toFixed(2)}`
                )}
            </button>

            <p className="text-xs text-text-tertiary text-center mt-2">
                🔒 Secured by Stripe. Your payment information is encrypted.
            </p>
        </form>
    );
};

interface StripePaymentProps {
    orderId: string;
    amount: number;
    currency: string;
    onSuccess: (paymentId: string) => void;
    onError: (error: string) => void;
}

const StripePayment: React.FC<StripePaymentProps> = (props) => {
    // Initialize Stripe with a default key (will be updated from backend)
    if (!stripePromise) {
        // You can set a default publishable key here or fetch it from backend
        stripePromise = loadStripe(import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY || '');
    }

    return (
        <Elements stripe={stripePromise}>
            <StripePaymentForm {...props} />
        </Elements>
    );
};

export default StripePayment;
