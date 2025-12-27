import { useState } from 'react';
import { FileText, ChevronDown, ChevronUp, ExternalLink } from 'lucide-react';
import type { ScrapedDataItem } from '../types/api';
import { format } from 'date-fns';

interface RawDataViewProps {
  data: ScrapedDataItem[];
}

export default function RawDataView({ data }: RawDataViewProps) {
  const [expandedItems, setExpandedItems] = useState<Set<number>>(new Set());

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedItems(newExpanded);
  };

  if (data.length === 0) {
    return (
      <div className="card">
        <div className="flex items-center mb-6">
          <FileText className="w-5 h-5 mr-2 text-primary-400" />
          <h2 className="text-xl font-semibold text-dark-100">Raw Scraped Data</h2>
        </div>
        <div className="text-center py-8 text-dark-500">
          No raw data available
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <FileText className="w-5 h-5 mr-2 text-primary-400" />
          <h2 className="text-xl font-semibold text-dark-100">Raw Scraped Data</h2>
        </div>
        <span className="text-sm text-dark-500">{data.length} sources</span>
      </div>

      <div className="space-y-4">
        {data.map((item, index) => {
          const isExpanded = expandedItems.has(index);
          return (
            <div
              key={index}
              className="bg-dark-800 border border-dark-700 rounded-lg overflow-hidden"
            >
              {/* Header */}
              <button
                onClick={() => toggleExpand(index)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-dark-700 transition-colors"
              >
                <div className="flex items-center space-x-3 flex-1 text-left">
                  <div className="w-2 h-2 rounded-full bg-primary-500" />
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="font-medium text-dark-100 capitalize">{item.platform}</span>
                      <span className="text-xs text-dark-500">
                        {format(new Date(item.scrapedAt), 'MMM d, yyyy HH:mm')}
                      </span>
                      {item.scrapeStatus && (
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          item.scrapeStatus === 'success'
                            ? 'bg-success-900/20 text-success-400 border border-success-700'
                            : 'bg-danger-900/20 text-danger-400 border border-danger-700'
                        }`}>
                          {item.scrapeStatus}
                        </span>
                      )}
                    </div>
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      onClick={(e) => e.stopPropagation()}
                      className="text-sm text-primary-400 hover:text-primary-300 flex items-center mt-1"
                    >
                      {item.url}
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>
                </div>
                {isExpanded ? (
                  <ChevronUp className="w-5 h-5 text-dark-500" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-dark-500" />
                )}
              </button>

              {/* Expanded Content */}
              {isExpanded && (
                <div className="px-4 pb-4 border-t border-dark-700">
                  <div className="mt-4 space-y-3">
                    {item.rawContent && (
                      <div>
                        <p className="text-xs font-medium text-dark-400 mb-2">Raw Content:</p>
                        <pre className="p-4 bg-dark-900 rounded-lg overflow-x-auto text-xs text-dark-300 max-h-64 overflow-y-auto">
                          {item.rawContent}
                        </pre>
                      </div>
                    )}
                    {item.metadata && Object.keys(item.metadata).length > 0 && (
                      <div>
                        <p className="text-xs font-medium text-dark-400 mb-2">Metadata:</p>
                        <pre className="p-4 bg-dark-900 rounded-lg overflow-x-auto text-xs text-dark-300">
                          {JSON.stringify(item.metadata, null, 2)}
                        </pre>
                      </div>
                    )}
                    {item.errorMessage && (
                      <div className="p-3 bg-danger-900/20 border border-danger-700 rounded-lg">
                        <p className="text-xs font-medium text-danger-400 mb-1">Error:</p>
                        <p className="text-xs text-danger-300">{item.errorMessage}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
