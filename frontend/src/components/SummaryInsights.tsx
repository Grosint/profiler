import { Brain, TrendingUp, BarChart3 } from 'lucide-react';
import type { ProfileDetailsResponse } from '../types/api';

interface SummaryInsightsProps {
  details: ProfileDetailsResponse;
}

export default function SummaryInsights({ details }: SummaryInsightsProps) {

  // Calculate insights from traits
  const topTraits = details.traits
    .sort((a, b) => b.score - a.score)
    .slice(0, 5)
    .map(t => ({ name: t.traitName, score: t.score * 100 }));

  const avgConfidence = details.traits.length > 0
    ? details.traits.reduce((sum, t) => sum + t.confidence, 0) / details.traits.length * 100
    : 0;

  const traitCounts = details.traits.reduce((acc, trait) => {
    acc[trait.traitType] = (acc[trait.traitType] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Top Trait */}
      {topTraits.length > 0 && (
        <div className="card bg-gradient-to-br from-primary-900/20 to-primary-800/10 border-primary-700">
          <div className="flex items-center mb-3">
            <TrendingUp className="w-5 h-5 mr-2 text-primary-400" />
            <h3 className="font-semibold text-dark-100">Top Trait</h3>
          </div>
          <p className="text-lg font-bold text-primary-300 mb-1">{topTraits[0].name}</p>
          <p className="text-sm text-dark-400">{topTraits[0].score.toFixed(1)}% score</p>
        </div>
      )}

      {/* Average Confidence */}
      <div className="card bg-gradient-to-br from-success-900/20 to-success-800/10 border-success-700">
        <div className="flex items-center mb-3">
          <Shield className="w-5 h-5 mr-2 text-success-400" />
          <h3 className="font-semibold text-dark-100">Confidence</h3>
        </div>
        <p className="text-lg font-bold text-success-300 mb-1">{avgConfidence.toFixed(1)}%</p>
        <p className="text-sm text-dark-400">Average across all traits</p>
      </div>

      {/* Total Traits */}
      <div className="card bg-gradient-to-br from-warning-900/20 to-warning-800/10 border-warning-700">
        <div className="flex items-center mb-3">
          <BarChart3 className="w-5 h-5 mr-2 text-warning-400" />
          <h3 className="font-semibold text-dark-100">Traits Analyzed</h3>
        </div>
        <p className="text-lg font-bold text-warning-300 mb-1">{details.traits.length}</p>
        <p className="text-sm text-dark-400">{Object.keys(traitCounts).length} categories</p>
      </div>

      {/* Analysis Status */}
      <div className="card bg-gradient-to-br from-primary-900/20 to-primary-800/10 border-primary-700">
        <div className="flex items-center mb-3">
          <Brain className="w-5 h-5 mr-2 text-primary-400" />
          <h3 className="font-semibold text-dark-100">Status</h3>
        </div>
        <p className="text-lg font-bold text-success-300 mb-1">Complete</p>
        <p className="text-sm text-dark-400">Analysis finished</p>
      </div>
    </div>
  );
}

function Shield({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}
