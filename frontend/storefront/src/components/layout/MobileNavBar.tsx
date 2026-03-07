import { Link, useLocation } from 'react-router-dom'
import { Home, Search, ShoppingCart, Heart, User } from 'lucide-react'
import { useCartStore } from '@/store/cartStore'
import { useWishlistStore } from '@/store/wishlistStore'
import { useAuthStore } from '@/store/authStore'

export default function MobileNavBar() {
    const location = useLocation()
    const totalItems = useCartStore((s) => s.getItemCount())
    const wishlistCount = useWishlistStore((s) => s.items.length)
    const isAuthenticated = useAuthStore((s) => s.isAuthenticated)

    const getStoreId = () => localStorage.getItem('store_id') || ''
    const link = (path: string) => {
        const sid = getStoreId()
        return sid ? `${path}?store_id=${sid}` : path
    }

    const tabs = [
        { to: link('/home'), icon: Home, label: 'Home', match: '/home' },
        { to: link('/search'), icon: Search, label: 'Explore', match: '/search' },
        { to: link('/cart'), icon: ShoppingCart, label: 'Cart', match: '/cart', badge: totalItems },
        { to: link('/wishlist'), icon: Heart, label: 'Wishlist', match: '/wishlist', badge: wishlistCount },
        { to: isAuthenticated ? link('/profile') : '/login', icon: User, label: 'Account', match: '/profile' },
    ]

    // Don't render on certain pages like login/register/checkout
    const hidePaths = ['/login', '/register', '/checkout', '/payment']
    if (hidePaths.some((p) => location.pathname.startsWith(p))) return null

    return (
        <nav className="mobile-nav fixed bottom-0 inset-x-0 z-50 md:hidden border-t border-border-color">
            <div className="grid grid-cols-5 pb-safe">
                {tabs.map((tab) => {
                    const active = location.pathname.startsWith(tab.match)
                    return (
                        <Link
                            key={tab.label}
                            to={tab.to}
                            className={`flex flex-col items-center justify-center py-2 px-1 relative transition-all duration-200
                                ${active ? 'text-theme-primary' : 'text-text-tertiary hover:text-text-secondary'}`}
                        >
                            <div className={`relative p-1.5 rounded-xl transition-all duration-200 ${active ? 'bg-theme-primary/10' : ''}`}>
                                <tab.icon className={`h-5 w-5 transition-all duration-200 ${active ? 'scale-110' : ''}`} />
                                {tab.badge && tab.badge > 0 && (
                                    <span className="absolute -top-1 -right-1 bg-red-500 text-white text-[9px] rounded-full h-4 w-4 flex items-center justify-center font-bold leading-none">
                                        {tab.badge > 9 ? '9+' : tab.badge}
                                    </span>
                                )}
                            </div>
                            <span className={`text-[10px] mt-0.5 leading-none transition-all duration-200 ${active ? 'font-semibold' : ''}`}>{tab.label}</span>
                        </Link>
                    )
                })}
            </div>
        </nav>
    )
}
