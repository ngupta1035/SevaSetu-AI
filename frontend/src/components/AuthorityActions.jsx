import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { adminApi, errorMessage } from '../services/api'

export default function AuthorityActions({ issue, onChange }) {
  const navigate = useNavigate()
  const [departments, setDepartments] = useState([])
  const [dept, setDept] = useState(issue.department_id || '')
  const [notes, setNotes] = useState('')
  const [comment, setComment] = useState('')
  const [afterFile, setAfterFile] = useState(null)
  const [msg, setMsg] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => { adminApi.departments().then(setDepartments).catch(() => {}) }, [])
  useEffect(() => { setDept(issue.department_id || '') }, [issue.department_id])

  const run = async (fn) => {
    setBusy(true); setMsg('')
    try { await fn(); setNotes(''); setComment(''); setAfterFile(null); await onChange() }
    catch (e) { setMsg(errorMessage(e)) }
    finally { setBusy(false) }
  }
  const s = issue.status

  return (
    <div className="actions card-inner">
      <h3>Authority actions</h3>
      {msg && <div className="alert">{msg}</div>}

      {(s === 'REPORTED' || s === 'ASSIGNED') && (
        <>
          <label>Department</label>
          <select value={dept} onChange={(e) => setDept(e.target.value)}>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <label>Assignee / work-order note</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="e.g. Ward officer, work order #123" />
          <button className="btn btn-primary" disabled={busy}
                  onClick={() => run(() => adminApi.assign(issue.id, { department_id: dept ? Number(dept) : null, notes: notes || null }))}>
            {s === 'REPORTED' ? 'Assign' : 'Re-assign'}
          </button>
        </>
      )}

      {s === 'ASSIGNED' && (
        <button className="btn btn-outline" disabled={busy}
                onClick={() => run(() => adminApi.setStatus(issue.id, { status: 'IN_PROGRESS', comment: comment || null }))}>
          Start work
        </button>
      )}

      {s === 'IN_PROGRESS' && (
        <>
          <label>Resolution notes</label>
          <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="What was done?" />
          <label>After-photo (optional)</label>
          <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setAfterFile(e.target.files?.[0] || null)} />
          <button className="btn btn-primary" disabled={busy}
                  onClick={() => run(() => adminApi.resolve(issue.id, { notes, file: afterFile }))}>
            Mark resolved
          </button>
        </>
      )}

      {s === 'RESOLVED' && (
        <>
          <p className="muted small">Compare the before / after photos below, then confirm the fix on your side.</p>
          <label>Verification comment</label>
          <input value={comment} onChange={(e) => setComment(e.target.value)} />
          <div className="btn-row">
            <button className="btn btn-primary" disabled={busy} onClick={() => run(() => adminApi.verify(issue.id, true, comment))}>Verify resolution</button>
            <button className="btn btn-outline" disabled={busy} onClick={() => run(() => adminApi.verify(issue.id, false, comment))}>Reject &amp; reopen</button>
          </div>
        </>
      )}
      {s === 'VERIFIED' && <p className="muted">This issue is resolved and verified.</p>}

      {issue.possible_duplicates?.filter((d) => d.review_status === 'PENDING').map((d) => (
        <div key={d.id} className="notice">
          Possible duplicate of <b>{d.candidate_code}</b> ({Math.round(d.distance_meters)} m away, proximity score {d.combined_score}).
          <div className="btn-row">
            <button className="btn btn-primary" disabled={busy} onClick={async () => {
              setBusy(true); setMsg('')
              try { await adminApi.reviewDuplicate(d.id, 'confirm'); navigate(`/issues/${d.candidate_issue_id}`) }
              catch (e) { setMsg(errorMessage(e)); setBusy(false) }
            }}>Merge into {d.candidate_code}</button>
            <button className="btn btn-outline" disabled={busy} onClick={() => run(() => adminApi.reviewDuplicate(d.id, 'dismiss'))}>Not a duplicate</button>
          </div>
        </div>
      ))}
    </div>
  )
}
