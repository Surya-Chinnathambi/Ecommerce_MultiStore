import React, { Suspense, lazy, useEffect } from 'react'
import { Routes, Route, Navigate, useLocation, Outlet } from 'react-router-dom'
import { Toaster } from './components/ui/Toaster'
import { ProtectedRoute } from './components/ProtectedRoute'
import SocialProofNotification from './components/marketing/SocialProofNotification'
import ScrollToTop from './components/ScrollToTop'
import Layout from './components/layout/Layout'
import Loader3D from '@/components/ui/Loader3D'
import GlobalScene3D from '@/components/ui/GlobalScene3D'

const Loading = () => <Loader3D />

// ── Lazy-loaded pages ─────────────────────────────────────────────────────────
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const ProductsPage = lazy(() => import('./pages/ProductsPage'))
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'))
const SearchResultsPage = lazy(() => import('./pages/SearchResultsPage'))
const TrackOrderPage = lazy(() => import('./pages/TrackOrderPage'))
const CategoriesPage = lazy(() => import('./pages/CategoryBrowsePage'))
const CategoryBrowsePage = lazy(() => import('./pages/CategoryBrowsePage'))
const CartPage = lazy(() => import('./pages/CartPage'))
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'))
const PaymentPage = lazy(() => import('./pages/PaymentPage'))
const OrderSuccessPage = lazy(() => import('./pages/OrderSuccessPage'))
const MyOrdersPage = lazy(() => import('./pages/MyOrdersPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const WishlistPage = lazy(() => import('./pages/WishlistPage'))

// Admin
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const AdminReviewsPage = lazy(() => import('./pages/AdminReviewsPage'))
const AdminInventoryAlertsPage = lazy(() => import('./pages/AdminInventoryAlertsPage'))
const AdminProductImportPage = lazy(() => import('./pages/AdminProductImportPage'))
const AdminOrdersPage = lazy(() => import('./pages/AdminOrdersPage'))
const AdminCouponsPage = lazy(() => import('./pages/admin/AdminCouponsPage'))
const AdminAdsPage = lazy(() => import('./pages/admin/AdminAdsPage'))
const AdminProductsPage = lazy(() => import('./pages/admin/AdminProductsPage'))
const AdminCustomersPage = lazy(() => import('./pages/admin/AdminCustomersPage'))
const AdminSettingsPage = lazy(() => import('./pages/admin/AdminSettingsPage'))
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'))
const BillingIntegrationPage = lazy(() => import('./pages/BillingIntegrationPage'))
const POSIntegrationPage = lazy(() => import('./pages/POSIntegrationPage'))
const MonitoringDashboard = lazy(() => import('./pages/MonitoringDashboard'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

// ── Role-scoped route wrappers ────────────────────────────────────────────────
function AdminRoute({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute requiredRole="admin" redirectTo="/home">
            {children}
        </ProtectedRoute>
    )
}

// ── Error Boundary ─────────────────────────────────────────────────────────────
class ErrorBoundary extends React.Component<{ children: React.ReactNode }, { hasError: boolean; error: Error | null }> {
    constructor(props: { children: React.ReactNode }) {
        super(props)
        this.state = { hasError: false, error: null }
    }
    static getDerivedStateFromError(error: Error) { return { hasError: true, error } }
    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen flex items-center justify-center bg-bg-primary p-8">
                    <div className="card max-w-2xl w-full p-8 border-red-500/20 bg-red-500/5">
                        <h2 className="text-2xl font-bold text-red-600 mb-4">Application Crash Detected</h2>
                        <p className="text-text-secondary mb-6">Something went wrong in the 3D rendering engine or application logic.</p>
                        <pre className="p-4 bg-black/5 rounded-xl text-xs overflow-auto max-h-60 mb-6 font-mono text-red-500/80">
                            {this.state.error?.toString()}
                        </pre>
                        <button onClick={() => window.location.reload()} className="btn btn-primary">
                            Reload Application
                        </button>
                    </div>
                </div>
            )
        }
        return this.props.children
    }
}

function AppContent() {
    const location = useLocation()
    const buildLink = (path: string) => {
        const params = new URLSearchParams(window.location.search)
        const storeId = params.get('store_id') || localStorage.getItem('store_id')
        return storeId ? `${path}?store_id=${storeId}` : path
    }

    return (
        <Suspense fallback={<Loading />}>
            <Routes location={location} key={location.pathname}>
                <Route path="/" element={<Navigate to={buildLink('/home')} replace />} />
                
                {/* Auth */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Main Storefront Layout */}
                <Route element={<Layout />}>
                    <Route path="/home" element={<HomePage />} />
                    <Route path="/products" element={<ProductsPage />} />
                    <Route path="/products/:productId" element={<ProductDetailPage />} />
                    <Route path="/search" element={<SearchResultsPage />} />
                    <Route path="/categories" element={<CategoriesPage />} />
                    <Route path="/categories/:slug" element={<CategoryBrowsePage />} />
                    <Route path="/track-order" element={<TrackOrderPage />} />
                    <Route path="/order-success/:orderNumber" element={<OrderSuccessPage />} />
                    
                    {/* Protected Routes */}
                    <Route element={<ProtectedRoute children={<Outlet />} />}>
                        <Route path="/cart" element={<CartPage />} />
                        <Route path="/checkout" element={<CheckoutPage />} />
                        <Route path="/payment/:orderNumber" element={<PaymentPage />} />
                        <Route path="/profile" element={<ProfilePage />} />
                        <Route path="/my-orders" element={<MyOrdersPage />} />
                        <Route path="/wishlist" element={<WishlistPage />} />
                    </Route>

                    {/* Admin Routes */}
                    <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
                    <Route path="/admin/reviews" element={<AdminRoute><AdminReviewsPage /></AdminRoute>} />
                    <Route path="/admin/inventory-alerts" element={<AdminRoute><AdminInventoryAlertsPage /></AdminRoute>} />
                    <Route path="/admin/orders" element={<AdminRoute><AdminOrdersPage /></AdminRoute>} />
                    <Route path="/admin/coupons" element={<AdminRoute><AdminCouponsPage /></AdminRoute>} />
                    <Route path="/admin/ads" element={<AdminRoute><AdminAdsPage /></AdminRoute>} />
                    <Route path="/admin/products" element={<AdminRoute><AdminProductsPage /></AdminRoute>} />
                    <Route path="/admin/customers" element={<AdminRoute><AdminCustomersPage /></AdminRoute>} />
                    <Route path="/admin/settings" element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
                    <Route path="/admin/analytics" element={<AdminRoute><AnalyticsDashboard /></AdminRoute>} />
                    <Route path="/admin/billing" element={<AdminRoute><BillingIntegrationPage /></AdminRoute>} />
                    <Route path="/admin/pos-integration" element={<AdminRoute><POSIntegrationPage /></AdminRoute>} />
                    <Route path="/admin/product-import" element={<AdminRoute><AdminProductImportPage /></AdminRoute>} />
                    <Route path="/monitoring" element={<AdminRoute><MonitoringDashboard /></AdminRoute>} />

                    <Route path="*" element={<NotFoundPage />} />
                </Route>
            </Routes>
        </Suspense>
    )
}

function App() {
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const urlStoreId = params.get('store_id')
        const storedId = localStorage.getItem('store_id')
        const storeIdToUse = urlStoreId || storedId || import.meta.env.VITE_DEFAULT_STORE_ID
        if (storeIdToUse) localStorage.setItem('store_id', storeIdToUse)
    }, [])

    return (
        <>
            <GlobalScene3D />
            <ErrorBoundary>
                <AppContent />
            </ErrorBoundary>
            <Toaster />
            <SocialProofNotification />
            <ScrollToTop />
        </>
    )
}

export default App
