import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const isAuthority = user && user.role !== 'CITIZEN'

  return (
    <header className="navbar">
      <Link to="/" className="brand">🌉 SevaSetu <span>AI</span></Link>
      <nav>
        {user && !isAuthority && (
          <>
            <Link to="/report">Report Issue</Link>
            <Link to="/my-reports">My Reports</Link>
          </>
        )}
        {isAuthority && (<><Link to="/authority">Dashboard</Link><Link to="/authority/map">Map</Link></>)}
        {user ? (
          <>
            <span className="who">{user.name}</span>
            <button className="btn btn-ghost" onClick={() => { logout(); navigate('/') }}>Logout</button>
          </>
        ) : (
          <>
            <Link to="/login">Login</Link>
            <Link to="/register" className="btn btn-primary">Register</Link>
          </>
        )}
      </nav>
    </header>
  )
}
