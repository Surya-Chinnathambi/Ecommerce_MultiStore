import { useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from '@/components/ui/Toaster'
import {
    HelpCircle, MessageSquare, Phone, Mail, Package,
    ShoppingBag, RotateCcw, CreditCard, Truck, Lock,
    ChevronDown, ChevronUp, Send, Loader2
} from 'lucide-react'

// ── FAQ Data ──────────────────────────────────────────────────────────────────
interface FaqItem {
    q: string
    a: string
}

interface FaqSection {
    icon: React.ReactNode
    title: string
    items: FaqItem[]
}

const FAQ_SECTIONS: FaqSection[] = [
    {
        icon: <ShoppingBag className="h-5 w-5 text-blue-500" />,
        title: 'Orders',
        items: [
            {
                q: 'How do I place an order?',
                a: 'Browse our products, add items to your cart, and proceed to checkout. You\'ll need to sign in (or create an account), enter a delivery address and choose your payment method.',
            },
            {
                q: 'Can I modify or cancel my order after placing it?',
                a: 'You can cancel an order before it has been shipped. Go to My Orders, select the order and tap "Cancel". Once the order is packed/shipped cancellation is no longer possible.',
            },
            {
                q: 'How do I track my order?',
                a: 'Visit the Track Order page or go to My Orders and click the order number to see real-time status updates.',
            },
        ],
    },
    {
        icon: <Truck className="h-5 w-5 text-green-500" />,
        title: 'Delivery & Shipping',
        items: [
            {
                q: 'How long does delivery take?',
                a: 'Standard delivery takes 3–7 business days. Express delivery (where available) takes 1–2 business days. You can check availability on the product page by entering your pincode.',
            },
            {
                q: 'Is there a minimum order for free shipping?',
                a: 'Free shipping is available on orders above ₹499. Orders below this amount attract a flat delivery fee shown at checkout.',
            },
            {
                q: 'Do you deliver to my pincode?',
                a: 'Enter your pincode on any product page to check delivery availability and estimated arrival date.',
            },
        ],
    },
    {
        icon: <RotateCcw className="h-5 w-5 text-orange-500" />,
        title: 'Returns & Refunds',
        items: [
            {
                q: 'What is the return policy?',
                a: 'We accept returns within 7 days of delivery for most products. Items must be unused and in original packaging. Some categories (perishables, personalised items) are non-returnable.',
            },
            {
                q: 'How do I initiate a return?',
                a: 'Go to My Orders, find the delivered order, and click "Return". Fill in the reason, upload photos if needed, and submit. Our team will review within 24 hours.',
            },
            {
                q: 'When will I receive my refund?',
                a: 'Refunds are processed within 2 business days of return pickup. The amount is credited back to the original payment method within 5–7 business days.',
            },
        ],
    },
    {
        icon: <CreditCard className="h-5 w-5 text-purple-500" />,
        title: 'Payments',
        items: [
            {
                q: 'What payment methods are accepted?',
                a: 'We accept UPI, credit/debit cards, net banking, wallets and Cash on Delivery (COD) for eligible orders.',
            },
            {
                q: 'Is my payment information secure?',
                a: 'Yes. All payments are processed through PCI-DSS compliant gateways. We never store your card details.',
            },
            {
                q: 'My payment failed but money was deducted. What do I do?',
                a: 'In case of a payment failure, any deducted amount is typically reversed within 5–7 business days by your bank. Contact us with your order number if it takes longer.',
            },
        ],
    },
    {
        icon: <Lock className="h-5 w-5 text-red-500" />,
        title: 'Account & Security',
        items: [
            {
                q: 'How do I reset my password?',
                a: 'On the login page click "Forgot password?" and enter your registered email. You\'ll receive a reset link valid for 30 minutes.',
            },
            {
                q: 'How do I update my delivery address?',
                a: 'Go to Profile → Addresses. You can add new addresses, edit existing ones, or set a default address there.',
            },
        ],
    },
    {
        icon: <Package className="h-5 w-5 text-teal-500" />,
        title: 'Products',
        items: [
            {
                q: 'How do I know if a product is in stock?',
                a: 'Products show stock status on their listing page ("In Stock", "Low Stock", or "Out of Stock"). You can request to be notified when an out-of-stock item is restocked.',
            },
            {
                q: 'Are product images accurate?',
                a: 'We work with verified sellers to ensure images are representative. Slight color variations can occur due to screen settings.',
            },
        ],
    },
]

// ── FAQ Accordion ─────────────────────────────────────────────────────────────
function FaqAccordion({ items }: { items: FaqItem[] }) {
    const [open, setOpen] = useState<number | null>(null)
    return (
        <div className="space-y-2">
            {items.map((item, i) => (
                <div key={i} className="card p-0 overflow-hidden">
                    <button
                        onClick={() => setOpen(open === i ? null : i)}
                        className="w-full flex items-center justify-between gap-3 px-4 py-3 text-left hover:bg-bg-tertiary/50 transition-colors"
                    >
                        <span className="font-medium text-sm text-text-primary">{item.q}</span>
                        {open === i
                            ? <ChevronUp className="h-4 w-4 text-theme-primary flex-shrink-0" />
                            : <ChevronDown className="h-4 w-4 text-text-tertiary flex-shrink-0" />}
                    </button>
                    {open === i && (
                        <div className="px-4 pb-4">
                            <p className="text-sm text-text-secondary leading-relaxed">{item.a}</p>
                        </div>
                    )}
                </div>
            ))}
        </div>
    )
}

// ── Contact Form ──────────────────────────────────────────────────────────────
function ContactForm() {
    const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' })
    const [sending, setSending] = useState(false)

    function set(field: keyof typeof form) {
        return (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) =>
            setForm(prev => ({ ...prev, [field]: e.target.value }))
    }

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault()
        if (!form.name || !form.email || !form.message) {
            toast.error('Please fill in all required fields')
            return
        }
        setSending(true)
        // Simulate send — replace with real API call if backend contact endpoint exists
        await new Promise(r => setTimeout(r, 1200))
        setSending(false)
        toast.success('Message sent! We\'ll get back to you within 24 hours.')
        setForm({ name: '', email: '', subject: '', message: '' })
    }

    return (
        <form onSubmit={handleSubmit} className="card space-y-4">
            <h2 className="font-semibold text-text-primary text-lg flex items-center gap-2">
                <Send className="h-5 w-5 text-theme-primary" /> Send us a message
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Name <span className="text-red-500">*</span>
                    </label>
                    <input className="input w-full" placeholder="Your name" value={form.name} onChange={set('name')} />
                </div>
                <div>
                    <label className="block text-sm font-medium text-text-secondary mb-1">
                        Email <span className="text-red-500">*</span>
                    </label>
                    <input type="email" className="input w-full" placeholder="you@example.com" value={form.email} onChange={set('email')} />
                </div>
            </div>
            <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">Subject</label>
                <select className="input w-full" title="Support topic" value={form.subject} onChange={set('subject')}>
                    <option value="">Select a topic…</option>
                    <option value="order">Order issue</option>
                    <option value="return">Return / Refund</option>
                    <option value="payment">Payment problem</option>
                    <option value="product">Product query</option>
                    <option value="account">Account issue</option>
                    <option value="other">Other</option>
                </select>
            </div>
            <div>
                <label className="block text-sm font-medium text-text-secondary mb-1">
                    Message <span className="text-red-500">*</span>
                </label>
                <textarea
                    className="input w-full resize-none"
                    rows={5}
                    placeholder="Describe your issue or question in detail…"
                    value={form.message}
                    onChange={set('message')}
                />
            </div>
            <button
                type="submit"
                disabled={sending}
                className="btn btn-primary w-full flex items-center justify-center gap-2"
            >
                {sending
                    ? <><Loader2 className="h-4 w-4 animate-spin" />Sending…</>
                    : <><Send className="h-4 w-4" />Send Message</>}
            </button>
        </form>
    )
}

