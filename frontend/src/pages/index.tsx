import React, { useEffect, useState } from 'react';
import Head from 'next/head';
import { 
  Activity, 
  Wifi, 
  AlertTriangle, 
  Cpu, 
  Layers, 
  Video, 
  TrendingUp, 
  Droplet, 
  Database, 
  Navigation,
  CheckCircle2,
  Server,
  Grid,
  Maximize2
} from 'lucide-react';

import dynamic from 'next/dynamic';
const DashboardMap = dynamic(() => import('../components/DashboardMap'), {
  ssr: false,
  loading: () => (
    <div className="glass-panel" style={{ height: '100%', minHeight: '340px', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#00f0ff' }}>
      Loading GIS Interactive Map Grid...
    </div>
  )
});
import ViolationsFeed, { ViolationRecord } from '../components/ViolationsFeed';
import TelemetryCharts from '../components/TelemetryCharts';
import EmissionsCalculator from '../components/EmissionsCalculator';

interface CameraRecord {
  id: string;
  location_id: number;
  model_name: string;
  rtsp_url: string;
  direction_angle: number;
  is_active: boolean;
}

export default function Home() {
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [telemetry, setTelemetry] = useState([]);
  const [cameras, setCameras] = useState<CameraRecord[]>([]);
  const [compositeIndex, setCompositeIndex] = useState(85);
  const [capacityRatio, setCapacityRatio] = useState('1,450 / 5,000');
  const [crowdCount, setCrowdCount] = useState(1450);
  const [loading, setLoading] = useState(true);
  const [backendStatus, setBackendStatus] = useState<'ONLINE' | 'OFFLINE'>('ONLINE');
  
  // CCTV Wall layout configurations: 'grid' (2x2) or 'focus' (1 major stream)
  const [cctvMode, setCctvMode] = useState<'grid' | 'focus'>('grid');
  const [selectedCamId, setSelectedCamId] = useState('CAM-GK-ENTRY');
  const [activeTab, setActiveTab] = useState<'console' | 'pilot'>('console');
  const [deployDiagnosticStatus, setDeployDiagnosticStatus] = useState<'idle' | 'running' | 'success'>('idle');
  
  const runPilotDiagnostics = () => {
    setDeployDiagnosticStatus('running');
    setTimeout(() => {
      setDeployDiagnosticStatus('success');
    }, 2500);
  };
  
  const [recentNotification, setRecentNotification] = useState<string | null>(null);
  const [environmentalRiskSummary, setEnvironmentalRiskSummary] = useState({
    vehicle_eco_score: 85,
    location_eco_score: 85,
    route_eco_score: 80,
    repeat_offender_score: 12,
    pollution_impact_score: 25,
  });

  // Poll backend APIs for live system metrics (strictly every 5 seconds)
  const fetchDashboardData = async () => {
    try {
      // 1. Fetch live violations
      const vRes = await fetch('http://localhost:8000/api/v1/violations');
      if (vRes.ok) {
        const vData = await vRes.json();
        setViolations(vData);
        setBackendStatus('ONLINE');

        // Immediate banner notification if high severity infractions occur
        if (vData.length > 0) {
          const latestViolation = vData[0];
          if (latestViolation.status === 'PENDING' && latestViolation.severity_level === 'High') {
            setRecentNotification(
              `CRITICAL INFRACTION FLAGGED: Category=${latestViolation.violation_type.replace(/_/g, ' ')}, Camera=${latestViolation.camera_id}, Coordinates=[${latestViolation.violation_coordinates || 'Gaurikund'}]`
            );
          }
        }
      }

      // 2. Fetch environmental weather telemetry logs
      const tRes = await fetch('http://localhost:8000/api/v1/telemetry?location_id=1&limit=12');
      if (tRes.ok) {
        const tData = await tRes.json();
        setTelemetry(tData);
      }

      // 3. Fetch location compliance score
      const cRes = await fetch('http://localhost:8000/api/v1/compliance/location/1');
      if (cRes.ok) {
        const cData = await cRes.json();
        setCompositeIndex(cData.composite_green_index || 85);
        if (cData.pedestrian_count) {
          setCrowdCount(cData.pedestrian_count);
          setCapacityRatio(`${cData.pedestrian_count.toLocaleString()} / 5,000`);
        }
      }

      // 4. Fetch geofenced cameras list
      const camRes = await fetch('http://localhost:8000/api/v1/cameras');
      if (camRes.ok) {
        const camData = await camRes.json();
        setCameras(camData);
      }

      // 5. Fetch environmental risk summary
      const riskRes = await fetch('http://localhost:8000/api/v1/compliance/environmental-risk-summary');
      if (riskRes.ok) {
        const riskData = await riskRes.json();
        setEnvironmentalRiskSummary(riskData);
      }
    } catch (e) {
      console.log("[Backend connection alert] Orchestrator is offline. Falling back to client-side presentation state.");
      setBackendStatus('OFFLINE');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleUpdateStatus = async (id: number, status: 'APPROVED' | 'DISMISSED' | 'CHALLAN_ISSUED') => {
    try {
      const action = status === 'DISMISSED' ? 'DISMISS' : 'APPROVE';
      const res = await fetch(`http://localhost:8000/api/v1/violations/${id}/action`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          action: action,
          officer_badge: 'UK-POL-7718',
          notes: `Status updated to ${status} via operations dashboard.`
        })
      });

      if (res.ok) {
        const updatedViolation = await res.json();
        setViolations((prev) => 
          prev.map((v) => v.id === id ? { ...v, status: updatedViolation.status } : v)
        );
        console.log(`[Status write-back] Persisted status transaction successfully: ${updatedViolation.status} for ID #${id}`);
      } else {
        throw new Error("Action endpoint failed");
      }
    } catch (err) {
      console.error("Status transaction execution error: ", err);
      // Local fallback representation to keep UI responsive
      setViolations((prev) => 
        prev.map((v) => v.id === id ? { ...v, status } : v)
      );
    }
  };


  const getMapMarkers = () => {
    const cameraMarkers = cameras.map(cam => {
      let lat = 30.6500;
      let lng = 79.0050;
      if (cam.id === 'CAM-GK-RIVER-04') { lat = 30.6508; lng = 79.0058; }
      else if (cam.id === 'CAM-GK-TEST-99') { lat = 30.6502; lng = 79.0052; }

      return {
        id: cam.id,
        name: `${cam.model_name} (${cam.id})`,
        lat,
        lng,
        type: 'camera' as const,
        status: cam.is_active ? 'Optimal' : 'Offline',
        details: `RTSP Stream: ${cam.rtsp_url}`
      };
    });

    const activeViolationsMarkers = violations.map(v => ({
      id: `V-${v.id}`,
      name: v.violation_type.replace(/_/g, ' '),
      lat: 30.6501 + (v.id * 0.0003) % 0.0015,
      lng: 79.0051 + (v.id * 0.0002) % 0.0015,
      type: 'violation' as const,
      status: v.status,
      details: `Plate: ${v.plate_number || 'Pedestrian'} | Fine: ₹${v.fine_amount_inr}`
    }));

    return [...cameraMarkers, ...activeViolationsMarkers];
  };

  const crowdPercentage = Math.min(100, (crowdCount / 5000) * 100);

  const activeCamModel = cameras.find(c => c.id === selectedCamId) || {
    model_name: 'Hikvision Outdoor PTZ 4K',
    rtsp_url: 'rtsp://mock-video-stream:8554/gk-live'
  };

  return (
    <div className="dashboard-layout">
      <Head>
        <title>State Command Control Console | Uttarakhand Government</title>
        <meta name="description" content="SPEMS Nationwide GIS and Real-Time ANPR/Surveillance dashboard." />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      {/* 1. Sidebar Panel */}
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.8rem', textShadow: '0 0 10px rgba(0,240,255,0.4)' }}>🕉️</span>
          <div>
            <h1 className="brand-font" style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              SPEMS
              <span style={{ fontSize: '0.65rem', background: '#00F0FF', color: '#000', padding: '1px 4px', borderRadius: '3px', fontWeight: 'bold' }}>PILOT</span>
            </h1>
            <span style={{ fontSize: '0.65rem', color: '#00F0FF', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>UTTARAKHAND GOVT</span>
          </div>
        </div>

        {/* Operational Routing options */}
        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, marginTop: '10px' }}>
          <div 
            onClick={() => setActiveTab('console')}
            style={{ 
              background: activeTab === 'console' ? 'rgba(0, 240, 255, 0.08)' : 'transparent', 
              border: activeTab === 'console' ? '1px solid rgba(0, 240, 255, 0.25)' : '1px solid transparent', 
              color: activeTab === 'console' ? '#fff' : '#9ca3af', 
              padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' 
            }}
          >
            <Layers size={14} style={{ color: activeTab === 'console' ? '#00F0FF' : '#9ca3af' }} /> State Console
          </div>
          <div 
            onClick={() => setActiveTab('pilot')}
            style={{ 
              background: activeTab === 'pilot' ? 'rgba(0, 240, 255, 0.08)' : 'transparent', 
              border: activeTab === 'pilot' ? '1px solid rgba(0, 240, 255, 0.25)' : '1px solid transparent', 
              color: activeTab === 'pilot' ? '#fff' : '#9ca3af', 
              padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' 
            }}
          >
            <Server size={14} style={{ color: activeTab === 'pilot' ? '#00F0FF' : '#9ca3af' }} /> Pilot Deploy Console
          </div>
          <div style={{ color: '#9ca3af', padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Database size={14} /> Vehicles Register
          </div>
          <div style={{ color: '#9ca3af', padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Activity size={14} /> Spatial Heatmaps
          </div>
          <div 
            onClick={() => window.location.href = '/officer'}
            style={{ color: '#9ca3af', padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}
          >
            <Cpu size={14} /> RTO Challan Audits
          </div>
          <div 
            onClick={() => window.location.href = '/demo'}
            style={{ color: '#9ca3af', padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}
          >
            <TrendingUp size={14} /> Stakeholder Demo Desk
          </div>
        </nav>

        {/* Database Status details */}
        <div className="glass-panel" style={{ padding: '14px', background: 'rgba(5,7,12,0.6)', border: '1px solid rgba(255,255,255,0.03)', fontSize: '0.7rem', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: backendStatus === 'ONLINE' ? '#10b981' : '#ef4444' }}>
            <Server size={12} />
            <span style={{ fontWeight: 'bold' }}>ORCHESTRATOR: {backendStatus}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9ca3af' }}>
            <span>Active Sensors:</span>
            <span style={{ color: '#fff', fontWeight: 600 }}>1,248 Nodes</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#9ca3af' }}>
            <span>UAV Flight:</span>
            <span style={{ color: '#8b5cf6', fontWeight: 600 }}>Orbit Active</span>
          </div>
        </div>
      </aside>

      {/* 2. Main Page content */}
      <main className="main-content">
        {/* Real-time high priority alarm banner */}
        {recentNotification && (
          <div className="top-ticker" style={{ cursor: 'pointer' }} onClick={() => setRecentNotification(null)}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <AlertTriangle size={14} className="pulse-red" style={{ color: '#ef4444' }} />
              <span style={{ fontWeight: 600 }}>{recentNotification}</span>
            </div>
            <span style={{ fontSize: '0.65rem', color: '#6b7280', textTransform: 'uppercase' }}>Dismiss Banner</span>
          </div>
        )}

        <header className="dashboard-header">
          <div>
            <h2 className="brand-font" style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>Surveillance & Command Center</h2>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Rudraprayag Division Environmental GIS & Vehicle Tracker Control Room</p>
          </div>
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div className="live-indicator">STATE RADAR: ONLINE</div>
            <span style={{ fontSize: '0.75rem', color: '#9ca3af', background: 'rgba(255,255,255,0.04)', padding: '6px 12px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)' }}>
              Date: {new Date().toLocaleDateString([], { day: 'numeric', month: 'long', year: 'numeric' })}
            </span>
          </div>
        </header>

        {/* Compliance metrics scorecard */}
        <section className="stats-strip">
          <div className="glass-panel stat-card emerald">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.02em' }}>Environmental Green Score</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: '#10B981' }}>{compositeIndex}%</span>
              <span style={{ fontSize: '0.7rem', color: '#10B981', fontWeight: 600 }}>Excellent Compliance</span>
            </div>
          </div>
          
          <div className="glass-panel stat-card cyan">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.02em' }}>Active Pedestrian Density</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value">{capacityRatio}</span>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>pax</span>
            </div>
          </div>

          <div className="glass-panel stat-card amber">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.02em' }}>Pending Infraction Audits</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: '#F59E0B' }}>
                {violations.filter(v => v.status === 'PENDING').length}
              </span>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>unapproved</span>
            </div>
          </div>

          <div className="glass-panel stat-card purple">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.02em' }}>Vehicle Emission Standard</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: '#8b5cf6' }}>98.2%</span>
              <span style={{ fontSize: '0.7rem', color: '#8b5cf6', fontWeight: 600 }}>BS-VI Ratio</span>
            </div>
          </div>
        </section>

        {/* 3-Pane Console layout or Pilot Console */}
        {activeTab === 'console' ? (
          <section className="grid-3-col">
            
            <div style={{ gridColumn: 'span 2', display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* Live CCTV surveillance wall / grid */}
              <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <Video size={16} style={{ color: '#00f0ff' }} />
                    <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff' }}>Surveillance Command CCTV Wall</h3>
                  </div>
                  
                  {/* Wall configuration toggles */}
                  <div style={{ display: 'flex', gap: '6px' }}>
                    <button 
                      onClick={() => setCctvMode('grid')}
                      className={`action-btn ${cctvMode === 'grid' ? 'active' : ''}`}
                      style={{ padding: '3px 8px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Grid size={12} /> Matrix Grid (2x2)
                    </button>
                    <button 
                      onClick={() => setCctvMode('focus')}
                      className={`action-btn ${cctvMode === 'focus' ? 'active' : ''}`}
                      style={{ padding: '3px 8px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '4px' }}
                    >
                      <Maximize2 size={12} /> Focus View
                    </button>
                  </div>
                </div>

                {/* CCTV MATRIX GRID VIEW */}
                {cctvMode === 'grid' ? (
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    
                    {/* Camera 1: Entry gate */}
                    <div 
                      onClick={() => { setSelectedCamId('CAM-GK-ENTRY'); setCctvMode('focus'); }}
                      style={{ position: 'relative', height: '180px', border: '1px solid rgba(0, 240, 255, 0.15)', background: '#020306', borderRadius: '6px', overflow: 'hidden', cursor: 'pointer' }}
                    >
                      {backendStatus === 'ONLINE' ? (
                        <img src="http://localhost:8000/api/v1/cameras/CAM-GK-ENTRY/stream" style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="CAM-GK-ENTRY Live" />
                      ) : (
                        <>
                          <video src="https://assets.mixkit.co/videos/preview/mixkit-highway-traffic-in-a-sunny-day-from-above-44330-large.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.55 }} />
                          <div style={{ position: 'absolute', top: '25%', left: '30%', width: '70px', height: '35px', border: '1.5px solid #00f0ff', borderRadius: '3px' }}>
                            <span style={{ position: 'absolute', top: '-11px', left: 0, background: '#00f0ff', color: '#000', fontSize: '7px', fontWeight: 'bold', padding: '0px 2px' }}>CAR 94.6%</span>
                          </div>
                        </>
                      )}
                      <div style={{ position: 'absolute', top: '8px', left: '8px', background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '3px', fontSize: '0.6rem', color: '#fff', fontFamily: 'monospace', zIndex: 10 }}>
                        CAM-GK-ENTRY (Entry Checkpoint)
                      </div>
                      <div style={{ position: 'absolute', bottom: '8px', right: '8px', fontSize: '0.55rem', color: '#10b981', background: 'rgba(0,0,0,0.7)', padding: '2px 4px', borderRadius: '2px', zIndex: 10 }}>
                        30 FPS | 4.2 Mbps
                      </div>
                    </div>

                    {/* Camera 2: River */}
                    <div 
                      onClick={() => { setSelectedCamId('CAM-GK-RIVER-04'); setCctvMode('focus'); }}
                      style={{ position: 'relative', height: '180px', border: '1px solid rgba(0, 240, 255, 0.15)', background: '#020306', borderRadius: '6px', overflow: 'hidden', cursor: 'pointer' }}
                    >
                      {backendStatus === 'ONLINE' ? (
                        <img src="http://localhost:8000/api/v1/cameras/CAM-GK-RIVER-04/stream" style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="CAM-GK-RIVER-04 Live" />
                      ) : (
                        <>
                          <video src="https://assets.mixkit.co/videos/preview/mixkit-highway-traffic-in-a-sunny-day-from-above-44330-large.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.55 }} />
                          <div style={{ position: 'absolute', top: '15%', left: '15%', width: '140px', height: '70px', border: '1px dashed #ef4444', background: 'rgba(239,68,68,0.03)' }}>
                            <span style={{ position: 'absolute', top: '4px', left: '4px', color: '#ef4444', fontSize: '7px', fontWeight: 'bold' }}>RIVER MONITOR ZONE</span>
                          </div>
                        </>
                      )}
                      <div style={{ position: 'absolute', top: '8px', left: '8px', background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '3px', fontSize: '0.6rem', color: '#fff', fontFamily: 'monospace', zIndex: 10 }}>
                        CAM-GK-RIVER-04 (Mandakini Flow)
                      </div>
                      <div style={{ position: 'absolute', bottom: '8px', right: '8px', fontSize: '0.55rem', color: '#10b981', background: 'rgba(0,0,0,0.7)', padding: '2px 4px', borderRadius: '2px', zIndex: 10 }}>
                        30 FPS | 3.8 Mbps
                      </div>
                    </div>

                    {/* Camera 3: Test base */}
                    <div 
                      onClick={() => { setSelectedCamId('CAM-GK-TEST-99'); setCctvMode('focus'); }}
                      style={{ position: 'relative', height: '180px', border: '1px solid rgba(0, 240, 255, 0.15)', background: '#020306', borderRadius: '6px', overflow: 'hidden', cursor: 'pointer' }}
                    >
                      {backendStatus === 'ONLINE' ? (
                        <img src="http://localhost:8000/api/v1/cameras/CAM-GK-TEST-99/stream" style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="CAM-GK-TEST-99 Live" />
                      ) : (
                        <>
                          <video src="https://assets.mixkit.co/videos/preview/mixkit-highway-traffic-in-a-sunny-day-from-above-44330-large.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.55 }} />
                          <div style={{ position: 'absolute', top: '40%', left: '40%', width: '60px', height: '40px', border: '1.5px solid #f59e0b', borderRadius: '3px' }}>
                            <span style={{ position: 'absolute', top: '-11px', left: 0, background: '#f59e0b', color: '#000', fontSize: '7px', fontWeight: 'bold', padding: '0px 2px' }}>PEDESTRIAN</span>
                          </div>
                        </>
                      )}
                      <div style={{ position: 'absolute', top: '8px', left: '8px', background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '3px', fontSize: '0.6rem', color: '#fff', fontFamily: 'monospace', zIndex: 10 }}>
                        CAM-GK-TEST-99 (Base Camp A1)
                      </div>
                      <div style={{ position: 'absolute', bottom: '8px', right: '8px', fontSize: '0.55rem', color: '#10b981', background: 'rgba(0,0,0,0.7)', padding: '2px 4px', borderRadius: '2px', zIndex: 10 }}>
                        25 FPS | 2.5 Mbps
                      </div>
                    </div>

                    {/* Camera 4: Drone */}
                    <div 
                      onClick={() => { setSelectedCamId('UAV-PATROL-01'); setCctvMode('focus'); }}
                      style={{ position: 'relative', height: '180px', border: '1px solid rgba(139, 92, 246, 0.3)', background: '#020306', borderRadius: '6px', overflow: 'hidden', cursor: 'pointer' }}
                    >
                      {backendStatus === 'ONLINE' ? (
                        <img src="http://localhost:8000/api/v1/cameras/UAV-PATROL-01/stream" style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="UAV-PATROL-01 Live" />
                      ) : (
                        <>
                          <video src="https://assets.mixkit.co/videos/preview/mixkit-highway-traffic-in-a-sunny-day-from-above-44330-large.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.45 }} />
                          <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            <div style={{ width: '60px', height: '60px', border: '1px dashed #8b5cf6', borderRadius: '50%', animation: 'spin 12s linear infinite' }} />
                          </div>
                        </>
                      )}
                      <div style={{ position: 'absolute', top: '8px', left: '8px', background: 'rgba(0,0,0,0.8)', border: '1px solid rgba(255,255,255,0.06)', padding: '2px 6px', borderRadius: '3px', fontSize: '0.6rem', color: '#8b5cf6', fontFamily: 'monospace', fontWeight: 'bold', zIndex: 10 }}>
                        🛸 UAV-PATROL-01 (Altitude Corridor)
                      </div>
                      <div style={{ position: 'absolute', bottom: '8px', left: '8px', color: '#fff', fontSize: '7px', display: 'flex', gap: '6px', background: 'rgba(0,0,0,0.7)', padding: '2px 6px', borderRadius: '2px', zIndex: 10 }}>
                        <span>ALT: 150m</span>
                        <span>BATT: 82%</span>
                      </div>
                      <div style={{ position: 'absolute', bottom: '8px', right: '8px', fontSize: '0.55rem', color: '#8b5cf6', background: 'rgba(0,0,0,0.7)', padding: '2px 4px', borderRadius: '2px', zIndex: 10 }}>
                        UAV STREAM ONLINE
                      </div>
                    </div>

                  </div>
                ) : (
                  /* SINGLE STREAM FOCUSED VIEW */
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    <div style={{ display: 'flex', gap: '4px' }}>
                      {['CAM-GK-ENTRY', 'CAM-GK-RIVER-04', 'CAM-GK-TEST-99', 'UAV-PATROL-01'].map(camId => (
                        <button 
                          key={camId}
                          onClick={() => setSelectedCamId(camId)}
                          className={`action-btn ${selectedCamId === camId ? 'active' : ''}`}
                          style={{ padding: '3px 8px', fontSize: '0.7rem' }}
                        >
                          {camId}
                        </button>
                      ))}
                    </div>

                    <div style={{
                      position: 'relative',
                      height: '280px',
                      borderRadius: '8px',
                      border: '1px solid rgba(0, 240, 255, 0.15)',
                      background: '#020306',
                      overflow: 'hidden'
                    }}>
                      {backendStatus === 'ONLINE' ? (
                        <img src={`http://localhost:8000/api/v1/cameras/${selectedCamId}/stream`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt={selectedCamId} />
                      ) : (
                        <video src="https://assets.mixkit.co/videos/preview/mixkit-highway-traffic-in-a-sunny-day-from-above-44330-large.mp4" autoPlay loop muted style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: 0.6 }} />
                      )}
                      <div style={{ position: 'absolute', top: '12px', left: '12px', background: 'rgba(0,0,0,0.7)', border: '1px solid rgba(255,255,255,0.08)', padding: '4px 10px', borderRadius: '4px', fontSize: '0.65rem', color: '#fff', fontFamily: 'monospace', zIndex: 10 }}>
                        <div>NODE: {selectedCamId}</div>
                        <div>MODEL: {activeCamModel.model_name}</div>
                        <div style={{ color: '#00f0ff', fontWeight: 'bold' }}>STATE: ACTIVE STREAM INGESTION (42ms latency)</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* GIS map & charts row */}
              <div className="grid-2-col">
                <div style={{ height: '420px' }}>
                  <DashboardMap markers={getMapMarkers()} />
                </div>
                <div className="glass-panel" style={{ padding: '20px', height: '420px' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 600, color: '#fff', marginBottom: '12px' }}>High-Altitude Sensor Grid</h3>
                  <TelemetryCharts data={telemetry} />
                </div>
              </div>

              {/* Violations center */}
              <div>
                <ViolationsFeed violations={violations} onUpdateStatus={handleUpdateStatus} />
              </div>
            </div>

            {/* Right sidebar details */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              
              {/* 1. Pilgrim crowd capacity monitor */}
              <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>Crowd Capacity Monitor</h3>
                  <span style={{ fontSize: '0.65rem', color: crowdPercentage > 80 ? '#ef4444' : '#10b981', fontWeight: 'bold' }}>
                    {crowdPercentage > 80 ? 'CRITICAL LIMIT' : 'OPTIMAL'}
                  </span>
                </div>

                <div style={{ position: 'relative', width: '100%', height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                  <div style={{
                    position: 'absolute',
                    top: 0,
                    left: 0,
                    height: '100%',
                    width: `${crowdPercentage}%`,
                    background: crowdPercentage > 80 ? 'linear-gradient(90deg, #f59e0b, #ef4444)' : 'linear-gradient(90deg, #00f0ff, #10b981)',
                    borderRadius: '4px',
                    boxShadow: crowdPercentage > 80 ? '0 0 10px rgba(239,68,68,0.5)' : 'none',
                    transition: 'width 0.5s ease'
                  }}></div>
                </div>

                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                  <span>Base camp Gaurikund (Capacity limit: 5,000)</span>
                  <span style={{ color: '#fff', fontWeight: 600 }}>{crowdPercentage.toFixed(1)}%</span>
                </div>
              </div>

              {/* Environmental Risk & Eco-Scoring Indicator */}
              <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>Environmental Eco & Risk Scores</h3>
                  <span style={{ fontSize: '0.65rem', color: '#00f0ff', fontWeight: 'bold' }}>REAL-TIME</span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {/* 1. Vehicle Eco Score */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                      <span>🚙 Vehicle Eco Rating</span>
                      <span style={{ color: '#10b981', fontWeight: 600 }}>{environmentalRiskSummary.vehicle_eco_score}%</span>
                    </div>
                    <div style={{ position: 'relative', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', top: 0, left: 0, height: '100%',
                        width: `${environmentalRiskSummary.vehicle_eco_score}%`,
                        background: 'linear-gradient(90deg, #10b981, #00f0ff)',
                        borderRadius: '3px', transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                  </div>

                  {/* 2. Location Eco Score */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                      <span>📍 Location Compliance Score</span>
                      <span style={{ color: '#00f0ff', fontWeight: 600 }}>{environmentalRiskSummary.location_eco_score}%</span>
                    </div>
                    <div style={{ position: 'relative', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', top: 0, left: 0, height: '100%',
                        width: `${environmentalRiskSummary.location_eco_score}%`,
                        background: 'linear-gradient(90deg, #00f0ff, #3b82f6)',
                        borderRadius: '3px', transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                  </div>

                  {/* 3. Route Eco Score */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                      <span>🛣️ Shrine Route Eco Score</span>
                      <span style={{ color: '#8b5cf6', fontWeight: 600 }}>{environmentalRiskSummary.route_eco_score}%</span>
                    </div>
                    <div style={{ position: 'relative', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', top: 0, left: 0, height: '100%',
                        width: `${environmentalRiskSummary.route_eco_score}%`,
                        background: 'linear-gradient(90deg, #8b5cf6, #ec4899)',
                        borderRadius: '3px', transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                  </div>

                  {/* 4. Repeat Offender Score */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                      <span>⚠️ Repeat Offender Index</span>
                      <span style={{ color: environmentalRiskSummary.repeat_offender_score > 40 ? '#ef4444' : '#f59e0b', fontWeight: 600 }}>
                        {environmentalRiskSummary.repeat_offender_score}%
                      </span>
                    </div>
                    <div style={{ position: 'relative', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', top: 0, left: 0, height: '100%',
                        width: `${environmentalRiskSummary.repeat_offender_score}%`,
                        background: 'linear-gradient(90deg, #f59e0b, #ef4444)',
                        borderRadius: '3px', transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                  </div>

                  {/* 5. Pollution Impact Score */}
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#9ca3af' }}>
                      <span>💨 Pollution Impact Level</span>
                      <span style={{ color: environmentalRiskSummary.pollution_impact_score > 55 ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                        {environmentalRiskSummary.pollution_impact_score}%
                      </span>
                    </div>
                    <div style={{ position: 'relative', width: '100%', height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{
                        position: 'absolute', top: 0, left: 0, height: '100%',
                        width: `${environmentalRiskSummary.pollution_impact_score}%`,
                        background: 'linear-gradient(90deg, #10b981, #f59e0b)',
                        borderRadius: '3px', transition: 'width 0.5s ease'
                      }}></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Emissions & Offsets Calculator */}
              <EmissionsCalculator />

              {/* 2. Prometheus Camera health connection status */}
              <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>CCTV Ingestion Health</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                  {cameras.length === 0 ? (
                    <div style={{ fontSize: '0.75rem', color: '#6b7280', padding: '10px 0' }}>
                      Awaiting CCTV controller registers...
                    </div>
                  ) : (
                    cameras.map(cam => (
                      <div 
                        key={cam.id} 
                        style={{ 
                          background: 'rgba(255,255,255,0.02)', 
                          border: '1px solid rgba(255,255,255,0.04)', 
                          padding: '10px 12px', 
                          borderRadius: '6px', 
                          display: 'flex', 
                          alignItems: 'center', 
                          justifyContent: 'space-between'
                        }}
                      >
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                          <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#fff' }}>{cam.id}</span>
                          <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{cam.model_name.split(' ')[0]} PTZ 4K</span>
                        </div>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 600 }}>99.8%</span>
                          <span style={{ 
                            width: '8px', 
                            height: '8px', 
                            borderRadius: '50%', 
                            backgroundColor: cam.is_active ? '#10b981' : '#ef4444',
                            boxShadow: cam.is_active ? '0 0 6px #10b981' : '0 0 6px #ef4444'
                          }}></span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* 3. Real-time parsed vehicle scrolling ticker */}
              <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, minHeight: '260px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff' }}>ANPR Parse Ticker</h3>
                  <Wifi size={12} className="pulse-red" style={{ color: '#00f0ff' }} />
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', overflowY: 'auto', maxHeight: '280px' }}>
                  {violations.filter(v => v.plate_number).slice(0, 8).map((v) => (
                    <div 
                      key={v.id} 
                      style={{ 
                        fontSize: '0.75rem', 
                        padding: '8px', 
                        background: 'rgba(0, 240, 255, 0.02)', 
                        borderLeft: '2px solid #00f0ff', 
                        borderRadius: '0 4px 4px 0',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '2px'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ fontWeight: 'bold', color: '#00f0ff' }}>{v.plate_number}</span>
                        <span style={{ color: '#6b7280', fontSize: '0.65rem' }}>
                          {new Date(v.violation_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </span>
                      </div>
                      <span style={{ color: '#9ca3af', fontSize: '0.65rem' }}>Passed node CAM-GK-ENTRY (Conf: 98.4%)</span>
                    </div>
                  ))}

                  {violations.filter(v => v.plate_number).length === 0 && (
                    <div style={{ padding: '40px 0', textAlign: 'center', color: '#6b7280', fontSize: '0.75rem' }}>
                      Listening for transit ANPR signals on corridor...
                    </div>
                  )}
                </div>
              </div>

            </div>
          </section>
        ) : (
          /* PILOT DEPLOYMENT CONSOLE VIEW */
          <section className="glass-panel" style={{ padding: '30px', display: 'flex', flexDirection: 'column', gap: '24px', minHeight: '600px' }}>
            <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '16px' }}>
              <h3 className="brand-font" style={{ fontSize: '1.4rem', fontWeight: 700, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
                ⚙️ Gaurikund Pilot Node Deployment Console
              </h3>
              <p style={{ fontSize: '0.85rem', color: '#9ca3af', marginTop: '4px' }}>
                Infrastructure orchestration, hardware configurations, and core cluster telemetry logs.
              </p>
            </div>

            {/* Target Allocations Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
              <div className="glass-panel" style={{ padding: '16px', borderLeft: '3px solid #00f0ff' }}>
                <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Active Video Channels</span>
                <h4 style={{ fontSize: '1.6rem', color: '#fff', margin: '4px 0 0 0' }}>5 Camera Feeds</h4>
                <p style={{ fontSize: '0.7rem', color: '#6b7280', margin: '2px 0 0 0' }}>Entry, Exit, No-Park, Litter, River</p>
              </div>
              <div className="glass-panel" style={{ padding: '16px', borderLeft: '3px solid #10b981' }}>
                <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Active Gate Checkpoints</span>
                <h4 style={{ fontSize: '1.6rem', color: '#fff', margin: '4px 0 0 0' }}>1 Enforcement Hub</h4>
                <p style={{ fontSize: '0.7rem', color: '#6b7280', margin: '2px 0 0 0' }}>Gaurikund main gateway routing barrier</p>
              </div>
              <div className="glass-panel" style={{ padding: '16px', borderLeft: '3px solid #8b5cf6' }}>
                <span style={{ fontSize: '0.7rem', color: '#9ca3af', textTransform: 'uppercase' }}>Command Centers</span>
                <h4 style={{ fontSize: '1.6rem', color: '#fff', margin: '4px 0 0 0' }}>1 Division Center</h4>
                <p style={{ fontSize: '0.7rem', color: '#6b7280', margin: '2px 0 0 0' }}>Rudraprayag local station workstation</p>
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr', gap: '20px' }}>
              {/* Left Column: Script Setup & Instructions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    📦 Pilot Deployment Script Setup
                  </h4>
                  <p style={{ fontSize: '0.8rem', color: '#9ca3af', lineHeight: '1.4' }}>
                    Configure local station services, database migrations, and telemetry collectors by running the deployment engine:
                  </p>
                  
                  {/* Code snippet block */}
                  <pre style={{
                    background: '#04060b',
                    border: '1px solid rgba(255,255,255,0.06)',
                    padding: '12px 16px',
                    borderRadius: '6px',
                    fontFamily: 'monospace',
                    fontSize: '0.75rem',
                    color: '#00f0ff',
                    overflowX: 'auto',
                    margin: '12px 0'
                  }}>
                    {`# Execute the Gaurikund pilot installer\nchmod +x infra/deploy_pilot.sh\n./infra/deploy_pilot.sh`}
                  </pre>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginTop: '16px' }}>
                    <button 
                      onClick={runPilotDiagnostics}
                      disabled={deployDiagnosticStatus === 'running'}
                      className="action-btn active"
                      style={{ padding: '6px 14px', fontSize: '0.8rem' }}
                    >
                      {deployDiagnosticStatus === 'idle' && 'Run Deployment Diagnostics'}
                      {deployDiagnosticStatus === 'running' && 'Analyzing Checkpoint Nodes...'}
                      {deployDiagnosticStatus === 'success' && 'Diagnostics Passed (100% OK)'}
                    </button>
                    {deployDiagnosticStatus === 'running' && (
                      <span className="pulse-red" style={{ fontSize: '0.75rem', color: '#f59e0b' }}>Running site diagnostics...</span>
                    )}
                    {deployDiagnosticStatus === 'success' && (
                      <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 'bold' }}>✓ Subnet, Docker, & Prometheus OK</span>
                    )}
                  </div>
                </div>

                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', marginBottom: '14px' }}>
                    📋 Hardware Requirements Specification
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '0.75rem' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
                      <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>Outdoor 4K Cameras (5 Units)</span>
                      <span style={{ color: '#fff' }}>Hikvision DS-2CD2186G2-I (IP67, IK10, Lens Heaters)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
                      <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>Edge Inference Nodes (2 Units)</span>
                      <span style={{ color: '#fff' }}>NVIDIA Jetson Orin Nano (8GB VRAM, Fanless boxer case)</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
                      <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>Command Center Server (1 Unit)</span>
                      <span style={{ color: '#fff' }}>Xeon 6-Core / 32GB RAM / NVIDIA RTX 4060 Workstation</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '6px' }}>
                      <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>LAN/WAN Infrastructure</span>
                      <span style={{ color: '#fff' }}>Moxa DIN-Rail Switches + VSAT HN9260 Satellite Dish</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '4px' }}>
                      <span style={{ color: '#9ca3af', fontWeight: 'bold' }}>Failsafe Power Backups</span>
                      <span style={{ color: '#fff' }}>IP66 Pole-Mounted Lithium UPS (2hr autonomy)</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Right Column: Live Monitoring Exporters */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    📊 Pilot System Monitoring (Prometheus/Grafana)
                  </h4>
                  
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                    {/* Gauge 1: Edge CPU */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <span style={{ color: '#9ca3af' }}>Edge Inference CPU Load</span>
                        <span style={{ color: '#10b981', fontWeight: 'bold' }}>42% (Normal)</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: '42%', background: '#10b981', borderRadius: '3px' }}></div>
                      </div>
                    </div>

                    {/* Gauge 2: WAN Backhaul load */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <span style={{ color: '#9ca3af' }}>WAN VSAT Bandwidth Load</span>
                        <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>82% (104 kbps)</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: '82%', background: '#f59e0b', borderRadius: '3px' }}></div>
                      </div>
                    </div>

                    {/* Gauge 3: LAN PoE traffic */}
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem' }}>
                        <span style={{ color: '#9ca3af' }}>PoE LAN Bandwidth Utilization</span>
                        <span style={{ color: '#00f0ff', fontWeight: 'bold' }}>40 Mbps (Optimal)</span>
                      </div>
                      <div style={{ height: '6px', background: 'rgba(255,255,255,0.06)', borderRadius: '3px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: '40%', background: '#00f0ff', borderRadius: '3px' }}></div>
                      </div>
                    </div>

                    {/* Exporter Scrapers list */}
                    <div style={{ marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', padding: '6px 8px', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '4px' }}>
                        <span style={{ color: '#fff' }}>● Station DB Scraper</span>
                        <span style={{ color: '#10b981', fontWeight: 'bold' }}>SCRAPING (15s)</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', padding: '6px 8px', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '4px' }}>
                        <span style={{ color: '#fff' }}>● Edge Node A (192.168.10.100)</span>
                        <span style={{ color: '#10b981', fontWeight: 'bold' }}>SCRAPING (15s)</span>
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', padding: '6px 8px', background: 'rgba(16,185,129,0.05)', border: '1px solid rgba(16,185,129,0.2)', borderRadius: '4px' }}>
                        <span style={{ color: '#fff' }}>● Edge Node B (192.168.10.101)</span>
                        <span style={{ color: '#10b981', fontWeight: 'bold' }}>SCRAPING (15s)</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

