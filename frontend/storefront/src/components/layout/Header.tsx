import { Link, useNavigate } from 'react-router-dom'
import { ShoppingCart, Menu, User, LogOut, Activity, CreditCard, Search } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useAuthStore } from '@/store/authStore'
import { useQuery } from '@tanstack/react-query'
import { storeApi } from '@/lib/api'
import { useState } from 'react'
import GlobalSearch from '@/components/GlobalSearch'
import ThemeToggle from '@/components/ThemeToggle'

export default function Header() {
    const navigate = useNavigate()
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
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
    const [userMenuOpen, setUserMenuOpen] = useState(false)
    const [searchQuery, setSearchQuery] = useState('')

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault()
        if (searchQuery.trim()) {
            navigate(buildLink(`/products?search=${encodeURIComponent(searchQuery)}`))
        }
    }

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
        <header className="bg-bg-primary shadow-sm sticky top-0 z-50 border-b border-border-color">
            <div className="container mx-auto px-4">
                {/* Top bar */}
                <div className="py-3 border-b border-border-color">
                    <div className="flex items-center justify-between gap-4">
                        <Link to={buildLink("/home")} className="flex items-center space-x-3 flex-shrink-0">
                            {storeData?.logo_url && (
                                <img src={storeData.logo_url} alt={storeData.name} className="h-10 w-10 object-contain" />
                            )}
                            <div>
                                <h1 className="text-2xl font-bold text-theme-primary">
                                    {storeData?.name || 'Loading...'}
                                </h1>
                                {storeData?.city && (
                                    <p className="text-sm text-text-secondary">{storeData.city}</p>
                                )}
                            </div>
                        </Link>

                        {/* Global Search - desktop */}
                        <div className="hidden md:flex flex-1 max-w-2xl">
                            <GlobalSearch />
                        </div>

                        <div className="flex items-center space-x-4">
                            {/* Theme Toggle */}
                            <ThemeToggle />

                            {/* Auth Section */}
                            {isAuthenticated && user ? (
                                <div className="relative">
                                    <button
                                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                                        className="flex items-center space-x-2 text-text-primary hover:text-theme-primary"
                                        aria-label="User menu"
                                    >
                                        <User className="h-6 w-6" />
                                        <span className="hidden md:inline text-sm font-medium">{user.full_name}</span>
                                    </button>

                                    {userMenuOpen && (
                                        <div className="absolute right-0 mt-2 w-48 bg-bg-primary rounded-md shadow-lg py-1 z-50 border border-border-color">
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
                                <div className="flex items-center space-x-3">
                                    <Link
                                        to="/login"
                                        className="text-text-primary hover:text-theme-primary font-medium text-sm"
                                    >
                                        Login
                                    </Link>
                                    <Link
                                        to="/register"
                                        className="bg-theme-primary text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-theme-primary-hover"
                                    >
                                        Sign Up
                                    </Link>
                                </div>
                            )}

                            {/* Cart */}
                            <Link to={buildLink("/cart")} className="relative" aria-label="Shopping cart">
                                <ShoppingCart className="h-6 w-6 text-text-primary" />
                                {totalItems > 0 && (
                                    <span className="absolute -top-2 -right-2 bg-theme-primary text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                                        {totalItems}
                                    </span>
                                )}
                            </Link>

                            {/* Mobile menu button */}
                            <button
                                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                                className="md:hidden"
                                aria-label="Toggle mobile menu"
                            >
                                <Menu className="h-6 w-6" />
                            </button>
                        </div>
                    </div>
                </div>

                {/* Navigation */}
                <nav className={`${mobileMenuOpen ? 'block' : 'hidden'} md:block py-3`}>
                    <ul className="flex flex-col md:flex-row md:items-center md:space-x-8 space-y-2 md:space-y-0">
                        <li>
                            <Link to={buildLink("/home")} className="text-text-primary hover:text-theme-primary font-medium">
                                Home
                            </Link>
                        </li>
                        <li>
                            <Link to={buildLink("/products")} className="text-text-primary hover:text-theme-primary font-medium">
                                Products
                            </Link>
                        </li>
                        <li>
                            <Link to={buildLink("/track-order")} className="text-text-primary hover:text-theme-primary font-medium">
                                Track Order
                            </Link>
                        </li>
                        {isAuthenticated && (
                            <li>
                                <Link to={buildLink("/referrals")} className="text-text-primary hover:text-theme-primary font-medium">
                                    Refer & Earn
                                </Link>
                            </li>
                        )}
                        {user?.role === 'admin' || user?.role === 'super_admin' ? (
                            <>
                                <li>
                                    <Link to={buildLink("/admin")} className="text-theme-primary hover:text-theme-primary-hover font-bold">
                                        Admin Dashboard
                                    </Link>
                                </li>
                                <li>
                                    <Link to={buildLink("/admin/product-import")} className="text-theme-accent hover:text-theme-primary font-bold">
                                        Import Products
                                    </Link>
                                </li>
                            </>
                        ) : null}
                        {isAuthenticated && (
                            <li className="md:hidden">
                                <Link to={buildLink("/profile")} className="text-text-primary hover:text-theme-primary font-medium">
                                    My Profile
                                </Link>
                            </li>
                        )}
                    </ul>
                </nav>

                {/* Mobile search */}
                <div className="md:hidden pb-3">
                    <form onSubmit={handleSearch}>
                        <div className="relative">
                            <input
                                type="text"
                                placeholder="Search products..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                                className="w-full pl-10 pr-4 py-2 border border-border-color bg-bg-secondary text-text-primary rounded-lg focus:ring-2 focus:ring-theme-primary"
                            />
                            <Search className="absolute left-3 top-2.5 h-5 w-5 text-text-tertiary" />
                        </div>
                    </form>
                </div>
            </div>
        </header>
    )
}
