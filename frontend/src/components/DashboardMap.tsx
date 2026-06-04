import React, { useState, useEffect } from 'react';
import { Camera as CameraIcon, Shield, AlertTriangle, Radio, Navigation, Wind } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle, Polygon } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet default icon asset resolution bugs
if (typeof window !== 'undefined') {
  delete (L.Icon.Default.prototype as any)._getIconUrl;
  L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
  });
}

interface MapMarker {
  id: string | number;
  name: string;
  lat: number;
  lng: number;
  type: 'camera' | 'sensor' | 'drone' | 'violation';
  status?: string;
  details?: string;
}

interface DashboardMapProps {
  markers: MapMarker[];
  center?: [number, number];
  zoom?: number;
}

// Route coordinates
const kedarnathRouteCoords: [number, number][] = [
  [29.9450, 78.1630], // Haridwar
  [30.0869, 78.2676], // Rishikesh
  [30.1460, 78.5990], // Devprayag
  [30.2840, 78.9810], // Rudraprayag
  [30.6300, 79.0200], // Sonprayag
  [30.6500, 79.0050], // Gaurikund Base
  [30.6750, 79.0120], // Jungle Chatti
  [30.7000, 79.0300], // Rambara Transit
  [30.7352, 79.0669], // Kedarnath Shrine
];

const badrinathRouteCoords: [number, number][] = [
  [30.2840, 78.9810], // Rudraprayag
  [30.2600, 79.2200], // Karnaprayag
  [30.4300, 79.4300], // Pipalkoti
  [30.5500, 79.5660], // Joshimath
  [30.6200, 79.5600], // Govindghat
  [30.7433, 79.4938], // Badrinath Shrine
];

const gangotriRouteCoords: [number, number][] = [
  [30.0869, 78.2676], // Rishikesh
  [30.3500, 78.3900], // Chamba
  [30.7268, 78.4354], // Uttarkashi
  [31.0360, 78.7360], // Harsil
  [30.9947, 78.9398], // Gangotri Shrine
];

const yamunotriRouteCoords: [number, number][] = [
  [30.0869, 78.2676], // Rishikesh
  [30.6200, 78.3200], // Dharasu
  [30.8100, 77.9800], // Barkot
  [30.9800, 78.4100], // Janki Chatti
  [31.0100, 78.4500], // Yamunotri Shrine
];

// Geofence polygon coordinates around Gaurikund Base Camp
const geofencePolygonCoords: [number, number][] = [
  [30.6400, 78.9950],
  [30.6400, 79.0150],
  [30.6600, 79.0150],
  [30.6600, 78.9950],
  [30.6400, 78.9950]
];

// Custom Leaflet DivIcon creation
const createCustomIcon = (type: string, id: string | number, status?: string) => {
  let color = '#00f0ff';
  let emoji = '📷';
  let pulse = '';

  if (type === 'violation') {
    color = '#ef4444';
    emoji = '⚠️';
    pulse = 'pulse-red';
  } else if (type === 'sensor') {
    color = '#10b981';
    emoji = '⚡';
  } else if (type === 'drone') {
    color = '#8b5cf6';
    emoji = '🛸';
    pulse = 'pulse-purple';
  }

  return L.divIcon({
    className: 'custom-map-icon',
    html: `
      <div class="map-marker-pin ${pulse}" style="
        background: rgba(10, 13, 22, 0.9);
        border: 2px solid ${color};
        color: #fff;
        padding: 3px 6px;
        border-radius: 4px;
        font-family: 'monospace';
        font-size: 9px;
        font-weight: bold;
        box-shadow: 0 0 8px ${color};
        display: flex;
        align-items: center;
        gap: 3px;
        white-space: nowrap;
        pointer-events: auto;
      ">
        <span>${emoji}</span>
        <span>${id}</span>
      </div>
    `,
    iconSize: [60, 20],
    iconAnchor: [30, 10]
  });
};

