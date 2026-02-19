import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { adminApi } from '@/lib/api'
import { toast } from '@/components/ui/Toaster'
import {
    Settings, Store, User, MapPin, Palette, Loader2, Save, Globe
} from 'lucide-react'

interface StoreFormState {
    name: string
    logo_url: string
    city: string
    state: string
    address: string
    pincode: string
    owner_name: string
    owner_phone: string
    owner_email: string
    primary_color: string
    secondary_color: string
}

const DEFAULT_FORM: StoreFormState = {
    name: '',
    logo_url: '',
    city: '',
    state: '',
    address: '',
    pincode: '',
    owner_name: '',
    owner_phone: '',
    owner_email: '',
    primary_color: '#6366f1',
    secondary_color: '#8b5cf6',
}

export default function AdminSettingsPage() {
    const qc = useQueryClient()
    const [form, setForm] = useState<StoreFormState>(DEFAULT_FORM)

    const { data: storeData, isLoading } = useQuery({
        queryKey: ['admin-store-info'],
        queryFn: () => adminApi.getStoreSettings().then(r => r.data),
    })

    useEffect(() => {
        if (!storeData) return
        const s = storeData.store ?? storeData
        setForm({
            name: s.name ?? '',
            logo_url: s.logo_url ?? '',
            city: s.city ?? '',
            state: s.state ?? '',
            address: s.address ?? '',
            pincode: s.pincode ?? '',
            owner_name: s.owner_name ?? '',
            owner_phone: s.owner_phone ?? '',
            owner_email: s.owner_email ?? '',
            primary_color: s.primary_color ?? '#6366f1',
            secondary_color: s.secondary_color ?? '#8b5cf6',
        })
    }, [storeData])

    const mutation = useMutation({
        mutationFn: (data: StoreFormState) => adminApi.updateStoreSettings(data as unknown as Record<string, unknown>),
        onSuccess: () => {
            toast.success('Settings saved!')
            qc.invalidateQueries({ queryKey: ['admin-store-info'] })
            qc.invalidateQueries({ queryKey: ['store-info'] })
        },
        onError: (err: any) => {
            toast.error(err?.response?.data?.detail ?? 'Failed to save settings')
        },
    })

    const set = (field: keyof StoreFormState) => (e: React.ChangeEvent<HTMLInputElement>) =>
        setForm(prev => ({ ...prev, [field]: e.target.value }))

    function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        mutation.mutate(form)
    }

    if (isLoading) {
        return (
            <div className="container mx-auto px-4 py-8">
                <div className="space-y-4">
                    {[...Array(6)].map((_, i) => <div key={i} className="skeleton h-14 rounded-xl" />)}
                </div>
            </div>
        )
    }

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in max-w-3xl">
            <h1 className="section-title flex items-center gap-2 mb-1">
                <Settings className="h-6 w-6 text-theme-primary" />
                Store Settings
            </h1>
            <p className="section-subtitle mb-8">Update your store profile, branding and contact details</p>

            <form onSubmit={handleSubmit} className="space-y-6">

                {/* Store Identity */}
                <section className="card">
                    <h2 className="flex items-center gap-2 font-semibold text-text-primary mb-4">
                        <Store className="h-4 w-4 text-theme-primary" /> Store Identity
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="sm:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1">Store Name</label>
                            <input className="input w-full" placeholder="My Awesome Store" value={form.name} onChange={set('name')} />
                        </div>
                        <div className="sm:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1">Logo URL</label>
                            <div className="flex gap-3">
                                <input
                                    className="input flex-1"
                                    placeholder="https://cdn.example.com/logo.png"
                                    value={form.logo_url}
                                    onChange={set('logo_url')}
                                />
                                {form.logo_url && (
                                    <img
                                        src={form.logo_url}
                                        alt="Logo preview"
                                        className="h-10 w-10 rounded-lg object-contain border border-border-color bg-bg-tertiary flex-shrink-0"
                                        onError={e => { (e.target as HTMLImageElement).style.display = 'none' }}
                                    />
                                )}
                            </div>
                        </div>
                    </div>
                </section>

                {/* Owner Details */}
                <section className="card">
                    <h2 className="flex items-center gap-2 font-semibold text-text-primary mb-4">
                        <User className="h-4 w-4 text-theme-primary" /> Owner Details
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Owner Name</label>
                            <input className="input w-full" placeholder="John Doe" value={form.owner_name} onChange={set('owner_name')} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Phone</label>
                            <input className="input w-full" placeholder="+91 98765 43210" value={form.owner_phone} onChange={set('owner_phone')} />
                        </div>
                        <div className="sm:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1 flex items-center gap-1">
                                <Globe className="h-3 w-3" /> Email
                            </label>
                            <input type="email" className="input w-full" placeholder="owner@store.com" value={form.owner_email} onChange={set('owner_email')} />
                        </div>
                    </div>
                </section>

                {/* Address */}
                <section className="card">
                    <h2 className="flex items-center gap-2 font-semibold text-text-primary mb-4">
                        <MapPin className="h-4 w-4 text-theme-primary" /> Address
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="sm:col-span-2">
                            <label className="block text-sm font-medium text-text-secondary mb-1">Street Address</label>
                            <input className="input w-full" placeholder="123 Main Street, Shop No. 5" value={form.address} onChange={set('address')} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">City</label>
                            <input className="input w-full" placeholder="Mumbai" value={form.city} onChange={set('city')} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">State</label>
                            <input className="input w-full" placeholder="Maharashtra" value={form.state} onChange={set('state')} />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-text-secondary mb-1">Pincode</label>
                            <input className="input w-full" placeholder="400001" value={form.pincode} onChange={set('pincode')} maxLength={10} />
                        </div>
                    </div>
                </section>

                {/* Branding */}
                <section className="card">
                    <h2 className="flex items-center gap-2 font-semibold text-text-primary mb-4">
                        <Palette className="h-4 w-4 text-theme-primary" /> Brand Colors
                    </h2>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                        {([
                            { field: 'primary_color', label: 'Primary Color' },
                            { field: 'secondary_color', label: 'Secondary Color' },
                        ] as const).map(({ field, label }) => (
                            <div key={field}>
                                <label className="block text-sm font-medium text-text-secondary mb-2">{label}</label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="color"
                                        value={form[field]}
                                        onChange={set(field)}
                                        title={label}
                                        aria-label={label}
                                        className="h-10 w-14 rounded-lg border border-border-color cursor-pointer bg-transparent p-0.5"
                                    />
                                    <input
                                        className="input flex-1 font-mono uppercase"
                                        value={form[field].toUpperCase()}
                                        onChange={set(field)}
                                        title={`${label} hex value`}
                                        placeholder="#000000"
                                        maxLength={7}
                                    />
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Save */}
                <div className="flex justify-end">
                    <button
                        type="submit"
                        disabled={mutation.isPending}
                        className="btn btn-primary flex items-center gap-2 px-8"
                    >
                        {mutation.isPending
                            ? <><Loader2 className="h-4 w-4 animate-spin" />Saving…</>
                            : <><Save className="h-4 w-4" />Save Settings</>}
                    </button>
                </div>
            </form>
        </div>
    )
}
