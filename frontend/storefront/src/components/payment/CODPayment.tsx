import React from 'react';

interface CODPaymentProps {
    orderId: string;
    amount: number;
    currency: string;
    onConfirm: () => void;
}

const CODPayment: React.FC<CODPaymentProps> = ({
    amount,
    currency,
    onConfirm
}) => {
    return (
        <div className="space-y-4">
            <div className="bg-bg-primary p-6 rounded-lg border border-border-color">
                <div className="flex items-center justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-semibold text-text-primary">Cash on Delivery</h3>
                        <p className="text-sm text-text-secondary">
                            Pay when your order is delivered
                        </p>
                    </div>
                    <div className="bg-green-100 p-3 rounded-full">
                        <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                        </svg>
                    </div>
                </div>

                <div className="bg-bg-tertiary p-4 rounded-lg mb-4">
                    <div className="flex justify-between items-center mb-3">
                        <span className="text-sm text-text-secondary">Amount to Pay</span>
                        <span className="text-2xl font-bold text-text-primary">
                            {currency} {amount.toFixed(2)}
                        </span>
                    </div>
                    <p className="text-xs text-text-tertiary">
                        Please keep exact change ready for smooth delivery
                    </p>
                </div>

                <div className="space-y-3 mb-6">
                    <div className="flex items-start">
                        <svg className="w-5 h-5 text-theme-primary mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <div>
                            <p className="text-sm font-medium text-text-primary">No advance payment needed</p>
                            <p className="text-xs text-text-tertiary">Pay only when you receive your order</p>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <svg className="w-5 h-5 text-theme-primary mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <div>
                            <p className="text-sm font-medium text-text-primary">Verify before payment</p>
                            <p className="text-xs text-text-tertiary">Check your order before making the payment</p>
                        </div>
                    </div>

                    <div className="flex items-start">
                        <svg className="w-5 h-5 text-theme-primary mr-3 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        <div>
                            <p className="text-sm font-medium text-text-primary">Cash or UPI accepted</p>
                            <p className="text-xs text-text-tertiary">Pay via cash or scan UPI QR at delivery</p>
                        </div>
                    </div>
                </div>

                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                    <div className="flex">
                        <svg className="w-5 h-5 text-yellow-600 mr-2" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                        </svg>
                        <div>
                            <p className="text-sm font-medium text-yellow-800">Important Note</p>
                            <p className="text-xs text-yellow-700 mt-1">
                                COD orders may have limited availability in certain areas. Please ensure someone is available to receive the order at the delivery address.
                            </p>
                        </div>
                    </div>
                </div>

                <button
                    onClick={onConfirm}
                    className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
                >
                    Confirm Cash on Delivery
                </button>

                <p className="text-xs text-text-tertiary text-center mt-3">
                    By confirming, you agree to pay cash at the time of delivery
                </p>
            </div>
        </div>
    );
};

export default CODPayment;
