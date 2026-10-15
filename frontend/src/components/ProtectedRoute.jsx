import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children, citizenOnly = false, authorityOnly = false }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (citizenOnly && user.role !== 'CITIZEN') return <Navigate to="/authority" replace />
  if (authorityOnly && user.role === 'CITIZEN') return <Navigate to="/my-reports" replace />
  return children
}