// ── Page shell ────────────────────────────────────────────────────────────────
export default function HelpContactPage() {
    const [activeSection, setActiveSection] = useState<string | null>(null)

    return (
        <div className="container mx-auto px-4 py-8 animate-fade-in">
            {/* Hero */}
            <div className="text-center mb-10">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-theme-primary/10 rounded-2xl mb-4">
                    <HelpCircle className="h-8 w-8 text-theme-primary" />
                </div>
                <h1 className="text-3xl font-black text-text-primary mb-2">How can we help?</h1>
                <p className="text-text-secondary max-w-md mx-auto">
                    Find answers to common questions or reach out to our support team.
                </p>
            </div>

            {/* Quick links */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-10">
                {[
                    { label: 'Track Order',    to: '/track-order', Icon: Truck },
                    { label: 'My Orders',      to: '/my-orders',   Icon: ShoppingBag },
                    { label: 'Returns',        to: '/my-orders',   Icon: RotateCcw },
                ].map(({ label, to, Icon }) => (
                    <Link
                        key={label}
                        to={to}
                        className="card flex flex-col items-center justify-center gap-2 py-4 hover:border-theme-primary hover:text-theme-primary transition-colors text-text-secondary"
                    >
                        <Icon className="h-6 w-6" />
                        <span className="text-sm font-medium">{label}</span>
                    </Link>
                ))}
                <button
                    onClick={() => document.getElementById('contact')?.scrollIntoView({ behavior: 'smooth' })}
                    className="card flex flex-col items-center justify-center gap-2 py-4 hover:border-theme-primary hover:text-theme-primary transition-colors text-text-secondary"
                >
                    <MessageSquare className="h-6 w-6" />
                    <span className="text-sm font-medium">Contact Us</span>
                </button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* FAQ col */}
                <div className="lg:col-span-2 space-y-6">
                    <h2 className="section-title">Frequently Asked Questions</h2>
                    {FAQ_SECTIONS.map(section => (
                        <div key={section.title}>
                            <button
                                onClick={() => setActiveSection(activeSection === section.title ? null : section.title)}
                                className="flex items-center gap-2 w-full text-left mb-3 group"
                            >
                                {section.icon}
                                <span className="font-semibold text-text-primary group-hover:text-theme-primary transition-colors">
                                    {section.title}
                                </span>
                                {activeSection === section.title
                                    ? <ChevronUp className="h-4 w-4 ml-auto text-theme-primary" />
                                    : <ChevronDown className="h-4 w-4 ml-auto text-text-tertiary" />}
                            </button>
                            {activeSection === section.title && (
                                <FaqAccordion items={section.items} />
                            )}
                        </div>
                    ))}
                </div>

                {/* Sidebar */}
                <div className="space-y-4">
                    {/* Contact info */}
                    <div className="card">
                        <h3 className="font-semibold text-text-primary mb-3">Contact us directly</h3>
                        <div className="space-y-3">
                            <a
                                href="mailto:support@store.com"
                                className="flex items-center gap-3 text-sm text-text-secondary hover:text-theme-primary transition-colors"
                            >
                                <div className="w-8 h-8 bg-blue-500/10 rounded-lg flex items-center justify-center">
                                    <Mail className="h-4 w-4 text-blue-500" />
                                </div>
                                support@store.com
                            </a>
                            <a
                                href="tel:+911800000000"
                                className="flex items-center gap-3 text-sm text-text-secondary hover:text-theme-primary transition-colors"
                            >
                                <div className="w-8 h-8 bg-green-500/10 rounded-lg flex items-center justify-center">
                                    <Phone className="h-4 w-4 text-green-500" />
                                </div>
                                1800-000-0000 (Toll Free)
                            </a>
                            <div className="flex items-center gap-3 text-sm text-text-secondary">
                                <div className="w-8 h-8 bg-orange-500/10 rounded-lg flex items-center justify-center">
                                    <MessageSquare className="h-4 w-4 text-orange-500" />
                                </div>
                                Live chat: Mon–Sat 9am–7pm
                            </div>
                        </div>
                    </div>

                    {/* Response time */}
                    <div className="card bg-theme-primary/5 border-theme-primary/20">
                        <p className="text-sm font-semibold text-theme-primary mb-1">Average response time</p>
                        <p className="text-2xl font-black text-text-primary">&lt; 4 hours</p>
                        <p className="text-xs text-text-tertiary mt-1">During business hours (Mon–Sat)</p>
                    </div>
                </div>
            </div>

            {/* Contact form */}
            <div id="contact" className="mt-12 max-w-2xl mx-auto">
                <ContactForm />
            </div>
        </div>
    )
}
