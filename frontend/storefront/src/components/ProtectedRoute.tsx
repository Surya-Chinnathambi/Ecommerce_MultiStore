import { Navigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

/** Numeric rank for each role — higher = more privileged. */
const ROLE_RANK: Record<string, number> = {
  customer: 0,
  seller: 1,
  admin: 2,
  super_admin: 3,
}

interface ProtectedRouteProps {
  children: React.ReactNode
  /**
   * Minimum role required to access this route.
   * If omitted, any authenticated user is allowed.
   */
  requiredRole?: 'seller' | 'admin' | 'super_admin'
  /** Where to redirect when access is denied. Defaults to "/home". */
  redirectTo?: string
}

export const ProtectedRoute = ({
  children,
  requiredRole,
  redirectTo = '/home',
}: ProtectedRouteProps) => {
  const { isAuthenticated, user } = useAuthStore()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requiredRole) {
    const userRank = ROLE_RANK[user?.role ?? 'customer'] ?? 0
    const neededRank = ROLE_RANK[requiredRole] ?? 99
    if (userRank < neededRank) {
      return <Navigate to={redirectTo} replace />
    }
  }

  return <>{children}</>
}
