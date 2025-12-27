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


class LinkedInScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.LINKEDIN

    def __init__(self, use_playwright: bool = True):
        """
        Initialize LinkedIn scraper.

        Args:
            use_playwright: If True, use Playwright for JavaScript rendering.
        """
        self.use_playwright = use_playwright

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        """
        Override scrape to handle LinkedIn-specific logic.
        """
        # Normalize LinkedIn URL
        url = self._normalize_url(url)

        if self.use_playwright:
            return await self._scrape_with_playwright(profile, url)
        else:
            return await self._scrape_with_http(profile, url)

    def _normalize_url(self, url: str) -> str:
        """Normalize LinkedIn URL to profile format."""
        url = url.strip().rstrip('/')
        if 'linkedin.com/in/' in url:
            # Extract username from URL
            username_match = re.search(r'linkedin\.com/in/([^/?]+)', url)
            if username_match:
                username = username_match.group(1)
                return f"https://www.linkedin.com/in/{username}"
        if not url.startswith('http'):
            return f"https://www.linkedin.com/in/{url}"
        return url

    async def _scrape_with_playwright(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape LinkedIn using Playwright."""
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

                # Extract text and metadata
                text, metadata = self._extract_linkedin_data(html, profile_data, posts)

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
                    "LinkedIn scrape succeeded",
                    extra={
                        "profile_id": str(profile.id),
                        "url": url,
                        "posts_count": len(posts)
                    },
                )
                return scraped

        except Exception as exc:
            logger.exception(
                "LinkedIn scrape failed",
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
        """Extract profile information from LinkedIn page."""
        try:
            profile_data = await page.evaluate("""
                () => {
                    const data = {};

                    // Extract name
                    const nameEl = document.querySelector('h1.text-heading-xlarge') ||
                                  document.querySelector('h1[class*="text-heading"]') ||
                                  document.querySelector('h1');
                    if (nameEl) {
                        data.name = nameEl.innerText.trim();
                    }

                    // Extract headline
                    const headlineEl = document.querySelector('.text-body-medium.break-words') ||
                                      document.querySelector('[class*="headline"]');
                    if (headlineEl) {
                        data.headline = headlineEl.innerText.trim();
                    }

                    // Extract location
                    const locationEl = document.querySelector('.text-body-small.inline.t-black--light.break-words');
                    if (locationEl) {
                        data.location = locationEl.innerText.trim();
                    }

                    // Extract about section
                    const aboutEl = document.querySelector('#about ~ .inline-show-more-text') ||
                                   document.querySelector('[id*="about"]');
                    if (aboutEl) {
                        data.about = aboutEl.innerText.trim();
                    }

                    // Extract experience
                    const experienceEls = document.querySelectorAll('#experience ~ .pvs-list__outer-container .pvs-list__item');
                    data.experience = [];
                    experienceEls.forEach((el, index) => {
                        if (index < 10) {
                            const titleEl = el.querySelector('.mr1.t-bold span[aria-hidden="true"]');
                            const companyEl = el.querySelector('.t-14.t-normal span[aria-hidden="true"]');
                            if (titleEl || companyEl) {
                                data.experience.push({
                                    title: titleEl ? titleEl.innerText.trim() : '',
                                    company: companyEl ? companyEl.innerText.trim() : ''
                                });
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
        """Extract posts from LinkedIn feed."""
        try:
            # Scroll to load posts
            await page.evaluate("""
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            await page.wait_for_timeout(3000)

            posts = await page.evaluate("""
                () => {
                    const posts = [];
                    const postElements = document.querySelectorAll('.feed-shared-update-v2');

                    postElements.forEach((postEl, index) => {
                        if (index < 20) {
                            try {
                                const textEl = postEl.querySelector('.feed-shared-text span[dir="ltr"]') ||
                                             postEl.querySelector('.feed-shared-text');
                                const text = textEl ? textEl.innerText.trim() : '';

                                const timeEl = postEl.querySelector('time');
                                const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

                                const likeEl = postEl.querySelector('[data-control-name="like_toggle"]');
                                let likeCount = 0;
                                if (likeEl) {
                                    const likeText = likeEl.getAttribute('aria-label') || '';
                                    const match = likeText.match(/[\\d,]+/);
                                    if (match) {
                                        likeCount = parseInt(match[0].replace(/,/g, '')) || 0;
                                    }
                                }

                                const commentEl = postEl.querySelector('[data-control-name="comment"]');
                                let commentCount = 0;
                                if (commentEl) {
                                    const commentText = commentEl.getAttribute('aria-label') || '';
                                    const match = commentText.match(/[\\d,]+/);
                                    if (match) {
                                        commentCount = parseInt(match[0].replace(/,/g, '')) || 0;
                                    }
                                }

                                if (text) {
                                    posts.push({
                                        id: `post_${index}_${Date.now()}`,
                                        text: text,
                                        created_at: timestamp,
                                        likes: likeCount,
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

    def _extract_linkedin_data(self, html: str, profile_data: Dict[str, Any], posts: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from LinkedIn HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        text_parts = []

        # Add profile information
        if profile_data.get('name'):
            text_parts.append(f"Name: {profile_data['name']}")
        if profile_data.get('headline'):
            text_parts.append(f"Headline: {profile_data['headline']}")
        if profile_data.get('about'):
            text_parts.append(f"About: {profile_data['about']}")
        if profile_data.get('location'):
            text_parts.append(f"Location: {profile_data['location']}")

        # Add posts
        for i, post in enumerate(posts[:10]):
            post_text = f"Post {i+1}: {post.get('text', '')[:200]}..."
            if post.get('likes'):
                post_text += f" Likes: {post['likes']}"
            if post.get('comments'):
                post_text += f" Comments: {post['comments']}"
            text_parts.append(post_text)

        text = " ".join(text_parts) if text_parts else "LinkedIn profile data"

        metadata = {
            'profile_info': profile_data,
            'posts': posts,
            'posts_count': len(posts),
            'content_length': len(html),
            'text_length': len(text),
            'scraping_method': 'playwright',
        }

        return text, metadata

    async def _scrape_with_http(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape LinkedIn using simple HTTP requests."""
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
            logger.exception("LinkedIn HTTP scrape failed", extra={"url": url})
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
