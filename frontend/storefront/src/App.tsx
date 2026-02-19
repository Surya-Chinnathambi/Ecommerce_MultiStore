import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from './components/ui/Toaster'
import { ProtectedRoute } from './components/ProtectedRoute'
import { PageSkeleton } from './components/ui/Skeleton'
import SocialProofNotification from './components/marketing/SocialProofNotification'
import ScrollToTop from './components/ScrollToTop'
import Layout from './components/layout/Layout'

// ── Lazy-loaded pages ─────────────────────────────────────────────────────────
// Auth (kept small — users hit these before the rest is downloaded)
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))

// Public storefront
const HomePage = lazy(() => import('./pages/HomePage'))
const ProductsPage = lazy(() => import('./pages/ProductsPage'))
const ProductDetailPage = lazy(() => import('./pages/ProductDetailPage'))
const SearchResultsPage = lazy(() => import('./pages/SearchResultsPage'))
const TrackOrderPage = lazy(() => import('./pages/TrackOrderPage'))

// Customer
const CartPage = lazy(() => import('./pages/CartPage'))
const CheckoutPage = lazy(() => import('./pages/CheckoutPage'))
const PaymentPage = lazy(() => import('./pages/PaymentPage'))
const OrderSuccessPage = lazy(() => import('./pages/OrderSuccessPage'))
const MyOrdersPage = lazy(() => import('./pages/MyOrdersPage'))
const ProfilePage = lazy(() => import('./pages/ProfilePage'))
const WishlistPage = lazy(() => import('./pages/WishlistPage'))
const ReturnRequestPage = lazy(() => import('./pages/ReturnRequestPage'))
const ReturnStatusPage = lazy(() => import('./pages/ReturnStatusPage'))

// Marketing
const ReferralProgram = lazy(() => import('./components/marketing/ReferralProgram'))

// Priority 3 pages
const NotificationsPage = lazy(() => import('./pages/NotificationsPage'))
const CategoryBrowsePage = lazy(() => import('./pages/CategoryBrowsePage'))
const HelpContactPage = lazy(() => import('./pages/HelpContactPage'))

// Seller
const SellerRegisterPage = lazy(() => import('./pages/seller/SellerRegisterPage'))
const SellerDashboardPage = lazy(() => import('./pages/seller/SellerDashboardPage'))
const SellerProductsPage = lazy(() => import('./pages/seller/SellerProductsPage'))
const SellerOrdersPage = lazy(() => import('./pages/seller/SellerOrdersPage'))

