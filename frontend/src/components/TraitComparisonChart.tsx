import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { BarChart3 } from 'lucide-react';
import type { TraitDetail, TraitType } from '../types/api';

interface TraitComparisonChartProps {
  traits: TraitDetail[];
}

const traitTypeLabels: Record<TraitType, string> = {
  personality: 'Personality',
  work_style: 'Work Style',
  communication: 'Communication',
  risk: 'Risk Assessment',
  cultural_fit: 'Cultural Fit',
  leadership: 'Leadership',
};

const traitColors: Record<TraitType, string> = {
  personality: '#3b82f6',
  work_style: '#22c55e',
  communication: '#f59e0b',
  risk: '#ef4444',
  cultural_fit: '#8b5cf6',
  leadership: '#06b6d4',
};

export default function TraitComparisonChart({ traits }: TraitComparisonChartProps) {
  // Group by trait type and calculate averages
  const byType = traits.reduce((acc, trait) => {
    if (!acc[trait.traitType]) {
      acc[trait.traitType] = [];
    }
    acc[trait.traitType].push(trait.score * 100);
    return acc;
  }, {} as Record<TraitType, number[]>);

  const chartData = Object.entries(byType).map(([type, scores]) => ({
    category: traitTypeLabels[type as TraitType],
    average: scores.reduce((a, b) => a + b, 0) / scores.length,
    min: Math.min(...scores),
    max: Math.max(...scores),
    count: scores.length,
    color: traitColors[type as TraitType],
  }));

  if (chartData.length === 0) {
    return null;
  }

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <BarChart3 className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Trait Category Comparison</h2>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
          <XAxis
            dataKey="category"
            tick={{ fill: '#9ca3af' }}
            angle={-45}
            textAnchor="end"
            height={100}
          />
          <YAxis
            tick={{ fill: '#9ca3af' }}
            domain={[0, 100]}
            label={{ value: 'Score (%)', angle: -90, position: 'insideLeft', fill: '#9ca3af' }}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#f3f4f6',
            }}
            formatter={(value: number) => `${value.toFixed(1)}%`}
          />
          <Legend wrapperStyle={{ color: '#9ca3af' }} />
          <Line
            type="monotone"
            dataKey="average"
            stroke="#3b82f6"
            strokeWidth={3}
            name="Average Score"
            dot={{ fill: '#3b82f6', r: 5 }}
          />
          <Line
            type="monotone"
            dataKey="min"
            stroke="#6b7280"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Minimum"
            dot={{ fill: '#6b7280', r: 3 }}
          />
          <Line
            type="monotone"
            dataKey="max"
            stroke="#9ca3af"
            strokeWidth={2}
            strokeDasharray="5 5"
            name="Maximum"
            dot={{ fill: '#9ca3af', r: 3 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
