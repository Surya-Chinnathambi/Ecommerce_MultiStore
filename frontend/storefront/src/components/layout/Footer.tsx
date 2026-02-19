import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { MapPin, Phone, Mail, Facebook, Instagram, Twitter, Heart, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useState } from 'react'

export default function Footer() {
    const { data: storeData } = useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    const [email, setEmail] = useState('')
    const [subscribed, setSubscribed] = useState(false)

    const handleSubscribe = (e: React.FormEvent) => {
        e.preventDefault()
        if (email) { setSubscribed(true) }
    }

    return (
        <footer className="bg-bg-primary border-t border-border-color mt-12">
            {/* Newsletter strip */}
            <div className="bg-gradient-to-r from-theme-primary to-theme-accent">
                <div className="container mx-auto px-4 py-8">
                    <div className="flex flex-col md:flex-row items-center justify-between gap-6">
                        <div className="text-white">
                            <h3 className="text-xl font-bold mb-1">Stay in the loop 📫</h3>
                            <p className="text-white/80 text-sm">Get deals, new arrivals &amp; exclusive offers straight to your inbox.</p>
                        </div>
                        {subscribed ? (
                            <p className="text-white font-semibold animate-bounce-in">✓ You’re subscribed!</p>
                        ) : (
                            <form onSubmit={handleSubscribe} className="flex gap-2 w-full md:w-auto">
                                <input
                                    type="email"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    placeholder="your@email.com"
                                    className="flex-1 md:w-64 px-4 py-2.5 rounded-xl bg-white/20 border border-white/30 text-white placeholder:text-white/60 focus:outline-none focus:ring-2 focus:ring-white/60 text-sm"
                                    required
                                />
                                <button
                                    type="submit"
                                    className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-white text-theme-primary font-semibold text-sm hover:bg-white/90 transition-colors flex-shrink-0"
                                >
                                    Subscribe <ArrowRight className="h-4 w-4" />
                                </button>
                            </form>
                        )}
                    </div>
                </div>
            </div>
            <div className="container mx-auto px-4 py-12">
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
                    {/* Store Info */}
                    <div className="lg:col-span-2">
                        <h3 className="text-xl font-bold text-gradient mb-4">{storeData?.name || 'Store'}</h3>
                        <p className="text-text-secondary mb-4 max-w-md">
                            Your one-stop destination for quality products. We're committed to providing the best shopping experience.
                        </p>
                        {storeData?.address && (
                            <div className="flex items-start gap-3 mb-3">
                                <MapPin className="h-5 w-5 text-theme-primary mt-0.5 flex-shrink-0" />
                                <p className="text-sm text-text-secondary">
                                    {storeData.address}
                                    {storeData.city && `, ${storeData.city}`}
                                    {storeData.state && `, ${storeData.state}`}
                                    {storeData.pincode && ` - ${storeData.pincode}`}
                                </p>
                            </div>
                        )}
                        {storeData?.owner_phone && (
                            <div className="flex items-center gap-3 mb-3">
                                <Phone className="h-5 w-5 text-theme-primary flex-shrink-0" />
                                <a href={`tel:${storeData.owner_phone}`} className="text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                    {storeData.owner_phone}
                                </a>
                            </div>
                        )}
                        {storeData?.email && (
                            <div className="flex items-center gap-3">
                                <Mail className="h-5 w-5 text-theme-primary flex-shrink-0" />
                                <a href={`mailto:${storeData.email}`} className="text-sm text-text-secondary hover:text-theme-primary transition-colors">
                                    {storeData.email}
                                </a>
                            </div>
                        )}
                    </div>

                    {/* Quick Links */}
                    <div>
                        <h3 className="font-semibold text-text-primary mb-4">Quick Links</h3>
                        <ul className="space-y-3">
                            {[
                                { to: '/', label: 'Home' },
                                { to: '/products', label: 'Products' },
                                { to: '/track-order', label: 'Track Order' },
                                { to: '/cart', label: 'Cart' },
                            ].map((link) => (
                                <li key={link.to}>
                                    <Link to={link.to} className="text-sm text-text-secondary hover:text-theme-primary transition-colors link-underline">
                                        {link.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Customer Support */}
                    <div>
                        <h3 className="font-semibold text-text-primary mb-4">Support</h3>
                        <ul className="space-y-3">
                            {[
                                { to: '/faq', label: 'FAQ' },
                                { to: '/shipping', label: 'Shipping Policy' },
                                { to: '/returns', label: 'Returns & Refunds' },
                                { to: '/contact', label: 'Contact Us' },
                            ].map((link) => (
                                <li key={link.to}>
                                    <Link to={link.to} className="text-sm text-text-secondary hover:text-theme-primary transition-colors link-underline">
                                        {link.label}
                                    </Link>
                                </li>
                            ))}
                        </ul>

                        {/* Social Links */}
                        <div className="mt-6">
                            <p className="text-sm font-semibold text-text-primary mb-3">Follow Us</p>
                            <div className="flex gap-3">
                                {[{ Icon: Facebook, label: 'Facebook' }, { Icon: Instagram, label: 'Instagram' }, { Icon: Twitter, label: 'Twitter' }].map(({ Icon, label }) => (
                                    <a
                                        key={label}
                                        href="#"
                                        aria-label={label}
                                        className="p-2 rounded-xl bg-bg-tertiary text-text-secondary hover:bg-theme-primary hover:text-white transition-all duration-300"
                                    >
                                        <Icon className="h-5 w-5" />
                                    </a>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Bottom Bar */}
                <div className="border-t border-border-color mt-10 pt-8 flex flex-col md:flex-row items-center justify-between gap-4">
                    <p className="text-sm text-text-tertiary">
                        © {new Date().getFullYear()} {storeData?.name || 'Store'}. All rights reserved.
                    </p>
                    <p className="text-sm text-text-tertiary flex items-center gap-1">
                        Made with <Heart className="h-4 w-4 text-red-500 fill-current" /> for amazing customers
                    </p>
                </div>
            </div>
        </footer>
    )
}
