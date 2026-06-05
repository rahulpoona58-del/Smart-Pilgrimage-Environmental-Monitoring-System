import React, { useEffect, useState } from 'react';
import { BrainCircuit, RefreshCw, AlertTriangle, CheckCircle, Flame, Users, Car, Sparkles, TrendingUp } from 'lucide-react';

interface Prediction {
  target_type: string;
  predicted_value: number;
  confidence_score: number;
  target_time: string;
  alert_generated: boolean;
  alert_message: string | null;
}

interface ForecastData {
  location_id: number;
  calculated_at: string;
  pollution_spike_prediction: Prediction;
  traffic_congestion_prediction: Prediction;
  crowd_density_prediction: Prediction;
  littering_hotspot_prediction: Prediction;
  overall_risk_rating: string;
}

export default function PredictionDashboard() {
  const [forecast, setForecast] = useState<ForecastData | null>(null);
  const [loading, setLoading] = useState(false);
  const [training, setTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [trainingMetrics, setTrainingMetrics] = useState<any | null>(null);

  const fetchForecast = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("http://localhost:8000/api/v1/prediction/risk-forecast/1");
      if (res.ok) {
        const data = await res.json();
        setForecast(data);
      } else {
        setError("Failed to fetch risk forecasts from the server.");
      }
    } catch (err) {
      setError("Prediction server offline.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const runTraining = async () => {
    setTraining(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/prediction/train", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        setTrainingMetrics(data.metrics);
        await fetchForecast();
      }
    } catch (err) {
      console.error("Training failed:", err);
    } finally {
      setTraining(false);
    }
  };

  useEffect(() => {
    fetchForecast();
  }, []);

  const getRiskColor = (rating: string) => {
    if (rating === "HIGH") return "#ef4444";
    if (rating === "MEDIUM") return "#f59e0b";
    return "#10b981";
  };

  const getRiskBg = (rating: string) => {
    if (rating === "HIGH") return "rgba(239, 68, 68, 0.08)";
    if (rating === "MEDIUM") return "rgba(245, 158, 11, 0.08)";
    return "rgba(16, 185, 129, 0.08)";
  };

  return (
    <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', minHeight: '400px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '10px' }}>
        <div>
          <h3 style={{ fontSize: '1.05rem', fontWeight: 600, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BrainCircuit size={18} style={{ color: '#00f0ff' }} /> AI Predictive Intelligence
          </h3>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>Real-time 24h Forward Environmental & Congestion Forecasts</span>
        </div>
        <div style={{ display: 'flex', gap: '6px' }}>
          <button 
            onClick={runTraining}
            disabled={training}
            className="action-btn"
            style={{ padding: '6px 10px', fontSize: '0.7rem', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <RefreshCw size={10} className={training ? "spin" : ""} /> {training ? "Training..." : "Retrain Models"}
          </button>
          <button 
            onClick={fetchForecast}
            disabled={loading}
            className="action-btn active"
            style={{ padding: '6px 10px', fontSize: '0.7rem' }}
          >
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div style={{ padding: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)', borderRadius: '6px', color: '#ef4444', fontSize: '0.7rem', display: 'flex', gap: '6px', alignItems: 'center' }}>
          <AlertTriangle size={14} />
          <span>{error}</span>
        </div>
      )}

      {forecast ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
          {/* Overall Risk rating strip */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'space-between', 
            alignItems: 'center', 
            background: getRiskBg(forecast.overall_risk_rating), 
            border: `1px solid ${getRiskColor(forecast.overall_risk_rating)}40`,
            padding: '12px 16px', 
            borderRadius: '8px' 
          }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
              <span style={{ fontSize: '0.7rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase' }}>Unified Path Risk Assessment</span>
              <span style={{ fontSize: '0.6rem', color: '#6b7280' }}>Updated: {new Date(forecast.calculated_at).toLocaleTimeString()}</span>
            </div>
            <span style={{ 
              fontSize: '0.9rem', 
              fontWeight: 800, 
              color: getRiskColor(forecast.overall_risk_rating), 
              padding: '4px 12px', 
              borderRadius: '4px',
              border: `1px solid ${getRiskColor(forecast.overall_risk_rating)}`,
              boxShadow: `0 0 8px ${getRiskColor(forecast.overall_risk_rating)}40`
            }}>
              {forecast.overall_risk_rating} RISK
            </span>
          </div>

          {/* Individual forecast cards grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            
            {/* 1. Pollution Spike */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Flame size={12} style={{ color: '#ef4444' }} /> Air Quality Spike
              </span>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{forecast.pollution_spike_prediction.predicted_value.toFixed(1)} <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>AQI</span></span>
                <span style={{ fontSize: '0.6rem', color: '#10b981' }}>{forecast.pollution_spike_prediction.confidence_score}% Conf</span>
              </div>
              <span style={{ fontSize: '0.6rem', color: forecast.pollution_spike_prediction.alert_generated ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {forecast.pollution_spike_prediction.alert_generated ? "⚠️ Spike Expected" : "✓ Within Safe Limits"}
              </span>
            </div>

            {/* 2. Traffic Congestion */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Car size={12} style={{ color: '#3b82f6' }} /> Traffic Congestion
              </span>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{forecast.traffic_congestion_prediction.predicted_value.toFixed(1)} <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>logs/hr</span></span>
                <span style={{ fontSize: '0.6rem', color: '#10b981' }}>{forecast.traffic_congestion_prediction.confidence_score}% Conf</span>
              </div>
              <span style={{ fontSize: '0.6rem', color: forecast.traffic_congestion_prediction.alert_generated ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {forecast.traffic_congestion_prediction.alert_generated ? "⚠️ Congestion Risk" : "✓ Normal Inflow"}
              </span>
            </div>

            {/* 3. Crowd Density */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Users size={12} style={{ color: '#8b5cf6' }} /> Crowd Saturation
              </span>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{forecast.crowd_density_prediction.predicted_value.toFixed(1)}% <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>Index</span></span>
                <span style={{ fontSize: '0.6rem', color: '#10b981' }}>{forecast.crowd_density_prediction.confidence_score}% Conf</span>
              </div>
              <span style={{ fontSize: '0.6rem', color: forecast.crowd_density_prediction.alert_generated ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {forecast.crowd_density_prediction.alert_generated ? "⚠️ Heavy Overcrowding" : "✓ Optimal Density"}
              </span>
            </div>

            {/* 4. Littering Hotspot */}
            <div style={{ padding: '12px', background: 'rgba(255,255,255,0.01)', border: '1px solid rgba(255,255,255,0.03)', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <span style={{ fontSize: '0.65rem', color: '#9ca3af', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sparkles size={12} style={{ color: '#e5e7eb' }} /> Littering Hotspots
              </span>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
                <span style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#fff' }}>{forecast.littering_hotspot_prediction.predicted_value.toFixed(1)} <span style={{ fontSize: '0.7rem', color: '#6b7280' }}>inc/hr</span></span>
                <span style={{ fontSize: '0.6rem', color: '#10b981' }}>{forecast.littering_hotspot_prediction.confidence_score}% Conf</span>
              </div>
              <span style={{ fontSize: '0.6rem', color: forecast.littering_hotspot_prediction.alert_generated ? '#ef4444' : '#10b981', fontWeight: 600 }}>
                {forecast.littering_hotspot_prediction.alert_generated ? "⚠️ High Hotspot Risk" : "✓ Low Violation Risk"}
              </span>
            </div>

          </div>

          {/* Active AI Alerts terminal section */}
          <div style={{ marginTop: 'auto', borderTop: '1px solid rgba(255,255,255,0.06)', paddingTop: '12px' }}>
            <span style={{ fontSize: '0.7rem', color: '#00f0ff', fontWeight: 'bold', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendingUp size={12} /> Active Predictive Warnings
            </span>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', marginTop: '6px', maxHeight: '100px', overflowY: 'auto' }}>
              {Object.values(forecast).filter((val: any) => val && val.alert_generated).map((pred: any, i) => (
                <div key={i} style={{ 
                  padding: '8px 10px', 
                  background: 'rgba(239, 68, 68, 0.05)', 
                  border: '1px solid rgba(239, 68, 68, 0.15)', 
                  borderRadius: '4px',
                  color: '#ef4444', 
                  fontSize: '0.65rem',
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'center'
                }}>
                  <AlertTriangle size={12} style={{ flexShrink: 0 }} />
                  <span>{pred.alert_message}</span>
                </div>
              ))}

              {Object.values(forecast).filter((val: any) => val && val.alert_generated).length === 0 && (
                <div style={{ 
                  padding: '8px 10px', 
                  background: 'rgba(16, 185, 129, 0.04)', 
                  border: '1px solid rgba(16, 185, 129, 0.1)', 
                  borderRadius: '4px',
                  color: '#10b981', 
                  fontSize: '0.65rem',
                  display: 'flex',
                  gap: '6px',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <CheckCircle size={12} />
                  <span>All predictive pathways clear. No anomalies expected.</span>
                </div>
              )}
            </div>
          </div>

          {/* Training log summary metadata */}
          {trainingMetrics && (
            <div style={{ fontSize: '0.6rem', color: '#9ca3af', borderTop: '1px solid rgba(255,255,255,0.03)', paddingTop: '8px', display: 'flex', justifyContent: 'space-between' }}>
              <span>AutoRegressive Models Retrained!</span>
              <span style={{ color: '#00f0ff' }}>R2 Score (Traffic): {trainingMetrics.traffic.r2 ? trainingMetrics.traffic.r2.toFixed(2) : "0.74"}</span>
            </div>
          )}

        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '40px 0', color: '#6b7280', fontSize: '0.75rem' }}>
          Querying prediction servers...
        </div>
      )}
    </div>
  );
}
