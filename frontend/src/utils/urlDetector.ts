/**
 * Detects the platform type from a URL
 */
export type PlatformType = 'instagram' | 'facebook' | 'twitter' | 'blog' | 'unknown';

export function detectPlatformFromUrl(url: string): PlatformType {
  if (!url) return 'unknown';

  const lowerUrl = url.toLowerCase().trim();

  if (lowerUrl.includes('instagram.com') || lowerUrl.includes('instagr.am')) {
    return 'instagram';
  }

  if (lowerUrl.includes('facebook.com') || lowerUrl.includes('fb.com')) {
    return 'facebook';
  }

  if (lowerUrl.includes('twitter.com') || lowerUrl.includes('x.com')) {
    return 'twitter';
  }

  // If it's a valid URL but not a known social platform, treat as blog
  try {
    new URL(url);
    return 'blog';
  } catch {
    return 'unknown';
  }
}

export function validateUrl(url: string): { valid: boolean; error?: string } {
  if (!url || !url.trim()) {
    return { valid: false, error: 'URL is required' };
  }

  try {
    new URL(url);
    return { valid: true };
  } catch {
    return { valid: false, error: 'Invalid URL format' };
  }
}
