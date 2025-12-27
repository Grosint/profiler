import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Instagram, Facebook, Twitter, Globe, Plus, X, Loader2, Link as LinkIcon, AlertCircle, MessageSquare, User } from 'lucide-react';
import { api } from '../services/api';
import type { CreateProfileRequest, CreatePostAnalysisRequest } from '../types/api';
import { detectPlatformFromUrl, validateUrl, isPostUrl, type PlatformType } from '../utils/urlDetector';

type InputMode = 'single' | 'multiple';
type SearchType = 'profile' | 'post';

export default function ProfileCreate() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchType, setSearchType] = useState<SearchType>('profile');
  const [inputMode, setInputMode] = useState<InputMode>('single');
  const [singleUrl, setSingleUrl] = useState('');
  const [detectedPlatform, setDetectedPlatform] = useState<PlatformType | null>(null);
  const [formData, setFormData] = useState<CreateProfileRequest>({
    subjectName: '',
    externalRefId: '',
    urls: {
      instagramUrl: '',
      facebookUrl: '',
      twitterUrl: '',
      blogUrls: [],
    },
    metadata: {},
  });
  const [blogUrl, setBlogUrl] = useState('');

  const handleSingleUrlChange = (url: string) => {
    setSingleUrl(url);
    if (url.trim()) {
      const platform = detectPlatformFromUrl(url);
      setDetectedPlatform(platform);

      // Auto-detect search type based on URL
      if (isPostUrl(url)) {
        setSearchType('post');
      } else {
        setSearchType('profile');
      }

      // Auto-populate the appropriate field
      const cleanedUrl = url.trim();
      if (platform === 'instagram') {
        setFormData({
          ...formData,
          urls: { ...formData.urls, instagramUrl: cleanedUrl, facebookUrl: '', twitterUrl: '', blogUrls: [] },
        });
      } else if (platform === 'facebook') {
        setFormData({
          ...formData,
          urls: { ...formData.urls, facebookUrl: cleanedUrl, instagramUrl: '', twitterUrl: '', blogUrls: [] },
        });
      } else if (platform === 'twitter') {
        setFormData({
          ...formData,
          urls: { ...formData.urls, twitterUrl: cleanedUrl, instagramUrl: '', facebookUrl: '', blogUrls: [] },
        });
      } else if (platform === 'blog') {
        setFormData({
          ...formData,
          urls: { ...formData.urls, blogUrls: [cleanedUrl], instagramUrl: '', facebookUrl: '', twitterUrl: '' },
        });
      }
    } else {
      setDetectedPlatform(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      // Handle post analysis
      if (searchType === 'post') {
        const validation = validateUrl(singleUrl);
        if (!validation.valid) {
          setError(validation.error || 'Please provide a valid URL');
          setLoading(false);
          return;
        }

        const platform = detectPlatformFromUrl(singleUrl);
        if (platform === 'unknown') {
          setError('Unable to detect platform. Please use a supported platform URL.');
          setLoading(false);
          return;
        }

        const payload: CreatePostAnalysisRequest = {
          postUrl: singleUrl.trim(),
          externalRefId: formData.externalRefId?.trim() || null,
          metadata: formData.metadata,
        };

        const response = await api.createPostAnalysis(payload);

        if (response.success && response.data) {
          navigate(`/posts/${response.data.id}`);
        } else {
          setError(response.error?.message || 'Failed to create post analysis');
        }
        setLoading(false);
        return;
      }

      // Handle profile analysis (existing code)
      let cleanedUrls;

      if (inputMode === 'single') {
        // Validate single URL
        const validation = validateUrl(singleUrl);
        if (!validation.valid) {
          setError(validation.error || 'Please provide a valid URL');
          setLoading(false);
          return;
        }

        const platform = detectPlatformFromUrl(singleUrl);
        if (platform === 'unknown') {
          setError('Unable to detect platform. Please use Instagram, Facebook, Twitter, or a blog URL.');
          setLoading(false);
          return;
        }

        cleanedUrls = {
          instagramUrl: platform === 'instagram' ? singleUrl.trim() : null,
          facebookUrl: platform === 'facebook' ? singleUrl.trim() : null,
          twitterUrl: platform === 'twitter' ? singleUrl.trim() : null,
          blogUrls: platform === 'blog' ? [singleUrl.trim()] : null,
        };
      } else {
        // Multiple URLs mode
        cleanedUrls = {
          instagramUrl: formData.urls.instagramUrl?.trim() || null,
          facebookUrl: formData.urls.facebookUrl?.trim() || null,
          twitterUrl: formData.urls.twitterUrl?.trim() || null,
          blogUrls: formData.urls.blogUrls?.filter(url => url.trim()) || null,
        };

        // Check if at least one URL is provided
        if (!cleanedUrls.instagramUrl && !cleanedUrls.facebookUrl &&
            !cleanedUrls.twitterUrl && (!cleanedUrls.blogUrls || cleanedUrls.blogUrls.length === 0)) {
          setError('Please provide at least one profile URL');
          setLoading(false);
          return;
        }
      }

      const payload: CreateProfileRequest = {
        subjectName: formData.subjectName?.trim() || null,
        externalRefId: formData.externalRefId?.trim() || null,
        urls: cleanedUrls,
        metadata: formData.metadata,
      };

      const response = await api.createProfile(payload);

      if (response.success && response.data) {
        navigate(`/profiles/${response.data.id}`);
      } else {
        setError(response.error?.message || 'Failed to create profile');
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || err.message || 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const addBlogUrl = () => {
    if (blogUrl.trim()) {
      setFormData({
        ...formData,
        urls: {
          ...formData.urls,
          blogUrls: [...(formData.urls.blogUrls || []), blogUrl.trim()],
        },
      });
      setBlogUrl('');
    }
  };

  const removeBlogUrl = (index: number) => {
    const newBlogUrls = [...(formData.urls.blogUrls || [])];
    newBlogUrls.splice(index, 1);
    setFormData({
      ...formData,
      urls: {
        ...formData.urls,
        blogUrls: newBlogUrls,
      },
    });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-dark-100 mb-2">Create New Profile</h1>
        <p className="text-dark-400">Enter profile URLs from supported platforms to begin analysis</p>
      </div>

      <form onSubmit={handleSubmit} className="card space-y-6">
        {/* Search Type Toggle */}
        <div className="flex items-center justify-between p-4 bg-dark-800 rounded-lg border border-dark-700">
          <span className="text-sm font-medium text-dark-300">Search Type:</span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setSearchType('profile')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                searchType === 'profile'
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
              }`}
            >
              <User className="w-4 h-4 inline mr-2" />
              Profile Search
            </button>
            <button
              type="button"
              onClick={() => setSearchType('post')}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                searchType === 'post'
                  ? 'bg-primary-600 text-white'
                  : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
              }`}
            >
              <MessageSquare className="w-4 h-4 inline mr-2" />
              Post Search
            </button>
          </div>
        </div>

        {/* Input Mode Toggle (only for profile search) */}
        {searchType === 'profile' && (
          <div className="flex items-center justify-between p-4 bg-dark-800 rounded-lg border border-dark-700">
            <span className="text-sm font-medium text-dark-300">Input Mode:</span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setInputMode('single')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  inputMode === 'single'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
                }`}
              >
                <LinkIcon className="w-4 h-4 inline mr-2" />
                Single URL
              </button>
              <button
                type="button"
                onClick={() => setInputMode('multiple')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  inputMode === 'multiple'
                    ? 'bg-primary-600 text-white'
                    : 'bg-dark-700 text-dark-400 hover:bg-dark-600'
                }`}
              >
                <Globe className="w-4 h-4 inline mr-2" />
                Multiple URLs
              </button>
            </div>
          </div>
        )}

        {/* Subject Information */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-dark-100 border-b border-dark-800 pb-2">
            Subject Information
          </h2>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              Subject Name (Optional)
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Enter subject name"
              value={formData.subjectName || ''}
              onChange={(e) => setFormData({ ...formData, subjectName: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-dark-300 mb-2">
              External Reference ID (Optional)
            </label>
            <input
              type="text"
              className="input-field"
              placeholder="Enter external reference ID"
              value={formData.externalRefId || ''}
              onChange={(e) => setFormData({ ...formData, externalRefId: e.target.value })}
            />
          </div>
        </div>

        {/* Profile URLs */}
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-dark-100 border-b border-dark-800 pb-2">
            Profile URLs
          </h2>

          {/* Single URL Mode */}
          {(inputMode === 'single' || searchType === 'post') && (
            <div>
              <label className="block text-sm font-medium text-dark-300 mb-2">
                {searchType === 'post' ? 'Post URL' : 'Profile URL'}
              </label>
              <input
                type="url"
                className="input-field"
                placeholder={
                  searchType === 'post'
                    ? "https://twitter.com/username/status/123456 or https://facebook.com/username/posts/123456 or https://instagram.com/p/ABC123"
                    : "https://www.instagram.com/username/ or https://twitter.com/username or https://facebook.com/username or any blog URL"
                }
                value={singleUrl}
                onChange={(e) => handleSingleUrlChange(e.target.value)}
                required
              />
              {detectedPlatform && detectedPlatform !== 'unknown' && (
                <div className="mt-2 flex items-center text-sm">
                  <span className="text-dark-400 mr-2">Detected platform:</span>
                  {detectedPlatform === 'instagram' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Instagram className="w-4 h-4 mr-1" />
                      Instagram
                    </span>
                  )}
                  {detectedPlatform === 'facebook' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Facebook className="w-4 h-4 mr-1" />
                      Facebook
                    </span>
                  )}
                  {detectedPlatform === 'twitter' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Twitter className="w-4 h-4 mr-1" />
                      Twitter/X
                    </span>
                  )}
                  {detectedPlatform === 'reddit' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Globe className="w-4 h-4 mr-1" />
                      Reddit
                    </span>
                  )}
                  {detectedPlatform === 'linkedin' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Globe className="w-4 h-4 mr-1" />
                      LinkedIn
                    </span>
                  )}
                  {detectedPlatform === 'blog' && (
                    <span className="inline-flex items-center px-2 py-1 rounded bg-primary-900/20 text-primary-300 border border-primary-700">
                      <Globe className="w-4 h-4 mr-1" />
                      Blog/Website
                    </span>
                  )}
                  {searchType === 'post' && isPostUrl(singleUrl) && (
                    <span className="ml-2 inline-flex items-center px-2 py-1 rounded bg-success-900/20 text-success-300 border border-success-700">
                      <MessageSquare className="w-4 h-4 mr-1" />
                      Post URL Detected
                    </span>
                  )}
                </div>
              )}
              {singleUrl && detectedPlatform === 'unknown' && (
                <div className="mt-2 flex items-center text-sm text-warning-400">
                  <AlertCircle className="w-4 h-4 mr-1" />
                  Unable to detect platform. Please ensure the URL is valid.
                </div>
              )}
            </div>
          )}

          {/* Multiple URLs Mode */}
          {inputMode === 'multiple' && (
            <>
              {/* Instagram */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  <Instagram className="w-4 h-4 inline mr-2" />
                  Instagram Profile URL
                </label>
                <input
                  type="url"
                  className="input-field"
                  placeholder="https://www.instagram.com/username/"
                  value={formData.urls.instagramUrl || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      urls: { ...formData.urls, instagramUrl: e.target.value },
                    })
                  }
                />
              </div>

              {/* Facebook */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  <Facebook className="w-4 h-4 inline mr-2" />
                  Facebook Profile URL
                </label>
                <input
                  type="url"
                  className="input-field"
                  placeholder="https://www.facebook.com/username"
                  value={formData.urls.facebookUrl || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      urls: { ...formData.urls, facebookUrl: e.target.value },
                    })
                  }
                />
              </div>

              {/* Twitter */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  <Twitter className="w-4 h-4 inline mr-2" />
                  Twitter/X Profile URL
                </label>
                <input
                  type="url"
                  className="input-field"
                  placeholder="https://twitter.com/username or https://x.com/username"
                  value={formData.urls.twitterUrl || ''}
                  onChange={(e) =>
                    setFormData({
                      ...formData,
                      urls: { ...formData.urls, twitterUrl: e.target.value },
                    })
                  }
                />
              </div>

              {/* Blog URLs */}
              <div>
                <label className="block text-sm font-medium text-dark-300 mb-2">
                  <Globe className="w-4 h-4 inline mr-2" />
                  Blog URLs
                </label>
                <div className="flex gap-2 mb-2">
                  <input
                    type="url"
                    className="input-field flex-1"
                    placeholder="https://example.com/blog"
                    value={blogUrl}
                    onChange={(e) => setBlogUrl(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') {
                        e.preventDefault();
                        addBlogUrl();
                      }
                    }}
                  />
                  <button
                    type="button"
                    onClick={addBlogUrl}
                    className="btn-secondary flex items-center"
                  >
                    <Plus className="w-4 h-4 mr-1" />
                    Add
                  </button>
                </div>
                {formData.urls.blogUrls && formData.urls.blogUrls.length > 0 && (
                  <div className="space-y-2">
                    {formData.urls.blogUrls.map((url, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between bg-dark-800 px-3 py-2 rounded-lg"
                      >
                        <span className="text-sm text-dark-300 truncate flex-1">{url}</span>
                        <button
                          type="button"
                          onClick={() => removeBlogUrl(index)}
                          className="text-danger-500 hover:text-danger-400 ml-2"
                        >
                          <X className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}

        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-danger-900/20 border border-danger-700 text-danger-300 px-4 py-3 rounded-lg">
            {error}
          </div>
        )}

        {/* Submit Button */}
        <div className="flex justify-end space-x-4 pt-4 border-t border-dark-800">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 inline mr-2 animate-spin" />
                {searchType === 'post' ? 'Analyzing Post...' : 'Creating Profile...'}
              </>
            ) : (
              searchType === 'post' ? 'Analyze Post' : 'Create Profile'
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
