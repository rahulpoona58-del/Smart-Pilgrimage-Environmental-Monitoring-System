import React, { useEffect, useState } from 'react';
import { Activity, ShieldAlert, CheckCircle, RefreshCw, AlertTriangle, ShieldCheck, Waves, HelpCircle } from 'lucide-react';

interface ActiveAlert {
  id: number;
  location_id: number;
  hazard_type: string;
  severity_level: string;
  trigger_source: string;
  description: string | null;
  sensor_readings: any | null;
  is_active: boolean;
  resolved_at: string | null;
  created_at: string;
}

interface DisasterStatus {
  location_id: number;
  landslide_risk_score: number;
  flood_risk_score: number;
  rockfall_risk_score: number;
  overall_hazard_index: number;
  status: string;
}

export default function DisasterDashboard() {
  const [status, setStatus] = useState<DisasterStatus | null>(null);
  const [alerts, setAlerts] = useState<ActiveAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [simulating, setSimulating] = useState(false);

  const fetchDisasterData = async () => {
    setLoading(true);
    setError(null);
    try {
      // Fetch status for Gaurikund Checkpoint (Location ID = 1)
      const statusRes = await fetch("http://localhost:8000/api/v1/disaster/status/1");
      if (statusRes.ok) {
        const statusData = await statusRes.json();
        setStatus(statusData);
      } else {
        setError("Failed to fetch disaster risk parameters.");
      }

      // Fetch active alerts
      const alertsRes = await fetch("http://localhost:8000/api/v1/disaster/alerts");
      if (alertsRes.ok) {
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);
      }
    } catch (err) {
      setError("Disaster monitoring API offline.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const resolveAlert = async (alertId: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/disaster/alerts/${alertId}/resolve`, {
        method: "POST"
      });
      if (res.ok) {
        await fetchDisasterData();
      }
    } catch (err) {
      console.error("Failed to resolve alert:", err);
    }
  };

  const triggerSimulation = async (type: 'landslide' | 'flood') => {
    setSimulating(true);
    try {
      if (type === 'landslide') {
        // Create two canvas elements representing frames with displacement (motion)
        const canvas1 = document.createElement('canvas');
        canvas1.width = 100;
        canvas1.height = 100;
        const ctx1 = canvas1.getContext('2d');
        if (ctx1) {
          ctx1.fillStyle = '#000000';
          ctx1.fillRect(0, 0, 100, 100);
          ctx1.fillStyle = '#ffffff';
          ctx1.fillRect(10, 10, 20, 20); // Square at top-left
        }

        const canvas2 = document.createElement('canvas');
        canvas2.width = 100;
        canvas2.height = 100;
        const ctx2 = canvas2.getContext('2d');
        if (ctx2) {
          ctx2.fillStyle = '#000000';
          ctx2.fillRect(0, 0, 100, 100);
          ctx2.fillStyle = '#ffffff';
          ctx2.fillRect(60, 60, 20, 20); // Square shifted to bottom-right (simulates motion displacement)
        }

        const blob1 = await new Promise<Blob>((resolve) => canvas1.toBlob((b) => resolve(b || new Blob()), 'image/png'));
        const blob2 = await new Promise<Blob>((resolve) => canvas2.toBlob((b) => resolve(b || new Blob()), 'image/png'));

        const formData = new FormData();
        formData.append("prev_frame", blob1, "frame1.png");
        formData.append("curr_frame", blob2, "frame2.png");

        const res = await fetch("http://localhost:8000/api/v1/disaster/evaluate/1?camera_id=CAM-GK-RIVER-04", {
          method: "POST",
          body: formData
        });
        
        if (res.ok) {
          await fetchDisasterData();
        }
      } else {
        // Simulate flood telemetry spike by posting an abnormal SensorData report first
        const sensorPayload = {
          location_id: 1,
          device_id: "IOT-FLOOD-SIM",
          pm25: 12.5,
          pm10: 22.0,
          aqi: 45,
          temperature: 8.5,
          humidity: 98.0, // High saturation rain indicator
          co2: 420.0,
          water_ph: 4.8, // Highly abnormal acid ph runoff indicator
          measured_at: new Date().toISOString()
        };

        const telemetryRes = await fetch("http://localhost:8000/api/v1/telemetry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(sensorPayload)
        });

        if (telemetryRes.ok) {
          // Trigger a re-calculation of the status
          const statusRes = await fetch("http://localhost:8000/api/v1/disaster/status/1?camera_id=CAM-GK-RIVER-04");
          if (statusRes.ok) {
            await fetchDisasterData();
          }
        }
      }
    } catch (err) {
      console.error("Simulation trigger failed:", err);
    } finally {
      setSimulating(false);
    }
  };

  useEffect(() => {
    fetchDisasterData();
  }, []);

  const getStatusColor = (rating: string) => {
    if (rating === "CRITICAL") return "#ef4444";
    if (rating === "WARNING") return "#f59e0b";
    return "#10b981";
  };

  const getStatusBg = (rating: string) => {
    if (rating === "CRITICAL") return "rgba(239, 68, 68, 0.08)";
    if (rating === "WARNING") return "rgba(245, 158, 11, 0.08)";
    return "rgba(16, 185, 129, 0.08)";
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', minHeight: '400px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '10px' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} style={{ color: '#ff3b30' }} /> Disaster Monitoring & Warning System
          </h3>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Optical Flow Landslide Detection & IoT Flood Risk Telemetry</span>
        </div>
        <button 
          onClick={fetchDisasterData}
          disabled={loading}
          className="action-btn active"
          style={{ padding: '6px 10px', fontSize: '0.7rem' }}
        >
          Refresh
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '6px', color: '#ef4444', fontSize: '0.7rem', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      {status ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
          {/* Status Indicator */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            background: getStatusBg(status.status), 
            border: `1px solid ${getStatusColor(status.status)}40`,
            padding: '12px 16px', 
            borderRadius: '8px' 
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Composite Regional Hazard Level</span>
              <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>Gaurikund Slope Sector</span>
            </div>
            <span style={{ 
              fontSize: '0.9rem', 
              fontWeight: 800, 
              color: getStatusColor(status.status), 
              padding: '4px 12px', 
              borderRadius: '4px',
              border: `1px solid ${getStatusColor(status.status)}`,
              boxShadow: `0 0 8px ${getStatusColor(status.status)}40`
            }}>
              {status.status}
            </span>
          </div>

          {/* Grid Metrics */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
            
            {/* Landslide Risk */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShieldAlert size={12} style={{ color: '#ef4444' }} /> Landslide Risk
              </span>
              <span style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#fff' }}>
                {status.landslide_risk_score.toFixed(0)}<span style={{ fontSize: '0.8rem', color: '#6b7280' }}>/100</span>
              </span>
              <span style={{ fontSize: '0.6rem', color: status.landslide_risk_score >= 50 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {status.landslide_risk_score >= 75 ? "⚠️ Active Displacement" : status.landslide_risk_score >= 40 ? "⚠ Elevated Activity" : "✓ Slope Stable"}
              </span>
            </div>

            {/* Flood Risk */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Waves size={12} style={{ color: '#3b82f6' }} /> Flood Hazard
              </span>
              <span style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#fff' }}>
                {status.flood_risk_score.toFixed(0)}<span style={{ fontSize: '0.8rem', color: '#6b7280' }}>/100</span>
              </span>
              <span style={{ fontSize: '0.6rem', color: status.flood_risk_score >= 50 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {status.flood_risk_score >= 75 ? "⚠️ Overflow Trigger" : status.flood_risk_score >= 40 ? "⚠ High Water pH/T" : "✓ Levels Normal"}
              </span>
            </div>

            {/* Rockfall Risk */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <AlertTriangle size={12} style={{ color: '#f59e0b' }} /> Rockfall Index
              </span>
              <span style={{ fontSize: '1.4rem', fontWeight: 'bold', color: '#fff' }}>
                {status.rockfall_risk_score.toFixed(0)}<span style={{ fontSize: '0.8rem', color: '#6b7280' }}>/100</span>
              </span>
              <span style={{ fontSize: '0.6rem', color: status.rockfall_risk_score >= 50 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {status.rockfall_risk_score >= 75 ? "⚠️ Rockfall Danger" : "✓ Clear Passageway"}
              </span>
            </div>

          </div>

          {/* Active Alerts Table */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span style={{ fontSize: '0.7rem', color: '#ef4444', fontWeight: 'bold', textTransform: 'uppercase' }}>
              Active Disaster Alarms ({alerts.length})
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '180px', overflowY: 'auto' }}>
              {alerts.map((alert) => (
                <div key={alert.id} style={{ 
                  padding: '10px', 
                  background: 'rgba(239, 68, 68, 0.04)', 
                  border: '1px solid rgba(239, 68, 68, 0.15)', 
                  borderRadius: '6px',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                    <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#ef4444' }}>
                      {alert.hazard_type.toUpperCase()} ALERT ({alert.severity_level})
                    </span>
                    <span style={{ fontSize: '0.65rem', color: '#d1d5db' }}>
                      {alert.description || "Localized environmental anomaly detected."}
                    </span>
                    <span style={{ fontSize: '0.55rem', color: '#9ca3af' }}>
                      Source: {alert.trigger_source} | Timestamp: {new Date(alert.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  <button 
                    onClick={() => resolveAlert(alert.id)}
                    className="action-btn"
                    style={{ padding: '4px 8px', fontSize: '0.6rem', background: '#10b981', color: '#fff', border: 'none' }}
                  >
                    Resolve
                  </button>
                </div>
              ))}

              {alerts.length === 0 && (
                <div style={{ 
                  padding: '16px', 
                  background: 'rgba(16, 185, 129, 0.04)', 
                  border: '1px solid rgba(16, 185, 129, 0.1)', 
                  borderRadius: '6px',
                  color: '#10b981', 
                  fontSize: '0.7rem',
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <ShieldCheck size={14} />
                  <span>No active landslide or flooding alerts registered. Regional corridors safe.</span>
                </div>
              )}
            </div>
          </div>

          {/* Simulation Controls */}
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <HelpCircle size={10} /> Test & Verification Panel
            </span>
            <div style={{ display: 'flex', gap: '8px', marginTop: '8px' }}>
              <button 
                onClick={() => triggerSimulation('landslide')}
                disabled={simulating}
                className="action-btn"
                style={{ padding: '6px 12px', fontSize: '0.65rem', flex: 1, borderColor: '#ef4444', color: '#ef4444' }}
              >
                {simulating ? "Simulating..." : "Trigger Landslide Event"}
              </button>
              <button 
                onClick={() => triggerSimulation('flood')}
                disabled={simulating}
                className="action-btn"
                style={{ padding: '6px 12px', fontSize: '0.65rem', flex: 1, borderColor: '#3b82f6', color: '#3b82f6' }}
              >
                {simulating ? "Simulating..." : "Trigger Flood Event"}
              </button>
            </div>
          </div>

        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280', fontSize: '0.75rem' }}>
          Querying hazard monitors...
        </div>
      )}
    </div>
  );
}
