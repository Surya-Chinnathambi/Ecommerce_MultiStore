import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Store, CheckCircle, AlertCircle } from 'lucide-react'
import { sellerApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'

export default function SellerRegisterPage() {
    const navigate = useNavigate()
    const [step, setStep] = useState(1)
    const [loading, setLoading] = useState(false)
    const [form, setForm] = useState({
        business_name: '',
        display_name: '',
        business_type: 'individual',
        gstin: '',
        pan: '',
        phone: '',
        address: '',
        city: '',
        state: '',
        pincode: '',
        bank_account_name: '',
        bank_account_number: '',
        bank_ifsc: '',
        bank_name: '',
        description: '',
    })

    const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }))

    const handleSubmit = async () => {
        setLoading(true)
        try {
            await sellerApi.register(form)
            toast.success("Application submitted! We'll review and approve within 24 hours.")
            navigate('/seller/dashboard')
        } catch (e: any) {
            toast.error(e.response?.data?.detail || 'Registration failed')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="bg-bg-secondary min-h-screen animate-fade-in">
            <div className="container mx-auto px-4 py-8 max-w-2xl">
                {/* Header */}
                <div className="text-center mb-8">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-theme-primary/10 mb-4">
                        <Store className="h-8 w-8 text-theme-primary" />
                    </div>
                    <h1 className="text-3xl font-bold text-text-primary mb-2">Become a Seller</h1>
                    <p className="text-text-secondary">Start selling to millions of customers</p>
                </div>

                {/* Step Indicator */}
                <div className="flex items-center justify-center gap-2 mb-8">
                    {[1, 2, 3].map((s) => (
                        <div key={s} className={`flex items-center ${s < 3 ? 'flex-1' : ''}`}>
                            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold transition-colors
                                ${step >= s ? 'bg-theme-primary text-white' : 'bg-bg-tertiary text-text-tertiary'}`}>
                                {step > s ? <CheckCircle className="h-5 w-5" /> : s}
                            </div>
                            {s < 3 && (
                                <div className={`flex-1 h-0.5 mx-2 ${step > s ? 'bg-theme-primary' : 'bg-border-color'}`} />
                            )}
                        </div>
                    ))}
                </div>

                <div className="card p-6">
                    {/* Step 1: Business Info */}
                    {step === 1 && (
                        <div className="space-y-4">
                            <h2 className="text-xl font-bold text-text-primary mb-4">Business Information</h2>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Business Name *</label>
                                    <input className="input" value={form.business_name}
                                        onChange={(e) => set('business_name', e.target.value)}
                                        placeholder="Legal business name" />
                                </div>
                                <div>
                                    <label className="label">Display Name *</label>
                                    <input className="input" value={form.display_name}
                                        onChange={(e) => set('display_name', e.target.value)}
                                        placeholder="Name shown to customers" />
                                </div>
                            </div>

                            <div>
                                <label className="label">Business Type</label>
                                <select title="Business type" className="input" value={form.business_type}
                                    onChange={(e) => set('business_type', e.target.value)}>
                                    <option value="individual">Individual / Sole Proprietor</option>
                                    <option value="partnership">Partnership</option>
                                    <option value="private_limited">Private Limited</option>
                                    <option value="llp">LLP</option>
                                    <option value="public_limited">Public Limited</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">GSTIN</label>
                                    <input className="input" value={form.gstin}
                                        onChange={(e) => set('gstin', e.target.value)}
                                        placeholder="22AAAAA0000A1Z5" maxLength={15} />
                                </div>
                                <div>
                                    <label className="label">PAN</label>
                                    <input className="input" value={form.pan}
                                        onChange={(e) => set('pan', e.target.value.toUpperCase())}
                                        placeholder="AAAPL1234C" maxLength={10} />
                                </div>
                            </div>

                            <div>
                                <label className="label">Phone *</label>
                                <input className="input" type="tel" value={form.phone}
                                    onChange={(e) => set('phone', e.target.value)}
                                    placeholder="+91 xxx xxx xxxx" />
                            </div>

                            <div>
                                <label className="label">Description</label>
                                <textarea className="input resize-none h-24" value={form.description}
                                    onChange={(e) => set('description', e.target.value)}
                                    placeholder="Tell customers about your business..." />
                            </div>

                            <button
                                onClick={() => setStep(2)}
                                disabled={!form.business_name || !form.display_name || !form.phone}
                                className="w-full btn btn-primary"
                            >
                                Continue
                            </button>
                        </div>
                    )}

                    {/* Step 2: Address */}
                    {step === 2 && (
                        <div className="space-y-4">
                            <h2 className="text-xl font-bold text-text-primary mb-4">Business Address</h2>

                            <div>
                                <label className="label">Address *</label>
                                <textarea className="input resize-none h-20" value={form.address}
                                    onChange={(e) => set('address', e.target.value)}
                                    placeholder="Street address, locality..." />
                            </div>

                            <div className="grid grid-cols-3 gap-4">
                                <div>
                                    <label className="label">City *</label>
                                    <input className="input" title="City" placeholder="Mumbai" value={form.city}
                                        onChange={(e) => set('city', e.target.value)} />
                                </div>
                                <div>
                                    <label className="label">State *</label>
                                    <input className="input" title="State" placeholder="Maharashtra" value={form.state}
                                        onChange={(e) => set('state', e.target.value)} />
                                </div>
                                <div>
                                    <label className="label">Pincode *</label>
                                    <input className="input" title="Pincode" placeholder="400001" value={form.pincode}
                                        onChange={(e) => set('pincode', e.target.value)}
                                        maxLength={6} />
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <button onClick={() => setStep(1)} className="btn btn-ghost flex-1">Back</button>
                                <button
                                    onClick={() => setStep(3)}
                                    disabled={!form.address || !form.city || !form.state || !form.pincode}
                                    className="btn btn-primary flex-1"
                                >
                                    Continue
                                </button>
                            </div>
                        </div>
                    )}

                    {/* Step 3: Bank details */}
                    {step === 3 && (
                        <div className="space-y-4">
                            <h2 className="text-xl font-bold text-text-primary mb-4">Bank Account Details</h2>
                            <p className="text-sm text-text-secondary">Your payouts will be credited to this account.</p>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Account Holder Name *</label>
                                    <input className="input" title="Account holder name" placeholder="Full name as on account" value={form.bank_account_name}
                                        onChange={(e) => set('bank_account_name', e.target.value)} />
                                </div>
                                <div>
                                    <label className="label">Bank Name *</label>
                                    <input className="input" title="Bank name" value={form.bank_name}
                                        onChange={(e) => set('bank_name', e.target.value)}
                                        placeholder="SBI, HDFC, ICICI..." />
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="label">Account Number *</label>
                                    <input className="input" type="text" title="Account number" placeholder="00001234567890" value={form.bank_account_number}
                                        onChange={(e) => set('bank_account_number', e.target.value)} />
                                </div>
                                <div>
                                    <label className="label">IFSC Code *</label>
                                    <input className="input" value={form.bank_ifsc}
                                        onChange={(e) => set('bank_ifsc', e.target.value.toUpperCase())}
                                        placeholder="SBIN0001234" maxLength={11} />
                                </div>
                            </div>

                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-xl p-4 border border-blue-200 dark:border-blue-800">
                                <div className="flex gap-2">
                                    <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 mt-0.5 flex-shrink-0" />
                                    <p className="text-xs text-blue-700 dark:text-blue-300">
                                        By registering, you agree to our Seller Terms of Service. Your application will be reviewed within 24 hours.
                                    </p>
                                </div>
                            </div>

                            <div className="flex gap-3">
                                <button onClick={() => setStep(2)} className="btn btn-ghost flex-1">Back</button>
                                <button
                                    onClick={handleSubmit}
                                    disabled={loading || !form.bank_account_name || !form.bank_account_number || !form.bank_ifsc}
                                    className="btn btn-primary flex-1"
                                >
                                    {loading ? 'Submitting...' : 'Submit Application'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
