import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { useEffect } from 'react'

// Leaflet's default marker icons break under bundlers; point them at the CDN.
const icon = L.icon({
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
  iconSize: [25, 41], iconAnchor: [12, 41],
})

function ClickHandler({ onPick }) {
  useMapEvents({ click: (e) => onPick(e.latlng.lat, e.latlng.lng) })
  return null
}

function Recenter({ position }) {
  const map = useMap()
  useEffect(() => { if (position) map.setView(position, Math.max(map.getZoom(), 16)) }, [position, map])
  return null
}

// Default centre: Hinjewadi, Pune (demo area)
const DEFAULT_CENTER = [18.5912, 73.7389]

export default function LocationPicker({ lat, lng, onPick }) {
  const position = lat != null && lng != null ? [lat, lng] : null
  return (
    <MapContainer center={position || DEFAULT_CENTER} zoom={position ? 16 : 13} className="map-picker">
      <TileLayer attribution="&copy; OpenStreetMap contributors"
                 url="https://tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <ClickHandler onPick={onPick} />
      <Recenter position={position} />
      {position && <Marker position={position} icon={icon} />}
    </MapContainer>
  )
}
