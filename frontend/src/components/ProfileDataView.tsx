import { Database, FileText, BarChart } from 'lucide-react';
import type { ProfileStatusResponse, ProfileDetailsResponse } from '../types/api';

interface ProfileDataViewProps {
  profile: ProfileStatusResponse;
  details?: ProfileDetailsResponse | null;
}

export default function ProfileDataView({ profile, details }: ProfileDataViewProps) {
  const summary = profile.summary || {};
  const hasTraits = details && details.traits.length > 0;
  const hasSummary = Object.keys(summary).length > 0;

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <Database className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Profile Data Summary</h2>
      </div>

      {hasSummary && (
        <div className="space-y-4 mb-6">
          <h3 className="text-sm font-medium text-dark-300 mb-3">Summary Data</h3>
          <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
            <details className="cursor-pointer">
              <summary className="text-sm font-medium text-dark-200 mb-2 hover:text-dark-100">
                View Raw Summary Data
              </summary>
              <pre className="text-xs text-dark-300 overflow-x-auto mt-2 max-h-96 overflow-y-auto">
                {JSON.stringify(summary, null, 2)}
              </pre>
            </details>
          </div>

          {/* Visual Summary Sections */}
          {summary.topTraits && Array.isArray(summary.topTraits) && summary.topTraits.length > 0 && (
            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <h4 className="text-sm font-medium text-dark-200 mb-2">Top Traits</h4>
              <div className="flex flex-wrap gap-2">
                {summary.topTraits.map((trait: string, idx: number) => (
                  <span key={idx} className="px-3 py-1 bg-primary-900/20 text-primary-300 rounded-full text-sm border border-primary-700">
                    {trait}
                  </span>
                ))}
              </div>
            </div>
          )}

          {summary.features && (
            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <h4 className="text-sm font-medium text-dark-200 mb-3">Features Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {summary.features.identity && (
                  <div>
                    <p className="text-xs text-dark-400 mb-1">Identity</p>
                    <p className="text-sm text-dark-300">
                      Confidence: {(summary.features.identity.identityConfidence * 100).toFixed(0)}%
                    </p>
                  </div>
                )}
                {summary.features.behavioral && (
                  <div>
                    <p className="text-xs text-dark-400 mb-1">Behavioral</p>
                    <p className="text-sm text-dark-300">
                      Frequency: {summary.features.behavioral.postingFrequencyTrend || 'N/A'}
                    </p>
                  </div>
                )}
                {summary.features.network && (
                  <div>
                    <p className="text-xs text-dark-400 mb-1">Network</p>
                    <p className="text-sm text-dark-300">
                      Communities: {summary.features.network.communityCount || 0}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {summary.narratives && summary.narratives.dominantThemes && (
            <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
              <h4 className="text-sm font-medium text-dark-200 mb-2">Dominant Themes</h4>
              <div className="flex flex-wrap gap-2">
                {summary.narratives.dominantThemes.map((theme: string, idx: number) => (
                  <span key={idx} className="px-2 py-1 bg-warning-900/20 text-warning-300 rounded text-xs border border-warning-700">
                    {theme}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
          <div className="flex items-center mb-2">
            <FileText className="w-4 h-4 mr-2 text-primary-400" />
            <span className="text-sm font-medium text-dark-300">Status</span>
          </div>
          <p className="text-lg font-semibold text-dark-100 capitalize">{profile.status}</p>
        </div>

        <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
          <div className="flex items-center mb-2">
            <BarChart className="w-4 h-4 mr-2 text-success-400" />
            <span className="text-sm font-medium text-dark-300">Traits</span>
          </div>
          <p className="text-lg font-semibold text-dark-100">
            {hasTraits ? details!.traits.length : profile.traitsOverview.length}
          </p>
        </div>

        <div className="bg-dark-800 rounded-lg p-4 border border-dark-700">
          <div className="flex items-center mb-2">
            <Database className="w-4 h-4 mr-2 text-warning-400" />
            <span className="text-sm font-medium text-dark-300">Categories</span>
          </div>
          <p className="text-lg font-semibold text-dark-100">
            {hasTraits
              ? new Set(details!.traits.map(t => t.traitType)).size
              : profile.traitsOverview.length}
          </p>
        </div>
      </div>

      {profile.traitsOverview.length > 0 && (
        <div className="mt-6 pt-6 border-t border-dark-800">
          <h3 className="text-sm font-medium text-dark-300 mb-4">Trait Overview</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {profile.traitsOverview.map((trait, idx) => (
              <div key={idx} className="bg-dark-800 rounded-lg p-3 border border-dark-700">
                <p className="text-xs text-dark-400 mb-1 capitalize">{trait.traitType.replace('_', ' ')}</p>
                <p className="text-lg font-semibold text-dark-100">
                  {(trait.averageScore * 100).toFixed(1)}%
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
