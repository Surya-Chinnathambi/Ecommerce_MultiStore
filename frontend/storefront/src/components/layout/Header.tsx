import { Link, useLocation } from 'react-router-dom'
import { ShoppingCart, Menu, X, LogOut, Activity, CreditCard, Heart, Bell, LayoutGrid, HelpCircle } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useAuthStore } from '@/store/authStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { useState, useEffect } from 'react'
import SearchAutocomplete from '@/components/SearchAutocomplete'
import ThemeToggle from '@/components/ThemeToggle'

export default function Header() {
    const getStoreId = () => {
        const params = new URLSearchParams(window.location.search)
        return params.get('store_id') || localStorage.getItem('store_id') || ''
    }

    const buildLink = (path: string) => {
        const storeId = getStoreId()
        return storeId ? `${path}?store_id=${storeId}` : path
    }

    const totalItems = useCartStore((state) => state.getTotalItems())
    const { user, isAuthenticated, logout } = useAuthStore()
    const wishlistCount = useWishlistStore((s) => s.items.length)
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const [scrolled, setScrolled] = useState(false)
    const location = useLocation()

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 16)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])

    const isActive = (path: string) => location.pathname.startsWith(path)

    // User initials avatar
    const initials = user?.full_name
        ? user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
        : 'U'

    const { data: storeData } = useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    const handleLogout = () => {
        logout()
        setUserMenuOpen(false)
        window.location.href = '/login'
    }

    return (
        <header className={`sticky top-0 z-50 border-b border-border-color transition-all duration-300 ${scrolled ? 'bg-bg-primary/95 backdrop-blur-md shadow-md' : 'bg-bg-primary'}`}>
            <div className="container mx-auto px-4">
                {/* Top bar */}
                <div className="py-3">
                    <div className="flex items-center justify-between gap-3">
                        <Link to={buildLink("/home")} className="flex items-center gap-3 min-w-0 flex-shrink-0">
                            {storeData?.logo_url && (
                                <img src={storeData.logo_url} alt={storeData.name} className="h-10 w-10 object-contain flex-shrink-0" />
                            )}
                            <div className="min-w-0">
                                <h1 className="text-lg sm:text-xl md:text-2xl font-bold text-theme-primary truncate">
                                    {storeData?.name || 'Loading...'}
                                </h1>
                                {storeData?.city && (
                                    <p className="text-xs sm:text-sm text-text-secondary truncate">{storeData.city}</p>
                                )}
                            </div>
                        </Link>

                        {/* Global Search - desktop */}
                        <div className="hidden md:flex flex-1 max-w-2xl">
                            <SearchAutocomplete />
                        </div>

                        <div className="flex items-center gap-2 sm:gap-3">
                            {/* Theme Toggle */}
                            <ThemeToggle />

                            {/* Auth Section */}
                            {isAuthenticated && user ? (
                                <div className="relative">
                                    <button
                                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                                        className="flex items-center gap-2 rounded-xl border border-border-color bg-bg-primary px-2 py-1.5 text-text-primary hover:bg-bg-tertiary/60 transition-colors"
                                        aria-label="User menu"
                                    >
                                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-theme-primary to-theme-accent flex items-center justify-center text-white text-sm font-bold flex-shrink-0">
                                            {initials}
                                        </div>
                                        <span className="hidden md:inline text-sm font-medium pr-1">{user.full_name.split(' ')[0]}</span>
                                    </button>

                                    {userMenuOpen && (
                                        <div className="absolute right-0 mt-2 w-56 overflow-hidden rounded-lg border border-border-color bg-bg-primary shadow-lg py-1 z-50">
                                            <Link
                                                to="/profile"
                                                className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                My Profile
                                            </Link>
                                            <Link
                                                to="/my-orders"
                                                className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                📦 My Orders
                                            </Link>
                                            <Link
                                                to="/wishlist"
                                                className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                ❤️ My Wishlist
                                            </Link>
                                            <Link
                                                to="/seller/dashboard"
                                                className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                🏪 Seller Dashboard
                                            </Link>
                                            {user.role === 'admin' && (
                                                <>
                                                    <Link
                                                        to="/admin/orders"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        🛍️ Manage Orders
                                                    </Link>
                                                    <Link
                                                        to="/admin/returns"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        🔄 Manage Returns
                                                    </Link>
                                                    <Link
                                                        to="/admin/coupons"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        🏷️ Manage Coupons
                                                    </Link>
                                                    <Link
                                                        to="/admin/ads"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        📢 Ads & Promotions
                                                    </Link>
                                                    <Link
                                                        to="/admin/inventory-alerts"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        🔔 Inventory Alerts
                                                    </Link>
                                                    <Link
                                                        to="/admin/reviews"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        ⭐ Manage Reviews
                                                    </Link>
                                                    <Link
                                                        to="/monitoring"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary flex items-center space-x-2"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        <Activity className="h-4 w-4" />
                                                        <span>System Monitor</span>
                                                    </Link>
                                                    <Link
                                                        to="/admin/billing"
                                                        className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary flex items-center space-x-2"
                                                        onClick={() => setUserMenuOpen(false)}
                                                    >
                                                        <CreditCard className="h-4 w-4" />
                                                        <span>Billing Integration</span>
                                                    </Link>
                                                </>
                                            )}
                                            <Link
                                                to="/referrals"
                                                className="block px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary"
                                                onClick={() => setUserMenuOpen(false)}
                                            >
                                                Refer & Earn
                                            </Link>
                                            <button
                                                onClick={handleLogout}
                                                className="w-full text-left px-4 py-2 text-sm text-text-primary hover:bg-bg-tertiary flex items-center space-x-2"
                                                aria-label="Logout"
                                            >
                                                <LogOut className="h-4 w-4" />
                                                <span>Logout</span>
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <div className="hidden sm:flex items-center gap-2">
                                    <Link
                                        to="/login"
                                        className="btn btn-secondary text-sm"
                                    >
                                        Login
                                    </Link>
                                    <Link
                                        to="/register"
                                        className="btn btn-primary text-sm"
                                    >
                                        Sign Up
                                    </Link>
                                </div>
                            )}

                            {/* Wishlist */}
                            {isAuthenticated && (
                                <Link
                                    to={buildLink("/wishlist")}
                                    className="relative rounded-lg border border-border-color bg-bg-primary p-2 text-text-primary hover:bg-bg-tertiary/60"
                                    aria-label="My wishlist"
                                >
                                    <Heart className="h-6 w-6" />
                                    {wishlistCount > 0 && (
                                        <span className="absolute -top-2 -right-2 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                                            {wishlistCount}
                                        </span>
                                    )}
                                </Link>
                            )}

                            {/* Notifications bell */}
                            {isAuthenticated && (
                                <Link
                                    to={buildLink("/notifications")}
                                    className="rounded-lg border border-border-color bg-bg-primary p-2 text-text-primary hover:bg-bg-tertiary/60"
                                    aria-label="Notifications"
                                    title="Notifications"
                                >
                                    <Bell className="h-6 w-6" />
                                </Link>
                            )}

                            {/* Cart */}
                            <Link
                                to={buildLink("/cart")}
                                className="relative rounded-lg border border-border-color bg-bg-primary p-2 text-text-primary hover:bg-bg-tertiary/60"
                                aria-label="Shopping cart"
                            >
                                <ShoppingCart className="h-6 w-6" />
                                {totalItems > 0 && (
                                    <span className="absolute -top-2 -right-2 bg-theme-primary text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                                        {totalItems}
                                    </span>
                                )}
                            </Link>

                            {/* Mobile menu button */}
                            <button
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                className="md:hidden rounded-lg border border-border-color bg-bg-primary p-2 text-text-primary hover:bg-bg-tertiary/60 transition-colors"
                                aria-label="Toggle mobile menu"
                            >
                                {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
                            </button>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className={`${mobileMenuOpen ? 'block animate-slide-in-left' : 'hidden'} md:block pb-3`}>
                    <div className="rounded-xl border border-border-color bg-bg-secondary/50 px-3 py-2 md:border-0 md:bg-transparent md:px-0 md:py-0">
                        <ul className="flex flex-col md:flex-row md:items-center md:gap-1 space-y-0.5 md:space-y-0">
                            <li>
                                <Link to={buildLink("/home")} className={`nav-link ${isActive('/home') ? 'nav-link-active' : ''}`}>
                                    Home
                                </Link>
                            </li>
                            <li>
                                <Link to={buildLink("/products")} className={`nav-link ${isActive('/products') ? 'nav-link-active' : ''}`}>
                                    Products
                                </Link>
                            </li>
                            <li>
                                <Link to={buildLink("/categories")} className={`nav-link ${isActive('/categories') ? 'nav-link-active' : ''}`}>
                                    <LayoutGrid className="inline h-3.5 w-3.5 mr-1" />
                                    Categories
                                </Link>
                            </li>
                            <li>
                                <Link to={buildLink("/track-order")} className={`nav-link ${isActive('/track-order') ? 'nav-link-active' : ''}`}>
                                    Track Order
                                </Link>
                            </li>
                            <li>
                                <Link to="/help" className={`nav-link ${isActive('/help') ? 'nav-link-active' : ''}`}>
                                    <HelpCircle className="inline h-3.5 w-3.5 mr-1" />
                                    Help
                                </Link>
                            </li>
                            {isAuthenticated && (
                                <li>
                                    <Link to={buildLink("/referrals")} className={`nav-link ${isActive('/referrals') ? 'nav-link-active' : ''}`}>
                                        Refer &amp; Earn
                                    </Link>
                                </li>
                            )}
                            {user?.role === 'admin' || user?.role === 'super_admin' ? (
                                <>
                                    <li>
                                        <Link to={buildLink("/admin")} className={`nav-link font-semibold ${isActive('/admin') ? 'nav-link-active' : 'text-theme-primary'}`}>
                                            Admin
                                        </Link>
                                    </li>
                                    <li>
                                        <Link to={buildLink("/admin/product-import")} className="nav-link text-theme-accent font-semibold">
                                            Import Products
                                        </Link>
                                    </li>
                                </>
                            ) : null}
                            {isAuthenticated && (
                                <li className="md:hidden">
                                    <Link to={buildLink("/profile")} className={`nav-link ${isActive('/profile') ? 'nav-link-active' : ''}`}>
                                        My Profile
                                    </Link>
                                </li>
                            )}
                        </ul>

                        {!isAuthenticated && (
                            <div className="mt-2 flex gap-2 sm:hidden">
                                <Link to="/login" className="btn btn-secondary flex-1 text-center text-sm">
                                    Login
                                </Link>
                                <Link to="/register" className="btn btn-primary flex-1 text-center text-sm">
                                    Sign Up
                                </Link>
                            </div>
                        )}
                    </div>
                </nav>

                {/* Mobile search */}
                <div className="md:hidden pb-3">
                    <SearchAutocomplete />
                </div>
            </div>
        </header>
    )
}
