import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Activity, 
  TrendingUp, 
  Coins, 
  Leaf, 
  Users, 
  Play, 
  Pause, 
  RotateCcw, 
  LayoutDashboard, 
  BarChart3, 
  Info, 
  Globe, 
  Building2,
  Shield,
  ArrowLeft,
  Settings
} from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler } from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, BarElement, Title, Tooltip, Legend, Filler);

export default function DemoMode() {
  // Demo simulation state
  const [simulationActive, setSimulationActive] = useState(true);
  const [simulationSpeed, setSimulationSpeed] = useState<'normal' | 'fast' | 'extreme'>('normal');
  const [scenario, setScenario] = useState<'baseline' | 'festival' | 'monsoon_outage' | 'green_drive'>('baseline');
  
  // Real-time fluctuating metrics
  const [seconds, setSeconds] = useState(0);
  const [visitorCount, setVisitorCount] = useState(1420);
  const [aqi, setAqi] = useState(65);
  const [carbonLevel, setCarbonLevel] = useState(380);
  const [activeViolations, setActiveViolations] = useState<number>(3);
  const [complianceScore, setComplianceScore] = useState(88);
  const [totalRevenueFines, setTotalRevenueFines] = useState(145000);
  const [laborSavings, setLaborSavings] = useState(240000);
  const [processedPlatesCount, setProcessedPlatesCount] = useState(1248);

  // Time-series history arrays for analytics charts
  const [aqiHistory, setAqiHistory] = useState<number[]>([60, 62, 65, 63, 64, 65]);
  const [savingsHistory, setSavingsHistory] = useState<number[]>([40000, 80000, 120000, 160000, 200000, 240000]);

  // ANPR feed logs
  const [anprLogs, setAnprLogs] = useState<Array<{ plate: string; time: string; status: string; node: string }>>([
    { plate: 'UK07TA1230', time: '21:45:02', status: 'Compliant', node: 'CAM-GK-ENTRY' },
    { plate: 'DL03CA7718', time: '21:44:30', status: 'Restricted Parking (Warning)', node: 'CAM-GK-PARK' },
    { plate: 'HR26AQ9052', time: '21:43:12', status: 'Compliant', node: 'CAM-GK-EXIT' },
    { plate: 'MH12KK4560', time: '21:42:05', status: 'Littering Flagged', node: 'CAM-GK-RIVER' }
  ]);

  // Simulation core clock loop
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (simulationActive) {
      const msDelay = simulationSpeed === 'extreme' ? 300 : simulationSpeed === 'fast' ? 1000 : 2500;
      interval = setInterval(() => {
        setSeconds(prev => prev + 1);

        // Scenario rules
        let aqiNoise = (Math.random() * 4 - 2);
        let carbonNoise = (Math.random() * 10 - 5);
        let visitorNoise = Math.floor(Math.random() * 15 - 7);

        if (scenario === 'festival') {
          // High load, declining environment
          setVisitorCount(prev => Math.min(5000, prev + Math.floor(Math.random() * 30 + 10)));
          setAqi(prev => Math.min(300, prev + Math.random() * 2 + 0.5));
          setCarbonLevel(prev => Math.min(650, prev + Math.random() * 5 + 2));
          setComplianceScore(prev => Math.max(45, prev - 0.2));
          setTotalRevenueFines(prev => prev + 1500);
          setProcessedPlatesCount(prev => prev + 3);
          
          if (Math.random() > 0.6) {
            setActiveViolations(prev => prev + 1);
            triggerNewAnprLog('Declining: Overcrowding / Littering');
          }
        } 
        else if (scenario === 'monsoon_outage') {
          // Off-grid storage buffering
          setVisitorCount(prev => Math.max(100, prev - Math.floor(Math.random() * 20)));
          setAqi(prev => Math.max(12, prev - Math.random() * 1.5));
          setComplianceScore(prev => Math.min(100, prev + 0.1));
          setTotalRevenueFines(prev => prev + 0); // Outage blocks instant payments
          
          if (Math.random() > 0.7) {
            triggerNewAnprLog('Buffered local SQLite storage');
          }
        }
        else if (scenario === 'green_drive') {
          // Compliance cleanup
          setVisitorCount(prev => Math.max(800, prev + visitorNoise));
          setAqi(prev => Math.max(25, prev - Math.random() * 1.2));
          setCarbonLevel(prev => Math.max(300, prev - 2));
          setComplianceScore(prev => Math.min(100, prev + 0.3));
          setTotalRevenueFines(prev => prev + 250);
          setProcessedPlatesCount(prev => prev + 1);
          if (Math.random() > 0.8 && activeViolations > 0) {
            setActiveViolations(prev => prev - 1);
          }
          if (Math.random() > 0.6) {
            triggerNewAnprLog('Compliant');
          }
        }
        else {
          // Baseline status
          setVisitorCount(prev => Math.max(1000, Math.min(2500, prev + visitorNoise)));
          setAqi(prev => Math.max(40, Math.min(120, prev + aqiNoise)));
          setCarbonLevel(prev => Math.max(340, Math.min(420, prev + carbonNoise)));
          setComplianceScore(prev => Math.max(75, Math.min(95, prev + (Math.random() * 0.4 - 0.2))));
          setTotalRevenueFines(prev => prev + 500);
          setLaborSavings(prev => prev + 250);
          setProcessedPlatesCount(prev => prev + 1);
          
          if (Math.random() > 0.7) {
            triggerNewAnprLog(Math.random() > 0.85 ? 'Littering Flagged' : 'Compliant');
          }
        }

      }, msDelay);
    }
    return () => clearInterval(interval);
  }, [simulationActive, simulationSpeed, scenario, activeViolations]);

  // Update chart histories when clock ticks
  useEffect(() => {
    if (seconds > 0) {
      setAqiHistory(prev => {
        const next = [...prev, parseFloat(aqi.toFixed(1))];
        return next.slice(-8); // Keep last 8 elements
      });
      setSavingsHistory(prev => {
        const next = [...prev, laborSavings];
        return next.slice(-8);
      });
    }
  }, [seconds]);

  // Utility to push new ANPR logs
  const triggerNewAnprLog = (status: string) => {
    const states = ['UA', 'UK', 'DL', 'HR', 'MH', 'UP'];
    const randomPlate = `${states[Math.floor(Math.random() * states.length)]}07TA${Math.floor(1000 + Math.random() * 9000)}`;
    const nodes = ['CAM-GK-ENTRY', 'CAM-GK-EXIT', 'CAM-GK-PARK', 'CAM-GK-RIVER'];
    const timeStr = new Date().toTimeString().split(' ')[0];
    
    setAnprLogs(prev => [
      { plate: randomPlate, time: timeStr, status: status, node: nodes[Math.floor(Math.random() * nodes.length)] },
      ...prev.slice(0, 5)
    ]);
  };

  // Reset all registers to baseline
  const handleReset = () => {
    setSeconds(0);
    setVisitorCount(1420);
    setAqi(65);
    setCarbonLevel(380);
    setActiveViolations(3);
    setComplianceScore(88);
    setTotalRevenueFines(145000);
    setLaborSavings(240000);
    setProcessedPlatesCount(1248);
    setAqiHistory([60, 62, 65, 63, 64, 65]);
    setSavingsHistory([40000, 80000, 120000, 160000, 200000, 240000]);
  };

  // Chart Data definitions
  const aqiChartData = {
    labels: aqiHistory.map((_, i) => `T-${8 - i}`),
    datasets: [{
      label: 'Predicted PM2.5 / AQI Hotspot Tendency',
      data: aqiHistory,
      backgroundColor: 'rgba(0, 240, 255, 0.08)',
      borderColor: '#00f0ff',
      pointBackgroundColor: '#00f0ff',
      borderWidth: 2,
      fill: true,
      tension: 0.3
    }]
  };

  const financeChartData = {
    labels: savingsHistory.map((_, i) => `T-${8 - i}`),
    datasets: [{
      label: 'Cumulative Labor & O&M Budget Saved (INR)',
      data: savingsHistory,
      backgroundColor: 'rgba(16, 185, 129, 0.1)',
      borderColor: '#10b981',
      pointBackgroundColor: '#10b981',
      borderWidth: 2,
      fill: true,
      tension: 0.2
    }]
  };

  return (
    <div className="dashboard-layout" style={{ background: '#020306', minHeight: '100vh', color: '#fff' }}>
      <Head>
        <title>SPEMS Pitch Deck & Stakeholder Demo Room</title>
      </Head>

      {/* Sidebar - Pitch controls */}
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.8rem', textShadow: '0 0 10px rgba(0,240,255,0.4)' }}>🕉️</span>
          <div>
            <h1 className="brand-font" style={{ fontSize: '1.2rem', fontWeight: 800, color: '#fff' }}>
              SPEMS DEMO
              <span style={{ fontSize: '0.6rem', background: '#f59e0b', color: '#000', padding: '1px 4px', borderRadius: '3px', fontWeight: 'bold', marginLeft: '6px' }}>PITCH</span>
            </h1>
            <span style={{ fontSize: '0.65rem', color: '#00F0FF', fontWeight: 'bold' }}>STAKEHOLDER DESK</span>
          </div>
        </div>

        {/* Simulator controls */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '20px' }}>
          <span style={{ fontSize: '0.7rem', color: '#00f0ff', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>🔧 Simulator Engine</span>
          
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={() => setSimulationActive(!simulationActive)}
              className="action-btn active"
              style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '6px', fontSize: '0.75rem', background: simulationActive ? '#ef4444' : '#10b981', borderColor: simulationActive ? '#ef4444' : '#10b981' }}
            >
              {simulationActive ? <Pause size={12} /> : <Play size={12} />}
              {simulationActive ? 'Pause Sim' : 'Resume Sim'}
            </button>
            <button 
              onClick={handleReset}
              className="action-btn"
              style={{ padding: '8px 12px' }}
              title="Reset metrics"
            >
              <RotateCcw size={12} />
            </button>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <label style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Simulation speed:</label>
            <div style={{ display: 'flex', gap: '4px' }}>
              {(['normal', 'fast', 'extreme'] as const).map(speed => (
                <button 
                  key={speed}
                  onClick={() => setSimulationSpeed(speed)}
                  className={`action-btn ${simulationSpeed === speed ? 'active' : ''}`}
                  style={{ flex: 1, padding: '3px 0', fontSize: '0.65rem', textTransform: 'capitalize' }}
                >
                  {speed}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Scenario Picker */}
        <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <span style={{ fontSize: '0.7rem', color: '#00f0ff', fontWeight: 'bold', textTransform: 'uppercase' }}>🎭 Load Scenarios</span>
          
          <button 
            onClick={() => setScenario('baseline')}
            className={`action-btn ${scenario === 'baseline' ? 'active' : ''}`}
            style={{ width: '100%', padding: '8px 10px', fontSize: '0.75rem', textAlign: 'left' }}
          >
            ● Baseline (Standard Season)
          </button>
          <button 
            onClick={() => setScenario('festival')}
            className={`action-btn ${scenario === 'festival' ? 'active' : ''}`}
            style={{ width: '100%', padding: '8px 10px', fontSize: '0.75rem', textAlign: 'left', borderColor: scenario === 'festival' ? '#ef4444' : '' }}
          >
            🔥 Festival Influx (Peak Crowd)
          </button>
          <button 
            onClick={() => setScenario('monsoon_outage')}
            className={`action-btn ${scenario === 'monsoon_outage' ? 'active' : ''}`}
            style={{ width: '100%', padding: '8px 10px', fontSize: '0.75rem', textAlign: 'left', borderColor: scenario === 'monsoon_outage' ? '#f59e0b' : '' }}
          >
            ⛈️ Monsoon Outage (Local Buffering)
          </button>
          <button 
            onClick={() => setScenario('green_drive')}
            className={`action-btn ${scenario === 'green_drive' ? 'active' : ''}`}
            style={{ width: '100%', padding: '8px 10px', fontSize: '0.75rem', textAlign: 'left', borderColor: scenario === 'green_drive' ? '#10b981' : '' }}
          >
            🍃 Eco Green Enforcement Drive
          </button>
        </div>

        <div style={{ textAlign: 'center', padding: '10px 0', marginTop: 'auto' }}>
          <Link href="/" style={{ color: '#00f0ff', fontSize: '0.75rem', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
            <ArrowLeft size={12} /> Return to Operations Desk
          </Link>
        </div>
      </aside>

      {/* Main Core Demo Pane */}
      <main className="main-content">
        
        {/* Header section */}
        <header className="dashboard-header">
          <div>
            <h2 className="brand-font" style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>SPEMS Executive Pitch Sandbox</h2>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Dynamic simulator illustrating local environmental saves, operational cost offsets, and IoT routing failures.</p>
          </div>
          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <span style={{ fontSize: '0.75rem', background: '#f59e0b', color: '#000', fontWeight: 'bold', padding: '4px 10px', borderRadius: '4px' }}>
              SCENARIO: {scenario.toUpperCase().replace(/_/g, ' ')}
            </span>
          </div>
        </header>

        {/* Simulated Smart City Twin (Gaurikund Corridor View) */}
        <section className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '14px', marginBottom: '20px' }}>
          <h3 style={{ fontSize: '1rem', fontWeight: 'bold', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Globe size={16} style={{ color: '#00f0ff' }} /> Simulated Gaurikund Checkpoint Corridor View
          </h3>
          
          <div style={{ 
            height: '140px', 
            borderRadius: '6px', 
            background: 'linear-gradient(135deg, #09101f, #04060c)', 
            border: '1px solid rgba(0, 240, 255, 0.1)',
            position: 'relative',
            overflow: 'hidden',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-around'
          }}>
            
            {/* Visual elements representing corridors and nodes */}
            <div style={{ position: 'relative', width: '22%', height: '80px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <span style={{ fontSize: '0.55rem', color: '#9ca3af' }}>Sonprayag Barrier</span>
              <span style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 'bold' }}>CAM-01 Ingest</span>
              <div style={{ width: '8px', height: '8px', background: '#10b981', borderRadius: '50%', position: 'absolute', top: '8px', right: '8px', boxShadow: '0 0 6px #10b981' }} />
            </div>

            <div style={{ width: '12%', height: '2px', background: 'dashed rgba(0, 240, 255, 0.25)', borderStyle: 'dashed' }} />

            <div style={{ position: 'relative', width: '22%', height: '80px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <span style={{ fontSize: '0.55rem', color: '#9ca3af' }}>Dwell Parking</span>
              <span style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 'bold' }}>CAM-03 ANPR</span>
              <div style={{ 
                width: '8px', height: '8px', 
                background: scenario === 'monsoon_outage' ? '#ef4444' : activeViolations > 4 ? '#f59e0b' : '#10b981', 
                borderRadius: '50%', position: 'absolute', top: '8px', right: '8px',
                boxShadow: `0 0 6px ${scenario === 'monsoon_outage' ? '#ef4444' : activeViolations > 4 ? '#f59e0b' : '#10b981'}` 
              }} />
            </div>

            <div style={{ width: '12%', height: '2px', background: 'dashed rgba(0, 240, 255, 0.25)', borderStyle: 'dashed' }} />

            <div style={{ position: 'relative', width: '22%', height: '80px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '6px', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
              <span style={{ fontSize: '0.55rem', color: '#9ca3af' }}>Riverbank Wall</span>
              <span style={{ fontSize: '0.8rem', color: '#fff', fontWeight: 'bold' }}>CAM-05 Plume</span>
              <div style={{ width: '8px', height: '8px', background: '#10b981', borderRadius: '50%', position: 'absolute', top: '8px', right: '8px', boxShadow: '0 0 6px #10b981' }} />
            </div>

            {/* Cloud connectivity lines */}
            <div style={{ position: 'absolute', bottom: '6px', left: '16px', fontSize: '0.6rem', color: '#9ca3af', fontFamily: 'monospace' }}>
              CLOCK SPEED: {simulationActive ? `${simulationSpeed.toUpperCase()} TIME` : 'PAUSED'} | TICKS: {seconds}
            </div>
            
            {scenario === 'monsoon_outage' && (
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(239, 68, 68, 0.08)', border: '1px solid #ef4444', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <span style={{ color: '#ef4444', fontWeight: 'bold', fontSize: '0.8rem', background: '#000', padding: '6px 14px', border: '1px solid #ef4444', borderRadius: '4px' }}>
                  ⚠️ WAN CONNECTIVITY LOST - OFFLINE SQLITE QUEUING ACTIVE
                </span>
              </div>
            )}

          </div>
        </section>

        {/* Dynamic Pitch scorecard */}
        <section className="stats-strip" style={{ marginBottom: '20px' }}>
          <div className="glass-panel stat-card cyan">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600 }}>Pilgrim Transit Load</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value">{visitorCount}</span>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>pax/hr</span>
            </div>
          </div>
          
          <div className="glass-panel stat-card amber">
            <span style={{ fontSize: '0.65rem', color: '#f59e0b', fontWeight: 600 }}>Avg Corridor Compliance</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: complianceScore < 70 ? '#ef4444' : '#f59e0b' }}>{complianceScore.toFixed(1)}%</span>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af' }}>green rating</span>
            </div>
          </div>

          <div className="glass-panel stat-card emerald">
            <span style={{ fontSize: '0.65rem', color: '#10b981', fontWeight: 600 }}>Estimated RTO fine Revenue</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: '#10b981' }}>₹{totalRevenueFines.toLocaleString()}</span>
              <span style={{ fontSize: '0.7rem', color: '#10b981' }}>INR</span>
            </div>
          </div>

          <div className="glass-panel stat-card purple">
            <span style={{ fontSize: '0.65rem', color: '#8b5cf6', fontWeight: 600 }}>Labour Redirection savings</span>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '2px' }}>
              <span className="stat-value" style={{ color: '#8b5cf6' }}>₹{laborSavings.toLocaleString()}</span>
              <span style={{ fontSize: '0.7rem', color: '#8b5cf6' }}>INR</span>
            </div>
          </div>
        </section>

        {/* Twin Chart Layout - Investor & Government Impact Analytics */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '20px' }}>
          
          {/* Chart 1: Air Quality Risk Analytics */}
          <div className="glass-panel" style={{ padding: '20px', height: '320px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Leaf size={14} style={{ color: '#00f0ff' }} /> Environmental Telemetry Prediction Index
              </h4>
              <span style={{ fontSize: '0.65rem', color: aqi > 150 ? '#ef4444' : '#10b981', fontWeight: 'bold' }}>
                AQI: {aqi.toFixed(0)} ({aqi > 150 ? 'UNHEALTHY' : 'MODERATE'})
              </span>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              <Line data={aqiChartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>

          {/* Chart 2: Smart City Financial ROI Analytics */}
          <div className="glass-panel" style={{ padding: '20px', height: '320px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Coins size={14} style={{ color: '#10b981' }} /> Projected Labour Savings Over Time
              </h4>
              <span style={{ fontSize: '0.65rem', color: '#10b981', fontWeight: 'bold' }}>
                Savings: +₹{(laborSavings / 1000).toFixed(0)}k
              </span>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
              <Line data={financeChartData} options={{ responsive: true, maintainAspectRatio: false }} />
            </div>
          </div>

        </div>

        {/* Lower row: Live Ingest & Impact stats */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px' }}>
          
          {/* Live ANPR Logs feed */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Activity size={14} style={{ color: '#00f0ff' }} /> Live Traffic ANPR Simulation feed
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {anprLogs.map((log, idx) => (
                <div 
                  key={idx}
                  style={{ 
                    fontSize: '0.75rem', 
                    padding: '8px 12px', 
                    background: 'rgba(255,255,255,0.01)', 
                    border: '1px solid rgba(255,255,255,0.03)', 
                    borderRadius: '4px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ display: 'flex', gap: '12px' }}>
                    <span style={{ fontWeight: 'bold', color: '#00f0ff' }}>{log.plate}</span>
                    <span style={{ color: '#9ca3af' }}>{log.node}</span>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    <span style={{ 
                      fontSize: '0.65rem',
                      fontWeight: 'bold',
                      color: log.status.includes('Litter') || log.status.includes('Park') || log.status.includes('Declin') ? '#ef4444' : '#10b981'
                    }}>
                      {log.status}
                    </span>
                    <span style={{ color: '#6b7280', fontSize: '0.65rem' }}>{log.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Investment Pitch Analytics */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendingUp size={14} style={{ color: '#8b5cf6' }} /> Business Case & Environmental Returns
            </h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.75rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ color: '#9ca3af' }}>Processed Plates:</span>
                <span style={{ color: '#fff', fontWeight: 'bold' }}>{processedPlatesCount} vehicles</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ color: '#9ca3af' }}>Nagar Panchayat Saves:</span>
                <span style={{ color: '#10b981', fontWeight: 'bold' }}>2.4 tons waste routed</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '6px', borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                <span style={{ color: '#9ca3af' }}>CO2 Carbon Level:</span>
                <span style={{ color: '#f59e0b', fontWeight: 'bold' }}>{carbonLevel.toFixed(0)} ppm</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ color: '#9ca3af' }}>Payback Period:</span>
                <span style={{ color: '#00f0ff', fontWeight: 'bold' }}>~1.5 Months (Pilot Amortization)</span>
              </div>
            </div>

            <div style={{ 
              marginTop: 'auto', 
              padding: '10px 12px', 
              background: 'rgba(139, 92, 246, 0.05)', 
              border: '1px solid rgba(139, 92, 246, 0.2)', 
              borderRadius: '6px',
              fontSize: '0.7rem',
              color: '#c084fc',
              lineHeight: '1.4'
            }}>
              💡 **CPO Summary**: SPEMS demonstrates a clear business model. Penalty revenues fully cover the annual cloud backhaul costs within 12 operating days, redirecting municipal budgets toward active conservation efforts.
            </div>

          </div>

        </div>

      </main>
    </div>
  );
}
