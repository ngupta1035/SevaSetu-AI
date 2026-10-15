const STATUS_LABEL = {
  REPORTED: 'Reported', ASSIGNED: 'Assigned', IN_PROGRESS: 'In Progress',
  RESOLVED: 'Resolved', VERIFIED: 'Verified',
}
const TYPE_LABEL = {
  POTHOLE: 'Pothole / Road damage', GARBAGE: 'Garbage / Waste',
  WATER_LEAKAGE: 'Water leakage', STREETLIGHT: 'Damaged streetlight',
}

export const typeLabel = (t) => TYPE_LABEL[t] || t

export function StatusBadge({ status }) {
  return <span className={`badge status-${status}`}>{STATUS_LABEL[status] || status}</span>
}

export function PriorityBadge({ score }) {
  if (score == null || score === 0) return <span className="badge badge-muted">Not scored yet</span>
  const level = score >= 70 ? 'HIGH' : score >= 40 ? 'MEDIUM' : 'LOW'
  return <span className={`badge prio-${level}`}>{level} · {Math.round(score)}</span>
}
