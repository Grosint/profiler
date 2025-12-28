import axios from 'axios';
import type {
  APIResponse,
  CreateProfileRequest,
  ProfileDetailsResponse,
  ProfileListItem,
  ProfileStatusResponse,
  ScrapedDataItem,
  ProfileStatus,
  CreatePostAnalysisRequest,
  PostStatusResponse,
  PostListItem,
  PostStatus,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-secret-key'; // Default for development

// #region agent log
// Always log API key status (first 8 chars only for security) - helps debug in production
console.log('[API Config] Base URL:', API_BASE_URL);
console.log('[API Config] API Key configured:', API_KEY ? `${API_KEY.substring(0, 8)}...` : 'NOT SET');
console.log('[API Config] API Key length:', API_KEY ? API_KEY.length : 0);
console.log('[API Config] VITE_API_KEY env var:', import.meta.env.VITE_API_KEY ? `${String(import.meta.env.VITE_API_KEY).substring(0, 8)}...` : 'NOT SET');
// #endregion

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
  },
});

export const api = {
  // List all profiles
  listProfiles: async (
    skip: number = 0,
    limit: number = 100,
    status?: ProfileStatus
  ): Promise<APIResponse<ProfileListItem[]>> => {
    const params: any = { skip, limit };
    if (status) params.status = status;
    const response = await apiClient.get<APIResponse<ProfileListItem[]>>('/profiles', { params });
    return response.data;
  },

  // Create a new profile
  createProfile: async (payload: CreateProfileRequest): Promise<APIResponse<ProfileStatusResponse>> => {
    const response = await apiClient.post<APIResponse<ProfileStatusResponse>>('/profiles', payload);
    return response.data;
  },

  // Get profile status
  getProfile: async (profileId: string): Promise<APIResponse<ProfileStatusResponse>> => {
    const response = await apiClient.get<APIResponse<ProfileStatusResponse>>(`/profiles/${profileId}`);
    return response.data;
  },

  // Get profile details
  getProfileDetails: async (profileId: string): Promise<APIResponse<ProfileDetailsResponse>> => {
    const response = await apiClient.get<APIResponse<ProfileDetailsResponse>>(`/profiles/${profileId}/details`);
    return response.data;
  },

  // Get raw scraped data
  getProfileRawData: async (profileId: string): Promise<APIResponse<ScrapedDataItem[]>> => {
    const response = await apiClient.get<APIResponse<ScrapedDataItem[]>>(`/profiles/${profileId}/raw-data`);
    return response.data;
  },

  // Post Analysis APIs
  // List all posts
  listPosts: async (
    skip: number = 0,
    limit: number = 100,
    status?: PostStatus
  ): Promise<APIResponse<PostListItem[]>> => {
    const params: any = { skip, limit };
    if (status) params.status = status;
    const response = await apiClient.get<APIResponse<PostListItem[]>>('/posts', { params });
    return response.data;
  },

  // Create a new post analysis
  createPostAnalysis: async (payload: CreatePostAnalysisRequest): Promise<APIResponse<PostStatusResponse>> => {
    const response = await apiClient.post<APIResponse<PostStatusResponse>>('/posts', payload);
    return response.data;
  },

  // Get post analysis status
  getPost: async (postId: string): Promise<APIResponse<PostStatusResponse>> => {
    const response = await apiClient.get<APIResponse<PostStatusResponse>>(`/posts/${postId}`);
    return response.data;
  },
};
