import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { 
  Shield, 
  Search, 
  FileText, 
  Check, 
  X, 
  Lock, 
  User, 
  Calendar, 
  MapPin, 
  Activity, 
  Database, 
  TrendingUp, 
  ArrowLeft, 
  AlertCircle, 
  Filter, 
  BarChart2, 
  RefreshCw, 
  FileDown,
  LockKeyhole
} from 'lucide-react';
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ArcElement } from 'chart.js';
import { Bar, Doughnut } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend);

interface ViolationRecord {
  id: number;
  camera_id: string;
  plate_number: string | null;
  violation_type: string;
  severity_level: string;
  fine_amount_inr: number;
  violation_timestamp: string;
  status: 'PENDING' | 'APPROVED' | 'DISMISSED';
  challan_reference: string | null;
  evidence_image_url: string | null;
  evidence_hash: string | null;
}

interface AuditLogRecord {
  id: number;
  violation_id: number;
  action_taken: string;
  action_timestamp: string;
  officer_badge: string;
  notes: string | null;
  client_ip: string;
}

export default function OfficerPortal() {
  // Login State
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [badgeId, setBadgeId] = useState('UK-POL-7718');
  const [pin, setPin] = useState('7718');
  const [loginError, setLoginError] = useState('');

  // Dashboard Data State
  const [violations, setViolations] = useState<ViolationRecord[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLogRecord[]>([]);
  const [selectedViolation, setSelectedViolation] = useState<ViolationRecord | null>(null);
  const [verificationResult, setVerificationResult] = useState<{ status: string; match: boolean; hash: string } | null>(null);
  const [historyLogs, setHistoryLogs] = useState<AuditLogRecord[]>([]);
  
  // Loading & Action states
  const [loading, setLoading] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionModal, setActionModal] = useState<{ show: boolean; type: 'APPROVE' | 'DISMISS'; notes: string } | null>(null);
  const [pdfLayout, setPdfLayout] = useState<{ show: boolean; layout: string; filename: string } | null>(null);

  // Filter States
  const [activeTab, setActiveTab] = useState<'queue' | 'audit' | 'analytics'>('queue');
  const [queueSubTab, setQueueSubTab] = useState<'PENDING' | 'APPROVED' | 'DISMISSED'>('PENDING');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('ALL');
  const [filterSeverity, setFilterSeverity] = useState('ALL');

  // Fetch Violations
  const fetchViolations = async () => {
    setLoading(true);
    try {
      const res = await fetch('http://localhost:8000/api/v1/violations');
      if (res.ok) {
        const data = await res.json();
        setViolations(data);
      }
    } catch (e) {
      console.error("Error fetching violations:", e);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Audit Logs
  const fetchAuditLogs = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/violations/audit-logs');
      if (res.ok) {
        const data = await res.json();
        setAuditLogs(data);
      }
    } catch (e) {
      console.error("Error fetching global audit logs:", e);
    }
  };

  // Run initial state checks
  useEffect(() => {
    if (isLoggedIn) {
      fetchViolations();
      fetchAuditLogs();
    }
  }, [isLoggedIn]);

  // Fetch selected violation dependencies (verification, history)
  useEffect(() => {
    if (selectedViolation) {
      verifyEvidence(selectedViolation.id);
      fetchViolationHistory(selectedViolation.id);
    } else {
      setVerificationResult(null);
      setHistoryLogs([]);
    }
  }, [selectedViolation]);

  // Cryptographic evidence integrity check
  const verifyEvidence = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/violations/${id}/verify`);
      if (res.ok) {
        const data = await res.json();
        setVerificationResult(data);
      }
    } catch (e) {
      console.error("Error verifying evidence seal:", e);
      setVerificationResult(null);
    }
  };

  // Fetch history for a single violation
  const fetchViolationHistory = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/violations/${id}/history`);
      if (res.ok) {
        const data = await res.json();
        setHistoryLogs(data);
      }
    } catch (e) {
      console.error("Error fetching ticket audit logs:", e);
    }
  };

  // Handle Login submission
  const handleLogin = (e: React.FormEvent) => {
    e.preventDefault();
    if (badgeId === 'UK-POL-7718' && pin === '7718') {
      setIsLoggedIn(true);
      setLoginError('');
    } else {
      setLoginError('Invalid Badge ID or Security PIN credential.');
    }
  };

  // Process case decision action
  const handleDecisionSubmit = async () => {
    if (!selectedViolation || !actionModal) return;
    setActionLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/v1/violations/${selectedViolation.id}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action: actionModal.type,
          officer_badge: badgeId,
          notes: actionModal.notes || `Processed by officer on command terminal.`
        })
      });

      if (res.ok) {
        const updated = await res.json();
        // Update local list state
        setViolations(prev => prev.map(v => v.id === updated.id ? updated : v));
        setSelectedViolation(updated);
        fetchAuditLogs();
        setActionModal(null);
      }
    } catch (e) {
      console.error("Error posting review decision:", e);
    } finally {
      setActionLoading(false);
    }
  };

  // Export PDF template content from API
  const handleDownloadPdf = async (id: number) => {
    try {
      const res = await fetch(`http://localhost:8000/api/v1/violations/${id}/pdf`);
      if (res.ok) {
        const data = await res.json();
        setPdfLayout({
          show: true,
          layout: data.pdf_ascii_layout,
          filename: data.filename
        });
      }
    } catch (e) {
      console.error("Error downloading ASCII PDF layout:", e);
    }
  };

  // Trigger browser text file download for ASCII legal sheet
  const triggerTextDownload = () => {
    if (!pdfLayout) return;
    const element = document.createElement("a");
    const file = new Blob([pdfLayout.layout], {type: 'text/plain'});
    element.href = URL.createObjectURL(file);
    element.download = pdfLayout.filename;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  // Filter queues logic
  const filteredViolations = violations.filter(v => {
    if (v.status !== queueSubTab) return false;
    
    // Search filter
    const matchesSearch = v.plate_number?.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          v.camera_id.toLowerCase().includes(searchTerm.toLowerCase());
    
    // Type filter
    const matchesType = filterType === 'ALL' || v.violation_type === filterType;

    // Severity filter
    const matchesSeverity = filterSeverity === 'ALL' || v.severity_level === filterSeverity;

    return matchesSearch && matchesType && matchesSeverity;
  });

  // Calculate quick stats counters
  const totalCount = violations.length;
  const pendingCount = violations.filter(v => v.status === 'PENDING').length;
  const approvedCount = violations.filter(v => v.status === 'APPROVED').length;
  const dismissedCount = violations.filter(v => v.status === 'DISMISSED').length;

  // Charting parameters
  const violationsByType = violations.reduce((acc: Record<string, number>, curr) => {
    const typeLabel = curr.violation_type.replace(/_/g, ' ');
    acc[typeLabel] = (acc[typeLabel] || 0) + 1;
    return acc;
  }, {});

  const typeChartData = {
    labels: Object.keys(violationsByType),
    datasets: [{
      data: Object.values(violationsByType),
      backgroundColor: ['rgba(0, 240, 255, 0.65)', 'rgba(139, 92, 246, 0.65)', 'rgba(245, 158, 11, 0.65)', 'rgba(239, 68, 68, 0.65)', 'rgba(16, 185, 129, 0.65)'],
      borderColor: ['#00f0ff', '#8b5cf6', '#f59e0b', '#ef4444', '#10b981'],
      borderWidth: 1
    }]
  };

  const violationsByCamera = violations.reduce((acc: Record<string, number>, curr) => {
    acc[curr.camera_id] = (acc[curr.camera_id] || 0) + 1;
    return acc;
  }, {});

  const cameraChartData = {
    labels: Object.keys(violationsByCamera),
    datasets: [{
      label: 'Infraction Events',
      data: Object.values(violationsByCamera),
      backgroundColor: 'rgba(0, 240, 255, 0.15)',
      borderColor: '#00f0ff',
      borderWidth: 1.5
    }]
  };

  // Renders the Login view screen
  if (!isLoggedIn) {
    return (
      <div className="dashboard-layout" style={{ justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#020307' }}>
        <Head>
          <title>Officer Security Portal | Uttarakhand State Gov</title>
        </Head>

        <form onSubmit={handleLogin} className="glass-panel" style={{ width: '100%', maxWidth: '400px', padding: '40px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div style={{ textAlign: 'center', marginBottom: '10px' }}>
            <div style={{ display: 'inline-flex', padding: '12px', borderRadius: '50%', background: 'rgba(0, 240, 255, 0.05)', border: '1px solid rgba(0, 240, 255, 0.2)', marginBottom: '16px' }}>
              <Shield size={36} style={{ color: '#00f0ff' }} />
            </div>
            <h1 className="brand-font" style={{ fontSize: '1.4rem', fontWeight: 800, color: '#fff' }}>SPEMS Verification Portal</h1>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af', marginTop: '6px' }}>Enforcement Officer Secure Terminal Login</p>
          </div>

          {loginError && (
            <div style={{ padding: '10px 12px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: '6px', color: '#ef4444', fontSize: '0.75rem', display: 'flex', gap: '8px', alignItems: 'center' }}>
              <AlertCircle size={14} />
              <span>{loginError}</span>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Officer Badge ID</label>
            <div style={{ position: 'relative' }}>
              <User size={14} style={{ position: 'absolute', left: '12px', top: '12px', color: '#6b7280' }} />
              <input 
                type="text" 
                value={badgeId} 
                onChange={(e) => setBadgeId(e.target.value)}
                placeholder="UK-POL-XXXX" 
                required
                style={{ width: '100%', background: '#04060b', border: '1px solid rgba(255,255,255,0.08)', padding: '10px 12px 10px 36px', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }} 
              />
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Security Access PIN</label>
            <div style={{ position: 'relative' }}>
              <LockKeyhole size={14} style={{ position: 'absolute', left: '12px', top: '12px', color: '#6b7280' }} />
              <input 
                type="password" 
                value={pin} 
                onChange={(e) => setPin(e.target.value)}
                placeholder="••••" 
                required
                style={{ width: '100%', background: '#04060b', border: '1px solid rgba(255,255,255,0.08)', padding: '10px 12px 10px 36px', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }} 
              />
            </div>
          </div>

          <button type="submit" className="action-btn active" style={{ width: '100%', padding: '10px 0', marginTop: '10px', fontSize: '0.85rem', display: 'flex', justifyContent: 'center', gap: '8px' }}>
            <Lock size={14} /> Validate Credentials
          </button>
          
          <div style={{ textAlign: 'center', marginTop: '6px' }}>
            <Link href="/" style={{ color: '#00f0ff', fontSize: '0.75rem', textDecoration: 'none' }}>
              ← Return to Main Operations Desk
            </Link>
          </div>
        </form>
      </div>
    );
  }

  // Renders the logged-in case management portal
  return (
    <div className="dashboard-layout">
      <Head>
        <title>Government Case Management Portal | SPEMS</title>
      </Head>

      {/* Main Sidebar Navigation Panel */}
      <aside className="sidebar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '1.8rem', textShadow: '0 0 10px rgba(0,240,255,0.4)' }}>🕉️</span>
          <div>
            <h1 className="brand-font" style={{ fontSize: '1.25rem', fontWeight: 800, color: '#fff', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '6px' }}>
              SPEMS
              <span style={{ fontSize: '0.65rem', background: '#00F0FF', color: '#000', padding: '1px 4px', borderRadius: '3px', fontWeight: 'bold' }}>LAW</span>
            </h1>
            <span style={{ fontSize: '0.65rem', color: '#00F0FF', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>OFFICER CONSOLE</span>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1, marginTop: '20px' }}>
          <div 
            onClick={() => setActiveTab('queue')}
            style={{ 
              background: activeTab === 'queue' ? 'rgba(0, 240, 255, 0.08)' : 'transparent', 
              border: activeTab === 'queue' ? '1px solid rgba(0, 240, 255, 0.25)' : '1px solid transparent', 
              color: activeTab === 'queue' ? '#fff' : '#9ca3af', 
              padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' 
            }}
          >
            <Shield size={14} style={{ color: activeTab === 'queue' ? '#00F0FF' : '#9ca3af' }} /> Case Review Queue
          </div>

          <div 
            onClick={() => setActiveTab('audit')}
            style={{ 
              background: activeTab === 'audit' ? 'rgba(0, 240, 255, 0.08)' : 'transparent', 
              border: activeTab === 'audit' ? '1px solid rgba(0, 240, 255, 0.25)' : '1px solid transparent', 
              color: activeTab === 'audit' ? '#fff' : '#9ca3af', 
              padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' 
            }}
          >
            <Database size={14} style={{ color: activeTab === 'audit' ? '#00F0FF' : '#9ca3af' }} /> System Audit Logs
          </div>

          <div 
            onClick={() => setActiveTab('analytics')}
            style={{ 
              background: activeTab === 'analytics' ? 'rgba(0, 240, 255, 0.08)' : 'transparent', 
              border: activeTab === 'analytics' ? '1px solid rgba(0, 240, 255, 0.25)' : '1px solid transparent', 
              color: activeTab === 'analytics' ? '#fff' : '#9ca3af', 
              padding: '10px 14px', borderRadius: '8px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' 
            }}
          >
            <BarChart2 size={14} style={{ color: activeTab === 'analytics' ? '#00F0FF' : '#9ca3af' }} /> Search & Analytics
          </div>
        </nav>

        {/* User Badging */}
        <div className="glass-panel" style={{ padding: '14px', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <div style={{ background: '#10b981', width: '8px', height: '8px', borderRadius: '50%', boxShadow: '0 0 8px #10b981' }} />
          <div style={{ display: 'flex', flexDirection: 'column' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', color: '#fff' }}>Badge: {badgeId}</span>
            <span style={{ fontSize: '0.6rem', color: '#9ca3af' }}>Rudraprayag Station Pool</span>
          </div>
        </div>

        <div style={{ textAlign: 'center', padding: '10px 0' }}>
          <Link href="/" style={{ color: '#ef4444', fontSize: '0.75rem', textDecoration: 'none', fontWeight: 'bold' }}>
            Logout Security Session
          </Link>
        </div>
      </aside>

      {/* Main Core Content Pane */}
      <main className="main-content">
        <header className="dashboard-header">
          <div>
            <h2 className="brand-font" style={{ fontSize: '1.5rem', fontWeight: 700, color: '#fff' }}>Government Enforcement Portal</h2>
            <p style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Legal Verification, Case Reviews & Official NIC Challan Dispatch Engine</p>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button onClick={fetchViolations} className="action-btn" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem' }}>
              <RefreshCw size={12} /> Sync DB Registry
            </button>
            <Link href="/" className="action-btn active" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.75rem', textDecoration: 'none' }}>
              <ArrowLeft size={12} /> Operator HUD
            </Link>
          </div>
        </header>

        {/* Dashboard scorecard */}
        <section className="stats-strip" style={{ marginBottom: '20px' }}>
          <div className="glass-panel stat-card cyan">
            <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 600, textTransform: 'uppercase' }}>Total Infractions Logged</span>
            <h3 className="stat-value">{totalCount}</h3>
          </div>
          <div className="glass-panel stat-card amber">
            <span style={{ fontSize: '0.65rem', color: '#f59e0b', fontWeight: 600, textTransform: 'uppercase' }}>Awaiting Review (Pending)</span>
            <h3 className="stat-value" style={{ color: '#f59e0b' }}>{pendingCount}</h3>
          </div>
          <div className="glass-panel stat-card emerald">
            <span style={{ fontSize: '0.65rem', color: '#10b981', fontWeight: 600, textTransform: 'uppercase' }}>Approved (NIC Dispatched)</span>
            <h3 className="stat-value" style={{ color: '#10b981' }}>{approvedCount}</h3>
          </div>
          <div className="glass-panel stat-card purple">
            <span style={{ fontSize: '0.65rem', color: '#8b5cf6', fontWeight: 600, textTransform: 'uppercase' }}>Dismissed (Canceled)</span>
            <h3 className="stat-value" style={{ color: '#8b5cf6' }}>{dismissedCount}</h3>
          </div>
        </section>

        {/* Tab 1: Case Review Queue */}
        {activeTab === 'queue' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '20px', minHeight: '600px' }}>
            
            {/* Left Column: Tickets List */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* Filter controls */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div style={{ display: 'flex', gap: '6px', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '10px' }}>
                  {(['PENDING', 'APPROVED', 'DISMISSED'] as const).map(tab => (
                    <button 
                      key={tab}
                      onClick={() => { setQueueSubTab(tab); setSelectedViolation(null); }}
                      className={`action-btn ${queueSubTab === tab ? 'active' : ''}`}
                      style={{ padding: '6px 14px', fontSize: '0.75rem', textTransform: 'capitalize' }}
                    >
                      {tab.toLowerCase()} Queue ({violations.filter(v => v.status === tab).length})
                    </button>
                  ))}
                </div>

                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ position: 'relative', flex: 1 }}>
                    <Search size={14} style={{ position: 'absolute', left: '10px', top: '10px', color: '#6b7280' }} />
                    <input 
                      type="text" 
                      placeholder="Search plate or camera node..." 
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      style={{ width: '100%', background: 'rgba(0,0,0,0.2)', border: '1px solid rgba(255,255,255,0.06)', padding: '8px 12px 8px 30px', borderRadius: '6px', color: '#fff', fontSize: '0.75rem' }}
                    />
                  </div>
                  <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                    <Filter size={12} style={{ color: '#9ca3af' }} />
                    <select 
                      value={filterType} 
                      onChange={(e) => setFilterType(e.target.value)}
                      style={{ background: '#020306', border: '1px solid rgba(255,255,255,0.06)', color: '#fff', fontSize: '0.75rem', padding: '8px 10px', borderRadius: '6px' }}
                    >
                      <option value="ALL">All Types</option>
                      <option value="Restricted_Zone_Entry">Restricted Parking</option>
                      <option value="Littering">Littering Detection</option>
                      <option value="Speed_Infraction">Speed Infraction</option>
                      <option value="Water_Boundary_Violation">River Contamination</option>
                    </select>
                    <select 
                      value={filterSeverity} 
                      onChange={(e) => setFilterSeverity(e.target.value)}
                      style={{ background: '#020306', border: '1px solid rgba(255,255,255,0.06)', color: '#fff', fontSize: '0.75rem', padding: '8px 10px', borderRadius: '6px' }}
                    >
                      <option value="ALL">All Severities</option>
                      <option value="LOW">Low</option>
                      <option value="MEDIUM">Medium</option>
                      <option value="HIGH">High</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Items List */}
              <div style={{ flex: 1, overflowY: 'auto', maxHeight: '550px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {loading ? (
                  <div style={{ textAlign: 'center', padding: '40px 0', color: '#9ca3af', fontSize: '0.8rem' }}>
                    Awaiting server response...
                  </div>
                ) : filteredViolations.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280', fontSize: '0.8rem' }}>
                    No infractions found matching search parameters.
                  </div>
                ) : (
                  filteredViolations.map(v => (
                    <div 
                      key={v.id}
                      onClick={() => setSelectedViolation(v)}
                      style={{ 
                        background: selectedViolation?.id === v.id ? 'rgba(0, 240, 255, 0.05)' : 'rgba(255, 255, 255, 0.01)',
                        border: selectedViolation?.id === v.id ? '1px solid #00f0ff' : '1px solid rgba(255, 255, 255, 0.04)',
                        padding: '12px 16px',
                        borderRadius: '6px',
                        cursor: 'pointer',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <span style={{ fontSize: '0.85rem', fontWeight: 'bold', color: '#fff' }}>{v.plate_number || 'PEDESTRIAN'}</span>
                          <span style={{ 
                            fontSize: '0.6rem', 
                            padding: '1px 6px', 
                            borderRadius: '3px',
                            background: v.severity_level === 'HIGH' ? 'rgba(239, 68, 68, 0.15)' : v.severity_level === 'MEDIUM' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: v.severity_level === 'HIGH' ? '#ef4444' : v.severity_level === 'MEDIUM' ? '#f59e0b' : '#10b981',
                            fontWeight: 'bold'
                          }}>
                            {v.severity_level}
                          </span>
                        </div>
                        <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>{v.violation_type.replace(/_/g, ' ')} | Node: {v.camera_id}</span>
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '2px' }}>
                        <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#00f0ff' }}>₹{v.fine_amount_inr}</span>
                        <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>
                          {new Date(v.violation_timestamp).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' })}
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Right Column: Evidence & Case Details Panel */}
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {selectedViolation ? (
                <>
                  <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                      <h4 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>Case Audit ID: #{selectedViolation.id}</h4>
                      <p style={{ fontSize: '0.7rem', color: '#9ca3af' }}>Logged: {new Date(selectedViolation.violation_timestamp).toLocaleString()}</p>
                    </div>
                    {selectedViolation.challan_reference && (
                      <span style={{ fontSize: '0.65rem', background: 'rgba(16,185,129,0.1)', border: '1px solid #10b981', color: '#10b981', padding: '2px 8px', borderRadius: '4px', fontFamily: 'monospace', fontWeight: 'bold' }}>
                        {selectedViolation.challan_reference}
                      </span>
                    )}
                  </div>

                  {/* Cryptographic Seal Verification badge */}
                  {verificationResult && (
                    <div style={{ 
                      padding: '10px 14px', 
                      background: verificationResult.match ? 'rgba(16, 185, 129, 0.06)' : 'rgba(239, 68, 68, 0.06)',
                      border: verificationResult.match ? '1px solid rgba(16, 185, 129, 0.2)' : '1px solid rgba(239, 68, 68, 0.2)',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      fontSize: '0.7rem'
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Shield size={14} style={{ color: verificationResult.match ? '#10b981' : '#ef4444' }} />
                        <span style={{ color: '#fff', fontWeight: 'bold' }}>Cryptographic Proof Seal:</span>
                        <span style={{ color: verificationResult.match ? '#10b981' : '#ef4444' }}>
                          {verificationResult.match ? 'VERIFIED (SECURE)' : 'SEAL INTEGRITY BROKEN'}
                        </span>
                      </div>
                      <span style={{ fontFamily: 'monospace', color: '#6b7280', fontSize: '0.6rem' }}>
                        {verificationResult.hash.slice(0, 8)}...
                      </span>
                    </div>
                  )}

                  {/* Evidence Display Panel */}
                  <div style={{ position: 'relative', height: '220px', borderRadius: '6px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.06)', background: '#030408' }}>
                    {selectedViolation.evidence_image_url ? (
                      <img src={`http://localhost:8000${selectedViolation.evidence_image_url}`} style={{ width: '100%', height: '100%', objectFit: 'cover' }} alt="Violation Visual Proof" />
                    ) : (
                      <div style={{ width: '100%', height: '100%', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '8px', color: '#6b7280' }}>
                        <AlertCircle size={24} />
                        <span style={{ fontSize: '0.75rem' }}>Visual camera crop missing.</span>
                      </div>
                    )}
                    <div style={{ position: 'absolute', bottom: '8px', left: '8px', padding: '4px 8px', borderRadius: '4px', background: 'rgba(0,0,0,0.85)', color: '#fff', fontSize: '0.6rem', border: '1px solid rgba(255,255,255,0.08)' }}>
                      🔒 CRYPTO LEAD SEAL: {selectedViolation.evidence_hash ? selectedViolation.evidence_hash.slice(0, 16) : 'NULL'}
                    </div>
                  </div>

                  {/* Core Details Grid */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', fontSize: '0.75rem' }}>
                    <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.6rem' }}>License Plate</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>{selectedViolation.plate_number || 'N/A (Pedestrian)'}</span>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.6rem' }}>Fine Assessment</span>
                      <span style={{ color: '#00f0ff', fontWeight: 'bold' }}>₹{selectedViolation.fine_amount_inr} INR</span>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.6rem' }}>Inference Camera Node</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>{selectedViolation.camera_id}</span>
                    </div>
                    <div style={{ padding: '8px 10px', background: 'rgba(255,255,255,0.02)', borderRadius: '4px' }}>
                      <span style={{ color: '#9ca3af', display: 'block', fontSize: '0.6rem' }}>Location Area</span>
                      <span style={{ color: '#fff', fontWeight: 'bold' }}>Gaurikund Zone A</span>
                    </div>
                  </div>

                  {/* History & Case logs sub-section */}
                  {historyLogs.length > 0 && (
                    <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
                      <span style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', display: 'block', marginBottom: '8px' }}>Action Log History</span>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', maxHeight: '100px', overflowY: 'auto' }}>
                        {historyLogs.map(log => (
                          <div key={log.id} style={{ fontSize: '0.65rem', padding: '6px 8px', background: 'rgba(255,255,255,0.01)', borderRadius: '4px', display: 'flex', justifyContent: 'space-between' }}>
                            <div>
                              <span style={{ color: '#fff', fontWeight: 'bold' }}>{log.action_taken}</span>
                              <span style={{ color: '#9ca3af' }}> by {log.officer_badge}</span>
                              {log.notes && <p style={{ color: '#6b7280', margin: '2px 0 0 0', fontSize: '0.6rem' }}>"{log.notes}"</p>}
                            </div>
                            <span style={{ color: '#6b7280' }}>
                              {new Date(log.action_timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Decision Controls */}
                  <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '16px', display: 'flex', gap: '10px' }}>
                    {selectedViolation.status === 'PENDING' ? (
                      <>
                        <button 
                          onClick={() => setActionModal({ show: true, type: 'APPROVE', notes: '' })}
                          className="action-btn active" 
                          style={{ flex: 1, padding: '10px 0', fontSize: '0.8rem', display: 'flex', justifyContent: 'center', gap: '6px', background: '#10b981', border: '1px solid #10b981' }}
                        >
                          <Check size={14} /> Approve & Issue Challan
                        </button>
                        <button 
                          onClick={() => setActionModal({ show: true, type: 'DISMISS', notes: '' })}
                          className="action-btn" 
                          style={{ flex: 1, padding: '10px 0', fontSize: '0.8rem', display: 'flex', justifyContent: 'center', gap: '6px', color: '#ef4444', borderColor: 'rgba(239,68,68,0.3)' }}
                        >
                          <X size={14} /> Dismiss Violation
                        </button>
                      </>
                    ) : (
                      <button 
                        onClick={() => handleDownloadPdf(selectedViolation.id)}
                        className="action-btn active" 
                        style={{ width: '100%', padding: '10px 0', fontSize: '0.8rem', display: 'flex', justifyContent: 'center', gap: '6px' }}
                      >
                        <FileDown size={14} /> Export Court Evidence Challan
                      </button>
                    )}
                  </div>
                </>
              ) : (
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', gap: '10px', color: '#6b7280' }}>
                  <FileText size={32} />
                  <span style={{ fontSize: '0.8rem' }}>Select an infraction ticket from the queue list to audit evidence.</span>
                </div>
              )}
            </div>

          </div>
        )}

        {/* Tab 2: System Audit Logs */}
        {activeTab === 'audit' && (
          <div className="glass-panel" style={{ padding: '24px', minHeight: '600px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px' }}>
              <h3 className="brand-font" style={{ fontSize: '1.2rem', fontWeight: 700, color: '#fff' }}>Unified System Audit Trail</h3>
              <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginTop: '4px' }}>Real-time logging of officer decisions, database modifications, and client signature seals.</p>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', maxHeight: '550px' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', textAlign: 'left' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#9ca3af' }}>
                    <th style={{ padding: '10px' }}>Timestamp</th>
                    <th style={{ padding: '10px' }}>Case ID</th>
                    <th style={{ padding: '10px' }}>Action</th>
                    <th style={{ padding: '10px' }}>Officer ID</th>
                    <th style={{ padding: '10px' }}>Terminal IP</th>
                    <th style={{ padding: '10px' }}>Enforcement Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.length === 0 ? (
                    <tr>
                      <td colSpan={6} style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>No audit actions committed in this log window.</td>
                    </tr>
                  ) : (
                    auditLogs.map(log => (
                      <tr key={log.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', color: '#fff' }}>
                        <td style={{ padding: '10px', color: '#9ca3af' }}>{new Date(log.action_timestamp).toLocaleString()}</td>
                        <td style={{ padding: '10px', color: '#00f0ff', fontWeight: 'bold' }}>#{log.violation_id}</td>
                        <td style={{ padding: '10px' }}>
                          <span style={{ 
                            fontSize: '0.65rem', 
                            padding: '2px 6px', 
                            borderRadius: '3px',
                            background: log.action_taken === 'APPROVE' ? 'rgba(16,185,129,0.15)' : 'rgba(239,68,68,0.15)',
                            color: log.action_taken === 'APPROVE' ? '#10b981' : '#ef4444',
                            fontWeight: 'bold'
                          }}>
                            {log.action_taken}D
                          </span>
                        </td>
                        <td style={{ padding: '10px' }}>{log.officer_badge}</td>
                        <td style={{ padding: '10px', fontFamily: 'monospace', color: '#6b7280' }}>{log.client_ip}</td>
                        <td style={{ padding: '10px', color: '#9ca3af' }}>{log.notes || 'N/A'}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab 3: Search and Analytics */}
        {activeTab === 'analytics' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Quick Metrics charts */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              <div className="glass-panel" style={{ padding: '24px', height: '340px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff' }}>Violation Category Breakdown</h4>
                <div style={{ flex: 1, position: 'relative', display: 'flex', justifyContent: 'center' }}>
                  {violations.length > 0 ? (
                    <Doughnut data={typeChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                  ) : (
                    <span style={{ alignSelf: 'center', fontSize: '0.8rem', color: '#6b7280' }}>Waiting for database logs...</span>
                  )}
                </div>
              </div>

              <div className="glass-panel" style={{ padding: '24px', height: '340px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <h4 style={{ fontSize: '0.9rem', fontWeight: 'bold', color: '#fff' }}>Violation Counts by Camera Node</h4>
                <div style={{ flex: 1, position: 'relative' }}>
                  {violations.length > 0 ? (
                    <Bar data={cameraChartData} options={{ responsive: true, maintainAspectRatio: false }} />
                  ) : (
                    <span style={{ alignSelf: 'center', fontSize: '0.8rem', color: '#6b7280' }}>Waiting for database logs...</span>
                  )}
                </div>
              </div>
            </div>

            {/* General Database Query panel */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 className="brand-font" style={{ fontSize: '1.1rem', fontWeight: 700, color: '#fff', marginBottom: '12px' }}>Operational Query Panel</h3>
              <p style={{ fontSize: '0.75rem', color: '#9ca3af', marginBottom: '16px' }}>Filter global state data to check historical vehicle plates, eco-standards, and RTO registration details.</p>
              
              <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                <div style={{ flex: 1, minWidth: '200px', display: 'flex', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: '6px', overflow: 'hidden' }}>
                  <span style={{ padding: '8px 12px', background: 'rgba(255,255,255,0.03)', color: '#9ca3af', fontSize: '0.75rem' }}>Registry Query</span>
                  <input type="text" placeholder="Enter Registration Mark (e.g. UK07TA1230)" style={{ flex: 1, border: 'none', background: 'transparent', color: '#fff', fontSize: '0.75rem', padding: '0 10px' }} />
                </div>
                <button className="action-btn active" style={{ padding: '8px 20px', fontSize: '0.75rem' }}>Execute Search</button>
              </div>
            </div>
          </div>
        )}

      </main>

      {/* Decision Action Modal overlay */}
      {actionModal && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '460px', padding: '30px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <h3 style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>
              {actionModal.type === 'APPROVE' ? '✓ Approve & Dispatch E-Challan' : '⚠️ Dismiss Infraction Violation'}
            </h3>
            <p style={{ fontSize: '0.75rem', color: '#9ca3af', lineHeight: '1.4' }}>
              {actionModal.type === 'APPROVE' 
                ? 'Approving this case will generate a unique e-challan reference, sync state registries, and dispatch the fine to the vehicle owner.'
                : 'Dismissing this case will clear the violation record state and restore compliance points to the vehicle\'s score index.'}
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold' }}>Enforcement Officer Notes</label>
              <textarea 
                rows={3}
                placeholder="Enter justification notes..."
                value={actionModal.notes}
                onChange={(e) => setActionModal({ ...actionModal, notes: e.target.value })}
                style={{ width: '100%', background: '#04060b', border: '1px solid rgba(255,255,255,0.08)', padding: '8px 10px', borderRadius: '6px', color: '#fff', fontSize: '0.75rem', resize: 'none' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
              <button 
                onClick={handleDecisionSubmit}
                disabled={actionLoading}
                className="action-btn active"
                style={{ flex: 1, padding: '10px 0', fontSize: '0.8rem', background: actionModal.type === 'APPROVE' ? '#10b981' : '#ef4444', borderColor: actionModal.type === 'APPROVE' ? '#10b981' : '#ef4444' }}
              >
                {actionLoading ? 'Processing...' : 'Confirm Action'}
              </button>
              <button 
                onClick={() => setActionModal(null)}
                disabled={actionLoading}
                className="action-btn"
                style={{ flex: 1, padding: '10px 0', fontSize: '0.8rem' }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* PDF ASCII Preview Modal overlay */}
      {pdfLayout && (
        <div style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1000, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="glass-panel" style={{ width: '100%', maxWidth: '750px', padding: '30px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '12px' }}>
              <h3 style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#fff' }}>NIC Legal Evidence Sheet - ASCII Layout</h3>
              <button onClick={() => setPdfLayout(null)} className="action-btn" style={{ padding: '2px 8px', fontSize: '0.7rem' }}>Close</button>
            </div>
            
            <pre style={{
              background: '#04060b',
              border: '1px solid rgba(255,255,255,0.06)',
              padding: '16px',
              borderRadius: '6px',
              fontFamily: 'monospace',
              fontSize: '0.65rem',
              color: '#10b981',
              overflowY: 'auto',
              maxHeight: '380px',
              whiteSpace: 'pre-wrap',
              lineHeight: '1.3'
            }}>
              {pdfLayout.layout}
            </pre>

            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end', marginTop: '10px' }}>
              <button onClick={triggerTextDownload} className="action-btn active" style={{ padding: '8px 20px', fontSize: '0.75rem', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <FileDown size={14} /> Download Challan File
              </button>
              <button onClick={() => setPdfLayout(null)} className="action-btn" style={{ padding: '8px 20px', fontSize: '0.75rem' }}>Dismiss</button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
