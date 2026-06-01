import React from 'react';

interface TelemetryData {
  pm25: number;
  pm10: number;
  aqi: number;
  temperature: number;
  humidity: number;
  co2: number;
  water_ph: number;
  measured_at: string;
}

interface TelemetryChartsProps {
  data: TelemetryData[];
}

export default function TelemetryCharts({ data }: TelemetryChartsProps) {
  // Take latest data element for numerical cards
  const latest = data[0] || {
    pm25: 12.4,
    pm10: 24.5,
    aqi: 38,
    temperature: 14.2,
    humidity: 62.0,
    co2: 405.0,
    water_ph: 7.2
  };

  const getAQIColor = (aqi: number) => {
    if (aqi < 50) return '#10B981'; // Good
    if (aqi < 100) return '#F59E0B'; // Moderate
    return '#EF4444'; // Poor
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* Dynamic atmospheric grid stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px' }}>
        <div className="glass-panel" style={{ padding: '12px', textAlign: 'center', background: 'rgba(15, 20, 32, 0.4)' }}>
          <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '4px' }}>AIR INDEX (AQI)</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: getAQIColor(latest.aqi) }}>
            {latest.aqi}
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '12px', textAlign: 'center', background: 'rgba(15, 20, 32, 0.4)' }}>
          <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '4px' }}>PM2.5 DUST</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#fff' }}>
            {latest.pm25} <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>µg/m³</span>
          </div>
        </div>
        <div className="glass-panel" style={{ padding: '12px', textAlign: 'center', background: 'rgba(15, 20, 32, 0.4)' }}>
          <div style={{ fontSize: '0.7rem', color: '#9ca3af', marginBottom: '4px' }}>RIVER PH INDEX</div>
          <div style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#00F0FF' }}>
            {latest.water_ph} <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>pH</span>
          </div>
        </div>
      </div>

      {/* Visual Chart Canvas Proxy */}
      <div className="glass-panel" style={{ padding: '16px', flex: 1, position: 'relative', minHeight: '160px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', fontWeight: 600 }}>24-Hour Telemetry Timeline</span>
          <div style={{ display: 'flex', gap: '8px', fontSize: '0.7rem' }}>
            <span style={{ color: '#00F0FF' }}>● AQI</span>
            <span style={{ color: '#10B981' }}>● PM2.5</span>
            <span style={{ color: '#F59E0B' }}>● PM10</span>
          </div>
        </div>

        {/* Dynamic Vector Line Graph Simulator */}
        <div style={{ flex: 1, borderBottom: '1px solid rgba(255,255,255,0.08)', position: 'relative', display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', padding: '10px 10px 0 10px' }}>
          
          {/* Simulated chart line paths using CSS grids */}
          {data.slice().reverse().map((d, idx) => {
            const heightPct = Math.min(95, Math.max(10, (d.aqi / 150) * 100));
            return (
              <div 
                key={idx} 
                style={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  gap: '4px',
                  width: '100%',
                  height: '100%',
                  justifyContent: 'flex-end'
                }}
              >
                {/* Bar chart representation */}
                <div 
                  style={{ 
                    width: '6px', 
                    height: `${heightPct}%`, 
                    background: 'linear-gradient(to top, rgba(0, 240, 255, 0.1), #00F0FF)', 
                    borderRadius: '3px',
                    boxShadow: '0 0 8px rgba(0, 240, 255, 0.2)',
                    transition: 'height 0.5s ease'
                  }}
                ></div>
                <span style={{ fontSize: '0.55rem', color: '#6b7280' }}>
                  {new Date(d.measured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              </div>
            );
          })}

          {data.length === 0 && (
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#6b7280', fontSize: '0.8rem' }}>
              Awaiting IoT stream telemetry signals...
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
