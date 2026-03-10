import { useState } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { authApi } from '../lib/api'
import { useAuthStore } from '../store/authStore'
import { Mail, Lock, LogIn, Eye, EyeOff, ShoppingBag, Check, AlertCircle, ArrowRight } from 'lucide-react'
import Button from '@/components/ui/Button'
import FormField, { getFieldAria } from '@/components/ui/FormField'

const features = [
  'Browse thousands of curated products',
  'Real-time order tracking',
  'Secure & fast checkout',
  'Exclusive member-only deals',
]

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [showPassword, setShowPassword] = useState(false)
  const navigate = useNavigate()
  const location = useLocation()
  const setAuth = useAuthStore((state) => state.setAuth)

  const from = (location.state as any)?.from?.pathname || '/home'

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const response = await authApi.login(email, password)
      const { access_token, user } = response.data
      setAuth(access_token, user)
      if (user.role === 'admin' || user.role === 'super_admin') {
        navigate('/admin', { replace: true })
      } else {
        navigate(from, { replace: true })
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex bg-bg-secondary">
      {/* -- Left panel � branding ----------------------------- */}
      <div className="hidden lg:flex lg:w-[52%] relative overflow-hidden items-center justify-center">
        {/* Background */}
        <div className="absolute inset-0 gradient-primary opacity-95" />
        {/* Mesh pattern */}
        <div className="absolute inset-0 auth-mesh-pattern" />
        {/* Decorative circles */}
        <div className="absolute -top-24 -left-24 h-96 w-96 rounded-full bg-white/5 blur-3xl" />
        <div className="absolute -bottom-24 -right-24 h-96 w-96 rounded-full bg-white/5 blur-3xl" />

        <div className="relative z-10 max-w-md px-12 text-white">
          <div className="flex items-center gap-3 mb-10">
            <div className="h-11 w-11 rounded-[var(--radius-xl)] bg-white/20 border border-white/30 flex items-center justify-center">
              <ShoppingBag className="h-6 w-6 text-white" />
            </div>
            <span className="text-xl font-bold tracking-tight">E-Commerce</span>
          </div>

          <h2 className="text-4xl font-extrabold leading-tight mb-4 tracking-tight">
            Welcome back to your store
          </h2>
          <p className="text-white/70 text-lg leading-relaxed mb-10">
            Sign in to manage orders, discover new products, and enjoy your personalized shopping experience.
          </p>

          <ul className="space-y-4">
            {features.map(f => (
              <li key={f} className="flex items-center gap-3 text-white/85 text-sm">
                <span className="h-6 w-6 rounded-full bg-white/20 border border-white/30 flex items-center justify-center flex-shrink-0">
                  <Check className="h-3.5 w-3.5 text-white" />
                </span>
                {f}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* -- Right panel � form -------------------------------- */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12">
        {/* Mobile logo */}
        <div className="lg:hidden flex items-center gap-3 mb-10">
          <ShoppingBag className="h-8 w-8 text-theme-primary" />
          <span className="text-2xl font-bold text-text-primary">E-Commerce</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h1 className="text-2xl font-bold text-text-primary mb-1.5">Sign in to your account</h1>
            <p className="text-sm text-text-secondary">
              Don't have an account?{' '}
              <Link to={`/register${window.location.search}`} className="font-medium text-theme-primary hover:text-theme-primary-hover transition-colors">
                Create one <ArrowRight className="inline h-3.5 w-3.5" />
              </Link>
            </p>
          </div>

          {error && (
            <div className="alert alert-error mb-6 animate-slide-down">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Email */}
            <FormField id="email" label="Email address" required error={error || undefined}>
              <div className="relative">
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                <input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  className={`input pl-10 ${error ? 'input-error' : ''}`}
                  {...getFieldAria({ error: error || undefined }, 'email')}
                />
              </div>
            </FormField>

            {/* Password */}
            <FormField id="password" label="Password" required error={error || undefined}>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-text-tertiary pointer-events-none" />
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  placeholder="Your password"
                  className={`input pl-10 pr-11 ${error ? 'input-error' : ''}`}
                  {...getFieldAria({ error: error || undefined }, 'password')}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(v => !v)}
                  className="absolute inset-y-0 right-0 pr-3.5 flex items-center text-text-tertiary hover:text-text-secondary transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </FormField>

            <Button
              type="submit"
              loading={loading}
              className="w-full mt-2"
              size="lg"
              leftIcon={<LogIn className="h-4 w-4" />}
            >
              {loading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>

          <p className="mt-8 text-center text-xs text-text-quaternary">
            By signing in, you agree to our{' '}
            <Link to="/terms" className="underline underline-offset-2 hover:text-text-tertiary">Terms</Link>
            {' '}and{' '}
            <Link to="/privacy" className="underline underline-offset-2 hover:text-text-tertiary">Privacy Policy</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