// Admin
const AdminDashboard = lazy(() => import('./pages/AdminDashboard'))
const AdminReviewsPage = lazy(() => import('./pages/AdminReviewsPage'))
const AdminInventoryAlertsPage = lazy(() => import('./pages/AdminInventoryAlertsPage'))
const AdminProductImportPage = lazy(() => import('./pages/AdminProductImportPage'))
const AdminOrdersPage = lazy(() => import('./pages/AdminOrdersPage'))
const AdminCouponsPage = lazy(() => import('./pages/admin/AdminCouponsPage'))
const AdminReturnsPage = lazy(() => import('./pages/admin/AdminReturnsPage'))
const AdminAdsPage = lazy(() => import('./pages/admin/AdminAdsPage'))
const AdminProductsPage = lazy(() => import('./pages/admin/AdminProductsPage'))
const AdminCustomersPage = lazy(() => import('./pages/admin/AdminCustomersPage'))
const AdminSettingsPage = lazy(() => import('./pages/admin/AdminSettingsPage'))
const AnalyticsDashboard = lazy(() => import('./components/AnalyticsDashboard'))
const BillingIntegrationPage = lazy(() => import('./pages/BillingIntegrationPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))
const POSIntegrationPage = lazy(() => import('./pages/POSIntegrationPage'))
const MonitoringDashboard = lazy(() => import('./pages/MonitoringDashboard'))

// ── Role-scoped route wrappers ────────────────────────────────────────────────
function AdminRoute({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute requiredRole="admin" redirectTo="/home">
            {children}
        </ProtectedRoute>
    )
}

function SellerRoute({ children }: { children: React.ReactNode }) {
    return (
        <ProtectedRoute requiredRole="seller" redirectTo="/home">
            {children}
        </ProtectedRoute>
    )
}

// ── App ───────────────────────────────────────────────────────────────────────
function App() {
    // Resolve store_id on first render
    useEffect(() => {
        const params = new URLSearchParams(window.location.search)
        const urlStoreId = params.get('store_id')
        const storedId = localStorage.getItem('store_id')
        const defaultId = import.meta.env.VITE_DEFAULT_STORE_ID

        const storeIdToUse = urlStoreId || storedId || defaultId
        if (storeIdToUse) localStorage.setItem('store_id', storeIdToUse)
    }, [])

    return (
        <>
            <Suspense fallback={<PageSkeleton />}>
                <Routes>
                    {/* Default */}
                    <Route path="/" element={<Navigate to="/login" replace />} />

                    {/* Auth (no layout) */}
                    <Route path="/login" element={<LoginPage />} />
                    <Route path="/register" element={<RegisterPage />} />

                    {/* Public storefront */}
                    <Route path="/home" element={<Layout />}>
                        <Route index element={<HomePage />} />
                    </Route>
                    <Route path="/products" element={<Layout />}>
                        <Route index element={<ProductsPage />} />
                        <Route path=":productId" element={<ProductDetailPage />} />
                    </Route>
                    <Route path="/search" element={<Layout />}>
                        <Route index element={<SearchResultsPage />} />
                    </Route>
                    <Route path="/track-order" element={<Layout />}>
                        <Route index element={<TrackOrderPage />} />
                    </Route>
                    <Route path="/order-success/:orderNumber" element={<Layout />}>
                        <Route index element={<OrderSuccessPage />} />
                    </Route>

                    {/* Customer — any authenticated user */}
                    <Route path="/cart" element={<Layout />}>
                        <Route index element={<ProtectedRoute><CartPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/checkout" element={<Layout />}>
                        <Route index element={<ProtectedRoute><CheckoutPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/payment/:orderNumber" element={<Layout />}>
                        <Route index element={<ProtectedRoute><PaymentPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/profile" element={<Layout />}>
                        <Route index element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/my-orders" element={<Layout />}>
                        <Route index element={<ProtectedRoute><MyOrdersPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/wishlist" element={<Layout />}>
                        <Route index element={<ProtectedRoute><WishlistPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/returns/new/:orderId" element={<Layout />}>
                        <Route index element={<ProtectedRoute><ReturnRequestPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/returns/:returnId" element={<Layout />}>
                        <Route index element={<ProtectedRoute><ReturnStatusPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/referrals" element={<Layout />}>
                        <Route index element={<ProtectedRoute><ReferralProgram /></ProtectedRoute>} />
                    </Route>
                    <Route path="/notifications" element={<Layout />}>
                        <Route index element={<ProtectedRoute><NotificationsPage /></ProtectedRoute>} />
                    </Route>

                    {/* Public pages */}
                    <Route path="/categories" element={<Layout />}>
                        <Route index element={<CategoryBrowsePage />} />
                        <Route path=":slug" element={<CategoryBrowsePage />} />
                    </Route>
                    <Route path="/help" element={<Layout />}>
                        <Route index element={<HelpContactPage />} />
                    </Route>

                    {/* Seller — requires seller role */}
                    <Route path="/seller/register" element={<Layout />}>
                        <Route index element={<ProtectedRoute><SellerRegisterPage /></ProtectedRoute>} />
                    </Route>
                    <Route path="/seller/dashboard" element={<Layout />}>
                        <Route index element={<SellerRoute><SellerDashboardPage /></SellerRoute>} />
                    </Route>
                    <Route path="/seller/products" element={<Layout />}>
                        <Route index element={<SellerRoute><SellerProductsPage /></SellerRoute>} />
                    </Route>
                    <Route path="/seller/orders" element={<Layout />}>
                        <Route index element={<SellerRoute><SellerOrdersPage /></SellerRoute>} />
                    </Route>

                    {/* Admin — requires admin role */}
                    <Route path="/admin" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminDashboard /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/reviews" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminReviewsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/inventory-alerts" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminInventoryAlertsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/orders" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminOrdersPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/coupons" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminCouponsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/returns" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminReturnsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/ads" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminAdsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/products" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminProductsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/customers" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminCustomersPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/settings" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminSettingsPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/analytics" element={<Layout />}>
                        <Route index element={<AdminRoute><AnalyticsDashboard /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/billing" element={<Layout />}>
                        <Route index element={<AdminRoute><BillingIntegrationPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/pos-integration" element={<Layout />}>
                        <Route index element={<AdminRoute><POSIntegrationPage /></AdminRoute>} />
                    </Route>
                    <Route path="/admin/product-import" element={<Layout />}>
                        <Route index element={<AdminRoute><AdminProductImportPage /></AdminRoute>} />
                    </Route>
                    <Route path="/monitoring" element={<Layout />}>
                        <Route index element={<AdminRoute><MonitoringDashboard /></AdminRoute>} />
                    </Route>
                    {/* 404 catch-all */}
                    <Route path="*" element={<Layout />}>
                        <Route index element={<NotFoundPage />} />
                    </Route>
                </Routes>
            </Suspense>
            <Toaster />
            <SocialProofNotification />
            <ScrollToTop />
        </>
    )
}

export default App
