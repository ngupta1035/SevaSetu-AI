import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { issuesApi, errorMessage } from '../services/api'
import { StatusBadge, PriorityBadge, typeLabel } from '../components/Badges'

export default function MyReports() {
  const [issues, setIssues] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    issuesApi.mine().then(setIssues).catch((e) => setError(errorMessage(e)))
  }, [])

  if (error) return <div className="alert">{error}</div>
  if (!issues) return <p className="muted">Loading…</p>

  return (
    <div>
      <div className="row-between">
        <h2>My Reports</h2>
        <Link className="btn btn-primary" to="/report">+ New report</Link>
      </div>
      {issues.length === 0 && <div className="card"><p>You haven't reported anything yet.</p></div>}
      <div className="list">
        {issues.map((i) => (
          <Link key={i.id} to={`/issues/${i.id}`} className="card issue-row">
            <div>
              <b>{i.issue_code}</b> — {typeLabel(i.issue_type)}
              <div className="muted small">{i.address || `${i.latitude.toFixed(4)}, ${i.longitude.toFixed(4)}`} · {new Date(i.created_at).toLocaleDateString()}</div>
            </div>
            <div className="badges"><PriorityBadge score={i.priority_score} /><StatusBadge status={i.status} /></div>
          </Link>
        ))}
      </div>
    </div>
  )
}
