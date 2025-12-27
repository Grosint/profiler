import axios from 'axios';
import type {
  APIResponse,
  CreateProfileRequest,
  ProfileDetailsResponse,
  ProfileListItem,
  ProfileStatusResponse,
  ScrapedDataItem,
  ProfileStatus,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const API_KEY = import.meta.env.VITE_API_KEY || 'dev-secret-key'; // Default for development

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': API_KEY,
  },
});

// Log API key status in development (first 8 chars only for security)
if (import.meta.env.DEV) {
  console.log('API Base URL:', API_BASE_URL);
  console.log('API Key configured:', API_KEY ? `${API_KEY.substring(0, 8)}...` : 'NOT SET');
}

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
};
