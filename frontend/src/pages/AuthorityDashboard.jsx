import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { adminApi, errorMessage } from '../services/api'
import { StatusBadge, PriorityBadge, typeLabel } from '../components/Badges'
import { CategoryChart, StatusChart, DepartmentChart, TrendChart } from '../components/Charts'

const STATUSES = ['REPORTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED']
const TYPES = ['POTHOLE', 'GARBAGE', 'WATER_LEAKAGE', 'STREETLIGHT']

function Kpi({ label, value, tone }) {
  return (
    <div className={`kpi ${tone || ''}`}>
      <div className="kpi-value">{value ?? '—'}</div>
      <div className="kpi-label">{label}</div>
    </div>
  )
}

export default function AuthorityDashboard() {
  const [stats, setStats] = useState(null)
  const [rows, setRows] = useState(null)
  const [trend, setTrend] = useState(null)
  const [hotspots, setHotspots] = useState([])
  const [error, setError] = useState('')
  const [filters, setFilters] = useState({ status: '', issue_type: '', search: '', open_only: false, sort: 'priority' })

  const load = useCallback(() => {
    const params = Object.fromEntries(Object.entries(filters).filter(([, v]) => v !== '' && v !== false))
    Promise.all([adminApi.dashboard(), adminApi.issues(params), adminApi.analytics(14), adminApi.map({ open_only: true })])
      .then(([s, r, a, m]) => { setStats(s); setRows(r); setTrend(a.trend); setHotspots(m.hotspots); setError('') })
      .catch((e) => setError(errorMessage(e)))
  }, [filters])

  useEffect(() => { load() }, [load])
  const set = (k) => (e) => setFilters({ ...filters, [k]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  if (error) return <div className="alert">{error}</div>
  if (!stats || !rows) return <p className="muted">Loading dashboard…</p>

  return (
    <div>
      <h2>Authority Dashboard</h2>
      <div className="kpis">
        <Kpi label="Total issues" value={stats.total} />
        <Kpi label="Open" value={stats.open} />
        <Kpi label="High priority" value={stats.high_priority} tone="danger" />
        <Kpi label="Pending (new)" value={stats.pending} tone="warn" />
        <Kpi label="Resolved" value={stats.resolved} tone="ok" />
        <Kpi label="Avg resolution (h)" value={stats.avg_resolution_hours} />
      </div>
      {rows.some((r) => (r.description || '').includes('[synthetic demo]')) && (
        <div className="notice info">ℹ️ Demo environment: most records shown here are <b>synthetic</b> and were generated for demonstration.</div>
      )}
      {stats.pending_duplicates > 0 && (
        <div className="notice">⚠️ {stats.pending_duplicates} possible duplicate(s) awaiting review — look for the “dup” tag in the table.</div>
      )}

      <div className="charts">
        <div className="card chart-card"><h4>Issues by category</h4><CategoryChart data={stats.by_category} /></div>
        <div className="card chart-card"><h4>Issues by status</h4><StatusChart data={stats.by_status} /></div>
        <div className="card chart-card"><h4>Department workload</h4><DepartmentChart data={stats.by_department} /></div>
        <div className="card chart-card"><h4>Last 14 days</h4>{trend && <TrendChart data={trend} />}</div>
      </div>

      <div className="card chart-card">
        <div className="row-between">
          <h4>Civic hotspots</h4>
          <Link to="/authority/map" className="btn btn-outline">Open map →</Link>
        </div>
        {hotspots.length === 0 && <p className="muted small">No hotspots yet — a hotspot is 3+ open issues within about 250 m of each other.</p>}
        {hotspots.slice(0, 3).map((h) => (
          <div key={h.rank} className="hotspot-row">
            <b>#{h.rank} {h.label}</b>
            <span className="muted small"> — {h.issue_count} issues · {h.report_count} reports · avg priority {h.avg_priority} · mostly {typeLabel(h.dominant_type)}</span>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="filters">
          <input placeholder="Search code, address, description…" value={filters.search} onChange={set('search')} />
          <select value={filters.status} onChange={set('status')}>
            <option value="">All statuses</option>
            {STATUSES.map((s) => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
          </select>
          <select value={filters.issue_type} onChange={set('issue_type')}>
            <option value="">All categories</option>
            {TYPES.map((t) => <option key={t} value={t}>{typeLabel(t)}</option>)}
          </select>
          <select value={filters.sort} onChange={set('sort')}>
            <option value="priority">Sort: priority</option>
            <option value="newest">Sort: newest</option>
            <option value="oldest">Sort: oldest</option>
          </select>
          <label className="inline"><input type="checkbox" checked={filters.open_only} onChange={set('open_only')} /> Open only</label>
        </div>

        <div className="table-wrap">
          <table className="table">
            <thead><tr><th>Code</th><th>Category</th><th>Priority</th><th>Department</th><th>Reports</th><th>Status</th><th>Reported</th></tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td><Link to={`/issues/${r.id}`}><b>{r.issue_code}</b></Link>{r.pending_duplicates > 0 && <span className="tag">dup</span>}</td>
                  <td>{typeLabel(r.issue_type)}<div className="muted small">{r.address || ''}</div></td>
                  <td><PriorityBadge score={r.priority_score} /></td>
                  <td>{r.department_name || '—'}</td>
                  <td>{r.report_count}</td>
                  <td><StatusBadge status={r.status} /></td>
                  <td className="small">{new Date(r.created_at).toLocaleDateString()}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={7} className="muted">No issues match these filters.</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
