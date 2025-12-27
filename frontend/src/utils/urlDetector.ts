/**
 * Detects the platform type from a URL
 */
export type PlatformType = 'instagram' | 'facebook' | 'twitter' | 'reddit' | 'linkedin' | 'blog' | 'unknown';

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

  if (lowerUrl.includes('reddit.com')) {
    return 'reddit';
  }

  if (lowerUrl.includes('linkedin.com')) {
    return 'linkedin';
  }

  // If it's a valid URL but not a known social platform, treat as blog
  try {
    new URL(url);
    return 'blog';
  } catch {
    return 'unknown';
  }
}

/**
 * Check if URL is a post URL (not a profile URL)
 */
export function isPostUrl(url: string): boolean {
  if (!url) return false;

  const lowerUrl = url.toLowerCase().trim();

  // Twitter/X post patterns
  if (/twitter\.com\/[^/]+\/status\/\d+/.test(lowerUrl) ||
      /x\.com\/[^/]+\/status\/\d+/.test(lowerUrl)) {
    return true;
  }

  // Facebook post patterns
  if (/facebook\.com\/[^/]+\/posts\/\d+/.test(lowerUrl) ||
      /facebook\.com\/[^/]+\/photos\//.test(lowerUrl) ||
      /facebook\.com\/permalink\.php/.test(lowerUrl)) {
    return true;
  }

  // Instagram post patterns
  if (/instagram\.com\/p\/[^/]+/.test(lowerUrl) ||
      /instagram\.com\/reel\/[^/]+/.test(lowerUrl)) {
    return true;
  }

  // Reddit post patterns
  if (/reddit\.com\/r\/[^/]+\/comments\//.test(lowerUrl)) {
    return true;
  }

  // LinkedIn post patterns
  if (/linkedin\.com\/feed\/update\//.test(lowerUrl) ||
      /linkedin\.com\/posts\//.test(lowerUrl)) {
    return true;
  }

  return false;
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
