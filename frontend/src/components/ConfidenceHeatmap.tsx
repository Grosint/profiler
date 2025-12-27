import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Shield } from 'lucide-react';
import type { TraitDetail } from '../types/api';

interface ConfidenceHeatmapProps {
  traits: TraitDetail[];
}

export default function ConfidenceHeatmap({ traits }: ConfidenceHeatmapProps) {
  const chartData = traits
    .map(trait => ({
      name: trait.traitName.length > 20 ? trait.traitName.substring(0, 20) + '...' : trait.traitName,
      fullName: trait.traitName,
      confidence: trait.confidence * 100,
      score: trait.score * 100,
    }))
    .sort((a, b) => b.confidence - a.confidence)
    .slice(0, 10); // Top 10 by confidence

  if (chartData.length === 0) {
    return null;
  }

  const getColor = (confidence: number) => {
    if (confidence >= 80) return '#22c55e';
    if (confidence >= 60) return '#f59e0b';
    return '#ef4444';
  };

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <Shield className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Confidence Heatmap (Top 10 Traits)</h2>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} layout="vertical">
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis type="number" domain={[0, 100]} tick={{ fill: '#9ca3af' }} />
          <YAxis
            dataKey="name"
            type="category"
            tick={{ fill: '#9ca3af', fontSize: 12 }}
            width={150}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#f3f4f6',
            }}
            formatter={(value: number, name: string, props: any) => [
              `${value.toFixed(1)}%`,
              `${name === 'confidence' ? 'Confidence' : 'Score'}: ${props.payload.fullName}`,
            ]}
          />
          <Bar dataKey="confidence" radius={[0, 4, 4, 0]}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getColor(entry.confidence)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
