import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Home() {
  const { user } = useAuth()
  const isAuthority = user && user.role !== 'CITIZEN'
  return (
    <section className="hero">
      <h1>Report • Track • Improve Your City</h1>
      <p>
        SevaSetu AI turns citizen-reported civic problems into prioritised, location-aware
        actions for authorities.
      </p>
      <div className="hero-actions">
        {isAuthority ? (
          <Link className="btn btn-primary btn-lg" to="/authority">Open Authority Dashboard</Link>
        ) : (
          <>
            <Link className="btn btn-primary btn-lg" to={user ? '/report' : '/login'}>Report an Issue</Link>
            <Link className="btn btn-outline btn-lg" to={user ? '/my-reports' : '/login'}>Track My Reports</Link>
          </>
        )}
      </div>
      <div className="how">
        <h3>How it works</h3>
        <ol>
          <li><b>Report</b><span>Photo, location and a short note — the AI suggests the issue type.</span></li>
          <li><b>Prioritise</b><span>A transparent score ranks urgency; nearby reports merge into one issue.</span></li>
          <li><b>Route</b><span>The issue goes to the right department and appears on the authority map.</span></li>
          <li><b>Resolve</b><span>Authorities act, upload an after-photo and verify — citizens track every step.</span></li>
        </ol>
      </div>
      <div className="categories">
        <div>🕳️<b>Potholes</b><small>Road damage</small></div>
        <div>🗑️<b>Garbage</b><small>Waste accumulation</small></div>
        <div>💧<b>Water leakage</b><small>Pipes &amp; mains</small></div>
        <div>💡<b>Streetlights</b><small>Damaged / not working</small></div>
      </div>
    </section>
  )
}
