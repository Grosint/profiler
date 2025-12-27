import { Clock, CheckCircle, FileText } from 'lucide-react';
import { format } from 'date-fns';
import type { ProfileStatusResponse, ProfileDetailsResponse, ScrapedDataItem } from '../types/api';

interface ActivityTimelineProps {
  profile: ProfileStatusResponse;
  details?: ProfileDetailsResponse | null;
  rawData: ScrapedDataItem[];
}

export default function ActivityTimeline({ profile, details, rawData }: ActivityTimelineProps) {
  const events = [
    {
      type: 'created',
      timestamp: profile.createdAt,
      title: 'Profile Created',
      description: 'Profile analysis job initiated',
      icon: CheckCircle,
      color: 'text-primary-400',
    },
    ...(rawData.map((item) => ({
      type: 'scraped',
      timestamp: item.scrapedAt,
      title: `Data Scraped: ${item.platform}`,
      description: `Scraped from ${item.url}`,
      icon: FileText,
      color: 'text-success-400',
    }))),
    {
      type: 'processed',
      timestamp: profile.updatedAt,
      title: 'Analysis Completed',
      description: details ? 'Profile traits and insights generated' : 'Processing completed',
      icon: CheckCircle,
      color: 'text-success-400',
    },
  ].sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  return (
    <div className="card">
      <div className="flex items-center mb-6">
        <Clock className="w-5 h-5 mr-2 text-primary-400" />
        <h2 className="text-xl font-semibold text-dark-100">Activity Timeline</h2>
      </div>

      <div className="relative">
        {/* Timeline Line */}
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-dark-700" />

        {/* Events */}
        <div className="space-y-6">
          {events.map((event, index) => {
            const Icon = event.icon;
            return (
              <div key={index} className="relative flex items-start">
                {/* Icon */}
                <div className={`relative z-10 flex items-center justify-center w-8 h-8 rounded-full bg-dark-800 border-2 border-dark-700 ${event.color}`}>
                  <Icon className="w-4 h-4" />
                </div>

                {/* Content */}
                <div className="ml-4 flex-1 pb-6">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-medium text-dark-100">{event.title}</h3>
                    <span className="text-xs text-dark-500">
                      {format(new Date(event.timestamp), 'MMM d, yyyy HH:mm')}
                    </span>
                  </div>
                  <p className="text-sm text-dark-400">{event.description}</p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
