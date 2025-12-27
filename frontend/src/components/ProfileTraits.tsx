import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Brain, TrendingUp } from 'lucide-react';
import type { TraitDetail, TraitType } from '../types/api';

interface ProfileTraitsProps {
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

export default function ProfileTraits({ traits }: ProfileTraitsProps) {
  const chartData = traits.map(trait => ({
    name: trait.traitName,
    score: trait.score * 100,
    confidence: trait.confidence * 100,
    type: trait.traitType,
  }));

  const groupedByType = traits.reduce((acc, trait) => {
    if (!acc[trait.traitType]) {
      acc[trait.traitType] = [];
    }
    acc[trait.traitType].push(trait);
    return acc;
  }, {} as Record<TraitType, TraitDetail[]>);

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <Brain className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Profile Traits</h2>
      </div>

      {/* Overall Chart */}
      <div className="mb-8">
        <h3 className="text-sm font-medium text-dark-300 mb-4">Trait Scores Overview</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
            <XAxis
              dataKey="name"
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
              formatter={(value: number, name: string) => [`${value.toFixed(1)}%`, name]}
            />
            <Bar dataKey="score" radius={[4, 4, 0, 0]}>
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={traitColors[entry.type]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Trait Details by Category */}
      <div className="space-y-6">
        {Object.entries(groupedByType).map(([type, typeTraits]) => (
          <div key={type} className="border-t border-dark-800 pt-6">
            <h3 className="text-lg font-semibold text-dark-100 mb-4 flex items-center">
              <div
                className="w-3 h-3 rounded-full mr-2"
                style={{ backgroundColor: traitColors[type as TraitType] }}
              />
              {traitTypeLabels[type as TraitType]}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {typeTraits.map((trait) => (
                <TraitCard key={trait.traitName} trait={trait} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

interface TraitCardProps {
  trait: TraitDetail;
}

function TraitCard({ trait }: TraitCardProps) {
  const scorePercent = trait.score * 100;
  const confidencePercent = trait.confidence * 100;

  return (
    <div className="bg-dark-800 border border-dark-700 rounded-lg p-4">
      <div className="flex items-center justify-between mb-2">
        <h4 className="font-medium text-dark-100">{trait.traitName}</h4>
        <span className="text-sm text-dark-400">{scorePercent.toFixed(1)}%</span>
      </div>

      {/* Score Bar */}
      <div className="w-full bg-dark-700 rounded-full h-2 mb-3">
        <div
          className="bg-primary-500 h-2 rounded-full transition-all duration-300"
          style={{ width: `${scorePercent}%` }}
        />
      </div>

      {/* Confidence */}
      <div className="flex items-center justify-between text-xs text-dark-500 mb-3">
        <span>Confidence: {confidencePercent.toFixed(0)}%</span>
        <div className="flex items-center">
          <TrendingUp className="w-3 h-3 mr-1" />
          <span>High</span>
        </div>
      </div>

      {/* Evidence Snippets */}
      {trait.evidenceSnippets.length > 0 && (
        <div className="mt-3 pt-3 border-t border-dark-700">
          <p className="text-xs font-medium text-dark-400 mb-2">Evidence:</p>
          <ul className="space-y-1">
            {trait.evidenceSnippets.slice(0, 2).map((snippet, idx) => (
              <li key={idx} className="text-xs text-dark-500 italic">
                "{snippet.substring(0, 100)}..."
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
