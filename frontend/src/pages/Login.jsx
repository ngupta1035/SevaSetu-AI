import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { errorMessage } from '../services/api'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const submit = async () => {
    setError('')
    if (!email || !password) return setError('Enter your email and password')
    setBusy(true)
    try {
      const user = await login(email, password)
      navigate(user.role === 'CITIZEN' ? '/report' : '/authority')
    } catch (e) {
      setError(errorMessage(e))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card narrow">
      <h2>Login</h2>
      {error && <div className="alert">{error}</div>}
      <label>Email</label>
      <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submit()} />
      <label>Password</label>
      <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submit()} />
      <button className="btn btn-primary btn-block" onClick={submit} disabled={busy}>{busy ? 'Signing in…' : 'Login'}</button>
      <p className="muted">New here? <Link to="/register">Create an account</Link></p>
      <div className="demo-box">
        <div className="hint">Demo accounts (prototype)</div>
        <button type="button" className="btn btn-outline" onClick={() => { setEmail('citizen@demo.sevasetu'); setPassword('demo1234') }}>Use citizen demo</button>
        <button type="button" className="btn btn-outline" onClick={() => { setEmail('authority@demo.sevasetu'); setPassword('demo1234') }}>Use authority demo</button>
      </div>
    </div>
  )
}
