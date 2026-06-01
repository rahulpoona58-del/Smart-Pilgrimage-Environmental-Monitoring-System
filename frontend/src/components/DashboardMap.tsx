import React, { useEffect, useState } from 'react';

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

export default function DashboardMap({ markers, center = [30.6500, 79.0050], zoom = 13 }: DashboardMapProps) {
  const [isClient, setIsClient] = useState(false);

  useEffect(() => {
    // Flag to prevent NextJS server-side rendering (SSR) of Leaflet libraries
    setIsClient(true);
  }, []);

  if (!isClient) {
    return (
      <div className="glass-panel" style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#0f1420' }}>
        <p style={{ color: '#9ca3af' }}>Bootstrapping Dynamic GIS Systems...</p>
      </div>
    );
  }

  // Fallback map container render. In actual browser deployments, dynamic dynamic-loading is executed:
  // import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'react-leaflet';
  return (
    <div className="glass-panel" style={{ height: '100%', position: 'relative', overflow: 'hidden' }}>
      {/* Mock Map Canvas visualization representing Leaflet view bounds */}
      <div style={{
        position: 'absolute',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundImage: 'radial-gradient(rgba(0, 240, 255, 0.08) 1.5px, transparent 1.5px)',
        backgroundSize: '24px 24px',
        backgroundColor: '#0a0d16',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '16px'
      }}>
        {/* Map Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', zIndex: 10 }}>
          <div style={{ background: 'rgba(15, 20, 32, 0.9)', border: '1px solid rgba(255,255,255,0.08)', padding: '6px 12px', borderRadius: '8px', fontSize: '0.8rem' }}>
            <span style={{ color: '#00F0FF', fontWeight: 'bold' }}>GIS OVERLAY ACTIVE:</span> Gaurikund Bounding Box
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button style={{ background: '#171d2f', border: '1px solid rgba(255,255,255,0.08)', color: '#fff', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem' }}>Heatmap</button>
            <button style={{ background: '#171d2f', border: '1px solid rgba(255,255,255,0.08)', color: '#fff', padding: '4px 10px', borderRadius: '6px', cursor: 'pointer', fontSize: '0.75rem' }}>Satellite</button>
          </div>
        </div>

        {/* Map Plot Markers Layer */}
        <div style={{ position: 'relative', flex: 1, margin: '20px 0' }}>
          {/* Static Bounding polygon representation */}
          <div style={{
            position: 'absolute',
            top: '20%',
            left: '20%',
            width: '60%',
            height: '60%',
            border: '2px dashed rgba(0, 240, 255, 0.3)',
            background: 'rgba(0, 240, 255, 0.03)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: '0.75rem',
            color: 'rgba(0,240,255,0.5)'
          }}>
            GEOCONSTRAINT FENCE: ZONE-A-NO-PARK
          </div>

          {/* Render Active Markers on Grid */}
          {markers.map((m) => {
            // Semi-randomly position markers inside panel for visual simulation
            const hash = m.lat + m.lng;
            const top = `${30 + (hash * 157) % 50}%`;
            const left = `${30 + (hash * 283) % 50}%`;
            
            let color = '#00F0FF';
            let icon = '📷';
            if (m.type === 'sensor') { color = '#10B981'; icon = '⚡'; }
            if (m.type === 'drone') { color = '#A78BFA'; icon = '🛸'; }
            if (m.type === 'violation') { color = '#EF4444'; icon = '⚠️'; }

            return (
              <div 
                key={m.id}
                style={{
                  position: 'absolute',
                  top: top,
                  left: left,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  background: 'rgba(15, 20, 32, 0.95)',
                  border: `1px solid ${color}`,
                  padding: '4px 8px',
                  borderRadius: '6px',
                  boxShadow: `0 0 10px ${color}20`,
                  fontSize: '0.7rem',
                  cursor: 'pointer',
                  zIndex: 20
                }}
              >
                <span>{icon}</span>
                <span style={{ fontWeight: 600 }}>{m.name}</span>
              </div>
            );
          })}
        </div>

        {/* Map Legend */}
        <div style={{ display: 'flex', gap: '16px', zIndex: 10, background: 'rgba(15, 20, 32, 0.9)', padding: '6px 12px', borderRadius: '8px', fontSize: '0.75rem', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ color: '#00F0FF' }}>📷</span> CCTV Nodes</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ color: '#10B981' }}>⚡</span> IoT Weather</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ color: '#A78BFA' }}>🛸</span> Active UAV</div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><span style={{ color: '#EF4444' }}>⚠️</span> Violations</div>
        </div>
      </div>
    </div>
  );
}
