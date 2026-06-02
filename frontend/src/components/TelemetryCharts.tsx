import React, { useEffect, useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';
import { Line, Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

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

type TabType = 'aqi' | 'co2' | 'climate' | 'water';

export default function TelemetryCharts({ data }: TelemetryChartsProps) {
  const [isClient, setIsClient] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('aqi');

  useEffect(() => {
    setIsClient(true);
  }, []);

  // Empty array as starting state. In actual browser deployments, dynamic API feeds are rendered.
  const defaultList: TelemetryData[] = data && data.length > 0 ? data : [];

  // Limit and sort chronologically (oldest to newest for plotting left-to-right)
  const chartDataPoints = [...defaultList].reverse().slice(-12);

  const labels = chartDataPoints.map(d => {
    try {
      return new Date(d.measured_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    } catch {
      return '';
    }
  });

  const latest = defaultList[0] || {
    pm25: 0, pm10: 0, aqi: 0, temperature: 0, humidity: 0, co2: 0, water_ph: 0
  };

  const getAQILevel = (aqi: number) => {
    if (aqi <= 50) return { label: 'Good', color: '#10B981' };
    if (aqi <= 100) return { label: 'Moderate', color: '#F59E0B' };
    return { label: 'Poor', color: '#EF4444' };
  };

  const aqiLevel = getAQILevel(latest.aqi);

  if (!isClient) {
    return (
      <div style={{ height: '320px', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ color: '#9ca3af', fontSize: '0.85rem' }}>Synchronizing IoT telemetry grids...</span>
      </div>
    );
  }

  // Chart configuration builder based on active tab
  let chartElement = null;

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          color: '#9ca3af',
          font: { family: 'Inter', size: 10 }
        }
      },
      tooltip: {
        backgroundColor: '#0c0f17',
        titleColor: '#fff',
        bodyColor: '#e5e7eb',
        borderColor: 'rgba(255,255,255,0.08)',
        borderWidth: 1,
        bodyFont: { family: 'Inter' }
      }
    },
    scales: {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#6b7280', font: { size: 9 } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.03)' },
        ticks: { color: '#6b7280', font: { size: 9 } }
      }
    }
  };

  if (activeTab === 'aqi') {
    const aqiDataset = {
      labels,
      datasets: [
        {
          label: 'AQI Index',
          data: chartDataPoints.map(d => d.aqi),
          borderColor: '#00f0ff',
          backgroundColor: 'rgba(0, 240, 255, 0.05)',
          fill: true,
          tension: 0.35,
          borderWidth: 2
        },
        {
          label: 'PM2.5 (µg/m³)',
          data: chartDataPoints.map(d => d.pm25),
          borderColor: '#10b981',
          backgroundColor: 'transparent',
          tension: 0.35,
          borderWidth: 1.5
        },
        {
          label: 'PM10 (µg/m³)',
          data: chartDataPoints.map(d => d.pm10),
          borderColor: '#f59e0b',
          backgroundColor: 'transparent',
          tension: 0.35,
          borderWidth: 1.5
        }
      ]
    };
    chartElement = <Line data={aqiDataset} options={chartOptions} height={180} />;
  } else if (activeTab === 'co2') {
    const co2Dataset = {
      labels,
      datasets: [
        {
          label: 'CO2 Emission Level (ppm)',
          data: chartDataPoints.map(d => d.co2),
          borderColor: '#8b5cf6',
          backgroundColor: 'rgba(139, 92, 246, 0.15)',
          fill: true,
          tension: 0.2,
          borderWidth: 2
        }
      ]
    };
    chartElement = <Bar data={co2Dataset} options={chartOptions} height={180} />;
  } else if (activeTab === 'climate') {
    const climateDataset = {
      labels,
      datasets: [
        {
          label: 'Temperature (°C)',
          data: chartDataPoints.map(d => d.temperature),
          borderColor: '#ef4444',
          backgroundColor: 'transparent',
          tension: 0.3,
          borderWidth: 2
        },
        {
          label: 'Humidity (%)',
          data: chartDataPoints.map(d => d.humidity),
          borderColor: '#3b82f6',
          backgroundColor: 'transparent',
          tension: 0.3,
          borderWidth: 1.5
        }
      ]
    };
    chartElement = <Line data={climateDataset} options={chartOptions} height={180} />;
  } else if (activeTab === 'water') {
    const waterDataset = {
      labels,
      datasets: [
        {
          label: 'River Alaknanda water pH',
          data: chartDataPoints.map(d => d.water_ph),
          borderColor: '#00f0ff',
          backgroundColor: 'rgba(0, 240, 255, 0.05)',
          fill: true,
          tension: 0.1,
          borderWidth: 2
        }
      ]
    };
    chartElement = <Line data={waterDataset} options={{
      ...chartOptions,
      scales: {
        ...chartOptions.scales,
        y: {
          ...chartOptions.scales.y,
          min: 6,
          max: 9,
          ticks: { stepSize: 0.5, color: '#6b7280' }
        }
      }
    }} height={180} />;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%' }}>
      {/* Vitals metrics strip */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '12px' }}>
        <div className="glass-panel" style={{ padding: '10px 14px', background: 'rgba(15, 20, 32, 0.4)' }}>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.02em' }}>Air Quality (AQI)</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.3rem', fontWeight: 700, color: aqiLevel.color }}>{latest.aqi}</span>
            <span style={{ fontSize: '0.7rem', color: aqiLevel.color, fontWeight: 600 }}>{aqiLevel.label}</span>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '10px 14px', background: 'rgba(15, 20, 32, 0.4)' }}>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.02em' }}>CO2 Standards</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.3rem', fontWeight: 700, color: '#8b5cf6' }}>{latest.co2}</span>
            <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>ppm</span>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '10px 14px', background: 'rgba(15, 20, 32, 0.4)' }}>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.02em' }}>Ambient Air Temp</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.3rem', fontWeight: 700, color: '#ef4444' }}>{latest.temperature}</span>
            <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>°C</span>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '10px 14px', background: 'rgba(15, 20, 32, 0.4)' }}>
          <span style={{ fontSize: '0.65rem', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.02em' }}>River Chemistry pH</span>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px', marginTop: '4px' }}>
            <span style={{ fontSize: '1.3rem', fontWeight: 700, color: '#00f0ff' }}>{latest.water_ph}</span>
            <span style={{ fontSize: '0.65rem', color: '#9ca3af' }}>pH</span>
          </div>
        </div>
      </div>

      {/* Tabs list */}
      <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)', paddingBottom: '1px' }}>
        <button 
          onClick={() => setActiveTab('aqi')}
          className={`action-btn ${activeTab === 'aqi' ? 'active' : ''}`}
          style={{ borderBottomLeftRadius: 0, borderBottomRightRadius: 0, borderBottom: 'none', background: 'transparent' }}
        >
          💨 AQI & Dust
        </button>
        <button 
          onClick={() => setActiveTab('co2')}
          className={`action-btn ${activeTab === 'co2' ? 'active' : ''}`}
          style={{ borderBottomLeftRadius: 0, borderBottomRightRadius: 0, borderBottom: 'none', background: 'transparent' }}
        >
          🔥 CO2 Emissions
        </button>
        <button 
          onClick={() => setActiveTab('climate')}
          className={`action-btn ${activeTab === 'climate' ? 'active' : ''}`}
          style={{ borderBottomLeftRadius: 0, borderBottomRightRadius: 0, borderBottom: 'none', background: 'transparent' }}
        >
          🌡️ Weather Stats
        </button>
        <button 
          onClick={() => setActiveTab('water')}
          className={`action-btn ${activeTab === 'water' ? 'active' : ''}`}
          style={{ borderBottomLeftRadius: 0, borderBottomRightRadius: 0, borderBottom: 'none', background: 'transparent' }}
        >
          💧 River Quality
        </button>
      </div>

      {/* Chart wrapper */}
      <div style={{ flex: 1, minHeight: '190px', position: 'relative' }}>
        {chartElement}
      </div>
    </div>
  );
}
