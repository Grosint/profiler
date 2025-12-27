import { RefreshCw, Calendar, Hash } from 'lucide-react';
import { format } from 'date-fns';
import { getStatusColor, getStatusIcon } from '../utils/statusUtils';
import type { ProfileStatusResponse, ProfileDetailsResponse } from '../types/api';

interface ProfileHeaderProps {
  profile: ProfileStatusResponse;
  details?: ProfileDetailsResponse | null;
  onRefresh: () => void;
}

export default function ProfileHeader({ profile, details, onRefresh }: ProfileHeaderProps) {
  const StatusIcon = getStatusIcon(profile.status);
  const statusColor = getStatusColor(profile.status);

  return (
    <div className="card">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-3">
            <h1 className="text-3xl font-bold text-dark-100">
              {details?.subjectName || profile.id}
            </h1>
            <span className={`status-badge ${statusColor}`}>
              <StatusIcon className="w-4 h-4 mr-1" />
              {profile.status}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            {details?.externalRefId && (
              <div className="flex items-center text-dark-400">
                <Hash className="w-4 h-4 mr-2 text-dark-500" />
                <span className="font-medium mr-1">Ref ID:</span>
                <span>{details.externalRefId}</span>
              </div>
            )}
            <div className="flex items-center text-dark-400">
              <Calendar className="w-4 h-4 mr-2 text-dark-500" />
              <span className="font-medium mr-1">Created:</span>
              <span>{format(new Date(profile.createdAt), 'MMM d, yyyy HH:mm')}</span>
            </div>
            <div className="flex items-center text-dark-400">
              <Calendar className="w-4 h-4 mr-2 text-dark-500" />
              <span className="font-medium mr-1">Updated:</span>
              <span>{format(new Date(profile.updatedAt), 'MMM d, yyyy HH:mm')}</span>
            </div>
          </div>
        </div>

        <button
          onClick={onRefresh}
          className="btn-secondary flex items-center"
          title="Refresh profile data"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </button>
      </div>

      {/* URLs */}
      {details && (
        <div className="pt-4 border-t border-dark-800">
          <h3 className="text-sm font-medium text-dark-300 mb-2">Source URLs</h3>
          <div className="flex flex-wrap gap-2">
            {details.id && (
              <a
                href="#"
                className="text-xs bg-dark-800 px-2 py-1 rounded text-primary-400 hover:text-primary-300"
              >
                Profile ID: {details.id}
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
