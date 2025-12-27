import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';
import { TrendingUp } from 'lucide-react';
import type { TraitDetail, TraitType } from '../types/api';

interface TraitDistributionChartProps {
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

export default function TraitDistributionChart({ traits }: TraitDistributionChartProps) {
  // Group traits by type and calculate average scores
  const distribution = traits.reduce((acc, trait) => {
    if (!acc[trait.traitType]) {
      acc[trait.traitType] = { count: 0, totalScore: 0 };
    }
    acc[trait.traitType].count += 1;
    acc[trait.traitType].totalScore += trait.score;
    return acc;
  }, {} as Record<TraitType, { count: number; totalScore: number }>);

  const chartData = Object.entries(distribution).map(([type, data]) => ({
    name: traitTypeLabels[type as TraitType],
    value: (data.totalScore / data.count) * 100,
    count: data.count,
    color: traitColors[type as TraitType],
  }));

  if (chartData.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center mb-6">
          <TrendingUp className="w-5 h-5 mr-2 text-primary-400" />
          <h2 className="text-xl font-semibold text-dark-100">Trait Distribution</h2>
        </div>
        <div className="text-center py-8 text-dark-500">
          No trait data available
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <TrendingUp className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Trait Distribution by Category</h2>
      </div>
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, value }) => `${name}: ${value.toFixed(1)}%`}
            outerRadius={100}
            fill="#8884d8"
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              backgroundColor: '#1f2937',
              border: '1px solid #374151',
              borderRadius: '8px',
              color: '#f3f4f6',
            }}
            formatter={(value: number, name: string, props: any) => [
              `${value.toFixed(1)}% (${props.payload.count} traits)`,
              name,
            ]}
          />
          <Legend
            wrapperStyle={{ color: '#9ca3af' }}
            formatter={(value) => <span style={{ color: '#9ca3af' }}>{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
