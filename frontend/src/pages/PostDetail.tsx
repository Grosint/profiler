import { useParams, Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import { ArrowLeft, Loader2, AlertCircle, MessageSquare, User, Flag } from 'lucide-react';
import { format } from 'date-fns';
import { api } from '../services/api';
import { getStatusColor, getStatusIcon } from '../utils/statusUtils';
import { Instagram, Facebook, Twitter, Globe } from 'lucide-react';

function PlatformIcon({ platform }: { platform: string }) {
  const platformLower = platform.toLowerCase();
  const iconClass = "w-5 h-5";

  if (platformLower === 'instagram') {
    return <Instagram className={iconClass} />;
  } else if (platformLower === 'facebook') {
    return <Facebook className={iconClass} />;
  } else if (platformLower === 'twitter') {
    return <Twitter className={iconClass} />;
  } else {
    return <Globe className={iconClass} />;
  }
}

export default function PostDetail() {
  const { postId } = useParams<{ postId: string }>();

  const { data: postResponse, isLoading, error } = useQuery(
    ['post', postId],
    () => api.getPost(postId!),
    {
      enabled: !!postId,
      refetchInterval: 5000, // Refetch every 5 seconds
    }
  );

  const post = postResponse?.data;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="max-w-4xl mx-auto">
        <Link to="/" className="btn-secondary mb-4 inline-flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>
        <div className="card bg-danger-900/20 border-danger-700">
          <AlertCircle className="w-12 h-12 text-danger-400 mx-auto mb-4" />
          <p className="text-center text-danger-300">
            Failed to load post analysis. Please try again.
          </p>
        </div>
      </div>
    );
  }

  const StatusIcon = getStatusIcon(post.status);
  const statusColor = getStatusColor(post.status);
  const analysis = post.analysis;

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <Link to="/" className="btn-secondary inline-flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>
        <span className={`status-badge ${statusColor}`}>
          <StatusIcon className="w-4 h-4 mr-2" />
          {post.status}
        </span>
      </div>

      {/* Post Info Card */}
      <div className="card">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center gap-3">
            <PlatformIcon platform={post.platform} />
            <MessageSquare className="w-5 h-5 text-primary-400" />
            <div>
              <h1 className="text-2xl font-bold text-dark-100">Post Analysis</h1>
              <p className="text-sm text-dark-400 mt-1">
                {post.postType === 'post' ? 'Post Search' : 'Profile Search'} • {post.platform}
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="text-sm font-medium text-dark-300">Post URL</label>
            <a
              href={post.postUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="block text-primary-400 hover:text-primary-300 break-all mt-1"
            >
              {post.postUrl}
            </a>
          </div>

          {post.externalRefId && (
            <div>
              <label className="text-sm font-medium text-dark-300">External Reference ID</label>
              <p className="text-dark-100 mt-1">{post.externalRefId}</p>
            </div>
          )}

          <div className="flex items-center gap-4 text-sm text-dark-400">
            <span>
              Created: {format(new Date(post.createdAt), 'MMM d, yyyy HH:mm')}
            </span>
            <span>
              Updated: {format(new Date(post.updatedAt), 'MMM d, yyyy HH:mm')}
            </span>
          </div>
        </div>
      </div>

      {/* Analysis Results */}
      {analysis && (
        <>
          {/* Post Content */}
          <div className="card">
            <h2 className="text-xl font-semibold text-dark-100 mb-4">Post Content</h2>
            <div className="bg-dark-800 rounded-lg p-4">
              <p className="text-dark-200 whitespace-pre-wrap">{analysis.post_text || 'No content available'}</p>
              {analysis.author_username && (
                <div className="mt-4 flex items-center gap-2 text-sm text-dark-400">
                  <User className="w-4 h-4" />
                  <span>
                    {analysis.author_name || analysis.author_username}
                    {analysis.author_url && (
                      <a
                        href={analysis.author_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="ml-2 text-primary-400 hover:text-primary-300"
                      >
                        (@{analysis.author_username})
                      </a>
                    )}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card border border-primary-700">
              <div className="text-sm text-dark-400 mb-1">Total Comments</div>
              <div className="text-2xl font-bold text-primary-300">{analysis.comments_count}</div>
            </div>
            <div className="card border border-primary-700">
              <div className="text-sm text-dark-400 mb-1">Analyzed</div>
              <div className="text-2xl font-bold text-primary-300">{analysis.comments_analyzed}</div>
            </div>
            <div className="card border border-danger-700">
              <div className="text-sm text-dark-400 mb-1">Toxic Comments</div>
              <div className="text-2xl font-bold text-danger-300">{analysis.toxic_comments_count}</div>
            </div>
            <div className="card border border-danger-700">
              <div className="text-sm text-dark-400 mb-1">Anti-National</div>
              <div className="text-2xl font-bold text-danger-300">{analysis.anti_national_comments_count}</div>
            </div>
          </div>

          {/* Flagged Commenters */}
          {analysis.flagged_commenters && analysis.flagged_commenters.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-dark-100 mb-4 flex items-center">
                <Flag className="w-5 h-5 mr-2 text-danger-400" />
                Flagged Commenters ({analysis.flagged_commenters.length})
              </h2>
              <div className="space-y-4">
                {analysis.flagged_commenters.map((commenter: any, index: number) => (
                  <div
                    key={index}
                    className="bg-dark-800 border border-danger-700 rounded-lg p-4"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-dark-400" />
                        <span className="font-semibold text-dark-100">
                          {commenter.name || commenter.username}
                        </span>
                        {commenter.username && (
                          <span className="text-sm text-dark-400">@{commenter.username}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 text-sm">
                        <span className="text-danger-400">
                          {commenter.anti_national_comments_count || 0} anti-national
                        </span>
                        <span className="text-warning-400">
                          {commenter.toxic_comments_count || 0} toxic
                        </span>
                      </div>
                    </div>
                    {commenter.comments && commenter.comments.length > 0 && (
                      <div className="mt-2 space-y-2">
                        {commenter.comments.slice(0, 3).map((comment: any, cIndex: number) => (
                          <div
                            key={cIndex}
                            className="bg-dark-900 rounded p-2 text-sm text-dark-300"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              {comment.is_anti_national && (
                                <span className="text-xs bg-danger-900/30 text-danger-300 px-2 py-0.5 rounded">
                                  Anti-National
                                </span>
                              )}
                              {comment.toxicity_score > 0 && (
                                <span className="text-xs text-warning-400">
                                  Toxicity: {(comment.toxicity_score * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                            <p className="text-dark-200">{comment.text}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All Comments */}
          {analysis.comments && analysis.comments.length > 0 && (
            <div className="card">
              <h2 className="text-xl font-semibold text-dark-100 mb-4">All Comments</h2>
              <div className="space-y-3 max-h-96 overflow-y-auto">
                {analysis.comments.map((comment) => (
                  <div
                    key={comment.comment_id}
                    className={`bg-dark-800 rounded-lg p-4 border ${
                      comment.is_anti_national
                        ? 'border-danger-700'
                        : comment.is_toxic
                        ? 'border-warning-700'
                        : 'border-dark-700'
                    }`}
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-dark-400" />
                        <span className="font-medium text-dark-200">
                          {comment.author_name || comment.author_username || 'Unknown'}
                        </span>
                        {comment.author_username && (
                          <span className="text-sm text-dark-400">@{comment.author_username}</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {comment.is_anti_national && (
                          <span className="text-xs bg-danger-900/30 text-danger-300 px-2 py-1 rounded">
                            Anti-National
                          </span>
                        )}
                        {comment.is_toxic && !comment.is_anti_national && (
                          <span className="text-xs bg-warning-900/30 text-warning-300 px-2 py-1 rounded">
                            Toxic
                          </span>
                        )}
                      </div>
                    </div>
                    <p className="text-dark-200 mb-2">{comment.text}</p>
                    <div className="flex items-center gap-4 text-xs text-dark-500">
                      {comment.toxicity_score > 0 && (
                        <span>Toxicity: {(comment.toxicity_score * 100).toFixed(0)}%</span>
                      )}
                      <span>Sentiment: {comment.sentiment}</span>
                      {comment.timestamp && (
                        <span>{format(new Date(comment.timestamp), 'MMM d, yyyy HH:mm')}</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}

      {!analysis && post.status === 'completed' && (
        <div className="card">
          <AlertCircle className="w-12 h-12 text-warning-400 mx-auto mb-4" />
          <p className="text-center text-dark-400">
            Analysis completed but no results available.
          </p>
        </div>
      )}

      {post.errorMessage && (
        <div className="card bg-danger-900/20 border-danger-700">
          <AlertCircle className="w-5 h-5 text-danger-400 mb-2" />
          <p className="text-danger-300">{post.errorMessage}</p>
        </div>
      )}
    </div>
  );
}
