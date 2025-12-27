import json
import logging
import re
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.core.http_client import http_client
from app.models.scraped_data import ScrapePlatform, ScrapeStatus, ScrapedData
from app.models.profile import Profile
from .base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class RedditScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.REDDIT

    def __init__(self, use_playwright: bool = True):
        """
        Initialize Reddit scraper.

        Args:
            use_playwright: If True, use Playwright for JavaScript rendering.
        """
        self.use_playwright = use_playwright

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        """
        Override scrape to handle Reddit-specific logic.
        """
        # Normalize Reddit URL
        url = self._normalize_url(url)

        if self.use_playwright:
            return await self._scrape_with_playwright(profile, url)
        else:
            return await self._scrape_with_http(profile, url)

    def _normalize_url(self, url: str) -> str:
        """Normalize Reddit URL to user profile format."""
        url = url.strip().rstrip('/')
        if 'reddit.com/user/' in url or 'reddit.com/u/' in url:
            # Extract username from URL
            username_match = re.search(r'reddit\.com/(?:user|u)/([^/?]+)', url)
            if username_match:
                username = username_match.group(1)
                return f"https://www.reddit.com/user/{username}"
        if not url.startswith('http'):
            return f"https://www.reddit.com/user/{url}"
        return url

    async def _scrape_with_playwright(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Reddit using Playwright."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # Navigate to profile
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(5000)

                # Extract HTML
                html = await page.content()

                # Extract profile data
                profile_data = await self._extract_profile_data(page)

                # Extract posts
                posts = await self._extract_posts(page)

                # Extract comments
                comments = await self._extract_comments(page)

                # Extract text and metadata
                text, metadata = self._extract_reddit_data(html, profile_data, posts, comments)

                await browser.close()

                scraped = ScrapedData(
                    profile=profile,
                    platform=self.platform,
                    url=url,
                    rawContent=text,
                    metadata=metadata,
                    scrapeStatus=ScrapeStatus.SUCCESS,
                )
                await scraped.insert()

                logger.info(
                    "Reddit scrape succeeded",
                    extra={
                        "profile_id": str(profile.id),
                        "url": url,
                        "posts_count": len(posts),
                        "comments_count": len(comments)
                    },
                )
                return scraped

        except Exception as exc:
            logger.exception(
                "Reddit scrape failed",
                extra={"profile_id": str(getattr(profile, "id", "")), "url": url},
            )
            scraped = ScrapedData(
                profile=profile,
                platform=self.platform,
                url=url,
                rawContent="",
                metadata={},
                scrapeStatus=ScrapeStatus.FAILED,
                errorMessage=str(exc),
            )
            await scraped.insert()
            return scraped

    async def _extract_profile_data(self, page) -> Dict[str, Any]:
        """Extract profile information from Reddit page."""
        try:
            profile_data = await page.evaluate("""
                () => {
                    const data = {};

                    // Extract username
                    const usernameEl = document.querySelector('h1[class*="Username"]') ||
                                      document.querySelector('h1') ||
                                      document.querySelector('[class*="username"]');
                    if (usernameEl) {
                        data.username = usernameEl.innerText.trim();
                    }

                    // Extract karma
                    const karmaEl = document.querySelector('[class*="Karma"]') ||
                                   document.querySelector('[class*="karma"]');
                    if (karmaEl) {
                        const karmaText = karmaEl.innerText.trim();
                        const match = karmaText.match(/[\\d,]+/);
                        if (match) {
                            data.karma = parseInt(match[0].replace(/,/g, '')) || 0;
                        }
                    }

                    // Extract cake day
                    const cakeDayEl = document.querySelector('[class*="CakeDay"]') ||
                                     document.querySelector('[class*="cake"]');
                    if (cakeDayEl) {
                        data.cake_day = cakeDayEl.innerText.trim();
                    }

                    // Extract subreddits
                    const subredditEls = document.querySelectorAll('[class*="Subreddit"] a');
                    data.subreddits = [];
                    subredditEls.forEach((el, index) => {
                        if (index < 20) {
                            const href = el.getAttribute('href') || '';
                            const match = href.match(/\\/r\\/([^\\/]+)/);
                            if (match) {
                                data.subreddits.push(match[1]);
                            }
                        }
                    });

                    return data;
                }
            """)
            return profile_data or {}
        except Exception as e:
            logger.debug(f"Error extracting profile data: {e}")
            return {}

    async def _extract_posts(self, page) -> List[Dict[str, Any]]:
        """Extract posts from Reddit profile."""
        try:
            # Scroll to load more posts
            await page.evaluate("""
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            await page.wait_for_timeout(3000)

            posts = await page.evaluate("""
                () => {
                    const posts = [];
                    const postElements = document.querySelectorAll('[data-testid="post-container"]') ||
                                       document.querySelectorAll('[class*="Post"]');

                    postElements.forEach((postEl, index) => {
                        if (index < 20) {
                            try {
                                const titleEl = postEl.querySelector('h3') ||
                                              postEl.querySelector('[class*="Title"]');
                                const title = titleEl ? titleEl.innerText.trim() : '';

                                const textEl = postEl.querySelector('[class*="PostBody"]') ||
                                             postEl.querySelector('[class*="post-body"]');
                                const text = textEl ? textEl.innerText.trim() : '';

                                const timeEl = postEl.querySelector('time');
                                const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

                                const upvoteEl = postEl.querySelector('[class*="Upvote"]') ||
                                               postEl.querySelector('button[aria-label*="upvote"]');
                                let upvotes = 0;
                                if (upvoteEl) {
                                    const upvoteText = upvoteEl.getAttribute('aria-label') || '';
                                    const match = upvoteText.match(/[\\d,]+/);
                                    if (match) {
                                        upvotes = parseInt(match[0].replace(/,/g, '')) || 0;
                                    }
                                }

                                const commentEl = postEl.querySelector('[class*="Comment"]');
                                let commentCount = 0;
                                if (commentEl) {
                                    const commentText = commentEl.innerText.trim();
                                    const match = commentText.match(/[\\d,]+/);
                                    if (match) {
                                        commentCount = parseInt(match[0].replace(/,/g, '')) || 0;
                                    }
                                }

                                const subredditEl = postEl.querySelector('a[href*="/r/"]');
                                const subreddit = subredditEl ? subredditEl.innerText.trim() : '';

                                if (title || text) {
                                    posts.push({
                                        id: `post_${index}_${Date.now()}`,
                                        title: title,
                                        text: text,
                                        subreddit: subreddit,
                                        created_at: timestamp,
                                        upvotes: upvotes,
                                        comments: commentCount
                                    });
                                }
                            } catch (e) {
                                console.error('Error extracting post:', e);
                            }
                        }
                    });
                    return posts;
                }
            """)
            return posts or []
        except Exception as e:
            logger.debug(f"Error extracting posts: {e}")
            return []

    async def _extract_comments(self, page) -> List[Dict[str, Any]]:
        """Extract comments from Reddit profile."""
        try:
            comments = await page.evaluate("""
                () => {
                    const comments = [];
                    const commentElements = document.querySelectorAll('[data-testid="comment"]') ||
                                          document.querySelectorAll('[class*="Comment"]');

                    commentElements.forEach((commentEl, index) => {
                        if (index < 50) {
                            try {
                                const textEl = commentEl.querySelector('[class*="CommentBody"]') ||
                                             commentEl.querySelector('[class*="comment-body"]');
                                const text = textEl ? textEl.innerText.trim() : '';

                                const timeEl = commentEl.querySelector('time');
                                const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

                                const upvoteEl = commentEl.querySelector('[class*="Upvote"]');
                                let upvotes = 0;
                                if (upvoteEl) {
                                    const upvoteText = upvoteEl.getAttribute('aria-label') || '';
                                    const match = upvoteText.match(/[\\d,]+/);
                                    if (match) {
                                        upvotes = parseInt(match[0].replace(/,/g, '')) || 0;
                                    }
                                }

                                const subredditEl = commentEl.querySelector('a[href*="/r/"]');
                                const subreddit = subredditEl ? subredditEl.innerText.trim() : '';

                                if (text) {
                                    comments.push({
                                        id: `comment_${index}_${Date.now()}`,
                                        text: text,
                                        subreddit: subreddit,
                                        created_at: timestamp,
                                        upvotes: upvotes
                                    });
                                }
                            } catch (e) {
                                console.error('Error extracting comment:', e);
                            }
                        }
                    });
                    return comments;
                }
            """)
            return comments or []
        except Exception as e:
            logger.debug(f"Error extracting comments: {e}")
            return []

    def _extract_reddit_data(
        self, html: str, profile_data: Dict[str, Any], posts: List[Dict[str, Any]], comments: List[Dict[str, Any]]
    ) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from Reddit HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        text_parts = []

        # Add profile information
        if profile_data.get('username'):
            text_parts.append(f"Username: {profile_data['username']}")
        if profile_data.get('karma'):
            text_parts.append(f"Karma: {profile_data['karma']}")
        if profile_data.get('subreddits'):
            text_parts.append(f"Subreddits: {', '.join(profile_data['subreddits'][:10])}")

        # Add posts
        for i, post in enumerate(posts[:10]):
            post_text = f"Post {i+1}: {post.get('title', '')} {post.get('text', '')[:200]}..."
            if post.get('upvotes'):
                post_text += f" Upvotes: {post['upvotes']}"
            if post.get('comments'):
                post_text += f" Comments: {post['comments']}"
            text_parts.append(post_text)

        # Add comments
        for i, comment in enumerate(comments[:10]):
            comment_text = f"Comment {i+1}: {comment.get('text', '')[:200]}..."
            if comment.get('upvotes'):
                comment_text += f" Upvotes: {comment['upvotes']}"
            text_parts.append(comment_text)

        text = " ".join(text_parts) if text_parts else "Reddit profile data"

        metadata = {
            'profile_info': profile_data,
            'posts': posts,
            'comments': comments,
            'posts_count': len(posts),
            'comments_count': len(comments),
            'content_length': len(html),
            'text_length': len(text),
            'scraping_method': 'playwright',
        }

        return text, metadata

    async def _scrape_with_http(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Reddit using simple HTTP requests."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            }

            response = await http_client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

            soup = BeautifulSoup(html, 'html.parser')
            text = " ".join(soup.stripped_strings)

            scraped = ScrapedData(
                profile=profile,
                platform=self.platform,
                url=url,
                rawContent=text,
                metadata={'scraping_method': 'http'},
                scrapeStatus=ScrapeStatus.SUCCESS,
            )
            await scraped.insert()
            return scraped

        except Exception as exc:
            logger.exception("Reddit HTTP scrape failed", extra={"url": url})
            scraped = ScrapedData(
                profile=profile,
                platform=self.platform,
                url=url,
                rawContent="",
                metadata={},
                scrapeStatus=ScrapeStatus.FAILED,
                errorMessage=str(exc),
            )
            await scraped.insert()
            return scraped
