import { useEffect, useState } from 'react'
import { Link, useLocation, useParams } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import AuthorityActions from '../components/AuthorityActions'
import { issuesApi, errorMessage } from '../services/api'
import { StatusBadge, PriorityBadge, typeLabel } from '../components/Badges'

const FACTORS = [
  ['severity', 'Severity', 30], ['frequency', 'Report frequency', 20], ['location', 'Location criticality', 20],
  ['traffic', 'Traffic / footfall (proxy)', 15], ['time', 'Time unresolved', 15],
]
const STEPS = ['REPORTED', 'ASSIGNED', 'IN_PROGRESS', 'RESOLVED', 'VERIFIED']

export default function IssueDetails() {
  const { id } = useParams()
  const { user } = useAuth()
  const location = useLocation()
  const [issue, setIssue] = useState(null)
  const [error, setError] = useState('')
  const isAuthority = user && user.role !== 'CITIZEN'

  const load = () => issuesApi.get(id).then(setIssue).catch((e) => setError(errorMessage(e)))
  useEffect(() => { load() }, [id])

  if (error) return <div className="alert">{error}</div>
  if (!issue) return <p className="muted">Loading…</p>
  const current = STEPS.indexOf(issue.status)

  return (
    <div className="card">
      <Link to={isAuthority ? '/authority' : '/my-reports'} className="muted">← Back</Link>
      {location.state?.merged && (
        <div className="notice">✅ A report for this problem already existed nearby, so yours was added to it
          ({issue.report_count} reports now) — more reports raise its priority.</div>
      )}
      <div className="row-between">
        <h2>{issue.issue_code}</h2>
        <div className="badges"><PriorityBadge score={issue.priority_score} /><StatusBadge status={issue.status} /></div>
      </div>

      <div className="stepper">
        {STEPS.map((s, i) => (
          <div key={s} className={`step ${i <= current ? 'done' : ''}`}><span>{i + 1}</span>{s.replace('_', ' ')}</div>
        ))}
      </div>

      {isAuthority && <AuthorityActions issue={issue} onChange={load} />}

      <dl className="facts">
        <dt>Issue type</dt><dd>{typeLabel(issue.issue_type)}</dd>
        <dt>Department</dt><dd>{issue.department_name || '—'}</dd>
        <dt>Location</dt><dd>{issue.address || '—'} ({issue.latitude.toFixed(5)}, {issue.longitude.toFixed(5)})</dd>
        <dt>Description</dt><dd>{issue.description || '—'}</dd>
        <dt>Reports merged</dt><dd>{issue.report_count}</dd>
        {issue.model_confidence != null && (<><dt>Model confidence</dt><dd>{Math.round(issue.model_confidence * 100)}%</dd></>)}
      </dl>

      {issue.resolution && (issue.resolution.after_image_url || issue.resolution.resolution_notes) ? (
        <>
          <h3>Before / after</h3>
          <div className="before-after">
            <figure><img src={issue.resolution.before_image_url} alt="before" /><figcaption>Before</figcaption></figure>
            {issue.resolution.after_image_url
              ? <figure><img src={issue.resolution.after_image_url} alt="after" /><figcaption>After</figcaption></figure>
              : <figure className="no-photo"><div>No after-photo uploaded</div><figcaption>After</figcaption></figure>}
          </div>
          <p className="muted small">
            Resolution {issue.resolution.verification_status.toLowerCase()}
            {issue.resolution.resolution_notes ? ` — ${issue.resolution.resolution_notes}` : ''}
          </p>
        </>
      ) : null}

      {issue.reports.length > 0 && <h3>Citizen photo{issue.reports.length > 1 ? 's' : ''}</h3>}
      <div className="photo-grid">
        {issue.reports.map((r) => r.image_url && <img key={r.id} src={r.image_url} alt="reported issue" />)}
      </div>

      {issue.predictions.length > 0 && (
        <>
          <h3>AI analysis</h3>
          <p className="muted small">
            {issue.predictions[0].model_name} · detected class <b>{issue.predictions[0].predicted_class}</b> ·
            model confidence {Math.round(issue.predictions[0].confidence * 100)}% ·
            {' '}{issue.predictions[0].inference_time_ms} ms
          </p>
        </>
      )}

      {issue.priority_breakdown && (
        <>
          <h3>Priority score: {Math.round(issue.priority_breakdown.score)} / 100 ({issue.priority_breakdown.level})</h3>
          {FACTORS.map(([key, label, w]) => (
            <div key={key} className="bar-row">
              <span>{label} <small>({w}%)</small></span>
              <div className="bar"><div style={{ width: `${issue.priority_breakdown.components[key]}%` }} /></div>
              <b>{Math.round(issue.priority_breakdown.components[key])}</b>
            </div>
          ))}
          <p className="hint">{issue.priority_breakdown.note} Severity source: {issue.priority_breakdown.severity_source}.</p>
        </>
      )}

      <h3>Timeline</h3>
      <ul className="timeline">
        {issue.events.map((e, idx) => (
          <li key={idx}>
            <b>{e.new_status.replace('_', ' ')}</b> — {new Date(e.created_at).toLocaleString()}
            {e.comment && <div className="muted small">{e.comment}</div>}
          </li>
        ))}
      </ul>
    </div>
  )
}
