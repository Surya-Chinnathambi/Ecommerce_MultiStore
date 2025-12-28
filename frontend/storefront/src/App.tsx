import { Routes, Route, Navigate } from 'react-router-dom'
import { useEffect } from 'react'
import { Toaster } from './components/ui/Toaster'
import { ProtectedRoute } from './components/ProtectedRoute'
import Layout from './components/layout/Layout'
import HomePage from './pages/HomePage'
import ProductsPage from './pages/ProductsPage'
import ProductDetailPage from './pages/ProductDetailPage'
import CartPage from './pages/CartPage'
import CheckoutPage from './pages/CheckoutPage'
import OrderSuccessPage from './pages/OrderSuccessPage'
import PaymentPage from './pages/PaymentPage'
import TrackOrderPage from './pages/TrackOrderPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProfilePage from './pages/ProfilePage'
import AdminDashboard from './pages/AdminDashboard'
import AdminReviewsPage from './pages/AdminReviewsPage'
import AdminInventoryAlertsPage from './pages/AdminInventoryAlertsPage'
import AdminProductImportPage from './pages/AdminProductImportPage'
import AdminOrdersPage from './pages/AdminOrdersPage'
import MyOrdersPage from './pages/MyOrdersPage'
import MonitoringDashboard from './pages/MonitoringDashboard'
import BillingIntegrationPage from './pages/BillingIntegrationPage'
import SocialProofNotification from './components/marketing/SocialProofNotification'
import ReferralProgram from './components/marketing/ReferralProgram'

function App() {
    // Fix store_id on app load
    useEffect(() => {
        const CORRECT_STORE_ID = 'a8e00641-d794-4ae1-a8c0-6bd2bd8fee2a'

        // Check if URL has store_id parameter
        const params = new URLSearchParams(window.location.search)
        const urlStoreId = params.get('store_id')

        // If URL has store_id, use it; otherwise use the default correct one
        const storeIdToUse = urlStoreId || CORRECT_STORE_ID

        // Always ensure correct store_id is set
        localStorage.setItem('store_id', storeIdToUse)
    }, [])

    return (
        <>
            <Routes>
                {/* Default route redirects to login */}
                <Route path="/" element={<Navigate to="/login" replace />} />

                {/* Auth routes without layout */}
                <Route path="/login" element={<LoginPage />} />
                <Route path="/register" element={<RegisterPage />} />

                {/* Main routes with layout */}
                <Route path="/home" element={<Layout />}>
                    <Route index element={<HomePage />} />
                </Route>
                <Route path="/products" element={<Layout />}>
                    <Route index element={<ProductsPage />} />
                    <Route path=":productId" element={<ProductDetailPage />} />
                </Route>

                {/* Protected routes */}
                <Route path="/cart" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <CartPage />
                        </ProtectedRoute>
                    } />
                </Route>
                <Route path="/checkout" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <CheckoutPage />
                        </ProtectedRoute>
                    } />
                </Route>
                <Route path="/profile" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <ProfilePage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Referral Program */}
                <Route path="/referrals" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <ReferralProgram />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Admin routes */}
                <Route path="/admin" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <AdminDashboard />
                        </ProtectedRoute>
                    } />
                </Route>
                <Route path="/admin/reviews" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <AdminReviewsPage />
                        </ProtectedRoute>
                    } />
                </Route>
                <Route path="/admin/inventory-alerts" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <AdminInventoryAlertsPage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Monitoring Dashboard */}
                <Route path="/monitoring" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <MonitoringDashboard />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Billing Integration */}
                <Route path="/admin/billing" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <BillingIntegrationPage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Product Import from Billing Software */}
                <Route path="/admin/product-import" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <AdminProductImportPage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Admin Orders Management */}
                <Route path="/admin/orders" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <AdminOrdersPage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Customer Order History */}
                <Route path="/my-orders" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <MyOrdersPage />
                        </ProtectedRoute>
                    } />
                </Route>

                {/* Order routes */}
                <Route path="/payment/:orderNumber" element={<Layout />}>
                    <Route index element={
                        <ProtectedRoute>
                            <PaymentPage />
                        </ProtectedRoute>
                    } />
                </Route>
                <Route path="/order-success/:orderNumber" element={<Layout />}>
                    <Route index element={<OrderSuccessPage />} />
                </Route>
                <Route path="/track-order" element={<Layout />}>
                    <Route index element={<TrackOrderPage />} />
                </Route>
            </Routes>
            <Toaster />
            <SocialProofNotification />
        </>
    )
}

export default App
