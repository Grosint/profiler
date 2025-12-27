import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer } from 'recharts';
import type { TraitDetail } from '../types/api';

interface RiskIndicatorsProps {
  traits: TraitDetail[];
  narratives?: Record<string, string>;
}

export default function RiskIndicators({ traits, narratives }: RiskIndicatorsProps) {
  // Calculate risk vectors
  const riskVectors = {
    behavioral: traits.find(t => t.traitName.toLowerCase().includes('behavior'))?.score || 0,
    network: traits.find(t => t.traitName.toLowerCase().includes('network'))?.score || 0,
    volatility: traits.find(t => t.traitName.toLowerCase().includes('volatil'))?.score || 0,
    escalation: traits.find(t => t.traitName.toLowerCase().includes('escalat'))?.score || 0,
  };

  const radarData = [
    { axis: 'Behavioral', value: riskVectors.behavioral * 100 },
    { axis: 'Network', value: riskVectors.network * 100 },
    { axis: 'Volatility', value: riskVectors.volatility * 100 },
    { axis: 'Escalation', value: riskVectors.escalation * 100 },
  ];

  const getRiskLevel = (value: number) => {
    if (value >= 70) return { level: 'High', color: 'danger', icon: TrendingUp };
    if (value >= 40) return { level: 'Medium', color: 'warning', icon: Minus };
    return { level: 'Low', color: 'success', icon: TrendingDown };
  };

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <AlertTriangle className="w-5 h-5 mr-2 text-warning-400" />
        <h2 className="text-xl font-semibold text-dark-100">Risk Indicators</h2>
      </div>

      {/* Radar Chart */}
      <div className="mb-6">
        <ResponsiveContainer width="100%" height={200}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#374151" />
            <PolarAngleAxis
              dataKey="axis"
              tick={{ fill: '#9ca3af', fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: '#9ca3af', fontSize: 10 }}
            />
            <Radar
              name="Risk"
              dataKey="value"
              stroke="#ef4444"
              fill="#ef4444"
              fillOpacity={0.3}
            />
          </RadarChart>
        </ResponsiveContainer>
      </div>

      {/* Risk Vectors */}
      <div className="space-y-3">
        {Object.entries(riskVectors).map(([key, value]) => {
          const risk = getRiskLevel(value * 100);
          const Icon = risk.icon;

          const colorClasses = {
            danger: 'text-danger-400',
            warning: 'text-warning-400',
            success: 'text-success-400',
          };

          const bgColorClasses = {
            danger: 'bg-danger-500',
            warning: 'bg-warning-500',
            success: 'bg-success-500',
          };

          const colorClass = colorClasses[risk.color as keyof typeof colorClasses];
          const bgColorClass = bgColorClasses[risk.color as keyof typeof bgColorClasses];

          return (
            <div key={key} className="bg-dark-800 rounded-lg p-3 border border-dark-700">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  <Icon className={`w-4 h-4 mr-2 ${colorClass}`} />
                  <span className="text-sm font-medium text-dark-200 capitalize">{key}</span>
                </div>
                <span className={`text-sm font-semibold ${colorClass}`}>
                  {risk.level}
                </span>
              </div>
              <div className="w-full bg-dark-700 rounded-full h-1.5">
                <div
                  className={`${bgColorClass} h-1.5 rounded-full transition-all duration-300`}
                  style={{ width: `${value * 100}%` }}
                />
              </div>
              <p className="text-xs text-dark-500 mt-1">
                Score: {(value * 100).toFixed(1)}% | Confidence: High
              </p>
            </div>
          );
        })}
      </div>

      {/* Risk Narrative */}
      {narratives?.riskNarrative && (
        <div className="mt-6 pt-6 border-t border-dark-800">
          <h3 className="text-sm font-medium text-dark-300 mb-2">Risk Assessment</h3>
          <p className="text-sm text-dark-400 leading-relaxed">
            {narratives.riskNarrative}
          </p>
        </div>
      )}
    </div>
  );
}
