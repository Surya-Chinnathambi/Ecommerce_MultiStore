import React, { useState, useEffect } from 'react';
import StripePayment from './StripePayment';
import RazorpayPayment from './RazorpayPayment';
import CODPayment from './CODPayment';
import { api } from '../../lib/api';

interface PaymentMethod {
    gateway: string;
    name: string;
    enabled: boolean;
    supported_methods: string[];
    min_amount?: number;
    max_amount?: number;
    transaction_fee_percent?: number;
}

interface PaymentGatewayProps {
    orderId: string;
    amount: number;
    currency: string;
    customerName: string;
    customerEmail: string;
    customerPhone: string;
    onSuccess: (paymentId: string) => void;
    onError: (error: string) => void;
}

const PaymentGateway: React.FC<PaymentGatewayProps> = ({
    orderId,
    amount,
    currency,
    customerName,
    customerEmail,
    customerPhone,
    onSuccess,
    onError
}) => {
    const [paymentMethods, setPaymentMethods] = useState<PaymentMethod[]>([]);
    const [selectedGateway, setSelectedGateway] = useState<string>('');
    const [loading, setLoading] = useState(true);
    const [, setCodProcessing] = useState(false);

    useEffect(() => {
        fetchPaymentMethods();
    }, []);

    const fetchPaymentMethods = async () => {
        try {
            const response = await api.get('/payments/methods');
            const methods = response.data.filter((m: PaymentMethod) => m.enabled);
            setPaymentMethods(methods);

            // Auto-select first available method
            if (methods.length > 0) {
                setSelectedGateway(methods[0].gateway);
            }

            setLoading(false);
        } catch (error) {
            console.error('Failed to fetch payment methods:', error);
            onError('Failed to load payment methods');
            setLoading(false);
        }
    };

    const handleCODConfirm = async () => {
        setCodProcessing(true);
        try {
            // Create COD payment intent
            const intentResponse = await api.post('/payments/intent', {
                order_id: orderId,
                payment_gateway: 'cod',
                payment_method: 'cod'
            });

            const paymentId = intentResponse.data.payment_id;

            // Confirm COD payment
            await api.post('/payments/confirm', {
                payment_id: paymentId,
                gateway_payment_id: `COD-${orderId}`
            });

            onSuccess(paymentId);
        } catch (error: any) {
            onError(error.response?.data?.detail || 'Failed to process COD payment');
        } finally {
            setCodProcessing(false);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-theme-primary"></div>
            </div>
        );
    }

    if (paymentMethods.length === 0) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
                <svg className="w-12 h-12 text-red-500 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-lg font-semibold text-text-primary mb-2">No Payment Methods Available</h3>
                <p className="text-sm text-text-secondary">
                    Please contact support to enable payment methods for your account.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Payment Method Selector */}
            <div>
                <h3 className="text-lg font-semibold mb-4 text-text-primary">Select Payment Method</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {paymentMethods.map((method) => (
                        <button
                            key={method.gateway}
                            onClick={() => setSelectedGateway(method.gateway)}
                            className={`p-4 border-2 rounded-lg transition-all ${selectedGateway === method.gateway
                                ? 'border-theme-primary bg-theme-primary/10'
                                : 'border-border-color hover:border-border-color/70 bg-bg-primary'
                                }`}
                        >
                            <div className="flex flex-col items-center text-center">
                                <div className="mb-2">
                                    {method.gateway === 'stripe' && (
                                        <img src="/stripe-logo.svg" alt="Stripe" className="h-8" />
                                    )}
                                    {method.gateway === 'razorpay' && (
                                        <div className="text-2xl font-bold text-blue-600">Razorpay</div>
                                    )}
                                    {method.gateway === 'cod' && (
                                        <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                                        </svg>
                                    )}
                                </div>
                                <p className="font-medium text-text-primary">{method.name}</p>
                                <p className="text-xs text-text-tertiary mt-1">
                                    {method.transaction_fee_percent && method.transaction_fee_percent > 0
                                        ? `${method.transaction_fee_percent}% fee`
                                        : 'No fees'}
                                </p>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Payment Form */}
            <div>
                {selectedGateway === 'stripe' && (
                    <StripePayment
                        orderId={orderId}
                        amount={amount}
                        currency={currency}
                        onSuccess={onSuccess}
                        onError={onError}
                    />
                )}

                {selectedGateway === 'razorpay' && (
                    <RazorpayPayment
                        orderId={orderId}
                        amount={amount}
                        currency={currency}
                        customerName={customerName}
                        customerEmail={customerEmail}
                        customerPhone={customerPhone}
                        onSuccess={onSuccess}
                        onError={onError}
                    />
                )}

                {selectedGateway === 'cod' && (
                    <CODPayment
                        orderId={orderId}
                        amount={amount}
                        currency={currency}
                        onConfirm={handleCODConfirm}
                    />
                )}
            </div>

            {/* Security Badges */}
            <div className="bg-bg-tertiary rounded-lg p-4">
                <div className="flex items-center justify-center space-x-6 text-sm text-text-secondary">
                    <div className="flex items-center">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span>Secure Payment</span>
                    </div>
                    <div className="flex items-center">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
                        </svg>
                        <span>256-bit Encryption</span>
                    </div>
                    <div className="flex items-center">
                        <svg className="w-5 h-5 text-green-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <span>PCI Compliant</span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default PaymentGateway;
