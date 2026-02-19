import { Link, useNavigate } from 'react-router-dom'
import { Home, ArrowLeft, Package, Search } from 'lucide-react'

export default function NotFoundPage() {
    const navigate = useNavigate()

    return (
        <div className="min-h-screen bg-bg-secondary flex items-center justify-center px-4 animate-fade-in">
            <div className="max-w-md w-full text-center">

                {/* Large 404 */}
                <div className="relative mb-6 select-none">
                    <span className="text-[9rem] font-black leading-none text-theme-primary/10 block">
                        404
                    </span>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <div className="w-20 h-20 rounded-3xl bg-theme-primary/10 flex items-center justify-center">
                            <Package className="h-10 w-10 text-theme-primary" />
                        </div>
                    </div>
                </div>

                <h1 className="text-2xl font-bold text-text-primary mb-2">Page Not Found</h1>
                <p className="text-text-secondary mb-8">
                    The page you're looking for doesn't exist or has been moved. Let's get you back on track.
                </p>

                {/* Action buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center mb-8">
                    <button
                        onClick={() => navigate(-1)}
                        className="btn btn-outline"
                    >
                        <ArrowLeft className="h-4 w-4" />
                        Go Back
                    </button>
                    <Link to="/home" className="btn btn-primary">
                        <Home className="h-4 w-4" />
                        Back to Home
                    </Link>
                </div>

                {/* Quick links */}
                <div className="card">
                    <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">Quick Links</p>
                    <div className="grid grid-cols-2 gap-2">
                        {[
                            { to: '/products', icon: Package, label: 'Browse Products' },
                            { to: '/search', icon: Search, label: 'Search' },
                            { to: '/track-order', icon: '📦', label: 'Track Order', emoji: true },
                            { to: '/my-orders', icon: '🛍️', label: 'My Orders', emoji: true },
                        ].map(link => (
                            <Link
                                key={link.to}
                                to={link.to}
                                className="flex items-center gap-2 p-3 rounded-xl bg-bg-tertiary hover:bg-bg-secondary border border-transparent hover:border-theme-primary/20 transition-all text-sm font-medium text-text-secondary hover:text-text-primary"
                            >
                                {link.emoji
                                    ? <span className="text-lg">{link.icon as string}</span>
                                    : (() => { const Icon = link.icon as any; return <Icon className="h-4 w-4 text-theme-primary" /> })()
                                }
                                {link.label}
                            </Link>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    )
}
