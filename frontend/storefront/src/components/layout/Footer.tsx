import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { MapPin, Phone, Mail, Facebook, Instagram, Twitter, Heart, ArrowRight, Send } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'

const quickLinks = [
    { to: '/', label: 'Home' },
    { to: '/products', label: 'Products' },
    { to: '/categories', label: 'Categories' },
    { to: '/cart', label: 'Cart' },
    { to: '/track-order', label: 'Track Order' },
]

const supportLinks = [
    { to: '/faq', label: 'FAQ' },
    { to: '/shipping', label: 'Shipping Policy' },
    { to: '/returns', label: 'Returns & Refunds' },
    { to: '/contact', label: 'Contact Us' },
    { to: '/help', label: 'Help Center' },
]

export default function Footer() {
    const { data: storeData } = useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    const [email, setEmail] = useState('')
    const [subscribed, setSubscribed] = useState(false)

    const handleSubscribe = (e: React.FormEvent) => {
        e.preventDefault()
        if (email.trim()) { setSubscribed(true) }
    }

    return (
        <footer className="mt-16 border-t border-border-color bg-bg-primary">
            {/* Newsletter */}
            <div className="gradient-primary">
                <div className="container-wide py-10">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div>
                            <h3 className="text-xl font-bold text-white mb-1">Stay ahead of the deals</h3>
                            <p className="text-white/70 text-sm">
                                Get exclusive offers, new arrivals, and flash sales — delivered weekly.
                            </p>
                        </div>

                        {subscribed ? (
                            <div className="flex items-center gap-2 rounded-[var(--radius-xl)] bg-white/20 border border-white/30 px-5 py-3 text-white font-semibold animate-bounce-in">
                                <Send className="h-4 w-4" />
                                You're subscribed!
                            </div>
                        ) : (
                            <form onSubmit={handleSubscribe} className="flex gap-2 w-full md:w-auto">
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="your@email.com"
                                    required
                                    className="flex-1 md:w-64 rounded-[var(--radius-xl)] bg-white/15 border border-white/25 px-4 py-2.5 text-sm text-white placeholder:text-white/50 focus:outline-none focus:ring-2 focus:ring-white/40 transition-all"
                                />
                                <button
                                    type="submit"
                                    className="flex items-center gap-1.5 rounded-[var(--radius-xl)] bg-white px-5 py-2.5 text-sm font-semibold text-theme-primary hover:bg-white/90 transition-colors flex-shrink-0 shadow-sm"
                                >
                                    Subscribe <ArrowRight className="h-4 w-4" />
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>

            {/* Main footer */}
            <div className="container-wide py-14">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-10">
                    {/* Brand col */}
                    <div className="lg:col-span-2">
                        <h3 className="text-lg font-bold text-text-primary mb-3">
                            {storeData?.name || 'Store'}
                        </h3>
                        <p className="text-text-secondary text-sm leading-relaxed mb-6 max-w-sm">
                            Your trusted destination for quality products. We believe in making great shopping simple, fast, and delightful.
                        </p>

                        {storeData?.address && (
                            <div className="flex items-start gap-3 mb-3 text-sm text-text-secondary">
                                <MapPin className="h-4 w-4 text-theme-primary mt-0.5 flex-shrink-0" />
                                <span>
                                    {storeData.address}
                                    {storeData.city && `, ${storeData.city}`}
                                    {storeData.state && `, ${storeData.state}`}
                                    {storeData.pincode && ` – ${storeData.pincode}`}
                                </span>
                            </div>
                        )}
                        {storeData?.owner_phone && (
                            <a href={`tel:${storeData.owner_phone}`} className="flex items-center gap-3 mb-3 text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                <Phone className="h-4 w-4 text-theme-primary flex-shrink-0" />
                                {storeData.owner_phone}
                            </a>
                        )}
                        {storeData?.email && (
                            <a href={`mailto:${storeData.email}`} className="flex items-center gap-3 text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                <Mail className="h-4 w-4 text-theme-primary flex-shrink-0" />
                                {storeData.email}
                            </a>
                        )}
                    </div>

                    {/* Quick Links */}
                    <div>
                        <p className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4">Quick Links</p>
                        <ul className="space-y-2.5">
                            {quickLinks.map(l => (
                                <li key={l.to}>
                                    <Link to={l.to} className="text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                        {l.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Support + Social */}
                    <div>
                        <p className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-4">Support</p>
                        <ul className="space-y-2.5 mb-7">
                            {supportLinks.map(l => (
                                <li key={l.to}>
                                    <Link to={l.to} className="text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                        {l.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>

                        <p className="text-sm font-semibold text-text-primary uppercase tracking-wider mb-3">Follow Us</p>
                        <div className="flex gap-2.5">
                            {[
                                { Icon: Facebook, label: 'Facebook' },
                                { Icon: Instagram, label: 'Instagram' },
                                { Icon: Twitter, label: 'X / Twitter' },
                            ].map(({ Icon, label }) => (
                                <a
                                    key={label}
                                    href="#"
                                    aria-label={label}
                                    className="h-9 w-9 rounded-[var(--radius-lg)] bg-bg-tertiary border border-border-color flex items-center justify-center text-text-tertiary hover:bg-theme-primary hover:text-white hover:border-theme-primary transition-all duration-200"
                                >
                                    <Icon className="h-4 w-4" />
                                </a>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Bottom bar */}
                <div className="mt-12 pt-6 border-t border-border-color flex flex-col sm:flex-row items-center justify-between gap-3">
                    <p className="text-sm text-text-tertiary">
                        © {new Date().getFullYear()} {storeData?.name || 'Store'}. All rights reserved.
                    </p>
                    <p className="text-sm text-text-tertiary flex items-center gap-1.5">
                        Made with <Heart className="h-3.5 w-3.5 text-red-400 fill-current" /> for amazing customers
                    </p>
                </div>
            </div>
        </footer>
    )
}

