import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: string
  email: string
  phone: string | null
  full_name: string
  role: string
  store_id: string | null
  is_active: boolean
  is_email_verified: boolean
  is_phone_verified: boolean
  created_at: string
  last_login_at: string | null
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  setAuth: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      setAuth: (token, user) => set({ token, user, isAuthenticated: true }),
      logout: () => set({ token: null, user: null, isAuthenticated: false }),
      updateUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
    }
  )
)
