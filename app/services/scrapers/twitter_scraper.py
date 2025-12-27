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


class TwitterScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.TWITTER

    def __init__(self, use_playwright: bool = True):
        """
        Initialize Twitter scraper.

        Args:
            use_playwright: If True, use Playwright for JavaScript rendering.
                          If False, use simple HTTP requests (may miss some data).
        """
        self.use_playwright = use_playwright

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        """
        Override scrape to handle Twitter-specific logic.
        """
        # Normalize Twitter URL
        url = self._normalize_url(url)

        if self.use_playwright:
            return await self._scrape_with_playwright(profile, url)
        else:
            return await self._scrape_with_http(profile, url)

    def _normalize_url(self, url: str) -> str:
        """Normalize Twitter URL to profile format."""
        url = url.strip().rstrip('/')
        if 'twitter.com/' in url or 'x.com/' in url:
            # Extract username from URL
            username_match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
            if username_match:
                username = username_match.group(1)
                # Remove @ if present
                username = username.lstrip('@')
                return f"https://twitter.com/{username}"
        if not url.startswith('http'):
            # Assume it's a username
            username = url.lstrip('@')
            return f"https://twitter.com/{username}"
        return url

    def _extract_username(self, url: str) -> str:
        """Extract username from Twitter URL."""
        match = re.search(r'(?:twitter\.com|x\.com)/([^/?]+)', url)
        if match:
            return match.group(1).lstrip('@')
        return url.replace('https://twitter.com/', '').replace('https://x.com/', '').lstrip('@').rstrip('/')

    async def _scrape_with_playwright(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Twitter using Playwright with network request interception."""
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
                        # Twitter/X uses various API endpoints
                        if any(pattern in url_str for pattern in [
                            '/2/timeline/profile/',
                            '/2/timeline/home.json',
                            '/1.1/statuses/user_timeline.json',
                            '/graphql/',
                            '/api/graphql',
                            '/TweetDetail',
                            '/UserTweets',
                            '/UserByScreenName',
                            '/TweetResultByRestId',
                            '/HomeTimeline',
                            '/SearchTimeline'
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
                            hasLoginPrompt: bodyText.includes('Sign in') || bodyText.includes('Log in') || bodyText.includes('Create account'),
                            hasTweets: document.querySelector('article') !== null ||
                                      document.querySelector('[data-testid="tweet"]') !== null ||
                                      document.querySelector('[role="article"]') !== null,
                            pageTitle: document.title,
                            hasContent: document.querySelector('main') !== null
                        };
                    }
                """)
                logger.info(f"Page check: {page_check}")

                # Try multiple selectors for tweets
                tweet_selectors = [
                    'article[data-testid="tweet"]',
                    '[data-testid="tweet"]',
                    'article',
                    '[role="article"]',
                    'div[data-testid="tweet"]'
                ]

                tweets_found = False
                for selector in tweet_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                        logger.info(f"Found tweets using selector: {selector}")
                        tweets_found = True
                        break
                    except:
                        continue

                if not tweets_found:
                    logger.warning("No tweet selectors found, but continuing to try API extraction")

                # Scroll to load more content
                await self._scroll_to_load_tweets(page)
                await page.wait_for_timeout(5000)  # Wait after scrolling for API requests

                # Extract HTML
                html = await page.content()

                # Extract tweets from multiple sources
                tweets = []

                # Log how many API responses we intercepted
                logger.info(f"Intercepted {len(api_responses)} API responses")
                if api_responses:
                    logger.info(f"API response URLs: {[r['url'][:80] for r in api_responses[:5]]}")

                # Method 1: Extract from API responses
                tweets_from_api = await self._extract_tweets_from_api(api_responses)
                logger.info(f"Extracted {len(tweets_from_api)} tweets from API responses")
                tweets.extend(tweets_from_api)

                # Method 2: Extract from page JavaScript context
                tweets_from_js = await self._extract_tweets_from_page_js(page)
                logger.info(f"Extracted {len(tweets_from_js)} tweets from JavaScript context")
                tweets.extend(tweets_from_js)

                # Method 3: Extract from DOM
                tweets_from_dom = await self._extract_tweets_from_dom(page)
                logger.info(f"Extracted {len(tweets_from_dom)} tweets from DOM")
                tweets.extend(tweets_from_dom)

                # Remove duplicates
                unique_tweets = self._deduplicate_tweets(tweets)
                logger.info(f"Total unique tweets: {len(unique_tweets)}")

                # Extract replies for each tweet
                for tweet in unique_tweets:
                    if tweet.get('id'):
                        tweet_replies = await self._extract_replies_for_tweet(page, tweet['id'])
                        if tweet_replies:
                            tweet['replies_data'] = tweet_replies
                            logger.info(f"Extracted {len(tweet_replies)} replies for tweet {tweet['id']}")

                # Extract text and metadata
                json_data = await self._extract_json_from_page(page)
                text, metadata = self._extract_twitter_data(html, json_data, unique_tweets)

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
                    "Twitter scrape succeeded",
                    extra={
                        "profile_id": str(profile.id),
                        "url": url,
                        "tweets_count": len(unique_tweets)
                    },
                )
                return scraped

        except Exception as exc:
            logger.exception(
                "Twitter scrape failed",
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

    async def _extract_tweets_from_api(self, api_responses: List[Dict]) -> List[Dict[str, Any]]:
        """Extract tweets from intercepted API responses."""
        tweets = []

        for response in api_responses:
            try:
                data = response.get('data', {})

                # Recursively search for tweets in the response
                def find_tweets_recursive(obj, depth=0):
                    if depth > 15:
                        return []

                    found_tweets = []

                    if isinstance(obj, dict):
                        # Look for various Twitter data structures
                        # Twitter API v2 structure
                        if 'data' in obj and isinstance(obj['data'], list):
                            for item in obj['data']:
                                tweet = self._parse_tweet_node(item)
                                if tweet:
                                    found_tweets.append(tweet)

                        # GraphQL structure
                        if 'user' in obj:
                            user = obj['user']
                            if 'result' in user:
                                result = user['result']
                                if 'timeline' in result:
                                    timeline = result['timeline']
                                    if 'timeline' in timeline:
                                        instructions = timeline['timeline'].get('instructions', [])
                                        for instruction in instructions:
                                            if 'entries' in instruction:
                                                for entry in instruction['entries']:
                                                    content = entry.get('content', {})
                                                    if 'itemContent' in content:
                                                        item_content = content['itemContent']
                                                        if 'tweet_results' in item_content:
                                                            tweet_result = item_content['tweet_results'].get('result', {})
                                                            tweet = self._parse_tweet_from_graphql(tweet_result)
                                                            if tweet:
                                                                found_tweets.append(tweet)

                        # Legacy API structure
                        if 'statuses' in obj:
                            for status in obj['statuses']:
                                tweet = self._parse_legacy_tweet(status)
                                if tweet:
                                    found_tweets.append(tweet)

                        # Recursively search
                        for value in obj.values():
                            found_tweets.extend(find_tweets_recursive(value, depth + 1))

                    elif isinstance(obj, list):
                        for item in obj:
                            found_tweets.extend(find_tweets_recursive(item, depth + 1))

                    return found_tweets

                found = find_tweets_recursive(data)
                tweets.extend(found)

            except Exception as e:
                logger.debug(f"Error extracting from API response: {e}")

        return tweets

    async def _extract_tweets_from_page_js(self, page) -> List[Dict[str, Any]]:
        """Extract tweets from page JavaScript context."""
        try:
            tweets = await page.evaluate("""
                () => {
                    const tweets = [];
                    try {
                        // Try to find tweets in window.__INITIAL_STATE__ or similar
                        if (window.__INITIAL_STATE__) {
                            const state = window.__INITIAL_STATE__;
                            // Navigate through state to find tweets
                            if (state.entities && state.entities.tweets) {
                                Object.values(state.entities.tweets).forEach(tweet => {
                                    tweets.push({
                                        id: tweet.id_str || tweet.id,
                                        text: tweet.full_text || tweet.text,
                                        created_at: tweet.created_at,
                                        retweet_count: tweet.retweet_count || 0,
                                        favorite_count: tweet.favorite_count || 0,
                                        reply_count: tweet.reply_count || 0,
                                        user: tweet.user ? {
                                            screen_name: tweet.user.screen_name,
                                            name: tweet.user.name
                                        } : null
                                    });
                                });
                            }
                        }

                        // Try to find in window.__NEXT_DATA__
                        if (window.__NEXT_DATA__) {
                            const nextData = window.__NEXT_DATA__;
                            if (nextData.props && nextData.props.pageProps) {
                                // Navigate through Next.js data structure
                                const pageProps = nextData.props.pageProps;
                                if (pageProps.tweets) {
                                    pageProps.tweets.forEach(tweet => {
                                        tweets.push({
                                            id: tweet.id_str || tweet.id,
                                            text: tweet.text || tweet.full_text,
                                            created_at: tweet.created_at,
                                            retweet_count: tweet.retweet_count || 0,
                                            favorite_count: tweet.favorite_count || 0
                                        });
                                    });
                                }
                            }
                        }

                        // Try to find in document.querySelectorAll for article elements
                        const articles = document.querySelectorAll('article[data-testid="tweet"]');
                        articles.forEach((article, index) => {
                            if (index < 20) { // Limit to first 20
                                try {
                                    const tweetText = article.querySelector('[data-testid="tweetText"]')?.innerText || '';
                                    const tweetId = article.getAttribute('data-tweet-id') || '';
                                    if (tweetText || tweetId) {
                                        tweets.push({
                                            id: tweetId,
                                            text: tweetText,
                                            source: 'dom_js'
                                        });
                                    }
                                } catch (e) {
                                    console.error('Error extracting tweet from article:', e);
                                }
                            }
                        });
                    } catch (e) {
                        console.error('Error extracting tweets from JS:', e);
                    }
                    return tweets;
                }
            """)
            return tweets or []
        except Exception as e:
            logger.debug(f"Error extracting tweets from JS: {e}")
            return []

    async def _extract_tweets_from_dom(self, page) -> List[Dict[str, Any]]:
        """Extract tweets from DOM as fallback."""
        tweets = []
        try:
            tweet_elements = await page.evaluate("""
                () => {
                    const tweets = [];
                    const articles = document.querySelectorAll('article[data-testid="tweet"]');
                    articles.forEach((article, index) => {
                        if (index < 20) { // Limit to first 20
                            try {
                                const tweetTextEl = article.querySelector('[data-testid="tweetText"]');
                                const tweetText = tweetTextEl ? tweetTextEl.innerText : '';

                                // Try to get tweet ID from various attributes
                                let tweetId = article.getAttribute('data-tweet-id') ||
                                             article.getAttribute('data-item-id') ||
                                             article.querySelector('a[href*="/status/"]')?.href?.match(/\\/status\\/(\\d+)/)?.[1] || '';

                                // Extract engagement metrics
                                const getMetric = (label) => {
                                    const buttons = article.querySelectorAll('button');
                                    for (const btn of buttons) {
                                        const labelEl = btn.querySelector(`[aria-label*="${label}"]`);
                                        if (labelEl) {
                                            const text = btn.innerText || '';
                                            const match = text.match(/[\\d,]+/);
                                            return match ? parseInt(match[0].replace(/,/g, '')) : 0;
                                        }
                                    }
                                    return 0;
                                };

                                const retweetCount = getMetric('Retweet');
                                const likeCount = getMetric('Like');
                                const replyCount = getMetric('Reply');

                                if (tweetText || tweetId) {
                                    tweets.push({
                                        id: tweetId,
                                        text: tweetText,
                                        retweet_count: retweetCount,
                                        favorite_count: likeCount,
                                        reply_count: replyCount,
                                        source: 'dom'
                                    });
                                }
                            } catch (e) {
                                console.error('Error extracting tweet from article:', e);
                            }
                        }
                    });
                    return tweets;
                }
            """)

            for tweet_elem in tweet_elements:
                tweets.append(tweet_elem)
        except Exception as e:
            logger.debug(f"Error extracting tweets from DOM: {e}")

        return tweets

    def _parse_tweet_node(self, node: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a single tweet node from Twitter API v2 structure."""
        try:
            if not node or not node.get('id'):
                return None

            tweet = {
                'id': node.get('id') or node.get('id_str'),
                'text': node.get('text') or node.get('full_text', ''),
                'created_at': node.get('created_at'),
                'retweet_count': node.get('public_metrics', {}).get('retweet_count', 0) or node.get('retweet_count', 0),
                'like_count': node.get('public_metrics', {}).get('like_count', 0) or node.get('favorite_count', 0),
                'reply_count': node.get('public_metrics', {}).get('reply_count', 0) or node.get('reply_count', 0),
                'quote_count': node.get('public_metrics', {}).get('quote_count', 0),
            }

            # Extract author info
            if 'author_id' in node:
                tweet['author_id'] = node['author_id']
            if 'author' in node:
                author = node['author']
                tweet['author'] = {
                    'username': author.get('username'),
                    'name': author.get('name'),
                    'id': author.get('id')
                }

            # Extract entities
            if 'entities' in node:
                entities = node['entities']
                tweet['hashtags'] = [tag.get('tag') for tag in entities.get('hashtags', [])]
                tweet['mentions'] = [mention.get('username') for mention in entities.get('mentions', [])]
                tweet['urls'] = [url.get('expanded_url') for url in entities.get('urls', [])]

            # Extract replies if available in the node structure
            replies_data = []
            if 'replies' in node:
                replies_obj = node['replies']
                if isinstance(replies_obj, dict) and 'data' in replies_obj:
                    for reply_node in replies_obj['data']:
                        reply = self._parse_tweet_node(reply_node)
                        if reply:
                            replies_data.append(reply)

            if replies_data:
                tweet['replies_data'] = replies_data

            return tweet

        except Exception as e:
            logger.debug(f"Error parsing tweet node: {e}")
            return None

    async def _extract_replies_for_tweet(self, page, tweet_id: str) -> List[Dict[str, Any]]:
        """Extract replies for a specific tweet from the DOM."""
        try:
            replies = await page.evaluate("""
                (tweetId) => {
                    const replies = [];
                    try {
                        // Find the tweet element
                        const tweetSelectors = [
                            `article[data-testid="tweet"][data-tweet-id="${tweetId}"]`,
                            `article[data-testid="tweet"]`,
                            `div[data-testid="tweet"]`
                        ];

                        let tweetElement = null;
                        for (const selector of tweetSelectors) {
                            const elements = document.querySelectorAll(selector);
                            for (const el of elements) {
                                const idAttr = el.getAttribute('data-tweet-id') ||
                                              el.querySelector('a[href*="/status/"]')?.href?.match(/\\/status\\/(\\d+)/)?.[1];
                                if (idAttr === tweetId || !tweetId) {
                                    tweetElement = el;
                                    break;
                                }
                            }
                            if (tweetElement) break;
                        }

                        if (!tweetElement) {
                            // Try to find replies in the thread
                            const allTweets = document.querySelectorAll('article[data-testid="tweet"]');
                            allTweets.forEach((tweetEl, index) => {
                                if (index < 20) { // Limit to first 20 replies
                                    try {
                                        const replyTextEl = tweetEl.querySelector('[data-testid="tweetText"]');
                                        const replyText = replyTextEl ? replyTextEl.innerText : '';

                                        const authorEl = tweetEl.querySelector('a[href*="/"]');
                                        let author = null;
                                        if (authorEl) {
                                            const href = authorEl.getAttribute('href') || '';
                                            const usernameMatch = href.match(/\\/([^\\/]+)$/);
                                            const username = usernameMatch ? usernameMatch[1] : '';
                                            author = {
                                                username: username,
                                                name: authorEl.innerText.trim(),
                                                url: href
                                            };
                                        }

                                        const timeEl = tweetEl.querySelector('time');
                                        const timestamp = timeEl ? timeEl.getAttribute('datetime') : null;

                                        const likeEl = tweetEl.querySelector('[data-testid="like"]');
                                        let likeCount = 0;
                                        if (likeEl) {
                                            const likeText = likeEl.getAttribute('aria-label') || '';
                                            const match = likeText.match(/[\\d,]+/);
                                            if (match) {
                                                likeCount = parseInt(match[0].replace(/,/g, '')) || 0;
                                            }
                                        }

                                        if (replyText || author) {
                                            replies.push({
                                                id: `reply_${index}_${Date.now()}`,
                                                text: replyText,
                                                author: author,
                                                created_at: timestamp,
                                                like_count: likeCount
                                            });
                                        }
                                    } catch (e) {
                                        console.error('Error extracting reply:', e);
                                    }
                                }
                            });
                        }
                    } catch (e) {
                        console.error('Error in reply extraction:', e);
                    }
                    return replies;
                }
            """, tweet_id)

            return replies or []
        except Exception as e:
            logger.debug(f"Error extracting replies for tweet {tweet_id}: {e}")
            return []

    def _parse_tweet_from_graphql(self, tweet_result: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a tweet from Twitter GraphQL structure."""
        try:
            # Navigate through GraphQL structure
            if 'tweet' in tweet_result:
                tweet_data = tweet_result['tweet']
            elif 'legacy' in tweet_result:
                tweet_data = tweet_result
            else:
                tweet_data = tweet_result

            if 'legacy' in tweet_data:
                legacy = tweet_data['legacy']
                tweet = {
                    'id': tweet_data.get('rest_id') or legacy.get('id_str'),
                    'text': legacy.get('full_text') or legacy.get('text', ''),
                    'created_at': legacy.get('created_at'),
                    'retweet_count': legacy.get('retweet_count', 0),
                    'favorite_count': legacy.get('favorite_count', 0),
                    'reply_count': legacy.get('reply_count', 0),
                    'quote_count': legacy.get('quote_count', 0),
                }

                # Extract entities
                if 'entities' in legacy:
                    entities = legacy['entities']
                    tweet['hashtags'] = [tag.get('text') for tag in entities.get('hashtags', [])]
                    tweet['mentions'] = [mention.get('screen_name') for mention in entities.get('user_mentions', [])]
                    tweet['urls'] = [url.get('expanded_url') for url in entities.get('urls', [])]

                # Extract author
                if 'core' in tweet_data and 'user_results' in tweet_data['core']:
                    user_result = tweet_data['core']['user_results'].get('result', {})
                    if 'legacy' in user_result:
                        user_legacy = user_result['legacy']
                        tweet['author'] = {
                            'username': user_legacy.get('screen_name'),
                            'name': user_legacy.get('name'),
                            'id': user_result.get('rest_id')
                        }

                return tweet

            return None

        except Exception as e:
            logger.debug(f"Error parsing tweet from GraphQL: {e}")
            return None

    def _parse_legacy_tweet(self, status: Dict[str, Any]) -> Dict[str, Any] | None:
        """Parse a tweet from legacy Twitter API structure."""
        try:
            if not status or not status.get('id_str'):
                return None

            tweet = {
                'id': status.get('id_str'),
                'text': status.get('full_text') or status.get('text', ''),
                'created_at': status.get('created_at'),
                'retweet_count': status.get('retweet_count', 0),
                'favorite_count': status.get('favorite_count', 0),
                'reply_count': status.get('reply_count', 0),
            }

            # Extract entities
            if 'entities' in status:
                entities = status['entities']
                tweet['hashtags'] = [tag.get('text') for tag in entities.get('hashtags', [])]
                tweet['mentions'] = [mention.get('screen_name') for mention in entities.get('user_mentions', [])]
                tweet['urls'] = [url.get('expanded_url') for url in entities.get('urls', [])]

            # Extract author
            if 'user' in status:
                user = status['user']
                tweet['author'] = {
                    'username': user.get('screen_name'),
                    'name': user.get('name'),
                    'id': user.get('id_str')
                }

            return tweet

        except Exception as e:
            logger.debug(f"Error parsing legacy tweet: {e}")
            return None

    def _deduplicate_tweets(self, tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate tweets based on ID."""
        seen = set()
        unique_tweets = []

        for tweet in tweets:
            identifier = tweet.get('id') or tweet.get('tweet_id')
            if identifier and identifier not in seen:
                seen.add(identifier)
                unique_tweets.append(tweet)
            elif not identifier and tweet.get('text'):
                # Use text as fallback identifier
                text_hash = hash(tweet.get('text', '')[:100])
                if text_hash not in seen:
                    seen.add(text_hash)
                    unique_tweets.append(tweet)

        return unique_tweets

    async def _scroll_to_load_tweets(self, page, max_scrolls: int = 10) -> None:
        """Scroll down to load more tweets."""
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
                        if (window.__INITIAL_STATE__) {
                            data.initial_state = window.__INITIAL_STATE__;
                        }
                        if (window.__NEXT_DATA__) {
                            data.next_data = window.__NEXT_DATA__;
                        }
                        if (window.__META_DATA__) {
                            data.meta_data = window.__META_DATA__;
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

    def _extract_twitter_data(self, html: str, json_data: Dict[str, Any], tweets: List[Dict[str, Any]] = None) -> tuple[str, Dict[str, Any]]:
        """Extract text and metadata from Twitter HTML and JSON."""
        soup = BeautifulSoup(html, 'html.parser')
        tweets = tweets or []

        # Extract profile information
        profile_info = {}
        text_parts = []

        # Extract from JSON data
        if 'next_data' in json_data:
            next_data = json_data['next_data']
            if 'props' in next_data and 'pageProps' in next_data['props']:
                page_props = next_data['props']['pageProps']
                if 'user' in page_props:
                    user = page_props['user']
                    profile_info.update({
                        'username': user.get('screen_name') or user.get('username'),
                        'name': user.get('name'),
                        'description': user.get('description') or user.get('bio'),
                        'followers_count': user.get('followers_count'),
                        'following_count': user.get('friends_count') or user.get('following_count'),
                        'tweets_count': user.get('statuses_count'),
                        'verified': user.get('verified', False),
                        'location': user.get('location'),
                        'created_at': user.get('created_at'),
                    })

        if 'initial_state' in json_data:
            initial_state = json_data['initial_state']
            if 'entities' in initial_state and 'users' in initial_state['entities']:
                users = initial_state['entities']['users']
                if users:
                    # Get first user (usually the profile owner)
                    user_id = list(users.keys())[0]
                    user = users[user_id]
                    profile_info.update({
                        'username': user.get('screen_name'),
                        'name': user.get('name'),
                        'description': user.get('description'),
                        'followers_count': user.get('followers_count'),
                        'following_count': user.get('friends_count'),
                        'tweets_count': user.get('statuses_count'),
                        'verified': user.get('verified', False),
                    })

        # Extract from meta tags
        meta_tags = {
            'title': soup.find('meta', property='og:title') or soup.find('meta', attrs={'name': 'twitter:title'}),
            'description': soup.find('meta', property='og:description') or soup.find('meta', attrs={'name': 'twitter:description'}),
            'image': soup.find('meta', property='og:image') or soup.find('meta', attrs={'name': 'twitter:image'}),
        }

        for key, tag in meta_tags.items():
            if tag and tag.get('content'):
                profile_info[f'meta_{key}'] = tag['content']
                if key == 'description':
                    text_parts.append(tag['content'])
                elif key == 'title':
                    text_parts.append(f"Title: {tag['content']}")

        # Extract profile description from page
        try:
            bio_element = soup.find('div', {'data-testid': 'UserDescription'}) or \
                         soup.find('div', class_=re.compile(r'.*bio.*', re.I))
            if bio_element:
                bio_text = bio_element.get_text(strip=True)
                if bio_text:
                    profile_info['bio'] = bio_text
                    text_parts.append(f"Bio: {bio_text}")
        except:
            pass

        # Add tweets to text
        for i, tweet in enumerate(tweets[:20]):  # Limit to first 20 tweets
            tweet_text = f"Tweet {i+1}: "
            if tweet.get('text'):
                tweet_text += f"{tweet['text'][:200]}... "
            if tweet.get('retweet_count'):
                tweet_text += f"Retweets: {tweet['retweet_count']} "
            if tweet.get('like_count') or tweet.get('favorite_count'):
                count = tweet.get('like_count') or tweet.get('favorite_count')
                tweet_text += f"Likes: {count} "
            if tweet.get('reply_count'):
                tweet_text += f"Replies: {tweet['reply_count']} "
            text_parts.append(tweet_text)

        # Combine text
        text = " ".join(text_parts) if text_parts else "Twitter profile data"

        # Build metadata with full reply data
        metadata = {
            'profile_info': profile_info,
            'tweets': tweets,
            'tweets_count': len(tweets),
            'json_data_keys': list(json_data.keys()),
            'content_length': len(html),
            'text_length': len(text),
            'has_json_data': bool(json_data),
            'scraping_method': 'playwright',
            'total_replies_extracted': sum(len(t.get('replies_data', [])) for t in tweets),
        }

        return text, metadata

    async def _scrape_with_http(self, profile: Profile, url: str) -> ScrapedData:
        """Scrape Twitter using simple HTTP requests."""
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
            tweets_data = {'tweets': []}
            text, metadata = self._extract_twitter_data(html, json_data, tweets_data['tweets'])

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
            logger.exception("Twitter HTTP scrape failed", extra={"url": url})
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
                # Look for __INITIAL_STATE__
                initial_state_match = re.search(
                    r'window\.__INITIAL_STATE__\s*=\s*({.+?});',
                    script.string,
                    re.DOTALL
                )
                if initial_state_match:
                    try:
                        data = json.loads(initial_state_match.group(1))
                        json_data['initial_state'] = data
                    except json.JSONDecodeError:
                        pass

                # Look for __NEXT_DATA__
                next_data_match = re.search(
                    r'__NEXT_DATA__\s*=\s*({.+?});',
                    script.string,
                    re.DOTALL
                )
                if next_data_match:
                    try:
                        data = json.loads(next_data_match.group(1))
                        json_data['next_data'] = data
                    except json.JSONDecodeError:
                        pass

        return json_data
