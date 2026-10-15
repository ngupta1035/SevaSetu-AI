import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { authApi, errorMessage } from '../services/api'

export default function Register() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ name: '', email: '', phone: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value })

  const submit = async () => {
    setError('')
    if (!form.name || !form.email || form.password.length < 6)
      return setError('Name, email and a password of at least 6 characters are required')
    setBusy(true)
    try {
      await authApi.register({ ...form, phone: form.phone || null })
      await login(form.email, form.password)
      navigate('/report')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card narrow">
      <h2>Create account</h2>
      {error && <div className="alert">{error}</div>}
      <label>Full name</label>
      <input value={form.name} onChange={set('name')} />
      <label>Email</label>
      <input type="email" value={form.email} onChange={set('email')} />
      <label>Phone (optional)</label>
      <input value={form.phone} onChange={set('phone')} />
      <label>Password</label>
      <input type="password" value={form.password} onChange={set('password')} />
      <button className="btn btn-primary btn-block" onClick={submit} disabled={busy}>{busy ? 'Creating…' : 'Register'}</button>
      <p className="muted">Already registered? <Link to="/login">Login</Link></p>
    </div>
  )
}
