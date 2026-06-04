import React, { useEffect, useState } from 'react';
import { Leaf, RefreshCw, Compass, ShieldAlert, Coins, Trees, AlertTriangle } from 'lucide-react';

interface Segment {
  vehicle_type: string;
  emission_standard: string;
  transits_count: int;
  co2_emitted_kg: number;
  pm_emitted_g: number;
}

interface EmissionsData {
  total_vehicles: number;
  total_transits: number;
  corridor_distance_km: number;
  total_co2_kg: number;
  total_pm_g: number;
  trees_offset_required: number;
  offset_cost_inr: number;
  idle_savings_kg: number;
  segments: Segment[];
}

interface HistoryRecord {
  id: number;
  calculated_at: string;
  total_vehicles: number;
  total_transits: number;
  total_co2_kg: number;
  total_pm_g: number;
  trees_offset: number;
  offset_cost_inr: number;
  idle_savings_kg: number;
}

export default function EmissionsCalculator() {
  const [data, setData] = useState<EmissionsData | null>(null);
  const [history, setHistory] = useState<HistoryRecord[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEmissions = async (saveToHistory = false) => {
    setLoading(true);
    setError(null);
    try {
      // 1. Fetch current calculator metrics
      const res = await fetch(`http://localhost:8000/api/v1/compliance/emissions/calculate?save_to_history=${saveToHistory}`);
      if (res.ok) {
        const result = await res.json();
        setData(result);
      } else {
        setError("Calculation endpoint returned an error.");
      }

      // 2. Fetch history records
      const histRes = await fetch("http://localhost:8000/api/v1/compliance/emissions/history?limit=5");
      if (histRes.ok) {
        const histResult = await histRes.json();
        setHistory(histResult);
      }
    } catch (err) {
      setError("Failed to connect to emissions calculator API.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEmissions(false);
  }, []);

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '10px' }}>
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Leaf size={16} style={{ color: '#10b981' }} /> Carbon Footprint & Offsets
          </h3>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Char Dham Transit Emissions Analytics</span>
        </div>
        <button 
          onClick={() => fetchEmissions(true)} 
          disabled={loading}
          className="action-btn"
          style={{ padding: '6px 10px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '6px' }}
        >
          <RefreshCw size={10} className={loading ? "spin" : ""} /> {loading ? "Computing..." : "Run Calculator"}
        </button>
      </div>

      {error && (
        <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '6px', color: '#ef4444', fontSize: '0.7rem', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      {data ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {/* Main emissions stats grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            <div style={{ padding: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.6rem', color: '#9ca3af', textTransform: 'uppercase', display: 'block' }}>Carbon Footprint</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{data.total_co2_kg.toFixed(2)} <span style={{ fontSize: '0.75rem', color: '#ef4444' }}>kg CO2e</span></span>
            </div>
            <div style={{ padding: '10px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.04)', borderRadius: '6px' }}>
              <span style={{ fontSize: '0.6rem', color: '#9ca3af', textTransform: 'uppercase', display: 'block' }}>Particulate Output</span>
              <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{data.total_pm_g.toFixed(2)} <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>grams PM</span></span>
            </div>
          </div>

          {/* Offset recommendations cards */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', background: 'rgba(16, 185, 129, 0.03)', border: '1px solid rgba(16, 185, 129, 0.1)', padding: '12px', borderRadius: '6px' }}>
            <span style={{ fontSize: '0.7rem', color: '#10b981', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Trees size={12} /> Local Offset Recommendations
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '0.75rem', color: '#e5e7eb' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '4px' }}>
                <span style={{ color: '#9ca3af' }}>🌲 Reforestation Target:</span>
                <span style={{ fontWeight: 'bold', color: '#fff' }}>{data.trees_offset_required} Deodar/Oak saplings</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid rgba(255,255,255,0.04)', paddingBottom: '4px' }}>
                <span style={{ color: '#9ca3af' }}>💰 Fund Allocation:</span>
                <span style={{ fontWeight: 'bold', color: '#10b981' }}>INR {data.offset_cost_inr.toLocaleString()}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '2px' }}>
                <span style={{ color: '#9ca3af' }}>🛑 Idle-Reduction Savings:</span>
                <span style={{ fontWeight: 'bold', color: '#00f0ff' }}>-{data.idle_savings_kg.toFixed(2)} kg CO2e / year</span>
              </div>
            </div>
          </div>

          {/* Segment breakdowns */}
          {data.segments.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Infraction Segments</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '100px', overflowY: 'auto' }}>
                {data.segments.map((seg, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.65rem', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', padding: '6px 8px', borderRadius: '4px' }}>
                    <span style={{ color: '#fff', fontWeight: 600 }}>{seg.vehicle_type} ({seg.emission_standard})</span>
                    <span style={{ color: '#9ca3af' }}>{seg.transits_count} transits | {seg.co2_emitted_kg} kg CO2</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Calculation History ticker */}
          {history.length > 0 && (
            <div style={{ borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '10px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Calculation History</span>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', maxHeight: '90px', overflowY: 'auto' }}>
                {history.map((record) => (
                  <div key={record.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.6rem', color: '#6b7280', padding: '2px 0' }}>
                    <span>{new Date(record.calculated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} ({record.total_transits} logs)</span>
                    <span style={{ color: '#e5e7eb' }}>{record.total_co2_kg.toFixed(1)} kg CO2 | 🌲 {record.trees_offset}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '20px 0', color: '#6b7280', fontSize: '0.75rem' }}>
          Loading emissions calculation models...
        </div>
      )}
    </div>
  );
}
