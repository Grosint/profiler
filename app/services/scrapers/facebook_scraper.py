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


class FacebookScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.FACEBOOK

    def __init__(self, use_playwright: bool = True):
        """
        Initialize Facebook scraper.

        Args:
            use_playwright: If True, use Playwright for JavaScript rendering.
                          If False, use simple HTTP requests (may miss some data).
        """
        self.use_playwright = use_playwright

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        """
        Override scrape to handle Facebook-specific logic.
        """
        # Normalize Facebook URL
        url = self._normalize_url(url)

        if self.use_playwright:
            return await self._scrape_with_playwright(profile, url)
        else:
            return await self._scrape_with_http(profile, url)

    def _normalize_url(self, url: str) -> str:
        """Normalize Facebook URL to profile format."""
        url = url.strip().rstrip('/')
        if 'facebook.com/' in url:
            # Extract username/page ID from URL
            username_match = re.search(r'facebook\.com/([^/?]+)', url)
            if username_match:
                username = username_match.group(1)
                # Remove @ if present
                username = username.lstrip('@')
                # Handle different Facebook URL formats
                if username.startswith('profile.php'):
                    # Keep as is for profile.php?id= format
                    return url
                elif username.startswith('pages/'):
                    # Keep as is for pages format
                    return url
                else:
                    return f"https://www.facebook.com/{username}"
        if not url.startswith('http'):
            # Assume it's a username
            username = url.lstrip('@')
            return f"https://www.facebook.com/{username}"
        return url

    def _extract_username(self, url: str) -> str:
        """Extract username from Facebook URL."""
        match = re.search(r'facebook\.com/([^/?]+)', url)
        if match:
            username = match.group(1)
            # Handle profile.php?id= format
            if username.startswith('profile.php'):
                id_match = re.search(r'id=(\d+)', url)
                if id_match:
                    return id_match.group(1)
            return username.lstrip('@')
        return url.replace('https://www.facebook.com/', '').replace('https://facebook.com/', '').lstrip('@').rstrip('/')

    async def _scrape_with_playwright(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Facebook using Playwright with network request interception."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # Store intercepted API responses
                api_responses = []

                # Intercept network requests to catch API calls
                async def handle_response(response):
                    try:
                        url_str = response.url
                        # Facebook uses GraphQL and various API endpoints
                        if any(pattern in url_str for pattern in [
                            '/graphql',
                            '/api/graphql',
                            '/api/graphqlbatch',
                            '/feed',
                            '/posts',
                            '/profile',
                            '/page_content',
                            '/home.php',
                            '/profile.php',
                            '/timeline',
                            '/stories',
                            '/videos',
                            '/photos'
                        ]):
                            try:
                                data = await response.json()
                                api_responses.append({
                                    'url': url_str,
                                    'data': data
                                })
                                logger.info(f"Intercepted API response from {url_str[:100]}...")
                            except Exception as e:
                                logger.debug(f"Could not parse response from {url_str}: {e}")
                    except Exception as e:
                        logger.debug(f"Error handling response: {e}")

                page.on('response', handle_response)

                # Navigate to profile
                logger.info(f"Navigating to {url}")
                await page.goto(url, wait_until='networkidle', timeout=30000)
                await page.wait_for_timeout(5000)  # Wait for initial load

                # Check if we're being asked to log in or if content is available
                page_check = await page.evaluate("""
                    () => {
                        const bodyText = document.body.innerText || '';
                        return {
                            hasLoginPrompt: bodyText.includes('Log in') ||
                                          bodyText.includes('Sign up') ||
                                          bodyText.includes('Create account') ||
                                          bodyText.includes('Log into Facebook'),
                            hasPosts: document.querySelector('[role="article"]') !== null ||
                                     document.querySelector('[data-pagelet]') !== null ||
                                     document.querySelector('div[data-ad-preview="message"]') !== null ||
                                     document.querySelector('div[data-testid="post_message"]') !== null,
                            pageTitle: document.title,
                            hasContent: document.querySelector('main') !== null ||
                                       document.querySelector('[role="main"]') !== null
                        };
                    }
                """)
                logger.info(f"Page check: {page_check}")

                # Try multiple selectors for posts
                post_selectors = [
                    '[role="article"]',
                    '[data-pagelet]',
                    'div[data-ad-preview="message"]',
                    'div[data-testid="post_message"]',
                    '[data-testid="story-subtitle"]',
                    'div[data-testid="fbfeed_story"]'
                ]

                posts_found = False
                for selector in post_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        logger.info(f"Found posts using selector: {selector}")
                        posts_found = True
                        break
                    except:
                        continue

                if not posts_found:
                    logger.warning("No post selectors found, but continuing to try API extraction")

                # Scroll to load more content
                await self._scroll_to_load_posts(page)
                await page.wait_for_timeout(5000)  # Wait after scrolling for API requests

                # Extract HTML
                html = await page.content()

                # Extract posts from multiple sources
                posts = []

                # Log how many API responses we intercepted
                logger.info(f"Intercepted {len(api_responses)} API responses")
                if api_responses:
                    logger.info(f"API response URLs: {[r['url'][:80] for r in api_responses[:5]]}")

                # Method 1: Extract from API responses
                posts_from_api = await self._extract_posts_from_api(api_responses)
                logger.info(f"Extracted {len(posts_from_api)} posts from API responses")
                posts.extend(posts_from_api)

                # Method 2: Extract from page JavaScript context
                posts_from_js = await self._extract_posts_from_page_js(page)
                logger.info(f"Extracted {len(posts_from_js)} posts from JavaScript context")
                posts.extend(posts_from_js)

                # Method 3: Extract from DOM
                posts_from_dom = await self._extract_posts_from_dom(page)
                logger.info(f"Extracted {len(posts_from_dom)} posts from DOM")
                posts.extend(posts_from_dom)

                # Remove duplicates
                unique_posts = self._deduplicate_posts(posts)
                logger.info(f"Total unique posts: {len(unique_posts)}")

                # Extract comments for each post
                for post in unique_posts:
                    if post.get('id'):
                        post_comments = await self._extract_comments_for_post(page, post['id'])
                        if post_comments:
                            post['comments_data'] = post_comments
                            logger.info(f"Extracted {len(post_comments)} comments for post {post['id']}")

                # Extract text and metadata
                json_data = await self._extract_json_from_page(page)
                text, metadata = self._extract_facebook_data(html, json_data, unique_posts)

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
                    "Facebook scrape succeeded",
                    extra={
                        "profile_id": str(profile.id),
                        "url": url,
                        "posts_count": len(unique_posts)
                    },
                )
                return scraped

        except Exception as exc:
            logger.exception(
                "Facebook scrape failed",
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

    async def _extract_posts_from_api(self, api_responses: List[Dict]) -> List[Dict[str, Any]]:
        """Extract posts from intercepted API responses."""
        posts = []

        for response in api_responses:
            try:
                data = response.get('data', {})

                # Recursively search for posts in the response
                def find_posts_recursive(obj, depth=0):
                    if depth > 15:
                        return []

                    found_posts = []

                    if isinstance(obj, dict):
                        # Look for various Facebook data structures
                        # GraphQL structure
                        if 'data' in obj:
                            data_obj = obj['data']
                            if isinstance(data_obj, list):
                                for item in data_obj:
                                    post = self._parse_post_node(item)
                                    if post:
                                        found_posts.append(post)
                            elif isinstance(data_obj, dict):
                                # Check for timeline, feed, posts keys
                                for key in ['timeline', 'feed', 'posts', 'edges', 'nodes']:
                                    if key in data_obj:
                                        items = data_obj[key]
                                        if isinstance(items, list):
                                            for item in items:
                                                if isinstance(item, dict):
                                                    # Handle edge/node structure
                                                    node = item.get('node') or item
                                                    post = self._parse_post_node(node)
                                                    if post:
                                                        found_posts.append(post)
                                        elif isinstance(items, dict):
                                            found_posts.extend(find_posts_recursive(items, depth + 1))

                        # Legacy API structure
                        if 'feed' in obj:
                            feed = obj['feed']
                            if isinstance(feed, dict) and 'data' in feed:
                                for item in feed['data']:
                                    post = self._parse_post_node(item)
                                    if post:
                                        found_posts.append(post)

                        # Check for post-like structures directly
                        if 'message' in obj or 'story' in obj or 'post_id' in obj:
                            post = self._parse_post_node(obj)
                            if post:
                                found_posts.append(post)

                        # Recursively search
                        for value in obj.values():
                            found_posts.extend(find_posts_recursive(value, depth + 1))

                    elif isinstance(obj, list):
                        for item in obj:
                            found_posts.extend(find_posts_recursive(item, depth + 1))

                    return found_posts

                found = find_posts_recursive(data)
                posts.extend(found)

            except Exception as e:
                logger.debug(f"Error extracting from API response: {e}")

        return posts

    async def _extract_posts_from_page_js(self, page) -> List[Dict[str, Any]]:
        """Extract posts from page JavaScript context."""
        try:
            posts = await page.evaluate("""
                () => {
                    const posts = [];
                    try {
                        // Try to find posts in window.__d or similar React data
                        if (window.__d) {
                            const data = window.__d;
                            // Navigate through React data structure
                            if (Array.isArray(data)) {
                                data.forEach(item => {
                                    if (item && typeof item === 'object') {
                                        if (item.message || item.story || item.post_id) {
                                            posts.push({
                                                id: item.post_id || item.id,
                                                text: item.message || item.story || '',
                                                created_time: item.created_time || item.timestamp,
                                                likes: item.likes || item.reaction_count || 0,
                                                comments: item.comments || item.comment_count || 0,
                                                shares: item.shares || item.share_count || 0
                                            });
                                        }
                                    }
                                });
                            }
                        }

                        // Try to find in window.__initialData__
                        if (window.__initialData__) {
                            const initialData = window.__initialData__;
                            if (initialData.feed && initialData.feed.entries) {
                                initialData.feed.entries.forEach(entry => {
                                    if (entry.message || entry.story) {
                                        posts.push({
                                            id: entry.post_id || entry.id,
                                            text: entry.message || entry.story || '',
                                            created_time: entry.created_time,
                                            likes: entry.likes || 0,
                                            comments: entry.comments || 0,
                                            shares: entry.shares || 0
                                        });
                                    }
                                });
                            }
                        }

                        // Try to find in document.querySelectorAll for article elements
                        const articles = document.querySelectorAll('[role="article"]');
                        articles.forEach((article, index) => {
                            if (index < 20) { // Limit to first 20
                                try {
                                    const postText = article.querySelector('[data-testid="post_message"]')?.innerText ||
                                                    article.querySelector('div[data-ad-preview="message"]')?.innerText || '';
                                    const postId = article.getAttribute('data-pagelet') ||
                                                 article.getAttribute('data-ft') || '';
                                    if (postText || postId) {
                                        posts.push({
                                            id: postId,
                                            text: postText,
                                            source: 'dom_js'
                                        });
                                    }
                                } catch (e) {
                                    console.error('Error extracting post from article:', e);
                                }
                            }
                        });
                    } catch (e) {
                        console.error('Error extracting posts from JS:', e);
                    }
                    return posts;
                }
            """)
            return posts or []
        except Exception as e:
            logger.debug(f"Error extracting posts from JS: {e}")
            return []

    async def _extract_posts_from_dom(self, page) -> List[Dict[str, Any]]:
        """Extract posts from DOM as fallback."""
        posts = []
        try:
            post_elements = await page.evaluate("""
                () => {
                    const posts = [];
                    const articles = document.querySelectorAll('[role="article"]');
                    articles.forEach((article, index) => {
                        if (index < 20) { // Limit to first 20
                            try {
                                const postTextEl = article.querySelector('[data-testid="post_message"]') ||
                                                  article.querySelector('div[data-ad-preview="message"]') ||
                                                  article.querySelector('[data-testid="story-subtitle"]');
                                const postText = postTextEl ? postTextEl.innerText : '';

                                // Try to get post ID from various attributes
                                let postId = article.getAttribute('data-pagelet') ||
                                            article.getAttribute('data-ft') ||
                                            article.getAttribute('data-post-id') ||
                                            article.querySelector('a[href*="/posts/"]')?.href?.match(/\\/posts\\/([^/?]+)/)?.[1] || '';

                                // Extract engagement metrics
                                const getMetric = (label) => {
                                    const buttons = article.querySelectorAll('button, span, div');
                                    for (const el of buttons) {
                                        const text = el.innerText || '';
                                        if (text.includes(label) || el.getAttribute('aria-label')?.includes(label)) {
                                            const match = text.match(/[\\d,]+/);
                                            return match ? parseInt(match[0].replace(/,/g, '')) : 0;
                                        }
                                    }
                                    return 0;
                                };

                                const likeCount = getMetric('Like') || getMetric('like');
                                const commentCount = getMetric('Comment') || getMetric('comment');
                                const shareCount = getMetric('Share') || getMetric('share');

                                if (postText || postId) {
                                    posts.push({
                                        id: postId,
                                        text: postText,
                                        likes: likeCount,
                                        comments: commentCount,
                                        shares: shareCount,
                                        source: 'dom'
                                    });
                                }
                            } catch (e) {
                                console.error('Error extracting post from article:', e);
                            }
                        }
                    });
                    return posts;
                }
            """)

            for post_elem in post_elements:
                posts.append(post_elem)
        except Exception as e:
            logger.debug(f"Error extracting posts from DOM: {e}")

        return posts

    def _parse_post_node(self, node: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single post node from Facebook API structure."""
        try:
            if not node:
                return None

            # Check if this looks like a post
            has_post_indicators = any(key in node for key in [
                'message', 'story', 'post_id', 'id', 'created_time', 'timestamp'
            ])

            if not has_post_indicators:
                return None

            post = {
                'id': node.get('post_id') or node.get('id') or node.get('legacy_post_id'),
                'text': node.get('message') or node.get('story') or node.get('description') or '',
                'created_time': node.get('created_time') or node.get('timestamp') or node.get('time'),
                'likes': node.get('likes', {}).get('summary', {}).get('total_count', 0) if isinstance(node.get('likes'), dict) else node.get('likes', 0),
                'comments': node.get('comments', {}).get('summary', {}).get('total_count', 0) if isinstance(node.get('comments'), dict) else node.get('comments', 0),
                'shares': node.get('shares', {}).get('count', 0) if isinstance(node.get('shares'), dict) else node.get('shares', 0),
            }

            # Extract reactions if available
            if 'reactions' in node:
                reactions = node['reactions']
                if isinstance(reactions, dict):
                    post['reactions'] = reactions.get('summary', {}).get('total_count', 0)
                else:
                    post['reactions'] = reactions

            # Extract attachments/media
            if 'attachments' in node:
                attachments = node['attachments']
                if isinstance(attachments, dict) and 'data' in attachments:
                    post['attachments'] = [att.get('type') for att in attachments['data'] if isinstance(att, dict)]
                elif isinstance(attachments, list):
                    post['attachments'] = [att.get('type') for att in attachments if isinstance(att, dict)]

            # Extract author info
            if 'from' in node:
                author = node['from']
                post['author'] = {
                    'name': author.get('name'),
                    'id': author.get('id'),
                    'username': author.get('username')
                }

            # Extract comments data if available
            comments_data = []
            if 'comments' in node and isinstance(node['comments'], dict):
                comments_obj = node['comments']
                if 'data' in comments_obj:
                    for comment_node in comments_obj['data']:
                        comment = self._parse_comment_node(comment_node)
                        if comment:
                            comments_data.append(comment)
                elif 'edges' in comments_obj:
                    for edge in comments_obj['edges']:
                        comment_node = edge.get('node', edge)
                        comment = self._parse_comment_node(comment_node)
                        if comment:
                            comments_data.append(comment)

            if comments_data:
                post['comments_data'] = comments_data

            return post

        except Exception as e:
            logger.debug(f"Error parsing post node: {e}")
            return None

    def _parse_comment_node(self, node: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single comment node from Facebook API structure."""
        try:
            if not node:
                return None

            comment = {
                'id': node.get('id') or node.get('comment_id'),
                'text': node.get('message') or node.get('text') or '',
                'created_time': node.get('created_time') or node.get('timestamp'),
                'like_count': node.get('like_count', 0) or (node.get('likes', {}).get('summary', {}).get('total_count', 0) if isinstance(node.get('likes'), dict) else 0),
            }

            # Extract comment author
            if 'from' in node:
                author = node['from']
                comment['author'] = {
                    'name': author.get('name'),
                    'id': author.get('id'),
                    'username': author.get('username') or author.get('name', '').lower().replace(' ', '.')
                }
            elif 'author' in node:
                author = node['author']
                comment['author'] = {
                    'name': author.get('name'),
                    'id': author.get('id'),
                    'username': author.get('username') or author.get('name', '').lower().replace(' ', '.')
                }

            # Extract comment replies
            replies = []
            if 'comments' in node:
                replies_obj = node['comments']
                if isinstance(replies_obj, dict):
                    if 'data' in replies_obj:
                        for reply_node in replies_obj['data']:
                            reply = self._parse_comment_node(reply_node)
                            if reply:
                                replies.append(reply)
                    elif 'edges' in replies_obj:
                        for edge in replies_obj['edges']:
                            reply_node = edge.get('node', edge)
                            reply = self._parse_comment_node(reply_node)
                            if reply:
                                replies.append(reply)

            if replies:
                comment['replies'] = replies

            return comment

        except Exception as e:
            logger.debug(f"Error parsing comment node: {e}")
            return None

    async def _extract_comments_for_post(self, page, post_id: str) -> List[Dict[str, Any]]:
        """Extract comments for a specific post from the DOM."""
        try:
            comments = await page.evaluate("""
                (postId) => {
                    const comments = [];
                    try {
                        // Try to find comments section for this post
                        // Facebook uses various selectors for comments
                        const commentSelectors = [
                            `[data-testid="UFI2Comment/root"]`,
                            `[role="article"] [data-testid="UFI2Comment/root"]`,
                            `div[data-testid="comment"]`,
                            `div[class*="comment"]`,
                            `div[data-testid="UFI2Comment/root_text"]`
                        ];

                        for (const selector of commentSelectors) {
                            const commentElements = document.querySelectorAll(selector);
                            if (commentElements.length > 0) {
                                commentElements.forEach((commentEl, index) => {
                                    if (index < 50) { // Limit to 50 comments per post
                                        try {
                                            // Extract comment text
                                            const textEl = commentEl.querySelector('[data-testid="UFI2Comment/root_text"]') ||
                                                          commentEl.querySelector('span[dir="auto"]') ||
                                                          commentEl.querySelector('div[data-testid="comment"] span') ||
                                                          commentEl.querySelector('.comment-text');
                                            const text = textEl ? textEl.innerText : '';

                                            // Extract author
                                            const authorEl = commentEl.querySelector('a[href*="/user/"]') ||
                                                            commentEl.querySelector('a[href*="/profile.php"]') ||
                                                            commentEl.querySelector('strong a') ||
                                                            commentEl.querySelector('[data-testid="UFI2Comment/author_name"]');
                                            let author = null;
                                            if (authorEl) {
                                                const href = authorEl.getAttribute('href') || '';
                                                const usernameMatch = href.match(/\\/(?:user|profile\\.php\\?id=|people\\/)([^\\/\\?]+)/);
                                                const username = usernameMatch ? usernameMatch[1] : authorEl.innerText.trim();
                                                author = {
                                                    name: authorEl.innerText.trim(),
                                                    username: username,
                                                    url: href
                                                };
                                            }

                                            // Extract timestamp
                                            const timeEl = commentEl.querySelector('a[href*="/permalink/"]') ||
                                                          commentEl.querySelector('abbr[data-utime]') ||
                                                          commentEl.querySelector('time');
                                            let timestamp = null;
                                            if (timeEl) {
                                                timestamp = timeEl.getAttribute('data-utime') ||
                                                           timeEl.getAttribute('datetime') ||
                                                           timeEl.getAttribute('title');
                                            }

                                            // Extract like count
                                            const likeEl = commentEl.querySelector('[aria-label*="Like"]') ||
                                                          commentEl.querySelector('[data-testid="UFI2Comment/like"]');
                                            let likeCount = 0;
                                            if (likeEl) {
                                                const likeText = likeEl.getAttribute('aria-label') || likeEl.innerText || '';
                                                const match = likeText.match(/[\\d,]+/);
                                                if (match) {
                                                    likeCount = parseInt(match[0].replace(/,/g, '')) || 0;
                                                }
                                            }

                                            if (text || author) {
                                                comments.push({
                                                    id: `comment_${index}_${Date.now()}`,
                                                    text: text,
                                                    author: author,
                                                    created_time: timestamp,
                                                    like_count: likeCount
                                                });
                                            }
                                        } catch (e) {
                                            console.error('Error extracting comment:', e);
                                        }
                                    }
                                });
                                break; // Found comments, stop trying other selectors
                            }
                        }
                    } catch (e) {
                        console.error('Error in comment extraction:', e);
                    }
                    return comments;
                }
            """, post_id)

            return comments or []
        except Exception as e:
            logger.debug(f"Error extracting comments for post {post_id}: {e}")
            return []

    def _deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on ID."""
        seen = set()
        unique_posts = []

        for post in posts:
            identifier = post.get('id') or post.get('post_id')
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_posts.append(post)
            elif not identifier and post.get('text'):
                # Use text as fallback identifier
                text_hash = hash(post.get('text', '')[:100])
                if text_hash not in seen:
                    seen.add(text_hash)
                    unique_posts.append(post)

        return unique_posts

    async def _scroll_to_load_posts(self, page, max_scrolls: int = 10) -> None:
        """Scroll down to load more posts."""
        try:
            for i in range(max_scrolls):
                # Scroll smoothly
                await page.evaluate("""
                    () => {
                        window.scrollTo({
                            top: document.body.scrollHeight,
                            behavior: 'smooth'
                        });
                    }
                """)
                await page.wait_for_timeout(3000)  # Wait for API requests to complete

                # Check if we've reached the bottom
                is_at_bottom = await page.evaluate("""
                    () => {
                        const scrollHeight = document.documentElement.scrollHeight || document.body.scrollHeight;
                        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                        const clientHeight = window.innerHeight || document.documentElement.clientHeight;
                        return (scrollTop + clientHeight) >= scrollHeight - 100;
                    }
                """)

                if is_at_bottom:
                    logger.debug(f"Reached bottom after {i+1} scrolls")
                    break

                # Also check if new content loaded
                await page.wait_for_timeout(1000)  # Additional wait for lazy loading
        except Exception as e:
            logger.debug(f"Error during scrolling: {e}")

    async def _extract_json_from_page(self, page) -> Dict[str, Any]:
        """Extract JSON data from page."""
        json_data = {}

        try:
            # Try to extract from various JavaScript variables
            page_data = await page.evaluate("""
                () => {
                    const data = {};
                    try {
                        if (window.__d) {
                            data.react_data = window.__d;
                        }
                        if (window.__initialData__) {
                            data.initial_data = window.__initialData__;
                        }
                        if (window.__APOLLO_STATE__) {
                            data.apollo_state = window.__APOLLO_STATE__;
                        }
                        if (window.__relay_internal__) {
                            data.relay_internal = window.__relay_internal__;
                        }
                    } catch (e) {
                        console.error('Error extracting page data:', e);
                    }
                    return data;
                }
            """)

            json_data.update(page_data)
        except Exception as e:
            logger.debug(f"Could not extract page data: {e}")

        return json_data

    def _extract_facebook_data(self, html: str, json_data: Dict[str, Any], posts: List[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from Facebook HTML and JSON."""
        soup = BeautifulSoup(html, 'html.parser')
        posts = posts or []

        # Extract profile information
        profile_info = {}
        text_parts = []

        # Extract from JSON data
        if 'initial_data' in json_data:
            initial_data = json_data['initial_data']
            if 'profile' in initial_data:
                profile = initial_data['profile']
                profile_info.update({
                    'name': profile.get('name'),
                    'username': profile.get('username'),
                    'bio': profile.get('bio') or profile.get('about'),
                    'followers_count': profile.get('followers_count'),
                    'likes_count': profile.get('likes_count'),
                    'verified': profile.get('verified', False),
                    'location': profile.get('location'),
                })

        # Extract from meta tags
        meta_tags = {
            'title': soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'title'}),
            'description': soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'description'}),
            'image': soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'image'}),
            'url': soup.find('meta', property='og:url'),
        }

        for key, tag in meta_tags.items():
            if tag and tag.get('content'):
                profile_info[f'meta_{key}'] = tag['content']
                if key == 'description':
                    text_parts.append(tag['content'])
                elif key == 'title':
                    text_parts.append(f"Title: {tag['content']}")

        # Extract profile name from page
        try:
            name_element = soup.find('h1') or soup.find('span', class_=re.compile(r'.*name.*', re.I))
            if name_element:
                name_text = name_element.get_text(strip=True)
                if name_text:
                    profile_info['name'] = profile_info.get('name') or name_text
                    text_parts.append(f"Name: {name_text}")
        except:
            pass

        # Extract bio/about from page
        try:
            bio_element = soup.find('div', class_=re.compile(r'.*bio.*', re.I)) or \
                         soup.find('div', class_=re.compile(r'.*about.*', re.I)) or \
                         soup.find('div', {'data-testid': 'profile-bio'})
            if bio_element:
                bio_text = bio_element.get_text(strip=True)
                if bio_text:
                    profile_info['bio'] = profile_info.get('bio') or bio_text
                    text_parts.append(f"Bio: {bio_text}")
        except:
            pass

        # Add posts to text
        for i, post in enumerate(posts[:20]):  # Limit to first 20 posts
            post_text = f"Post {i+1}: "
            if post.get('text'):
                post_text += f"{post['text'][:200]}... "
            if post.get('likes'):
                post_text += f"Likes: {post['likes']} "
            if post.get('comments'):
                post_text += f"Comments: {post['comments']} "
            if post.get('shares'):
                post_text += f"Shares: {post['shares']} "
            text_parts.append(post_text)

        # Combine text
        text = " ".join(text_parts) if text_parts else "Facebook profile data"

        # Build metadata with full comment data
        metadata = {
            'profile_info': profile_info,
            'posts': posts,
            'posts_count': len(posts),
            'json_data_keys': list(json_data.keys()),
            'content_length': len(html),
            'text_length': len(text),
            'has_json_data': bool(json_data),
            'scraping_method': 'playwright',
            'total_comments_extracted': sum(len(p.get('comments_data', [])) for p in posts),
        }

        return text, metadata

    async def _scrape_with_http(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Facebook using simple HTTP requests."""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }

            response = await http_client.get(url, headers=headers)
            response.raise_for_status()
            html = response.text

            json_data = self._extract_json_from_html(html)
            posts_data = {'posts': []}
            text, metadata = self._extract_facebook_data(html, json_data, posts_data['posts'])

            scraped = ScrapedData(
                profile=profile,
                platform=self.platform,
                url=url,
                rawContent=text,
                metadata=metadata,
                scrapeStatus=ScrapeStatus.SUCCESS,
            )
            await scraped.insert()
            return scraped

        except Exception as exc:
            logger.exception("Facebook HTTP scrape failed", extra={"url": url})
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

    def _extract_json_from_html(self, html: str) -> Dict[str, Any]:
        """Extract JSON data from HTML."""
        json_data = {}
        soup = BeautifulSoup(html, 'html.parser')

        # Look for various JavaScript variables
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                # Look for __d (React data)
                react_data_match = re.search(
                    r'window\.__d\s*=\s*(\[.+?\]);',
                    script.string,
                    re.DOTALL
                )
                if react_data_match:
                    try:
                        data = json.loads(react_data_match.group(1))
                        json_data['react_data'] = data
                    except json.JSONDecodeError:
                        pass

                # Look for __initialData__
                initial_data_match = re.search(
                    r'window\.__initialData__\s*=\s*({.+?});',
                    script.string,
                    re.DOTALL
                )
                if initial_data_match:
                    try:
                        data = json.loads(initial_data_match.group(1))
                        json_data['initial_data'] = data
                    except json.JSONDecodeError:
                        pass

                # Look for __APOLLO_STATE__
                apollo_match = re.search(
                    r'window\.__APOLLO_STATE__\s*=\s*({.+?});',
                    script.string,
                    re.DOTALL
                )
                if apollo_match:
                    try:
                        data = json.loads(apollo_match.group(1))
                        json_data['apollo_state'] = data
                    except json.JSONDecodeError:
                        pass

        return json_data
