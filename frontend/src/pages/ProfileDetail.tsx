import { useParams } from 'react-router-dom';
import { useQuery } from 'react-query';
import {
  Loader2,
  AlertCircle,
  ArrowLeft,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import ProfileHeader from '../components/ProfileHeader';
import ProfileTraits from '../components/ProfileTraits';
import ActivityTimeline from '../components/ActivityTimeline';
import NetworkGraph from '../components/NetworkGraph';
import RiskIndicators from '../components/RiskIndicators';
import RawDataView from '../components/RawDataView';
import ProfileSummary from '../components/ProfileSummary';
import TraitDistributionChart from '../components/TraitDistributionChart';
import TraitComparisonChart from '../components/TraitComparisonChart';
import ConfidenceHeatmap from '../components/ConfidenceHeatmap';
import SummaryInsights from '../components/SummaryInsights';
import ProfileDataView from '../components/ProfileDataView';

export default function ProfileDetail() {
  const { profileId } = useParams<{ profileId: string }>();

  const {
    data: profileData,
    isLoading: isLoadingProfile,
    error: profileError,
    refetch: refetchProfile,
  } = useQuery(
    ['profile', profileId],
    () => api.getProfile(profileId!),
    {
      enabled: !!profileId,
      refetchInterval: (data) => {
        // Poll if status is not completed or failed
        const status = data?.data?.status;
        if (status && !['completed', 'failed'].includes(status)) {
          return 5000; // Poll every 5 seconds
        }
        return false;
      },
    }
  );

  const {
    data: detailsData,
    isLoading: isLoadingDetails,
  } = useQuery(
    ['profile-details', profileId],
    () => api.getProfileDetails(profileId!),
    {
      enabled: !!profileId && profileData?.data?.status === 'completed',
    }
  );

  const {
    data: rawData,
  } = useQuery(
    ['profile-raw-data', profileId],
    () => api.getProfileRawData(profileId!),
    {
      enabled: !!profileId && profileData?.data?.status === 'completed',
    }
  );

  if (isLoadingProfile) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-primary-500" />
      </div>
    );
  }

  if (profileError || !profileData?.data) {
    return (
      <div className="card text-center py-12">
        <AlertCircle className="w-12 h-12 text-danger-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-dark-100 mb-2">Profile Not Found</h2>
        <p className="text-dark-400 mb-4">
          {profileError ? 'Failed to load profile' : 'The requested profile does not exist'}
        </p>
        <Link to="/" className="btn-primary inline-flex items-center">
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Dashboard
        </Link>
      </div>
    );
  }

  const profile = profileData.data;
  const details = detailsData?.data;
  const isCompleted = profile.status === 'completed';
  const isLoading = isLoadingProfile || (isCompleted && isLoadingDetails);

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        to="/"
        className="inline-flex items-center text-dark-400 hover:text-dark-200 transition-colors"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </Link>

      {/* Profile Header */}
      <ProfileHeader
        profile={profile}
        details={details}
        onRefresh={refetchProfile}
      />

      {/* Status Alert */}
      {profile.status === 'failed' && profile.errorMessage && (
        <div className="card bg-danger-900/20 border-danger-700">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-danger-400 mr-3 mt-0.5" />
            <div>
              <h3 className="font-semibold text-danger-300 mb-1">Processing Failed</h3>
              <p className="text-danger-400 text-sm">{profile.errorMessage}</p>
            </div>
          </div>
        </div>
      )}

      {/* Loading State - Only show if we don't have profile data */}
      {isLoading && !profile && (
        <div className="card text-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-primary-500 mx-auto mb-2" />
          <p className="text-dark-400">Loading profile details...</p>
        </div>
      )}

      {/* Content Grid */}
      {isCompleted && (
        <>
          {/* Always show ProfileDataView first - it shows summary and overview */}
          <ProfileDataView profile={profile} details={details || undefined} />

          {details && (
            <>
              {/* Quick Insights - Only show if we have traits */}
              {details.traits.length > 0 && <SummaryInsights details={details} />}

              {/* Summary Section */}
              <ProfileSummary details={details} />

              {/* Charts Grid - Multiple Visualizations */}
              {details.traits.length > 0 && (
                <>
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <TraitDistributionChart traits={details.traits} />
                    <ConfidenceHeatmap traits={details.traits} />
                  </div>

                  <TraitComparisonChart traits={details.traits} />
                </>
              )}

              {/* Main Content Grid */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Left Column - Main Content */}
                <div className="lg:col-span-2 space-y-6">
                  {/* Traits - Show detailed traits if available */}
                  {details.traits.length > 0 ? (
                    <ProfileTraits traits={details.traits} />
                  ) : (
                    <div className="card">
                      <div className="text-center py-8">
                        <p className="text-dark-400 mb-2">No detailed traits available</p>
                        <p className="text-sm text-dark-500">
                          Check the summary data above for analysis results
                        </p>
                      </div>
                    </div>
                  )}

                  {/* Activity Timeline */}
                  <ActivityTimeline
                    profile={profile}
                    details={details}
                    rawData={rawData?.data || []}
                  />

                  {/* Raw Data */}
                  <RawDataView data={rawData?.data || []} />
                </div>

                {/* Right Column - Sidebar */}
                <div className="space-y-6">
                  {/* Risk Indicators */}
                  {details.traits.length > 0 && (
                    <RiskIndicators
                      traits={details.traits}
                      narratives={details.narratives}
                    />
                  )}

                  {/* Network Graph */}
                  <NetworkGraph
                    profile={profile}
                    details={details}
                  />
                </div>
              </div>
            </>
          )}

          {/* Show message if details aren't loaded but profile is completed */}
          {!details && !isLoadingDetails && (
            <div className="card bg-warning-900/20 border-warning-700">
              <div className="flex items-start">
                <AlertCircle className="w-5 h-5 text-warning-400 mr-3 mt-0.5" />
                <div>
                  <h3 className="font-semibold text-warning-300 mb-1">Limited Data Available</h3>
                  <p className="text-warning-400 text-sm">
                    Profile analysis completed, but detailed traits may not be available.
                    Check the summary data above for available information.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Loading details state */}
          {isLoadingDetails && (
            <div className="card">
              <div className="text-center py-8">
                <Loader2 className="w-8 h-8 animate-spin text-primary-500 mx-auto mb-4" />
                <p className="text-dark-400 mb-2">Loading detailed analysis...</p>
                <p className="text-sm text-dark-500">
                  Profile processing completed. Fetching detailed results...
                </p>
              </div>
            </div>
          )}
        </>
      )}

      {/* Processing State */}
      {!isCompleted && profile.status !== 'failed' && (
        <div className="card">
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <Loader2 className="w-12 h-12 animate-spin text-primary-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-dark-100 mb-2">
                Processing Profile
              </h3>
              <p className="text-dark-400 mb-2">Status: {profile.status}</p>
              <p className="text-sm text-dark-500">
                This page will automatically update when processing completes
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
