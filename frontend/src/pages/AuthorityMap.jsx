import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { MapContainer, TileLayer, CircleMarker, Circle, Popup, useMap } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { adminApi, errorMessage } from '../services/api'
import { typeLabel } from '../components/Badges'

const TYPES = ['POTHOLE', 'GARBAGE', 'WATER_LEAKAGE', 'STREETLIGHT']
const color = (i) => {
  if (i.status === 'RESOLVED' || i.status === 'VERIFIED') return '#868e96'
  return i.priority >= 70 ? '#e03131' : i.priority >= 40 ? '#f08c00' : '#2f9e44'
}

function FlyTo({ target }) {
  const map = useMap()
  useEffect(() => { if (target) map.flyTo([target.center_lat, target.center_lon], 16, { duration: 0.8 }) }, [target, map])
  return null
}

function FitBounds({ issues }) {
  const map = useMap()
  useEffect(() => {
    if (issues.length) map.fitBounds(issues.map((i) => [i.lat, i.lon]), { padding: [40, 40], maxZoom: 16 })
  }, [issues, map])
  return null
}

export default function AuthorityMap() {
  const [data, setData] = useState(null)
  const [error, setError] = useState('')
  const [type, setType] = useState('')
  const [openOnly, setOpenOnly] = useState(true)
  const [showHotspots, setShowHotspots] = useState(true)
  const [focus, setFocus] = useState(null)

  useEffect(() => {
    const params = { open_only: openOnly }
    if (type) params.issue_type = type
    adminApi.map(params).then((d) => { setData(d); setError('') }).catch((e) => setError(errorMessage(e)))
  }, [type, openOnly])

  if (error) return <div className="alert">{error}</div>
  if (!data) return <p className="muted">Loading map…</p>

  return (
    <div>
      <div className="row-between">
        <h2>Issue Map &amp; Hotspots</h2>
        <Link to="/authority" className="muted">← Dashboard</Link>
      </div>
      <div className="filters">
        <select value={type} onChange={(e) => setType(e.target.value)}>
          <option value="">All categories</option>
          {TYPES.map((t) => <option key={t} value={t}>{typeLabel(t)}</option>)}
        </select>
        <label className="inline"><input type="checkbox" checked={openOnly} onChange={(e) => setOpenOnly(e.target.checked)} /> Open issues only</label>
        <label className="inline"><input type="checkbox" checked={showHotspots} onChange={(e) => setShowHotspots(e.target.checked)} /> Show hotspots</label>
      </div>

      <MapContainer center={[18.5912, 73.7389]} zoom={13} className="map-big">
        <TileLayer attribution="&copy; OpenStreetMap contributors" url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
        <FitBounds issues={data.issues} />
        <FlyTo target={focus} />
        {showHotspots && data.hotspots.map((h) => (
          <Circle key={h.rank} center={[h.center_lat, h.center_lon]} radius={h.radius_m}
                  pathOptions={{ color: '#c92a2a', fillColor: '#ff6b6b', fillOpacity: 0.15, weight: 2, dashArray: '6' }}>
            <Popup>
              <b>Hotspot #{h.rank}: {h.label}</b><br />
              {h.issue_count} open issues · {h.report_count} reports<br />
              Avg priority {h.avg_priority} (max {h.max_priority})<br />
              Mostly {typeLabel(h.dominant_type)}
            </Popup>
          </Circle>
        ))}
        {data.issues.map((i) => (
          <CircleMarker key={i.id} center={[i.lat, i.lon]} radius={6 + Math.min(i.reports, 6)}
                        pathOptions={{ color: '#fff', weight: 1.5, fillColor: color(i), fillOpacity: 0.9 }}>
            <Popup>
              <b>{i.code}</b> — {typeLabel(i.type)}<br />
              Priority {Math.round(i.priority)} · {i.status.replace('_', ' ')}<br />
              {i.reports} report(s){i.address ? ` · ${i.address}` : ''}<br />
              <Link to={`/issues/${i.id}`}>Open issue →</Link>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>

      <div className="legend">
        <span><i style={{ background: '#e03131' }} /> High priority</span>
        <span><i style={{ background: '#f08c00' }} /> Medium</span>
        <span><i style={{ background: '#2f9e44' }} /> Low</span>
        <span><i style={{ background: '#868e96' }} /> Resolved</span>
        <span><i className="ring" /> Hotspot (3+ open issues within ~250 m)</span>
        <span className="muted small">Larger dot = more reports</span>
      </div>

      <h3>Hotspot ranking</h3>
      {data.hotspots.length === 0 && <p className="muted">No hotspots detected for the current filter.</p>}
      {data.hotspots.map((h) => (
        <div key={h.rank} className="card hotspot-card clickable" onClick={() => { setFocus(h); window.scrollTo({ top: 0, behavior: 'smooth' }) }}>
          <b>#{h.rank} {h.label}</b> <span className="small muted">— click to zoom</span>
          <div className="muted small">{h.issue_count} issues · {h.report_count} reports · avg priority {h.avg_priority} · {typeLabel(h.dominant_type)}</div>
        </div>
      ))}
    </div>
  )
}
