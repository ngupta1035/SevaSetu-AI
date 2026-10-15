import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { issuesApi, aiApi, errorMessage } from '../services/api'
import { typeLabel } from '../components/Badges'
import LocationPicker from '../components/LocationPicker'

const TYPES = [
  ['POTHOLE', 'Pothole / Road damage'],
  ['GARBAGE', 'Garbage / Waste accumulation'],
  ['WATER_LEAKAGE', 'Water leakage'],
  ['STREETLIGHT', 'Damaged streetlight'],
]

export default function ReportIssue() {
  const navigate = useNavigate()
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [description, setDescription] = useState('')
  const [address, setAddress] = useState('')
  const [issueType, setIssueType] = useState('')
  const [coords, setCoords] = useState({ lat: null, lng: null })
  const [locMsg, setLocMsg] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [ai, setAi] = useState(null)        // { loading } | { detected, result } | null

  useEffect(() => {
    if (!file) { setPreview(null); setAi(null); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    setAi({ loading: true })
    aiApi.analyze(file).then(setAi).catch(() => setAi(null))
    return () => URL.revokeObjectURL(url)
  }, [file])

  const useCurrentLocation = () => {
    if (!navigator.geolocation) return setLocMsg('Geolocation is not supported by this browser — click on the map instead.')
    setLocMsg('Getting your location…')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setCoords({ lat: pos.coords.latitude, lng: pos.coords.longitude })
        setLocMsg(`Location captured (±${Math.round(pos.coords.accuracy)} m). You can fine-tune it on the map.`)
      },
      () => setLocMsg('Could not get your location — click the issue position on the map instead.'),
      { enableHighAccuracy: true, timeout: 10000 },
    )
  }

  const submit = async () => {
    setError('')
    if (!file) return setError('Please upload a photo of the issue')
    if (coords.lat == null) return setError('Please set the location (use current location or click the map)')
    if (!issueType && !(ai?.detected && ai.result.issue_type))
      return setError('The AI could not identify the issue — please select the issue type')
    const fd = new FormData()
    fd.append('image', file)
    fd.append('latitude', coords.lat)
    fd.append('longitude', coords.lng)
    if (issueType) fd.append('issue_type', issueType)
    if (description) fd.append('description', description)
    if (address) fd.append('address', address)
    setBusy(true)
    try {
      const issue = await issuesApi.create(fd)
      navigate(`/issues/${issue.id}`, { state: { merged: issue.merged } })
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <h2>Report a Civic Issue</h2>
      {error && <div className="alert">{error}</div>}

      <label>Issue photo</label>
      <input type="file" accept="image/jpeg,image/png,image/webp" onChange={(e) => setFile(e.target.files?.[0] || null)} />
      {preview && <img src={preview} alt="preview" className="preview" />}
      {ai?.loading && <p className="hint">🤖 Analysing photo…</p>}
      {ai && !ai.loading && ai.model_loaded === false && (
        <p className="hint">AI model not loaded on the server — please select the issue type.</p>
      )}
      {ai && !ai.loading && ai.model_loaded && !ai.detected && (
        <p className="hint">The AI found nothing it could classify — please select the issue type.</p>
      )}
      {ai?.detected && (
        <div className="ai-chip">
          🤖 AI detected <b>{typeLabel(ai.result.issue_type) || ai.result.predicted_class}</b>
          {' '}· model confidence {Math.round(ai.result.confidence * 100)}%
          {' '}· severity <b>{ai.result.severity}</b>
        </div>
      )}

      <label>Issue type</label>
      <select value={issueType} onChange={(e) => setIssueType(e.target.value)}>
        <option value="">🤖 AI detect automatically</option>
        {TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
      </select>

      <label>Description</label>
      <textarea rows={3} maxLength={1000} value={description} onChange={(e) => setDescription(e.target.value)} placeholder="e.g. Large pothole near the junction" />

      <label>Location</label>
      <button type="button" className="btn btn-outline" onClick={useCurrentLocation}>📍 Use Current Location</button>
      {locMsg && <p className="hint">{locMsg}</p>}
      <LocationPicker lat={coords.lat} lng={coords.lng} onPick={(lat, lng) => setCoords({ lat, lng })} />
      <p className="hint">
        {coords.lat != null ? `Selected: ${coords.lat.toFixed(5)}, ${coords.lng.toFixed(5)}` : 'Click the map to drop a pin.'}
      </p>

      <label>Landmark / address (optional)</label>
      <input value={address} onChange={(e) => setAddress(e.target.value)} placeholder="e.g. Hinjewadi Phase 1" />

      <button className="btn btn-primary btn-block" onClick={submit} disabled={busy}>{busy ? 'Submitting…' : 'Submit Report'}</button>
    </div>
  )
}
