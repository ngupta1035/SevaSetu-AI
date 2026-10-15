import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import ProtectedRoute from './components/ProtectedRoute'
import Home from './pages/Home'
import Login from './pages/Login'
import Register from './pages/Register'
import ReportIssue from './pages/ReportIssue'
import MyReports from './pages/MyReports'
import IssueDetails from './pages/IssueDetails'
import AuthorityDashboard from './pages/AuthorityDashboard'
import AuthorityMap from './pages/AuthorityMap'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Navbar />
        <main className="container wide">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/report" element={<ProtectedRoute citizenOnly><ReportIssue /></ProtectedRoute>} />
            <Route path="/my-reports" element={<ProtectedRoute citizenOnly><MyReports /></ProtectedRoute>} />
            <Route path="/issues/:id" element={<ProtectedRoute><IssueDetails /></ProtectedRoute>} />
            <Route path="/authority" element={<ProtectedRoute authorityOnly><AuthorityDashboard /></ProtectedRoute>} />
            <Route path="/authority/map" element={<ProtectedRoute authorityOnly><AuthorityMap /></ProtectedRoute>} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
        <footer className="footer">SevaSetu AI · working prototype · demo records are synthetic · AI confidence values are model confidence, not accuracy</footer>
      </BrowserRouter>
    </AuthProvider>
  )
}
