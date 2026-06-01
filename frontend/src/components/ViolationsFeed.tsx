import React from 'react';

export interface ViolationRecord {
  id: number;
  location_id: number;
  camera_id: string;
  plate_number: string | null;
  violation_type: string;
  severity_level: string;
  evidence_image_url: string;
  violation_timestamp: string;
  status: string;
  fine_amount_inr: number;
}

interface ViolationsFeedProps {
  violations: ViolationRecord[];
  onUpdateStatus: (id: number, status: 'APPROVED' | 'DISMISSED' | 'CHALLAN_ISSUED') => void;
}

export default function ViolationsFeed({ violations, onUpdateStatus }: ViolationsFeedProps) {
  
  const getSeverityStyle = (level: string) => {
    switch (level.toUpperCase()) {
      case 'HIGH':
        return { color: '#EF4444', bg: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.2)' };
      case 'MEDIUM':
        return { color: '#F59E0B', bg: 'rgba(245, 158, 11, 0.1)', border: '1px solid rgba(245, 158, 11, 0.2)' };
      default:
        return { color: '#10B981', bg: 'rgba(16, 185, 129, 0.1)', border: '1px solid rgba(16, 185, 129, 0.2)' };
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'CHALLAN_ISSUED': return '#10B981';
      case 'APPROVED': return '#00F0FF';
      case 'DISMISSED': return '#6B7280';
      default: return '#F59E0B';
    }
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h3 style={{ fontSize: '1.1rem', fontWeight: 600 }}>Real-Time Evidence Logs</h3>
        <span style={{ fontSize: '0.75rem', color: '#9ca3af' }}>{violations.length} incidents logged</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto', maxHeight: '420px', paddingRight: '4px' }}>
        {violations.length === 0 ? (
          <div style={{ padding: '40px 0', textAlign: 'center', color: '#6b7280', fontSize: '0.85rem' }}>
            No environmental violations reported in last window.
          </div>
        ) : (
          violations.map((v) => {
            const severity = getSeverityStyle(v.severity_level);
            return (
              <div 
                key={v.id} 
                className="glass-panel" 
                style={{ 
                  padding: '12px', 
                  display: 'grid', 
                  gridTemplateColumns: '80px 1fr', 
                  gap: '12px',
                  background: 'rgba(23, 29, 47, 0.4)',
                  borderColor: 'rgba(255, 255, 255, 0.04)'
                }}
              >
                {/* Crop evidence image */}
                <div style={{ position: 'relative', width: '80px', height: '80px', borderRadius: '6px', overflow: 'hidden', border: '1px solid rgba(255,255,255,0.08)' }}>
                  {/* Fallback to simple image box */}
                  <img 
                    src={v.evidence_image_url.startsWith('/') ? `http://localhost:8000${v.evidence_image_url}` : v.evidence_image_url} 
                    alt="Infraction Evidence"
                    style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                    onError={(e)=>{
                      // Show generic placeholder if API server is offline
                      e.currentTarget.src = 'https://images.unsplash.com/photo-1618220179428-22790b461013?w=150&auto=format&fit=crop';
                    }}
                  />
                </div>

                {/* Details layout */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.8rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 'bold', color: '#fff' }}>
                      {v.violation_type.replace('_', ' ')}
                    </span>
                    <span style={{ fontSize: '0.7rem', color: severity.color, background: severity.bg, border: severity.border, padding: '2px 6px', borderRadius: '4px' }}>
                      {v.severity_level}
                    </span>
                  </div>

                  <div style={{ color: '#9ca3af', fontSize: '0.75rem', display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    <span>📍 Gaurikund Base</span>
                    <span>•</span>
                    <span>📷 {v.camera_id}</span>
                    <span>•</span>
                    <span>🚗 {v.plate_number ? v.plate_number : 'Pedestrian'}</span>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                    <span style={{ color: '#00F0FF', fontWeight: 'bold' }}>
                      ₹{v.fine_amount_inr.toLocaleString('en-IN')}
                    </span>
                    
                    {/* Interactive Challan Control options */}
                    {v.status === 'PENDING' ? (
                      <div style={{ display: 'flex', gap: '6px' }}>
                        <button 
                          onClick={() => onUpdateStatus(v.id, 'APPROVED')}
                          style={{ background: '#1e293b', border: '1px solid #00F0FF30', color: '#00F0FF', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.7rem' }}
                        >
                          Approve
                        </button>
                        <button 
                          onClick={() => onUpdateStatus(v.id, 'DISMISSED')}
                          style={{ background: 'transparent', border: '1px solid rgba(255,255,255,0.08)', color: '#9ca3af', padding: '2px 8px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.7rem' }}
                        >
                          Dismiss
                        </button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: getStatusColor(v.status) }}></span>
                        <span style={{ fontSize: '0.7rem', color: getStatusColor(v.status), fontWeight: 'bold' }}>{v.status}</span>
                        
                        {v.status === 'APPROVED' && (
                          <button 
                            onClick={() => onUpdateStatus(v.id, 'CHALLAN_ISSUED')}
                            style={{ background: '#10B981', border: 'none', color: '#fff', padding: '2px 6px', borderRadius: '4px', cursor: 'pointer', fontSize: '0.7rem', fontWeight: 'bold' }}
                          >
                            Post Challan
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
