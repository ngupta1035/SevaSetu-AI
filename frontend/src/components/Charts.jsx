import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid,
  PieChart, Pie, Cell, Legend, LineChart, Line,
} from 'recharts'

const TYPE_SHORT = { POTHOLE: 'Pothole', GARBAGE: 'Garbage', WATER_LEAKAGE: 'Water', STREETLIGHT: 'Streetlight' }
const STATUS_COLORS = { REPORTED: '#4c8dff', ASSIGNED: '#9b6bff', IN_PROGRESS: '#f5a524', RESOLVED: '#37b26c', VERIFIED: '#1f8f4e' }
const PRIMARY = '#3b5bdb'

const toRows = (obj, labelFn = (k) => k) => Object.entries(obj).map(([k, v]) => ({ key: k, name: labelFn(k), value: v }))

export function CategoryChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={toRows(data, (k) => TYPE_SHORT[k] || k)}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" fontSize={12} />
        <YAxis allowDecimals={false} fontSize={12} width={28} />
        <Tooltip />
        <Bar dataKey="value" name="Issues" fill={PRIMARY} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function StatusChart({ data }) {
  const rows = toRows(data, (k) => k.replace('_', ' ')).filter((r) => r.value > 0)
  if (rows.length === 0) return <p className="muted">No data yet.</p>
  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie data={rows} dataKey="value" nameKey="name" innerRadius={45} outerRadius={78} paddingAngle={2}>
          {rows.map((r) => <Cell key={r.key} fill={STATUS_COLORS[r.key]} />)}
        </Pie>
        <Tooltip />
        <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
      </PieChart>
    </ResponsiveContainer>
  )
}

export function DepartmentChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={toRows(data)} layout="vertical">
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" allowDecimals={false} fontSize={12} />
        <YAxis type="category" dataKey="name" fontSize={12} width={78} />
        <Tooltip />
        <Bar dataKey="value" name="Issues" fill="#7048e8" radius={[0, 4, 4, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

export function TrendChart({ data }) {
  const rows = data.map((d) => ({ ...d, day: d.date.slice(5) }))
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={rows}>
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="day" fontSize={11} />
        <YAxis allowDecimals={false} fontSize={12} width={28} />
        <Tooltip />
        <Legend iconSize={10} wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="reported" name="Reported" stroke={PRIMARY} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="resolved" name="Resolved" stroke="#37b26c" strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  )
}
