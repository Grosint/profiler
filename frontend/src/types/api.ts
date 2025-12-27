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
