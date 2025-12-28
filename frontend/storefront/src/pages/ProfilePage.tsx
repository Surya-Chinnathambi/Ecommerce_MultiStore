import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'
import { authApi, orderApi } from '../lib/api'
import { Trash2, Plus, MapPin } from 'lucide-react'

interface Address {
  id: string
  full_name: string
  phone: string
  address_line1: string
  address_line2: string | null
  city: string
  state: string
  pincode: string
  landmark: string | null
  is_default: boolean
  address_type: string
  created_at: string
}

interface Order {
  id: string
  order_number: string
  total_amount: number
  status: string
  payment_status: string
  created_at: string
  items: Array<{
    product_name: string
    quantity: number
    price: number
  }>
}

export default function ProfilePage() {
  const { user, isAuthenticated, updateUser, logout } = useAuthStore()
  const navigate = useNavigate()

  const [activeTab, setActiveTab] = useState<'profile' | 'password' | 'addresses' | 'orders'>('profile')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState({ type: '', text: '' })

  // Profile form
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
  })

  // Password form
  const [passwordData, setPasswordData] = useState({
    old_password: '',
    new_password: '',
    confirm_password: '',
  })

  // Addresses
  const [addresses, setAddresses] = useState<Address[]>([])
  const [showAddressForm, setShowAddressForm] = useState(false)
  const [addressForm, setAddressForm] = useState({
    full_name: user?.full_name || '',
    phone: user?.phone || '',
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: '',
    landmark: '',
    is_default: false,
    address_type: 'home',
  })

  // Orders
  const [orders, setOrders] = useState<Order[]>([])
  const [ordersLoading, setOrdersLoading] = useState(false)

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login')
    }
  }, [isAuthenticated, navigate])

  useEffect(() => {
    if (activeTab === 'addresses') {
      loadAddresses()
    } else if (activeTab === 'orders') {
      loadOrders()
    }
  }, [activeTab])

  const loadAddresses = async () => {
    try {
      const response = await authApi.getAddresses()
      setAddresses(response.data)
    } catch (err) {
      console.error('Failed to load addresses:', err)
    }
  }

  const loadOrders = async () => {
    setOrdersLoading(true)
    try {
      const response = await orderApi.getOrders()
      setOrders(response.data.data || [])
    } catch (err) {
      console.error('Failed to load orders:', err)
      setOrders([])
    } finally {
      setOrdersLoading(false)
    }
  }

  const handleProfileUpdate = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    setLoading(true)

    try {
      const response = await authApi.updateProfile(profileData)
      updateUser(response.data)
      setMessage({ type: 'success', text: 'Profile updated successfully!' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to update profile' })
    } finally {
      setLoading(false)
    }
  }

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })

    if (passwordData.new_password !== passwordData.confirm_password) {
      setMessage({ type: 'error', text: 'New passwords do not match' })
      return
    }

    if (passwordData.new_password.length < 8) {
      setMessage({ type: 'error', text: 'Password must be at least 8 characters' })
      return
    }

    setLoading(true)

    try {
      await authApi.changePassword({
        old_password: passwordData.old_password,
        new_password: passwordData.new_password,
      })
      setMessage({ type: 'success', text: 'Password changed successfully!' })
      setPasswordData({ old_password: '', new_password: '', confirm_password: '' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to change password' })
    } finally {
      setLoading(false)
    }
  }

  const handleAddressSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setMessage({ type: '', text: '' })
    setLoading(true)

    try {
      await authApi.createAddress(addressForm)
      setMessage({ type: 'success', text: 'Address added successfully!' })
      setShowAddressForm(false)
      setAddressForm({
        full_name: user?.full_name || '',
        phone: user?.phone || '',
        address_line1: '',
        address_line2: '',
        city: '',
        state: '',
        pincode: '',
        landmark: '',
        is_default: false,
        address_type: 'home',
      })
      loadAddresses()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to add address' })
    } finally {
      setLoading(false)
    }
  }

  const handleDeleteAddress = async (id: string) => {
    if (!confirm('Are you sure you want to delete this address?')) return

    try {
      await authApi.deleteAddress(id)
      setMessage({ type: 'success', text: 'Address deleted successfully!' })
      loadAddresses()
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || 'Failed to delete address' })
    }
  }

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-bg-secondary py-8">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-bg-primary shadow rounded-lg border border-border-color">
          {/* Header */}
          <div className="px-6 py-4 border-b border-border-color">
            <div className="flex justify-between items-center">
              <div>
                <h1 className="text-2xl font-bold text-text-primary">My Account</h1>
                <p className="text-sm text-text-secondary">{user.email}</p>
              </div>
              <button
                onClick={handleLogout}
                className="px-4 py-2 border border-border-color rounded-md text-sm font-medium text-text-primary hover:bg-bg-tertiary"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="border-b border-border-color">
            <nav className="-mb-px flex space-x-8 px-6">
              {[
                { key: 'profile', label: 'Profile' },
                { key: 'password', label: 'Password' },
                { key: 'addresses', label: 'Addresses' },
                { key: 'orders', label: 'Order History' },
              ].map((tab) => (
                <button
                  key={tab.key}
                  onClick={() => setActiveTab(tab.key as any)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${activeTab === tab.key
                    ? 'border-theme-primary text-theme-primary'
                    : 'border-transparent text-text-secondary hover:text-text-primary hover:border-border-color'
                    }`}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="p-6">
            {message.text && (
              <div className={`mb-4 p-4 rounded-md ${message.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
                }`}>
                {message.text}
              </div>
            )}

            {activeTab === 'profile' && (
              <form onSubmit={handleProfileUpdate} className="space-y-6 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-text-primary">Email</label>
                  <input
                    type="email"
                    value={user.email}
                    disabled
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-tertiary text-text-tertiary cursor-not-allowed"
                    aria-label="Email address (read-only)"
                  />
                  <p className="mt-1 text-xs text-text-tertiary">Email cannot be changed</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary">Full Name</label>
                  <input
                    type="text"
                    value={profileData.full_name}
                    onChange={(e) => setProfileData({ ...profileData, full_name: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md focus:ring-theme-primary focus:border-theme-primary bg-bg-primary text-text-primary"
                    required
                    aria-label="Full name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary">Phone Number</label>
                  <input
                    type="tel"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md focus:ring-theme-primary focus:border-theme-primary bg-bg-primary text-text-primary"
                    placeholder="+919876543210"
                    aria-label="Phone number"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-theme-primary hover:bg-theme-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-theme-primary disabled:opacity-50"
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </form>
            )}

            {activeTab === 'password' && (
              <form onSubmit={handlePasswordChange} className="space-y-6 max-w-xl">
                <div>
                  <label className="block text-sm font-medium text-text-primary">Current Password</label>
                  <input
                    type="password"
                    value={passwordData.old_password}
                    onChange={(e) => setPasswordData({ ...passwordData, old_password: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md focus:ring-theme-primary focus:border-theme-primary bg-bg-primary text-text-primary"
                    required
                    aria-label="Current password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary">New Password</label>
                  <input
                    type="password"
                    value={passwordData.new_password}
                    onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md focus:ring-theme-primary focus:border-theme-primary bg-bg-primary text-text-primary"
                    placeholder="Min. 8 characters with uppercase, lowercase & digit"
                    required
                    aria-label="New password"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-text-primary">Confirm New Password</label>
                  <input
                    type="password"
                    value={passwordData.confirm_password}
                    onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                    className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md focus:ring-theme-primary focus:border-theme-primary bg-bg-primary text-text-primary"
                    required
                    aria-label="Confirm new password"
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-theme-primary hover:bg-theme-primary-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-theme-primary disabled:opacity-50"
                >
                  {loading ? 'Changing...' : 'Change Password'}
                </button>
              </form>
            )}

            {activeTab === 'addresses' && (
              <div className="space-y-6">
                <div className="flex justify-between items-center">
                  <h2 className="text-lg font-semibold text-text-primary">Saved Addresses</h2>
                  {!showAddressForm && (
                    <button
                      onClick={() => setShowAddressForm(true)}
                      className="flex items-center space-x-2 px-4 py-2 bg-theme-primary text-white rounded-md hover:bg-theme-primary-hover"
                    >
                      <Plus className="h-4 w-4" />
                      <span>Add New Address</span>
                    </button>
                  )}
                </div>

                {showAddressForm && (
                  <form onSubmit={handleAddressSubmit} className="border border-border-color rounded-lg p-6 space-y-4 bg-bg-primary">
                    <h3 className="font-semibold text-lg mb-4 text-text-primary">New Address</h3>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-text-primary">Full Name</label>
                        <input
                          type="text"
                          value={addressForm.full_name}
                          onChange={(e) => setAddressForm({ ...addressForm, full_name: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          required
                          aria-label="Full name for address"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-text-primary">Phone</label>
                        <input
                          type="tel"
                          value={addressForm.phone}
                          onChange={(e) => setAddressForm({ ...addressForm, phone: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          required
                          aria-label="Phone number for address"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-text-primary">Address Line 1</label>
                      <input
                        type="text"
                        value={addressForm.address_line1}
                        onChange={(e) => setAddressForm({ ...addressForm, address_line1: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                        placeholder="House/Flat No, Building Name"
                        required
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-text-primary">Address Line 2 (Optional)</label>
                      <input
                        type="text"
                        value={addressForm.address_line2}
                        onChange={(e) => setAddressForm({ ...addressForm, address_line2: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                        placeholder="Street, Area"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-text-primary">City</label>
                        <input
                          type="text"
                          value={addressForm.city}
                          onChange={(e) => setAddressForm({ ...addressForm, city: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          required
                          aria-label="City"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-text-primary">State</label>
                        <input
                          type="text"
                          value={addressForm.state}
                          onChange={(e) => setAddressForm({ ...addressForm, state: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          required
                          aria-label="State"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-text-primary">Pincode</label>
                        <input
                          type="text"
                          pattern="[0-9]{6}"
                          value={addressForm.pincode}
                          onChange={(e) => setAddressForm({ ...addressForm, pincode: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          placeholder="123456"
                          required
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-text-primary">Landmark (Optional)</label>
                      <input
                        type="text"
                        value={addressForm.landmark}
                        onChange={(e) => setAddressForm({ ...addressForm, landmark: e.target.value })}
                        className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                        aria-label="Landmark"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-text-primary">Address Type</label>
                        <select
                          value={addressForm.address_type}
                          onChange={(e) => setAddressForm({ ...addressForm, address_type: e.target.value })}
                          className="mt-1 block w-full px-3 py-2 border border-border-color rounded-md bg-bg-primary text-text-primary"
                          aria-label="Address type"
                        >
                          <option value="home">Home</option>
                          <option value="work">Work</option>
                          <option value="other">Other</option>
                        </select>
                      </div>
                      <div className="flex items-center mt-6">
                        <input
                          type="checkbox"
                          checked={addressForm.is_default}
                          onChange={(e) => setAddressForm({ ...addressForm, is_default: e.target.checked })}
                          className="h-4 w-4 text-theme-primary border-border-color rounded"
                          aria-label="Set as default address"
                        />
                        <label className="ml-2 text-sm text-text-primary">Set as default address</label>
                      </div>
                    </div>

                    <div className="flex space-x-3">
                      <button
                        type="submit"
                        disabled={loading}
                        className="flex-1 py-2 px-4 bg-theme-primary text-white rounded-md hover:bg-theme-primary-hover disabled:opacity-50"
                      >
                        {loading ? 'Saving...' : 'Save Address'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setShowAddressForm(false)}
                        className="px-4 py-2 border border-border-color rounded-md text-text-primary hover:bg-bg-tertiary"
                      >
                        Cancel
                      </button>
                    </div>
                  </form>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {addresses.map((address) => (
                    <div key={address.id} className="border border-border-color rounded-lg p-4 relative bg-bg-primary">
                      {address.is_default && (
                        <span className="absolute top-2 right-2 px-2 py-1 bg-theme-primary bg-opacity-10 text-theme-primary text-xs rounded">
                          Default
                        </span>
                      )}
                      <div className="flex items-start space-x-3">
                        <MapPin className="h-5 w-5 text-text-tertiary mt-1" />
                        <div className="flex-1">
                          <p className="font-semibold text-text-primary">{address.full_name}</p>
                          <p className="text-sm text-text-secondary">{address.phone}</p>
                          <p className="text-sm text-text-secondary mt-2">
                            {address.address_line1}
                            {address.address_line2 && `, ${address.address_line2}`}
                          </p>
                          <p className="text-sm text-text-secondary">
                            {address.city}, {address.state} - {address.pincode}
                          </p>
                          {address.landmark && (
                            <p className="text-sm text-text-tertiary">Landmark: {address.landmark}</p>
                          )}
                          <span className="inline-block mt-2 px-2 py-1 bg-bg-tertiary text-text-primary text-xs rounded capitalize">
                            {address.address_type}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDeleteAddress(address.id)}
                        className="absolute bottom-2 right-2 text-red-600 hover:text-red-800"
                        aria-label="Delete address"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ))}
                </div>

                {addresses.length === 0 && !showAddressForm && (
                  <div className="text-center py-12">
                    <MapPin className="h-12 w-12 text-text-tertiary mx-auto mb-4" />
                    <p className="text-text-tertiary">No saved addresses yet</p>
                    <button
                      onClick={() => setShowAddressForm(true)}
                      className="mt-4 text-theme-primary hover:text-theme-primary-hover font-medium"
                    >
                      Add your first address
                    </button>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'orders' && (
              <div className="space-y-6">
                <h2 className="text-lg font-semibold text-text-primary">Order History</h2>

                {ordersLoading ? (
                  <div className="text-center py-12">
                    <p className="text-text-tertiary">Loading orders...</p>
                  </div>
                ) : orders.length === 0 ? (
                  <div className="text-center py-12">
                    <p className="text-text-tertiary">No orders yet</p>
                    <button
                      onClick={() => navigate('/products')}
                      className="mt-4 text-theme-primary hover:text-theme-primary-hover font-medium"
                    >
                      Start Shopping
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {orders.map((order) => (
                      <div key={order.id} className="border border-border-color rounded-lg p-6 bg-bg-primary">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <p className="font-semibold text-lg text-text-primary">Order #{order.order_number}</p>
                            <p className="text-sm text-text-secondary">
                              {new Date(order.created_at).toLocaleDateString('en-IN', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-lg font-bold text-text-primary">₹{order.total_amount.toFixed(2)}</p>
                            <span className={`inline-block mt-1 px-3 py-1 text-xs font-semibold rounded-full ${order.status === 'delivered' ? 'bg-green-100 text-green-800' :
                              order.status === 'cancelled' ? 'bg-red-100 text-red-800' :
                                order.status === 'processing' ? 'bg-theme-primary/10 text-theme-primary' :
                                  'bg-yellow-100 text-yellow-800'
                              }`}>
                              {order.status.toUpperCase()}
                            </span>
                          </div>
                        </div>

                        <div className="border-t border-border-color pt-4">
                          <p className="text-sm font-medium text-text-primary mb-2">Items:</p>
                          <ul className="space-y-2">
                            {order.items.map((item, index) => (
                              <li key={index} className="flex justify-between text-sm">
                                <span className="text-text-secondary">
                                  {item.product_name} x {item.quantity}
                                </span>
                                <span className="text-text-primary font-medium">
                                  ₹{(item.price * item.quantity).toFixed(2)}
                                </span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Account Info */}
        <div className="mt-6 bg-bg-primary shadow rounded-lg p-6 border border-border-color">
          <h2 className="text-lg font-semibold mb-4 text-text-primary">Account Information</h2>
          <dl className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <dt className="text-sm font-medium text-text-tertiary">Account Type</dt>
              <dd className="mt-1 text-sm text-text-primary capitalize">{user.role}</dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-text-tertiary">Member Since</dt>
              <dd className="mt-1 text-sm text-text-primary">
                {new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>
            <div>
              <dt className="text-sm font-medium text-text-tertiary">Account Status</dt>
              <dd className="mt-1">
                <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>
    </div>
  )
}
