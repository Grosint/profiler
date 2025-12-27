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


class InstagramScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.INSTAGRAM

    def __init__(self, use_playwright: bool = True):
        """
        Initialize Instagram scraper.

        Args:
            use_playwright: If True, use Playwright for JavaScript rendering.
                          If False, use simple HTTP requests (may miss some data).
        """
        self.use_playwright = use_playwright

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        """
        Override scrape to handle Instagram-specific logic.
        """
        # Normalize Instagram URL
        url = self._normalize_url(url)

        if self.use_playwright:
            return await self._scrape_with_playwright(profile, url)
        else:
            return await self._scrape_with_http(profile, url)

    def _normalize_url(self, url: str) -> str:
        """Normalize Instagram URL to profile format."""
        url = url.strip().rstrip('/')
        if 'instagram.com/' in url:
            username_match = re.search(r'instagram\.com/([^/?]+)', url)
            if username_match:
                username = username_match.group(1)
                return f"https://www.instagram.com/{username}/"
        if not url.startswith('http'):
            return f"https://www.instagram.com/{url}/"
        return url

    def _extract_username(self, url: str) -> str:
        """Extract username from Instagram URL."""
        match = re.search(r'instagram\.com/([^/?]+)', url)
        if match:
            return match.group(1)
        return url.replace('https://www.instagram.com/', '').rstrip('/')

    async def _scrape_with_playwright(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Instagram using Playwright with network request interception."""
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                )
                page = await context.new_page()

                # Store intercepted GraphQL responses
                graphql_responses = []

                # Intercept network requests to catch GraphQL queries
                async def handle_response(response):
                    try:
                        url_str = response.url
                        # Instagram uses various GraphQL endpoints
                        if any(pattern in url_str for pattern in [
                            '/graphql/query/',
                            '/api/graphql',
                            '/query/',
                            '/api/v1/users/',
                            '/api/v1/feed/'
                        ]):
                            try:
                                data = await response.json()
                                graphql_responses.append({
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
                await page.wait_for_timeout(5000)  # Wait longer for initial load

                # Check if we're being asked to log in
                login_check = await page.evaluate("""
                    () => {
                        const bodyText = document.body.innerText || '';
                        return {
                            hasLoginPrompt: bodyText.includes('Log in') || bodyText.includes('Sign up'),
                            hasPosts: document.querySelector('article') !== null ||
                                     document.querySelector('[role="main"]') !== null ||
                                     document.querySelector('main') !== null,
                            pageTitle: document.title
                        };
                    }
                """)
                logger.info(f"Page check: {login_check}")

                # Try multiple selectors for posts
                post_selectors = [
                    'article',
                    'a[href*="/p/"]',
                    '[role="main"] article',
                    'main article',
                    'div[role="main"] a[href*="/p/"]'
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
                    logger.warning("No post selectors found, but continuing to try GraphQL extraction")

                # Scroll to load more content (even if selectors not found, scrolling might trigger GraphQL requests)
                await self._scroll_to_load_posts(page)
                await page.wait_for_timeout(5000)  # Wait longer after scrolling for GraphQL requests

                # Extract HTML
                html = await page.content()

                # Extract posts from multiple sources
                posts = []

                # Log how many GraphQL responses we intercepted
                logger.info(f"Intercepted {len(graphql_responses)} API responses")
                if graphql_responses:
                    logger.info(f"API response URLs: {[r['url'][:80] for r in graphql_responses[:5]]}")

                # Method 1: Extract from GraphQL responses
                posts_from_graphql = await self._extract_posts_from_graphql(graphql_responses)
                logger.info(f"Extracted {len(posts_from_graphql)} posts from GraphQL responses")
                posts.extend(posts_from_graphql)

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

                # Extract text and metadata
                json_data = await self._extract_json_from_page(page)
                text, metadata = self._extract_instagram_data(html, json_data, unique_posts)

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
                    "Instagram scrape succeeded",
                    extra={
                        "profile_id": str(profile.id),
                        "url": url,
                        "posts_count": len(unique_posts)
                    },
                )
                return scraped

        except Exception as exc:
            logger.exception(
                "Instagram scrape failed",
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

    async def _extract_posts_from_graphql(self, graphql_responses: List[Dict]) -> List[Dict[str, Any]]:
        """Extract posts from intercepted GraphQL responses."""
        posts = []

        for response in graphql_responses:
            try:
                data = response.get('data', {})

                # Recursively search for posts in the response
                def find_posts_recursive(obj, depth=0):
                    if depth > 10:
                        return []

                    found_posts = []

                    if isinstance(obj, dict):
                        # Look for edge_owner_to_timeline_media or similar structures
                        if 'edge_owner_to_timeline_media' in obj:
                            edges = obj['edge_owner_to_timeline_media'].get('edges', [])
                            for edge in edges:
                                node = edge.get('node', {})
                                post = self._parse_post_node(node)
                                if post:
                                    found_posts.append(post)

                        # Also check for user data
                        if 'user' in obj and isinstance(obj['user'], dict):
                            user = obj['user']
                            if 'edge_owner_to_timeline_media' in user:
                                edges = user['edge_owner_to_timeline_media'].get('edges', [])
                                for edge in edges:
                                    node = edge.get('node', {})
                                    post = self._parse_post_node(node)
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
                logger.debug(f"Error extracting from GraphQL response: {e}")

        return posts

    async def _extract_posts_from_page_js(self, page) -> List[Dict[str, Any]]:
        """Extract posts from page JavaScript context."""
        try:
            posts = await page.evaluate("""
                () => {
                    const posts = [];
                    try {
                        // Try to find posts in window._sharedData
                        if (window._sharedData && window._sharedData.entry_data) {
                            const entryData = window._sharedData.entry_data;
                            if (entryData.ProfilePage && entryData.ProfilePage[0]) {
                                const profilePage = entryData.ProfilePage[0];
                                if (profilePage.graphql && profilePage.graphql.user) {
                                    const user = profilePage.graphql.user;
                                    if (user.edge_owner_to_timeline_media) {
                                        const edges = user.edge_owner_to_timeline_media.edges || [];
                                        edges.forEach(edge => {
                                            if (edge.node) {
                                                const node = edge.node;
                                                const post = {
                                                    id: node.id,
                                                    shortcode: node.shortcode,
                                                    url: node.shortcode ? `https://www.instagram.com/p/${node.shortcode}/` : null,
                                                    caption: node.edge_media_to_caption?.edges?.[0]?.node?.text || '',
                                                    likes_count: node.edge_media_preview_like?.count || node.likes?.count || 0,
                                                    comments_count: node.edge_media_to_comment?.count || 0,
                                                    timestamp: node.taken_at_timestamp,
                                                    is_video: node.is_video || false,
                                                    display_url: node.display_url || node.display_src
                                                };

                                                // Extract comments
                                                if (node.edge_media_to_comment?.edges) {
                                                    post.comments = node.edge_media_to_comment.edges.slice(0, 10).map(commentEdge => {
                                                        const commentNode = commentEdge.node;
                                                        return {
                                                            text: commentNode.text || '',
                                                            username: commentNode.owner?.username || '',
                                                            timestamp: commentNode.created_at,
                                                            likes: commentNode.edge_liked_by?.count || 0
                                                        };
                                                    });
                                                }

                                                posts.push(post);
                                            }
                                        });
                                    }
                                }
                            }
                        }
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
                    const articles = document.querySelectorAll('article');
                    articles.forEach((article, index) => {
                        if (index < 12) { // Limit to first 12 posts
                            const links = article.querySelectorAll('a[href*="/p/"]');
                            links.forEach(link => {
                                const href = link.getAttribute('href');
                                const match = href.match(/\\/p\\/([^\\/]+)/);
                                if (match) {
                                    const shortcode = match[1];
                                    if (!posts.find(p => p.shortcode === shortcode)) {
                                        posts.push({
                                            shortcode: shortcode,
                                            url: 'https://www.instagram.com' + href,
                                            source: 'dom'
                                        });
                                    }
                                }
                            });
                        }
                    });
                    return posts;
                }
            """)

            for post_elem in post_elements:
                posts.append({
                    'shortcode': post_elem.get('shortcode'),
                    'url': post_elem.get('url'),
                    'source': 'dom'
                })
        except Exception as e:
            logger.debug(f"Error extracting posts from DOM: {e}")

        return posts

    def _parse_post_node(self, node: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single post node from Instagram's data structure."""
        try:
            if not node or not node.get('shortcode'):
                return None

            post = {
                'id': node.get('id'),
                'shortcode': node.get('shortcode'),
                'url': f"https://www.instagram.com/p/{node.get('shortcode')}/" if node.get('shortcode') else None,
                'timestamp': node.get('taken_at_timestamp'),
                'is_video': node.get('is_video', False),
                'dimensions': node.get('dimensions'),
            }

            # Extract caption
            edge_media_to_caption = node.get('edge_media_to_caption', {})
            edges = edge_media_to_caption.get('edges', [])
            if edges and len(edges) > 0:
                caption_node = edges[0].get('node', {})
                post['caption'] = caption_node.get('text', '')
            else:
                post['caption'] = node.get('caption', '')

            # Extract likes count
            edge_media_preview_like = node.get('edge_media_preview_like', {})
            post['likes_count'] = edge_media_preview_like.get('count', 0)
            if post['likes_count'] == 0:
                post['likes_count'] = node.get('likes', {}).get('count', 0)

            # Extract comments count
            edge_media_to_comment = node.get('edge_media_to_comment', {})
            post['comments_count'] = edge_media_to_comment.get('count', 0)

            # Extract display URL
            post['display_url'] = node.get('display_url') or node.get('display_src')

            # Extract comments (up to 50 for better analysis)
            comments = []
            if edge_media_to_comment.get('edges'):
                comment_edges = edge_media_to_comment['edges'][:50]  # Increased from 10 to 50
                for comment_edge in comment_edges:
                    comment_node = comment_edge.get('node', {})
                    if comment_node:
                        owner = comment_node.get('owner', {})
                        comment = {
                            'id': comment_node.get('id'),
                            'text': comment_node.get('text', ''),
                            'author': {
                                'username': owner.get('username', ''),
                                'id': owner.get('id'),
                                'is_verified': owner.get('is_verified', False)
                            },
                            'timestamp': comment_node.get('created_at'),
                            'likes': comment_node.get('edge_liked_by', {}).get('count', 0)
                        }

                        # Extract comment replies if available
                        if 'edge_threaded_comments' in comment_node:
                            replies_edges = comment_node.get('edge_threaded_comments', {}).get('edges', [])
                            replies = []
                            for reply_edge in replies_edges[:10]:  # Limit replies to 10 per comment
                                reply_node = reply_edge.get('node', {})
                                if reply_node:
                                    reply_owner = reply_node.get('owner', {})
                                    replies.append({
                                        'id': reply_node.get('id'),
                                        'text': reply_node.get('text', ''),
                                        'author': {
                                            'username': reply_owner.get('username', ''),
                                            'id': reply_owner.get('id'),
                                            'is_verified': reply_owner.get('is_verified', False)
                                        },
                                        'timestamp': reply_node.get('created_at'),
                                        'likes': reply_node.get('edge_liked_by', {}).get('count', 0)
                                    })
                            if replies:
                                comment['replies'] = replies

                        comments.append(comment)

            post['comments'] = comments

            return post

        except Exception as e:
            logger.debug(f"Error parsing post node: {e}")
            return None

    def _deduplicate_posts(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate posts based on shortcode or ID."""
        seen = set()
        unique_posts = []

        for post in posts:
            identifier = post.get('shortcode') or post.get('id')
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_posts.append(post)

        return unique_posts

    async def _scroll_to_load_posts(self, page, max_scrolls: int = 5) -> None:
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
                await page.wait_for_timeout(3000)  # Wait longer for GraphQL requests to complete

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
            shared_data = await page.evaluate("""
                () => {
                    try {
                        if (window._sharedData) return window._sharedData;
                        return null;
                    } catch (e) {
                        return null;
                    }
                }
            """)

            if shared_data:
                json_data['shared_data'] = shared_data
        except Exception as e:
            logger.debug(f"Could not extract shared data: {e}")

        return json_data

    def _extract_instagram_data(self, html: str, json_data: Dict[str, Any], posts: List[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from Instagram HTML and JSON."""
        soup = BeautifulSoup(html, 'html.parser')
        posts = posts or []

        # Extract profile information
        profile_info = {}
        text_parts = []

        # Extract from JSON data
        if 'shared_data' in json_data:
            shared = json_data['shared_data']
            if 'entry_data' in shared:
                entry_data = shared['entry_data']
                if 'ProfilePage' in entry_data:
                    profile_page = entry_data['ProfilePage'][0]
                    if 'graphql' in profile_page:
                        user = profile_page['graphql'].get('user', {})
                        profile_info.update({
                            'username': user.get('username'),
                            'full_name': user.get('full_name'),
                            'biography': user.get('biography'),
                            'followers': user.get('edge_followed_by', {}).get('count'),
                            'following': user.get('edge_follow', {}).get('count'),
                            'posts_count': user.get('edge_owner_to_timeline_media', {}).get('count'),
                            'is_verified': user.get('is_verified'),
                            'is_private': user.get('is_private'),
                        })

        # Extract from meta tags
        meta_tags = {
            'title': soup.find('meta', property='og:title'),
            'description': soup.find('meta', property='og:description'),
            'image': soup.find('meta', property='og:image'),
        }

        for key, tag in meta_tags.items():
            if tag and tag.get('content'):
                profile_info[f'meta_{key}'] = tag['content']
                if key == 'description':
                    text_parts.append(tag['content'])
                elif key == 'title':
                    text_parts.append(f"Title: {tag['content']}")

        # Add posts to text
        for i, post in enumerate(posts[:10]):
            post_text = f"Post {i+1}: "
            if post.get('caption'):
                post_text += f"Caption: {post['caption'][:200]}... "
            if post.get('likes_count'):
                post_text += f"Likes: {post['likes_count']} "
            if post.get('comments_count'):
                post_text += f"Comments: {post['comments_count']} "
            text_parts.append(post_text)

        # Combine text
        text = " ".join(text_parts) if text_parts else "Instagram profile data"

        # Build metadata with full comment data
        total_comments = sum(len(p.get('comments', [])) for p in posts)
        total_replies = sum(
            sum(len(c.get('replies', [])) for c in p.get('comments', []))
            for p in posts
        )
        metadata = {
            'profile_info': profile_info,
            'posts': posts,
            'posts_count': len(posts),
            'json_data_keys': list(json_data.keys()),
            'content_length': len(html),
            'text_length': len(text),
            'has_json_data': bool(json_data),
            'scraping_method': 'playwright',
            'total_comments_extracted': total_comments,
            'total_comment_replies_extracted': total_replies,
        }

        return text, metadata

    async def _scrape_with_http(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Instagram using simple HTTP requests."""
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
            text, metadata = self._extract_instagram_data(html, json_data, posts_data['posts'])

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
            logger.exception("Instagram HTTP scrape failed", extra={"url": url})
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

        # Look for window._sharedData
        scripts = soup.find_all('script')
        for script in scripts:
            if script.string:
                shared_data_match = re.search(
                    r'window\._sharedData\s*=\s*({.+?});',
                    script.string,
                    re.DOTALL
                )
                if shared_data_match:
                    try:
                        data = json.loads(shared_data_match.group(1))
                        json_data['shared_data'] = data
                    except json.JSONDecodeError:
                        pass

        return json_data
