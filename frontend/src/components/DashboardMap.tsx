import React, { useState } from 'react';
import { Camera, Shield, AlertTriangle, Radio, Navigation, Wind } from 'lucide-react';

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

export default function DashboardMap({ markers }: DashboardMapProps) {
  const [activeOverlay, setActiveOverlay] = useState<'standard' | 'heatmap' | 'satellite'>('standard');
  const [selectedNode, setSelectedNode] = useState<MapMarker | null>(null);

  // Key stations on the Kedarnath Valley Route
  const routeStations = [
    { name: 'Gaurikund Base Camp', elevation: '1,982m', status: 'Optimal', compliance: 92, x: 120, y: 350 },
    { name: 'Jungle Chatti Stop', elevation: '2,340m', status: 'Congested', compliance: 84, x: 260, y: 280 },
    { name: 'Rambara Transit Hub', elevation: '2,740m', status: 'Optimal', compliance: 89, x: 420, y: 200 },
    { name: 'Kedarnath Shrine', elevation: '3,583m', status: 'Optimal', compliance: 96, x: 580, y: 90 },
  ];

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
        zIndex: 10
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Radio size={14} className="pulse-red" style={{ color: '#00f0ff' }} />
          <span style={{ fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.02em' }}>
            SPATIAL OPERATIONS OVERLAY: <span style={{ color: '#00f0ff' }}>UTTARAKHAND ZONE-A</span>
          </span>
        </div>
        
        {/* Layer Switches */}
        <div style={{ display: 'flex', gap: '6px' }}>
          <button 
            onClick={() => setActiveOverlay('standard')}
            className={`action-btn ${activeOverlay === 'standard' ? 'active' : ''}`}
            style={{ padding: '3px 8px', fontSize: '0.7rem' }}
          >
            🗺️ GIS Route
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
            🛰️ Radar Node
          </button>
        </div>
      </div>

      {/* Main Map Visual Panel */}
      <div style={{
        flex: 1,
        position: 'relative',
        background: '#04070d',
        backgroundImage: 'radial-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px)',
        backgroundSize: '20px 20px',
        overflow: 'hidden',
        minHeight: '340px'
      }}>
        {/* Route Bounding Box details */}
        <div style={{
          position: 'absolute',
          top: '12px',
          left: '12px',
          background: 'rgba(5, 7, 12, 0.85)',
          border: '1px solid rgba(255,255,255,0.06)',
          padding: '8px 12px',
          borderRadius: '6px',
          fontSize: '0.7rem',
          color: '#9ca3af',
          pointerEvents: 'none',
          display: 'flex',
          flexDirection: 'column',
          gap: '4px'
        }}>
          <div>Bounding Box: <span style={{ color: '#fff', fontWeight: 500 }}>30.6400°N / 79.0050°E</span></div>
          <div>Trail Gradient: <span style={{ color: '#10b981', fontWeight: 500 }}>Mandakini Valley Ridge</span></div>
        </div>

        {/* Live Vector SVG Trail Map */}
        <svg 
          width="100%" 
          height="100%" 
          viewBox="0 0 700 400" 
          preserveAspectRatio="xMidYMid slice" 
          style={{ position: 'absolute', top: 0, left: 0 }}
        >
          {/* Defs for gradients & heatmaps */}
          <defs>
            <linearGradient id="routeGrad" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#00f0ff" stopOpacity="0.8" />
              <stop offset="50%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8" />
            </linearGradient>
            
            {/* Heatmap blur circles */}
            <radialGradient id="heatGaurikund" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.5" />
              <stop offset="50%" stopColor="#f59e0b" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </radialGradient>
            
            <radialGradient id="heatJungle" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#f59e0b" stopOpacity="0" />
            </radialGradient>
            
            <radialGradient id="heatViolation" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#ef4444" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#ef4444" stopOpacity="0" />
            </radialGradient>
          </defs>

          {/* 1. Pollution Heatmap Layers */}
          {activeOverlay === 'heatmap' && (
            <>
              {/* Gaurikund local high particulate zone */}
              <circle cx="120" cy="350" r="90" fill="url(#heatGaurikund)" />
              {/* Rambara/Jungle Chatti intermediate zone */}
              <circle cx="280" cy="270" r="70" fill="url(#heatJungle)" />
              {/* Mock active violations glowing heat spots */}
              {markers.filter(m => m.type === 'violation').map((m, idx) => {
                const hash = Number(m.id.toString().split('-')[1]) || idx;
                const cx = 150 + (hash * 131) % 400;
                const cy = 300 - (hash * 89) % 200;
                return (
                  <circle key={idx} cx={cx} cy={cy} r="50" fill="url(#heatViolation)" />
                );
              })}
            </>
          )}

          {/* 2. Geofence Boundary Polygon */}
          <polygon 
            points="80,380 280,330 350,220 180,240" 
            fill="none" 
            stroke="#00f0ff" 
            strokeWidth="1" 
            strokeDasharray="4 4" 
            opacity="0.5" 
          />
          <text x="90" y="270" fill="#00f0ff" fontSize="9" opacity="0.6" fontFamily="Inter">
            GEOCONSTRAINT: ZONE-A-NO-PARK
          </text>

          {/* UAV Flight Path Boundary */}
          <path 
            d="M 120,350 Q 280,180 580,90 Q 300,380 120,350 Z" 
            fill="none" 
            stroke="#8b5cf6" 
            strokeWidth="0.75" 
            strokeDasharray="5 3" 
            opacity="0.4"
          />
          <text x="320" y="160" fill="#8b5cf6" fontSize="9" opacity="0.6" fontFamily="Inter">
            UAV PATROL PATH (ALT: 150m)
          </text>

          {/* 3. Main Route Trail Path */}
          <path 
            d="M 120,350 Q 200,320 260,280 T 420,200 T 580,90" 
            fill="none" 
            stroke="url(#routeGrad)" 
            strokeWidth="4" 
            strokeLinecap="round"
            opacity="0.85"
          />

          {/* Route Station Nodes */}
          {routeStations.map((station, idx) => (
            <g key={idx} style={{ cursor: 'pointer' }} onClick={() => setSelectedNode({
              id: `ST-${idx}`,
              name: station.name,
              lat: 30.65 + idx * 0.02,
              lng: 79.0 + idx * 0.02,
              type: 'sensor',
              status: station.status,
              details: `Elevation: ${station.elevation} | Route Compliance score: ${station.compliance}%`
            })}>
              <circle cx={station.x} cy={station.y} r="8" fill="#05070c" stroke="#10b981" strokeWidth="2" />
              <circle cx={station.x} cy={station.y} r="3" fill="#10b981" />
              <text 
                x={station.x + 12} 
                y={station.y + 4} 
                fill="#ffffff" 
                fontSize="10" 
                fontWeight="500"
                fontFamily="Outfit"
              >
                {station.name}
              </text>
            </g>
          ))}
        </svg>

        {/* 4. Interactive markers from API (CCTVs, sensors, active violations) */}
        {markers.map((m) => {
          // Map latitude/longitude offsets into coordinate boxes in SVG bounds
          // Gaurikund central point: [30.6500, 79.0050]
          const latDiff = m.lat - 30.6500;
          const lngDiff = m.lng - 79.0050;
          
          // Scaled offset positions
          const x = 120 + Math.min(500, Math.max(-50, lngDiff * 140000));
          const y = 350 - Math.min(300, Math.max(-50, latDiff * 90000));

          let bg = '#0a0d16';
          let border = '#00f0ff';
          let icon = <Camera size={10} style={{ color: '#00f0ff' }} />;

          if (m.type === 'sensor') {
            border = '#10b981';
            icon = <Wind size={10} style={{ color: '#10b981' }} />;
          } else if (m.type === 'drone') {
            border = '#8b5cf6';
            icon = <Navigation size={10} style={{ color: '#8b5cf6' }} />;
          } else if (m.type === 'violation') {
            border = '#ef4444';
            icon = <AlertTriangle size={10} className="pulse-red" style={{ color: '#ef4444' }} />;
          }

          return (
            <div 
              key={m.id}
              onClick={() => setSelectedNode(m)}
              className="glass-panel"
              style={{
                position: 'absolute',
                top: `${y}px`,
                left: `${x}px`,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                padding: '3px 6px',
                borderWidth: '1px',
                borderColor: border,
                background: bg,
                borderRadius: '4px',
                fontSize: '0.65rem',
                cursor: 'pointer',
                boxShadow: `0 2px 10px rgba(0,0,0,0.5)`,
                zIndex: 20,
                transform: 'translate(-50%, -50%)',
                transition: 'all 0.2s ease'
              }}
            >
              {icon}
              <span style={{ fontWeight: 600, color: '#fff' }}>{m.id}</span>
            </div>
          );
        })}

        {/* Selected station/node detail popup */}
        {selectedNode && (
          <div className="glass-panel border-cyan" style={{
            position: 'absolute',
            bottom: '16px',
            right: '16px',
            width: '280px',
            padding: '12px',
            background: 'rgba(5,7,12,0.95)',
            zIndex: 30,
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
                <div>Status Index: <span style={{ color: selectedNode.status === 'Optimal' ? '#10b981' : '#f59e0b', fontWeight: 'bold' }}>{selectedNode.status}</span></div>
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
        zIndex: 10
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
          <span>Char Dham High-Altitude Border Security</span>
        </div>
      </div>
    </div>
  );
}
