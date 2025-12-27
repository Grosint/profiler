import { useState } from 'react';
import { Network, Users } from 'lucide-react';
import type { ProfileStatusResponse, ProfileDetailsResponse } from '../types/api';

interface NetworkGraphProps {
  profile: ProfileStatusResponse;
  details?: ProfileDetailsResponse | null;
}

export default function NetworkGraph({ profile, details }: NetworkGraphProps) {
  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');

  // Mock network data - in production, this would come from the API
  const networkData = {
    nodes: [
      { id: profile.id, name: details?.subjectName || 'Subject', group: 1, size: 20 },
      { id: 'node1', name: 'Connection 1', group: 2, size: 10 },
      { id: 'node2', name: 'Connection 2', group: 2, size: 10 },
      { id: 'node3', name: 'Connection 3', group: 3, size: 8 },
    ],
    links: [
      { source: profile.id, target: 'node1', value: 5 },
      { source: profile.id, target: 'node2', value: 3 },
      { source: 'node1', target: 'node3', value: 2 },
    ],
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Network className="w-5 h-5 mr-2 text-primary-400" />
          <h2 className="text-xl font-semibold text-dark-100">Network Graph</h2>
        </div>
        <div className="flex gap-2">
          <button
            onClick={() => setViewMode('2d')}
            className={`px-3 py-1 rounded text-sm ${
              viewMode === '2d'
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            2D
          </button>
          <button
            onClick={() => setViewMode('3d')}
            className={`px-3 py-1 rounded text-sm ${
              viewMode === '3d'
                ? 'bg-primary-600 text-white'
                : 'bg-dark-800 text-dark-400 hover:bg-dark-700'
            }`}
          >
            3D
          </button>
        </div>
      </div>

      {/* Network Visualization Placeholder */}
      <div className="bg-dark-800 rounded-lg h-64 flex items-center justify-center border border-dark-700">
        <div className="text-center">
          <Users className="w-12 h-12 text-dark-600 mx-auto mb-2" />
          <p className="text-dark-500 text-sm">Network visualization</p>
          <p className="text-dark-600 text-xs mt-1">
            {networkData.nodes.length} nodes, {networkData.links.length} connections
          </p>
        </div>
      </div>

      {/* Network Stats */}
      <div className="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-dark-800">
        <div>
          <p className="text-xs text-dark-500 mb-1">Total Nodes</p>
          <p className="text-lg font-semibold text-dark-100">{networkData.nodes.length}</p>
        </div>
        <div>
          <p className="text-xs text-dark-500 mb-1">Connections</p>
          <p className="text-lg font-semibold text-dark-100">{networkData.links.length}</p>
        </div>
      </div>
    </div>
  );
}