export default function DashboardMap({ markers, center = [30.4890, 78.8500], zoom = 9 }: DashboardMapProps) {
  const [activeOverlay, setActiveOverlay] = useState<'standard' | 'heatmap' | 'satellite'>('standard');
  const [selectedNode, setSelectedNode] = useState<MapMarker | null>(null);
  
  // Dynamic Map Layers mapping
  const getTileUrl = () => {
    if (activeOverlay === 'satellite') {
      return 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}';
    }
    // CartoDB Dark Matter tile server for dark theme aesthetics
    return 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png';
  };

  return (
    <div className="glass-panel" style={{ height: '100%', position: 'relative', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
      {/* Map Header Controls */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid rgba(255,255,255,0.05)',
        background: 'rgba(10,13,22,0.8)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        zIndex: 400
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={14} className="pulse-red" style={{ color: '#00f0ff' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.02em' }}>
            GEOSPATIAL COMMAND OVERLAY: <span style={{ color: '#00f0ff' }}>CHAR DHAM SECTORS</span>
          </span>
        </div>
        
        {/* Layer Toggles */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button 
            onClick={() => setActiveOverlay('standard')}
            className={`action-btn ${activeOverlay === 'standard' ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.7rem' }}
          >
            🗺️ GIS Terrain
          </button>
          <button 
            onClick={() => setActiveOverlay('heatmap')}
            className={`action-btn ${activeOverlay === 'heatmap' ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.7rem' }}
          >
            🔥 Pollution Heatmap
          </button>
          <button 
            onClick={() => setActiveOverlay('satellite')}
            className={`action-btn ${activeOverlay === 'satellite' ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.7rem' }}
          >
            🛰️ Satellite Radar
          </button>
        </div>
      </div>

      {/* Main Map Visual Panel */}
      <div style={{ flex: 1, position: 'relative', background: '#04070d', minHeight: '340px', zIndex: 1 }}>
        <MapContainer 
          center={center} 
          zoom={zoom} 
          style={{ width: '100%', height: '100%', background: '#04070d' }}
          zoomControl={true}
        >
          <TileLayer
            attribution='&copy; OpenStreetMap contributors &copy; CARTO'
            url={getTileUrl()}
          />

          {/* 1. Char Dham Road Corridors (Dynamic Polylines) */}
          <Polyline 
            positions={kedarnathRouteCoords} 
            pathOptions={{ 
              color: activeOverlay === 'heatmap' ? '#ef4444' : '#00f0ff', 
              weight: activeOverlay === 'heatmap' ? 6 : 4,
              opacity: 0.85
            }} 
          >
            <Popup>
              <div style={{color:'#000'}}>
                <strong>Kedarnath Route Corridor</strong><br/>
                Status: Congested near Gaurikund Base<br/>
                Vehicle Flow: Heavy
              </div>
            </Popup>
          </Polyline>

          <Polyline 
            positions={badrinathRouteCoords} 
            pathOptions={{ color: '#10b981', weight: 4, opacity: 0.8 }} 
          >
            <Popup>
              <div style={{color:'#000'}}>
                <strong>Badrinath Entrance Corridor</strong><br/>
                Status: Optimal Flow
              </div>
            </Popup>
          </Polyline>

          <Polyline 
            positions={gangotriRouteCoords} 
            pathOptions={{ color: '#8b5cf6', weight: 4, opacity: 0.8 }} 
          >
            <Popup>
              <div style={{color:'#000'}}>
                <strong>Gangotri Trail</strong><br/>
                Status: Clear
              </div>
            </Popup>
          </Polyline>

          <Polyline 
            positions={yamunotriRouteCoords} 
            pathOptions={{ color: '#f59e0b', weight: 4, opacity: 0.8 }} 
          >
            <Popup>
              <div style={{color:'#000'}}>
                <strong>Yamunotri Trail</strong><br/>
                Status: Clear
              </div>
            </Popup>
          </Polyline>

          {/* 2. Geofence Boundary Polygon (Gaurikund Zone A) */}
          <Polygon 
            positions={geofencePolygonCoords} 
            pathOptions={{ 
              color: '#00f0ff', 
              fillColor: '#00f0ff', 
              fillOpacity: 0.05, 
              dashArray: '5, 5' 
            }} 
          >
            <Popup>
              <div style={{color:'#000'}}>
                <strong>GEOFENCE: ZONE-A-NO-PARK</strong><br/>
                Automatic ANPR Tow Zone
              </div>
            </Popup>
          </Polygon>

          {/* 3. Pollution Hotspot Overlays */}
          {activeOverlay === 'heatmap' && (
            <>
              {/* High pollution zone - Gaurikund */}
              <Circle 
                center={[30.6500, 79.0050]} 
                radius={2500} 
                pathOptions={{ 
                  color: '#ef4444', 
                  fillColor: '#ef4444', 
                  fillOpacity: 0.35, 
                  weight: 1 
                }} 
              />
              {/* Moderate pollution zone - Joshimath */}
              <Circle 
                center={[30.5500, 79.5660]} 
                radius={2000} 
                pathOptions={{ 
                  color: '#f59e0b', 
                  fillColor: '#f59e0b', 
                  fillOpacity: 0.25, 
                  weight: 1 
                }} 
              />
              {/* Light pollution zone - Uttarkashi */}
              <Circle 
                center={[30.7268, 78.4354]} 
                radius={3000} 
                pathOptions={{ 
                  color: '#eab308', 
                  fillColor: '#eab308', 
                  fillOpacity: 0.15, 
                  weight: 1 
                }} 
              />
            </>
          )}

          {/* 4. Telemetry and Violations Markers */}
          {markers.map((m) => {
            if (!m.lat || !m.lng) return null;

            return (
              <Marker 
                key={m.id} 
                position={[m.lat, m.lng]} 
                icon={createCustomIcon(m.type, m.id, m.status)}
                eventHandlers={{
                  click: () => setSelectedNode(m)
                }}
              >
                <Popup>
                  <div style={{ color: '#000', fontFamily: 'Inter', fontSize: '11px' }}>
                    <strong style={{ textTransform: 'uppercase', color: m.type === 'violation' ? '#ef4444' : '#00f0ff' }}>
                      {m.type} Node Info
                    </strong>
                    <h4 style={{ margin: '4px 0 2px 0', fontSize: '12px' }}>{m.name}</h4>
                    <p style={{ margin: 0, color: '#374151' }}>{m.details}</p>
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>

        {/* Floating Selected Node Info Card */}
        {selectedNode && (
          <div className="glass-panel border-cyan" style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            width: '280px',
            padding: '12px',
            background: 'rgba(5,7,12,0.95)',
            zIndex: 400,
            display: 'flex',
            flexDirection: 'column',
            gap: '6px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#00f0ff', textTransform: 'uppercase' }}>
                {selectedNode.type} Node Details
              </span>
              <button 
                onClick={() => setSelectedNode(null)} 
                style={{ background: 'none', border: 'none', color: '#9ca3af', cursor: 'pointer', fontSize: '0.8rem' }}
              >
                ✕
              </button>
            </div>
            
            <h4 style={{ fontSize: '0.85rem', fontWeight: 600, color: '#fff' }}>{selectedNode.name}</h4>
            <div style={{ fontSize: '0.7rem', color: '#9ca3af', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <div>Latitude: <span style={{ color: '#fff' }}>{selectedNode.lat.toFixed(5)}</span></div>
              <div>Longitude: <span style={{ color: '#fff' }}>{selectedNode.lng.toFixed(5)}</span></div>
              {selectedNode.status && (
                <div>Status Index: <span style={{ color: selectedNode.status === 'Optimal' || selectedNode.status === 'APPROVED' ? '#10b981' : '#f59e0b', fontWeight: 'bold' }}>{selectedNode.status}</span></div>
              )}
              {selectedNode.details && (
                <div style={{ marginTop: '4px', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '4px', color: '#e5e7eb' }}>
                  {selectedNode.details}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Map Legend Footer */}
      <div style={{
        padding: '8px 16px',
        background: 'rgba(10,13,22,0.9)',
        borderTop: '1px solid rgba(255,255,255,0.05)',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '16px',
        fontSize: '0.7rem',
        color: '#9ca3af',
        zIndex: 400
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#00f0ff' }}>📷</span> CCTV Stations
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#10b981' }}>⚡</span> IoT Sensors
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#8b5cf6' }}>🛸</span> UAV Patrols
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <span style={{ color: '#ef4444' }}>⚠️</span> Active Violations
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wind size={10} style={{ color: '#f59e0b' }} />
          <span>Char Dham GIS Operations Center (Leaflet Integrated)</span>
        </div>
      </div>
    </div>
  );
}
