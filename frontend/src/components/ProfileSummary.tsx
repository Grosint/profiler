import { FileText, User, Brain } from 'lucide-react';
import type { ProfileDetailsResponse } from '../types/api';

interface ProfileSummaryProps {
  details: ProfileDetailsResponse;
}

export default function ProfileSummary({ details }: ProfileSummaryProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Personality Narrative */}
      {details.narratives?.personalityNarrative && (
        <div className="card">
          <div className="flex items-center mb-4">
            <Brain className="w-5 h-5 mr-2 text-primary-400" />
            <h3 className="font-semibold text-dark-100">Personality</h3>
          </div>
          <p className="text-sm text-dark-400 leading-relaxed">
            {details.narratives.personalityNarrative}
          </p>
        </div>
      )}

      {/* Risk Narrative */}
      {details.narratives?.riskNarrative && (
        <div className="card">
          <div className="flex items-center mb-4">
            <User className="w-5 h-5 mr-2 text-warning-400" />
            <h3 className="font-semibold text-dark-100">Risk Assessment</h3>
          </div>
          <p className="text-sm text-dark-400 leading-relaxed">
            {details.narratives.riskNarrative}
          </p>
        </div>
      )}

      {/* Summary Stats */}
      <div className="card">
        <div className="flex items-center mb-4">
          <FileText className="w-5 h-5 mr-2 text-success-400" />
          <h3 className="font-semibold text-dark-100">Summary</h3>
        </div>
        <div className="space-y-3">
          <div className="flex justify-between">
            <span className="text-sm text-dark-400">Total Traits</span>
            <span className="text-sm font-semibold text-dark-100">{details.traits.length}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-dark-400">Avg Confidence</span>
            <span className="text-sm font-semibold text-dark-100">
              {(
                details.traits.reduce((sum, t) => sum + t.confidence, 0) / details.traits.length
              ).toFixed(1)}
            </span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm text-dark-400">Analysis Status</span>
            <span className="text-sm font-semibold text-success-400">Complete</span>
          </div>
        </div>
      </div>
    </div>
  );
}
