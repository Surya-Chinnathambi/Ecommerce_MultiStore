import { Link, useLocation } from 'react-router-dom'
import {
    ShoppingCart, Menu, X, LogOut, Activity, CreditCard, Heart, Bell,
    LayoutGrid, HelpCircle, User, Package, Tag, Store, ChevronDown,
    BarChart3, AlertTriangle, Star, Megaphone, Import, Shield
} from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useAuthStore } from '@/store/authStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { useState, useEffect, useRef } from 'react'
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

    const totalItems = useCartStore((state) => state.getItemCount())
    const { user, isAuthenticated, logout } = useAuthStore()
    const wishlistCount = useWishlistStore((s) => s.items.length)
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const [scrolled, setScrolled] = useState(false)
    const location = useLocation()
    const menuRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        const onScroll = () => setScrolled(window.scrollY > 8)
        window.addEventListener('scroll', onScroll, { passive: true })
        return () => window.removeEventListener('scroll', onScroll)
    }, [])

    // Close menu on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
                setUserMenuOpen(false)
            }
        }
        document.addEventListener('mousedown', handler)
        return () => document.removeEventListener('mousedown', handler)
    }, [])

    // Close mobile menu on navigation
    useEffect(() => { setMobileMenuOpen(false) }, [location.pathname])

    const isActive = (path: string) => location.pathname.startsWith(path)

    const initials = user?.full_name
        ? user.full_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2).toUpperCase()
        : 'U'

    const { data: storeData } = useQuery({
        queryKey: ['store-info'],
        queryFn: () => storeApi.getStoreInfo().then(res => res.data.data),
    })

    useEffect(() => {
        if (storeData?.id && !localStorage.getItem('store_id')) {
            localStorage.setItem('store_id', storeData.id)
        }
    }, [storeData?.id])

    const handleLogout = () => {
        logout()
        setUserMenuOpen(false)
        window.location.href = '/login'
    }

    const isAdmin = user?.role === 'admin' || user?.role === 'super_admin'

    const navLinks = [
        { to: buildLink('/home'), label: 'Home', exact: '/home' },
        { to: buildLink('/products'), label: 'Products', exact: '/products' },
        { to: buildLink('/categories'), label: 'Categories', exact: '/categories', icon: <LayoutGrid className="h-3.5 w-3.5" /> },
        { to: buildLink('/track-order'), label: 'Track Order', exact: '/track-order' },
        { to: '/help', label: 'Help', exact: '/help', icon: <HelpCircle className="h-3.5 w-3.5" /> },
    ]

    return (
        <header className={`sticky top-0 z-50 transition-all duration-300 ${scrolled
            ? 'glass shadow-md border-b border-border-color/80'
            : 'bg-bg-primary border-b border-border-color'
            }`}>
            <div className="container-wide">
                {/* -- Main row ----------------------------------------- */}
                <div className="flex items-center gap-3 py-3">
                    {/* Logo / Brand */}
                    <Link to={buildLink('/home')} className="flex items-center gap-2.5 min-w-0 flex-shrink-0 group">
                        {storeData?.logo_url ? (
                            <img
                                src={storeData.logo_url}
                                alt={storeData?.name}
                                className="h-9 w-9 rounded-[var(--radius-lg)] object-contain border border-border-color shadow-xs flex-shrink-0"
                            />
                        ) : (
                            <div className="h-9 w-9 rounded-[var(--radius-lg)] gradient-primary flex items-center justify-center text-white font-black text-lg flex-shrink-0">
                                {(storeData?.name?.[0] || 'S').toUpperCase()}
                            </div>
                        )}
                        <div className="min-w-0 hidden sm:block">
                            <p className="text-base font-bold text-text-primary leading-none truncate group-hover:text-theme-primary transition-colors">
                                {storeData?.name || 'Shop'}
                            </p>
                            {storeData?.city && (
                                <p className="text-xs text-text-tertiary mt-0.5 truncate">{storeData.city}</p>
                            )}
                        </div>
                    </Link>

                    {/* Search � desktop */}
                    <div className="hidden md:flex flex-1 max-w-xl">
                        <SearchAutocomplete />
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1.5 ml-auto">
                        <ThemeToggle />

                        {/* Wishlist */}
                        {isAuthenticated && (
                            <Link
                                to={buildLink('/wishlist')}
                                aria-label="Wishlist"
                                className="btn btn-icon btn-ghost relative text-text-secondary hover:text-theme-primary"
                            >
                                <Heart className="h-5 w-5" />
                                {wishlistCount > 0 && (
                                    <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-red-500 text-[10px] font-bold text-white flex items-center justify-center leading-none">
                                        {wishlistCount > 9 ? '9+' : wishlistCount}
                                    </span>
                                )}
                            </Link>
                        )}

                        {/* Notifications */}
                        {isAuthenticated && (
                            <Link
                                to={buildLink('/notifications')}
                                aria-label="Notifications"
                                className="btn btn-icon btn-ghost text-text-secondary hover:text-theme-primary"
                            >
                                <Bell className="h-5 w-5" />
                            </Link>
                        )}

                        {/* Cart */}
                        <Link
                            to={buildLink('/cart')}
                            aria-label="Cart"
                            className="btn btn-icon btn-ghost relative text-text-secondary hover:text-theme-primary"
                        >
                            <ShoppingCart className="h-5 w-5" />
                            {totalItems > 0 && (
                                <span className="absolute -top-1 -right-1 h-4 w-4 rounded-full bg-theme-primary text-[10px] font-bold text-white flex items-center justify-center leading-none">
                                    {totalItems > 9 ? '9+' : totalItems}
                                </span>
                            )}
                        </Link>

                        {/* Auth */}
                        {isAuthenticated && user ? (
                            <div className="relative" ref={menuRef}>
                                <button
                                    onClick={() => setUserMenuOpen(v => !v)}
                                    className="flex items-center gap-1.5 rounded-[var(--radius-lg)] border border-border-color bg-bg-primary pl-1 pr-2.5 py-1 hover:bg-bg-tertiary hover:border-border-strong transition-all duration-150"
                                    aria-expanded={userMenuOpen}
                                    aria-haspopup="menu"
                                    aria-label="User menu"
                                >
                                    <div className="avatar avatar-sm gradient-primary text-white font-bold text-xs">
                                        {initials}
                                    </div>
                                    <span className="hidden md:block text-sm font-medium text-text-primary max-w-[80px] truncate">
                                        {user.full_name?.split(' ')[0] || 'Me'}
                                    </span>
                                    <ChevronDown className={`h-3.5 w-3.5 text-text-tertiary transition-transform duration-200 ${userMenuOpen ? 'rotate-180' : ''}`} />
                                </button>

                                {userMenuOpen && (
                                    <div className="absolute right-0 mt-2 w-64 bg-bg-primary border border-border-color rounded-[var(--radius-xl)] shadow-dropdown py-1.5 z-50 animate-scale-in">
                                        {/* User info header */}
                                        <div className="px-4 py-3 border-b border-border-color">
                                            <p className="text-sm font-semibold text-text-primary">{user.full_name}</p>
                                            <p className="text-xs text-text-tertiary mt-0.5 truncate">{user.email}</p>
                                            {isAdmin && (
                                                <span className="badge badge-primary mt-1.5">
                                                    <Shield className="h-3 w-3" />
                                                    {user.role}
                                                </span>
                                            )}
                                        </div>

                                        {/* Customer Links */}
                                        <div className="py-1">
                                            {[
                                                { to: '/profile', icon: <User className="h-4 w-4" />, label: 'My Profile' },
                                                { to: '/my-orders', icon: <Package className="h-4 w-4" />, label: 'My Orders' },
                                                { to: buildLink('/wishlist'), icon: <Heart className="h-4 w-4" />, label: 'Wishlist' },
                                                { to: '/referrals', icon: <Tag className="h-4 w-4" />, label: 'Refer & Earn' },
                                                { to: '/seller/dashboard', icon: <Store className="h-4 w-4" />, label: 'Seller Dashboard' },
                                            ].map(item => (
                                                <Link
                                                    key={item.to}
                                                    to={item.to}
                                                    onClick={() => setUserMenuOpen(false)}
                                                    className="flex items-center gap-3 px-4 py-2.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/60 transition-colors"
                                                >
                                                    <span className="text-text-tertiary">{item.icon}</span>
                                                    {item.label}
                                                </Link>
                                            ))}
                                        </div>

                                        {/* Admin Links */}
                                        {isAdmin && (
                                            <>
                                                <div className="border-t border-border-color pt-1 pb-0.5">
                                                    <p className="px-4 py-1.5 text-[10px] font-semibold uppercase tracking-widest text-text-quaternary">
                                                        Admin
                                                    </p>
                                                    {[
                                                        { to: buildLink('/admin'), icon: <BarChart3 className="h-4 w-4" />, label: 'Dashboard' },
                                                        { to: buildLink('/admin/orders'), icon: <Package className="h-4 w-4" />, label: 'Manage Orders' },
                                                        { to: buildLink('/admin/ads'), icon: <Megaphone className="h-4 w-4" />, label: 'Ads & Promotions' },
                                                        { to: buildLink('/admin/coupons'), icon: <Tag className="h-4 w-4" />, label: 'Coupons' },
                                                        { to: buildLink('/admin/reviews'), icon: <Star className="h-4 w-4" />, label: 'Reviews' },
                                                        { to: buildLink('/admin/inventory-alerts'), icon: <AlertTriangle className="h-4 w-4" />, label: 'Inventory Alerts' },
                                                        { to: buildLink('/admin/product-import'), icon: <Import className="h-4 w-4" />, label: 'Import Products' },
                                                        { to: '/monitoring', icon: <Activity className="h-4 w-4" />, label: 'System Monitor' },
                                                        { to: '/admin/billing', icon: <CreditCard className="h-4 w-4" />, label: 'Billing' },
                                                    ].map(item => (
                                                        <Link
                                                            key={item.to}
                                                            to={item.to}
                                                            onClick={() => setUserMenuOpen(false)}
                                                            className="flex items-center gap-3 px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/60 transition-colors"
                                                        >
                                                            <span className="text-text-tertiary">{item.icon}</span>
                                                            {item.label}
                                                        </Link>
                                                    ))}
                                                </div>
                                            </>
                                        )}

                                        {/* Logout */}
                                        <div className="border-t border-border-color pt-1">
                                            <button
                                                onClick={handleLogout}
                                                className="flex w-full items-center gap-3 px-4 py-2.5 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors"
                                            >
                                                <LogOut className="h-4 w-4" />
                                                Sign out
                                            </button>
                                        </div>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="hidden sm:flex items-center gap-2">
                                <Link to="/login" className="btn btn-ghost btn-sm text-text-secondary">Sign in</Link>
                                <Link to="/register" className="btn btn-primary btn-sm">Get started</Link>
                            </div>
                        )}

                        {/* Mobile toggle */}
                        <button
                            onClick={() => setMobileMenuOpen(v => !v)}
                            aria-label="Toggle menu"
                            className="md:hidden btn btn-icon btn-ghost text-text-secondary"
                        >
                            {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
                        </button>
                    </div>
                </div>

                {/* -- Nav bar ----------------------------------------- */}
                <nav className="hidden md:flex items-center gap-0.5 pb-2">
                    {navLinks.map(link => (
                        <Link
                            key={link.to}
                            to={link.to}
                            className={`nav-link text-sm ${isActive(link.exact) ? 'nav-link-active' : ''}`}
                        >
                            {link.icon && link.icon}
                            {link.label}
                        </Link>
                    ))}
                    {isAuthenticated && (
                        <Link to={buildLink('/referrals')} className={`nav-link text-sm ${isActive('/referrals') ? 'nav-link-active' : ''}`}>
                            Refer & Earn
                        </Link>
                    )}
                    {isAdmin && (
                        <Link
                            to={buildLink('/admin')}
                            className={`nav-link text-sm font-semibold text-theme-primary ml-1 ${isActive('/admin') ? 'nav-link-active' : ''}`}
                        >
                            Admin Panel
                        </Link>
                    )}
                </nav>

                {/* -- Mobile Search ----------------------------------- */}
                <div className="md:hidden pb-3">
                    <SearchAutocomplete />
                </div>
            </div>

            {/* -- Mobile menu ---------------------------------------- */}
            {mobileMenuOpen && (
                <div className="md:hidden border-t border-border-color bg-bg-primary animate-slide-down">
                    <div className="container-wide py-3 space-y-0.5">
                        {navLinks.map(link => (
                            <Link
                                key={link.to}
                                to={link.to}
                                className={`nav-link ${isActive(link.exact) ? 'nav-link-active' : ''}`}
                                onClick={() => setMobileMenuOpen(false)}
                            >
                                {link.icon && link.icon}
                                {link.label}
                            </Link>
                        ))}
                        {isAuthenticated && (
                            <Link to={buildLink('/referrals')} className="nav-link" onClick={() => setMobileMenuOpen(false)}>
                                Refer & Earn
                            </Link>
                        )}
                        {isAdmin && (
                            <Link to={buildLink('/admin')} className="nav-link font-semibold text-theme-primary" onClick={() => setMobileMenuOpen(false)}>
                                Admin Panel
                            </Link>
                        )}
                        {!isAuthenticated && (
                            <div className="flex gap-2 pt-3">
                                <Link to="/login" className="btn btn-secondary flex-1 text-center" onClick={() => setMobileMenuOpen(false)}>Sign in</Link>
                                <Link to="/register" className="btn btn-primary flex-1 text-center" onClick={() => setMobileMenuOpen(false)}>Get started</Link>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </header>
    )
}
