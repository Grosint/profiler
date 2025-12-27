import { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Plus,
  Search,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  TrendingUp,
  Activity,
  AlertCircle,
  RefreshCw,
  Instagram,
  Facebook,
  Twitter,
  Globe,
  User,
  MessageSquare
} from 'lucide-react';
import { format } from 'date-fns';
import { ProfileStatus, PostStatus, PostType } from '../types/api';
import { getStatusColor, getStatusIcon } from '../utils/statusUtils';
import { api } from '../services/api';

// Platform icon component
function PlatformIcon({ platform }: { platform: string }) {
  const platformLower = platform.toLowerCase();
  const iconClass = "w-4 h-4";

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

export default function Dashboard() {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<ProfileStatus | PostStatus | 'all'>('all');
  const [viewType, setViewType] = useState<'all' | 'profiles' | 'posts'>('all');

  // Fetch profiles from API
  const {
    data: profilesResponse,
    isLoading: profilesLoading,
    error: profilesError,
    refetch: refetchProfiles,
  } = useQuery(
    ['profiles', statusFilter === 'all' ? undefined : (statusFilter as ProfileStatus)],
    () => api.listProfiles(0, 1000, statusFilter === 'all' ? undefined : (statusFilter as ProfileStatus)),
    {
      refetchInterval: 10000,
      enabled: viewType === 'all' || viewType === 'profiles',
    }
  );

  // Fetch posts from API
  const {
    data: postsResponse,
    isLoading: postsLoading,
    error: postsError,
    refetch: refetchPosts,
  } = useQuery(
    ['posts', statusFilter === 'all' ? undefined : (statusFilter as PostStatus)],
    () => api.listPosts(0, 1000, statusFilter === 'all' ? undefined : (statusFilter as PostStatus)),
    {
      refetchInterval: 10000,
      enabled: viewType === 'all' || viewType === 'posts',
    }
  );

  const profiles = profilesResponse?.data || [];
  const posts = postsResponse?.data || [];

  const isLoading = profilesLoading || postsLoading;
  const error = profilesError || postsError;

  const refetch = () => {
    refetchProfiles();
    refetchPosts();
  };

  // Filter profiles and posts by search query
  const filteredProfiles = useMemo(() => {
    return profiles.filter(profile => {
      const matchesSearch = !searchQuery ||
        profile.subjectName?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        profile.externalRefId?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        profile.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [profiles, searchQuery]);

  const filteredPosts = useMemo(() => {
    return posts.filter(post => {
      const matchesSearch = !searchQuery ||
        post.postUrl?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.externalRefId?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        post.id.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesSearch;
    });
  }, [posts, searchQuery]);

  // Calculate statistics
  const stats = useMemo(() => {
    const allProfiles = profiles.length;
    const allPosts = posts.length;
    const completedProfiles = profiles.filter(p => p.status === ProfileStatus.COMPLETED).length;
    const completedPosts = posts.filter(p => p.status === PostStatus.COMPLETED).length;
    const processingProfiles = profiles.filter(p =>
      [ProfileStatus.SCRAPING, ProfileStatus.PROCESSING, ProfileStatus.ANALYZING, ProfileStatus.PENDING].includes(p.status)
    ).length;
    const processingPosts = posts.filter(p =>
      [PostStatus.SCRAPING, PostStatus.PROCESSING, PostStatus.ANALYZING, PostStatus.PENDING].includes(p.status)
    ).length;
    const failedProfiles = profiles.filter(p => p.status === ProfileStatus.FAILED).length;
    const failedPosts = posts.filter(p => p.status === PostStatus.FAILED).length;

    return {
      total: allProfiles + allPosts,
      totalProfiles: allProfiles,
      totalPosts: allPosts,
      completed: completedProfiles + completedPosts,
      processing: processingProfiles + processingPosts,
      failed: failedProfiles + failedPosts,
    };
  }, [profiles, posts]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-dark-100 mb-2">Intelligence Dashboard</h1>
          <p className="text-dark-400">Monitor and analyze profiles and posts</p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="btn-secondary flex items-center"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <Link to="/create" className="btn-primary flex items-center">
            <Plus className="w-5 h-5 mr-2" />
            New Analysis
          </Link>
        </div>
      </div>

      {/* View Type Toggle */}
      <div className="card">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-dark-300">View:</span>
          <div className="flex gap-2">
            <button
              onClick={() => setViewType('all')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewType === 'all'
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
              }`}
            >
              All
            </button>
            <button
              onClick={() => setViewType('profiles')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewType === 'profiles'
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
              }`}
            >
              <User className="w-4 h-4 inline mr-2" />
              Profiles
            </button>
            <button
              onClick={() => setViewType('posts')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                viewType === 'posts'
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Posts
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Profiles"
          value={stats.total}
          icon={<Activity className="w-5 h-5" />}
          color="primary"
        />
        <StatCard
          title="Completed"
          value={stats.completed}
          icon={<CheckCircle className="w-5 h-5" />}
          color="success"
        />
        <StatCard
          title="In Progress"
          value={stats.processing}
          icon={<Loader2 className="w-5 h-5" />}
          color="warning"
        />
        <StatCard
          title="Failed"
          value={stats.failed}
          icon={<XCircle className="w-5 h-5" />}
          color="danger"
        />
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-dark-500 w-5 h-5" />
            <input
              type="text"
              placeholder="Search profiles..."
              className="input-field pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
          <select
            className="input-field md:w-48"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as ProfileStatus | 'all')}
          >
            <option value="all">All Statuses</option>
            <option value={ProfileStatus.PENDING}>Pending</option>
            <option value={ProfileStatus.SCRAPING}>Scraping</option>
            <option value={ProfileStatus.PROCESSING}>Processing</option>
            <option value={ProfileStatus.ANALYZING}>Analyzing</option>
            <option value={ProfileStatus.COMPLETED}>Completed</option>
            <option value={ProfileStatus.FAILED}>Failed</option>
          </select>
        </div>
      </div>

      {/* Combined List */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-dark-100">
            {viewType === 'all' ? 'All Analyses' : viewType === 'profiles' ? 'Profiles' : 'Posts'}
          </h2>
          {isLoading && (
            <Loader2 className="w-5 h-5 animate-spin text-primary-500" />
          )}
        </div>

        {error ? (
          <div className="bg-danger-900/20 border border-danger-700 text-danger-300 px-4 py-3 rounded-lg mb-4">
            Failed to load data. Please try again.
          </div>
        ) : null}

        {isLoading && !profilesResponse && !postsResponse ? (
          <div className="text-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-4" />
            <p className="text-dark-400">Loading...</p>
          </div>
        ) : (
          (viewType === 'all' && filteredProfiles.length === 0 && filteredPosts.length === 0) ||
          (viewType === 'profiles' && filteredProfiles.length === 0) ||
          (viewType === 'posts' && filteredPosts.length === 0)
        ) ? (
          <div className="text-center py-12">
            <AlertCircle className="w-12 h-12 text-dark-600 mx-auto mb-4" />
            <p className="text-dark-400 mb-4">
              {searchQuery ? 'No results match your search' : 'No analyses found'}
            </p>
            <Link to="/create" className="btn-primary inline-flex items-center">
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Analysis
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {(viewType === 'all' || viewType === 'profiles') && filteredProfiles.map((profile) => (
              <ProfileCard key={`profile-${profile.id}`} profile={profile} />
            ))}
            {(viewType === 'all' || viewType === 'posts') && filteredPosts.map((post) => (
              <PostCard key={`post-${post.id}`} post={post} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: 'primary' | 'success' | 'warning' | 'danger';
}

function StatCard({ title, value, icon, color }: StatCardProps) {
  const colorClasses = {
    primary: 'bg-primary-900/20 border-primary-700 text-primary-300',
    success: 'bg-success-900/20 border-success-700 text-success-300',
    warning: 'bg-warning-900/20 border-warning-700 text-warning-300',
    danger: 'bg-danger-900/20 border-danger-700 text-danger-300',
  };

  return (
    <div className={`card border ${colorClasses[color]}`}>
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-dark-400 mb-1">{title}</p>
          <p className="text-3xl font-bold">{value}</p>
        </div>
        <div className={colorClasses[color]}>
          {icon}
        </div>
      </div>
    </div>
  );
}

interface ProfileCardProps {
  profile: {
    id: string;
    subjectName?: string | null;
    externalRefId?: string | null;
    status: ProfileStatus;
    createdAt: string;
    updatedAt: string;
    errorMessage?: string | null;
    traitsOverview: Array<{ traitType: string; averageScore: number }>;
  };
}

function ProfileCard({ profile }: ProfileCardProps) {
  const StatusIcon = getStatusIcon(profile.status);
  const statusColor = getStatusColor(profile.status);

  return (
    <Link
      to={`/profiles/${profile.id}`}
      className="block bg-dark-800 hover:bg-dark-700 border border-dark-700 rounded-lg p-4 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <User className="w-4 h-4 text-primary-400" />
            <h3 className="text-lg font-semibold text-dark-100">
              {profile.subjectName || profile.externalRefId || `Profile ${profile.id.substring(0, 8)}`}
            </h3>
            <span className={`status-badge ${statusColor}`}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {profile.status}
            </span>
            <span className="text-xs bg-primary-900/20 text-primary-300 px-2 py-1 rounded border border-primary-700">
              Profile Search
            </span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-dark-400 mb-2">
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              Created {format(new Date(profile.createdAt), 'MMM d, yyyy HH:mm')}
            </span>
            {profile.externalRefId && (
              <span className="text-xs bg-dark-700 px-2 py-0.5 rounded">
                Ref: {profile.externalRefId}
              </span>
            )}
          </div>
          {profile.traitsOverview.length > 0 && (
            <div className="flex items-center gap-2 text-xs text-dark-500">
              <Activity className="w-3 h-3" />
              <span>{profile.traitsOverview.length} trait categories analyzed</span>
            </div>
          )}
          {profile.errorMessage && (
            <div className="mt-2 text-danger-400 text-xs flex items-center">
              <AlertCircle className="w-3 h-3 mr-1" />
              {profile.errorMessage}
            </div>
          )}
        </div>
        <div className="text-dark-500">
          <TrendingUp className="w-5 h-5" />
        </div>
      </div>
    </Link>
  );
}

interface PostCardProps {
  post: {
    id: string;
    postUrl: string;
    postType: PostType;
    platform: string;
    status: PostStatus;
    createdAt: string;
    updatedAt: string;
    errorMessage?: string | null;
    externalRefId?: string | null;
    comments_count: number;
    flagged_commenters_count: number;
  };
}

function PostCard({ post }: PostCardProps) {
  const StatusIcon = getStatusIcon(post.status);
  const statusColor = getStatusColor(post.status);

  return (
    <Link
      to={`/posts/${post.id}`}
      className="block bg-dark-800 hover:bg-dark-700 border border-dark-700 rounded-lg p-4 transition-colors"
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <div className="flex items-center space-x-3 mb-2">
            <PlatformIcon platform={post.platform} />
            <MessageSquare className="w-4 h-4 text-primary-400" />
            <h3 className="text-lg font-semibold text-dark-100 truncate">
              {post.postUrl}
            </h3>
            <span className={`status-badge ${statusColor}`}>
              <StatusIcon className="w-3 h-3 mr-1" />
              {post.status}
            </span>
            <span className="text-xs bg-success-900/20 text-success-300 px-2 py-1 rounded border border-success-700">
              Post Search
            </span>
          </div>
          <div className="flex items-center space-x-4 text-sm text-dark-400 mb-2">
            <span className="flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              Created {format(new Date(post.createdAt), 'MMM d, yyyy HH:mm')}
            </span>
            {post.externalRefId && (
              <span className="text-xs bg-dark-700 px-2 py-0.5 rounded">
                Ref: {post.externalRefId}
              </span>
            )}
          </div>
          <div className="flex items-center gap-4 text-xs text-dark-500">
            <span className="flex items-center">
              <MessageSquare className="w-3 h-3 mr-1" />
              {post.comments_count} comments
            </span>
            {post.flagged_commenters_count > 0 && (
              <span className="flex items-center text-danger-400">
                <AlertCircle className="w-3 h-3 mr-1" />
                {post.flagged_commenters_count} flagged
              </span>
            )}
          </div>
          {post.errorMessage && (
            <div className="mt-2 text-danger-400 text-xs flex items-center">
              <AlertCircle className="w-3 h-3 mr-1" />
              {post.errorMessage}
            </div>
          )}
        </div>
        <div className="text-dark-500">
          <TrendingUp className="w-5 h-5" />
        </div>
      </div>
    </Link>
  );
}
