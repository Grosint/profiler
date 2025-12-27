export enum ProfileStatus {
  PENDING = 'pending',
  SCRAPING = 'scraping',
  PROCESSING = 'processing',
  ANALYZING = 'analyzing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum TraitType {
  PERSONALITY = 'personality',
  WORK_STYLE = 'work_style',
  COMMUNICATION = 'communication',
  RISK = 'risk',
  CULTURAL_FIT = 'cultural_fit',
  LEADERSHIP = 'leadership',
}

export interface ProfileUrls {
  instagramUrl?: string | null;
  facebookUrl?: string | null;
  twitterUrl?: string | null;
  blogUrls?: string[] | null;
}

export interface CreateProfileRequest {
  subjectName?: string | null;
  externalRefId?: string | null;
  urls: ProfileUrls;
  metadata?: Record<string, any> | null;
}

export interface TraitOverviewItem {
  traitType: TraitType;
  averageScore: number;
}

export interface ProfileStatusResponse {
  id: string;
  status: ProfileStatus;
  summary?: Record<string, any> | null;
  traitsOverview: TraitOverviewItem[];
  errorMessage?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface TraitDetail {
  traitType: TraitType;
  traitName: string;
  score: number;
  confidence: number;
  evidenceSnippets: string[];
  extra: Record<string, any>;
}

export interface ProfileDetailsResponse {
  id: string;
  subjectName?: string | null;
  externalRefId?: string | null;
  userId?: string | null;
  status: ProfileStatus;
  summary?: Record<string, any> | null;
  traits: TraitDetail[];
  narratives: Record<string, string>;
  createdAt: string;
  updatedAt: string;
}

export interface ScrapedDataItem {
  id: string;
  platform: string;
  url: string;
  rawContent: string;
  metadata: Record<string, any>;
  scrapedAt: string;
  scrapeStatus: string;
  errorMessage?: string | null;
}

export interface ProfileListItem {
  id: string;
  subjectName?: string | null;
  externalRefId?: string | null;
  status: ProfileStatus;
  traitsOverview: TraitOverviewItem[];
  errorMessage?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface APIResponse<T> {
  success: boolean;
  data?: T | null;
  error?: {
    message: string;
    code: string;
    details?: Record<string, any> | null;
  } | null;
}

// Post Analysis Types
export enum PostStatus {
  PENDING = 'pending',
  SCRAPING = 'scraping',
  PROCESSING = 'processing',
  ANALYZING = 'analyzing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

export enum PostType {
  PROFILE = 'profile',
  POST = 'post',
}

export interface CreatePostAnalysisRequest {
  postUrl: string;
  externalRefId?: string | null;
  metadata?: Record<string, any> | null;
}

export interface CommentAnalysisResponse {
  comment_id: string;
  author_username?: string | null;
  author_name?: string | null;
  author_url?: string | null;
  text: string;
  timestamp?: string | null;
  toxicity_score: number;
  is_toxic: boolean;
  is_anti_national: boolean;
  toxicity_labels: Array<Record<string, any>>;
  sentiment: string;
  sentiment_score: number;
}

export interface PostAnalysisResultResponse {
  post_id: string;
  post_url: string;
  post_text: string;
  author_username?: string | null;
  author_name?: string | null;
  author_url?: string | null;
  timestamp?: string | null;
  comments_count: number;
  comments_analyzed: number;
  toxic_comments_count: number;
  anti_national_comments_count: number;
  flagged_commenters: Array<Record<string, any>>;
  comments: CommentAnalysisResponse[];
}

export interface PostStatusResponse {
  id: string;
  postUrl: string;
  postType: PostType;
  platform: string;
  status: PostStatus;
  analysis?: PostAnalysisResultResponse | null;
  errorMessage?: string | null;
  externalRefId?: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PostListItem {
  id: string;
  postUrl: string;
  postType: PostType;
  platform: string;
  status: PostStatus;
  errorMessage?: string | null;
  externalRefId?: string | null;
  createdAt: string;
  updatedAt: string;
  comments_count: number;
  flagged_commenters_count: number;
}
