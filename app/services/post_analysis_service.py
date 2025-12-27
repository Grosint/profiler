"""
Post Analysis Service

Analyzes posts and their comments, identifying toxic and anti-national content.
"""

import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from beanie import PydanticObjectId

from app.models.post import Post, PostStatus, PostType, CommentAnalysis, PostAnalysisResult
from app.models.scraped_data import ScrapedData, ScrapeStatus
from app.schemas.post import CreatePostAnalysisRequest, PostStatusResponse, PostListItem
from app.services.toxicity_analyzer import ToxicityAnalyzer
from app.services.scrapers.base_scraper import BaseScraper
from app.services.scrapers.twitter_scraper import TwitterScraper
from app.services.scrapers.facebook_scraper import FacebookScraper
from app.services.scrapers.instagram_scraper import InstagramScraper
from app.services.scrapers.reddit_scraper import RedditScraper
from app.services.scrapers.linkedin_scraper import LinkedInScraper

logger = logging.getLogger(__name__)


def detect_platform_from_url(url: str) -> str:
    """Detect platform from URL."""
    url_lower = url.lower()
    if 'twitter.com' in url_lower or 'x.com' in url_lower:
        return 'twitter'
    elif 'facebook.com' in url_lower or 'fb.com' in url_lower:
        return 'facebook'
    elif 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'reddit.com' in url_lower:
        return 'reddit'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    else:
        return 'unknown'


def is_post_url(url: str) -> bool:
    """Check if URL is a post URL (not a profile URL)."""
    url_lower = url.lower()

    # Twitter/X post patterns
    if re.search(r'(twitter\.com|x\.com)/[^/]+/status/\d+', url_lower):
        return True

    # Facebook post patterns
    if re.search(r'facebook\.com/[^/]+/posts/\d+', url_lower) or \
       re.search(r'facebook\.com/[^/]+/photos/', url_lower) or \
       re.search(r'facebook\.com/permalink\.php', url_lower):
        return True

    # Instagram post patterns
    if re.search(r'instagram\.com/p/[^/]+', url_lower) or \
       re.search(r'instagram\.com/reel/[^/]+', url_lower):
        return True

    # Reddit post patterns
    if re.search(r'reddit\.com/r/[^/]+/comments/', url_lower):
        return True

    # LinkedIn post patterns
    if re.search(r'linkedin\.com/feed/update/', url_lower) or \
       re.search(r'linkedin\.com/posts/', url_lower):
        return True

    return False


def get_scraper_for_platform(platform: str) -> Optional[BaseScraper]:
    """Get appropriate scraper for platform."""
    if platform == 'twitter':
        return TwitterScraper(use_playwright=True)
    elif platform == 'facebook':
        return FacebookScraper(use_playwright=True)
    elif platform == 'instagram':
        return InstagramScraper(use_playwright=True)
    elif platform == 'reddit':
        return RedditScraper(use_playwright=True)
    elif platform == 'linkedin':
        return LinkedInScraper(use_playwright=True)
    return None


def parse_timestamp(timestamp_value: Any) -> Optional[datetime]:
    """
    Parse timestamp from various formats (Twitter, Facebook, etc.) to datetime.

    Handles:
    - Twitter format: 'Mon Oct 13 20:49:54 +0000 2025'
    - ISO format: '2025-10-13T20:49:54Z'
    - Unix timestamp: 1728844194
    - Already datetime objects
    """
    if timestamp_value is None:
        return None

    if isinstance(timestamp_value, datetime):
        return timestamp_value

    if isinstance(timestamp_value, (int, float)):
        try:
            return datetime.fromtimestamp(timestamp_value)
        except (ValueError, OSError):
            return None

    if not isinstance(timestamp_value, str):
        return None

    timestamp_str = timestamp_value.strip()
    if not timestamp_str:
        return None

    # Try Twitter format: 'Mon Oct 13 20:49:54 +0000 2025'
    try:
        return datetime.strptime(timestamp_str, '%a %b %d %H:%M:%S %z %Y')
    except ValueError:
        pass

    # Try ISO format with timezone: '2025-10-13T20:49:54+00:00'
    try:
        return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
    except ValueError:
        pass

    # Try ISO format without timezone: '2025-10-13T20:49:54'
    try:
        return datetime.strptime(timestamp_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        pass

    # Try common date formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y %H:%M:%S',
        '%m/%d/%Y %H:%M:%S',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return None


def is_anti_national_content(text: str, toxicity_score: float, toxicity_labels: List[Dict[str, Any]]) -> bool:
    """
    Detect anti-national content.

    This checks for:
    - High toxicity scores with specific keywords
    - Anti-national keywords and phrases
    - Negative sentiment about the nation/state
    """
    if not text:
        return False

    text_lower = text.lower()

    # Anti-national keywords (expandable list)
    anti_national_keywords = [
        'anti-national', 'anti national', 'traitor', 'betray', 'treason',
        'destroy india', 'break india', 'divide india', 'separatist',
        'khalistan', 'azad kashmir', 'free kashmir', 'independent kashmir',
        'anti-india', 'anti india', 'hate india', 'india should',
        'government is', 'modi is', 'bjp is', 'congress is',
        'burn india', 'kill indians', 'hate hindus', 'hate muslims',
        'pakistan zindabad', 'pakistan is better',
    ]

    # Check for anti-national keywords
    keyword_matches = sum(1 for keyword in anti_national_keywords if keyword in text_lower)

    # High toxicity with negative sentiment about nation
    if toxicity_score > 0.7 and keyword_matches > 0:
        return True

    # Multiple anti-national keywords
    if keyword_matches >= 2:
        return True

    # Check toxicity labels for hate/identity_hate
    for label_data in toxicity_labels:
        label = label_data.get('label', '').lower()
        score = label_data.get('score', 0.0)
        if ('hate' in label or 'identity_hate' in label) and score > 0.6:
            if keyword_matches > 0:
                return True

    return False


async def create_post_analysis_job(payload: CreatePostAnalysisRequest) -> Post:
    """Create a new post analysis job."""
    platform = detect_platform_from_url(payload.postUrl)
    post_type = PostType.POST if is_post_url(payload.postUrl) else PostType.PROFILE

    post = Post(
        postUrl=payload.postUrl,
        postType=post_type,
        platform=platform,
        externalRefId=payload.externalRefId,
        metadata=payload.metadata,
    )
    await post.insert()
    return post


async def analyze_post(post_id: str) -> PostAnalysisResult:
    """Analyze a post and its comments."""
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise ValueError("Post not found")

    await post.mark_status(PostStatus.SCRAPING)

    try:
        # Get scraper for platform
        scraper = get_scraper_for_platform(post.platform)
        if not scraper:
            raise ValueError(f"No scraper available for platform: {post.platform}")

        # Create a dummy profile for scraping (we'll refactor this later)
        from app.models.profile import Profile, ProfileUrls
        dummy_profile = None
        try:
            dummy_profile = Profile(
                subjectName="Post Analysis",
                urls=ProfileUrls(),
            )
            await dummy_profile.insert()
            logger.info(f"Created dummy profile for post analysis {post_id}")

            # Scrape the post
            logger.info(f"Starting to scrape post {post_id} from {post.postUrl}")
            scraped_data = await scraper.scrape(dummy_profile, post.postUrl)
            logger.info(f"Scraping completed for post {post_id}, status: {scraped_data.scrapeStatus}")

            if scraped_data.scrapeStatus != ScrapeStatus.SUCCESS:
                error_msg = scraped_data.errorMessage or "Scraping failed with unknown error"
                logger.error(f"Scraping failed for post {post_id}: {error_msg}")
                raise Exception(f"Scraping failed: {error_msg}")

            await post.mark_status(PostStatus.PROCESSING)
            logger.info(f"Post {post_id} moved to PROCESSING status")

            # Extract post and comments from scraped data
            post_data, comments_data = extract_post_and_comments(scraped_data, post.platform)
            logger.info(f"Extracted {len(comments_data)} comments from post {post_id}")

            # Analyze comments
            toxicity_analyzer = ToxicityAnalyzer()
            analyzed_comments = []
            flagged_commenters = {}

            for comment in comments_data:
                comment_text = comment.get('text', '') or comment.get('message', '')
                if not comment_text:
                    continue

                # Analyze toxicity
                analysis = toxicity_analyzer.analyze_comment(comment_text)

                # Check for anti-national content
                is_anti_national = is_anti_national_content(
                    comment_text,
                    analysis['toxicity_score'],
                    analysis['toxicity_labels']
                )

                # Parse timestamp
                raw_timestamp = comment.get('created_at') or comment.get('created_time')
                parsed_timestamp = parse_timestamp(raw_timestamp)

                # #region agent log
                try:
                    import os
                    log_path = '/Users/navitas28/Work/grosint/profiler/.cursor/debug.log'
                    if os.path.exists(os.path.dirname(log_path)) or os.path.exists('/app'):
                        # Use container path if local path doesn't exist
                        actual_log_path = log_path if os.path.exists(os.path.dirname(log_path)) else '/tmp/debug.log'
                        with open(actual_log_path, 'a') as f:
                            import json
                            f.write(json.dumps({
                                "sessionId": "debug-session",
                                "runId": "run1",
                                "hypothesisId": "A",
                                "location": "post_analysis_service.py:221",
                                "message": "Comment timestamp parsing",
                                "data": {
                                    "raw_timestamp": str(raw_timestamp) if raw_timestamp else None,
                                    "parsed_timestamp": str(parsed_timestamp) if parsed_timestamp else None,
                                    "timestamp_type": type(raw_timestamp).__name__ if raw_timestamp else None
                                },
                                "timestamp": int(datetime.now().timestamp() * 1000)
                            }) + "\n")
                except Exception:
                    pass  # Ignore logging errors
                # #endregion

                comment_analysis = CommentAnalysis(
                    comment_id=comment.get('id', f"comment_{len(analyzed_comments)}"),
                    author_username=comment.get('author', {}).get('username') or comment.get('username'),
                    author_name=comment.get('author', {}).get('name') or comment.get('name'),
                    author_url=comment.get('author', {}).get('url') or comment.get('author_url'),
                    text=comment_text,
                    timestamp=parsed_timestamp,
                    toxicity_score=analysis['toxicity_score'],
                    is_toxic=analysis['is_toxic'],
                    is_anti_national=is_anti_national,
                    toxicity_labels=analysis['toxicity_labels'],
                    sentiment=analysis['sentiment'],
                    sentiment_score=analysis['sentiment_score'],
                )

                analyzed_comments.append(comment_analysis)

                # Track flagged commenters
                author_username = comment_analysis.author_username
                if author_username and (is_anti_national or analysis['is_toxic']):
                    if author_username not in flagged_commenters:
                        flagged_commenters[author_username] = {
                            'username': author_username,
                            'name': comment_analysis.author_name,
                            'url': comment_analysis.author_url,
                            'toxic_comments_count': 0,
                            'anti_national_comments_count': 0,
                            'worst_toxicity_score': 0.0,
                            'comments': [],
                        }

                    flagged_commenters[author_username]['toxic_comments_count'] += 1
                    if is_anti_national:
                        flagged_commenters[author_username]['anti_national_comments_count'] += 1

                    if analysis['toxicity_score'] > flagged_commenters[author_username]['worst_toxicity_score']:
                        flagged_commenters[author_username]['worst_toxicity_score'] = analysis['toxicity_score']

                    flagged_commenters[author_username]['comments'].append({
                        'text': comment_text[:200],
                        'toxicity_score': analysis['toxicity_score'],
                        'is_anti_national': is_anti_national,
                    })

            logger.info(f"Analyzed {len(analyzed_comments)} comments, found {len(flagged_commenters)} flagged commenters")

            # Parse post timestamp
            raw_post_timestamp = post_data.get('created_at') or post_data.get('created_time')
            parsed_post_timestamp = parse_timestamp(raw_post_timestamp)

            # #region agent log
            try:
                import os
                log_path = '/Users/navitas28/Work/grosint/profiler/.cursor/debug.log'
                if os.path.exists(os.path.dirname(log_path)) or os.path.exists('/app'):
                    # Use container path if local path doesn't exist
                    actual_log_path = log_path if os.path.exists(os.path.dirname(log_path)) else '/tmp/debug.log'
                    with open(actual_log_path, 'a') as f:
                        import json
                        f.write(json.dumps({
                            "sessionId": "debug-session",
                            "runId": "run1",
                            "hypothesisId": "A",
                            "location": "post_analysis_service.py:269",
                            "message": "Post timestamp parsing",
                            "data": {
                                "raw_timestamp": str(raw_post_timestamp) if raw_post_timestamp else None,
                                "parsed_timestamp": str(parsed_post_timestamp) if parsed_post_timestamp else None,
                                "timestamp_type": type(raw_post_timestamp).__name__ if raw_post_timestamp else None,
                                "post_id": str(post.id)
                            },
                            "timestamp": int(datetime.now().timestamp() * 1000)
                        }) + "\n")
            except Exception:
                pass  # Ignore logging errors
            # #endregion

            # Create analysis result
            analysis_result = PostAnalysisResult(
                post_id=str(post.id),
                post_url=post.postUrl,
                post_text=post_data.get('text', '') or post_data.get('message', '') or 'No post content extracted',
                author_username=post_data.get('author', {}).get('username') or post_data.get('username'),
                author_name=post_data.get('author', {}).get('name') or post_data.get('name'),
                author_url=post_data.get('author', {}).get('url') or post_data.get('author_url'),
                timestamp=parsed_post_timestamp,
                comments_count=len(comments_data),
                comments_analyzed=len(analyzed_comments),
                toxic_comments_count=sum(1 for c in analyzed_comments if c.is_toxic),
                anti_national_comments_count=sum(1 for c in analyzed_comments if c.is_anti_national),
                flagged_commenters=list(flagged_commenters.values()),
                comments=analyzed_comments,
            )

            # Update post with analysis
            post.analysis = analysis_result
            await post.mark_status(PostStatus.COMPLETED)
            logger.info(f"Post {post_id} analysis completed successfully")

            # Clean up dummy profile
            if dummy_profile:
                await dummy_profile.delete()
                logger.info(f"Cleaned up dummy profile for post {post_id}")

            return analysis_result

        except Exception as e:
            logger.exception(f"Error analyzing post {post_id}: {e}")
            try:
                await post.mark_status(PostStatus.FAILED, str(e))
            except Exception as status_error:
                logger.error(f"Failed to update post status: {status_error}")
            if dummy_profile:
                try:
                    await dummy_profile.delete()
                except Exception as delete_error:
                    logger.error(f"Failed to delete dummy profile: {delete_error}")
            raise

    except Exception as e:
        logger.exception(f"Error in post analysis {post_id}")
        await post.mark_status(PostStatus.FAILED, str(e))
        raise


def extract_post_and_comments(scraped_data: ScrapedData, platform: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Extract post data and comments from scraped data."""
    metadata = scraped_data.metadata or {}
    comments = []
    post_data = {}

    if platform == 'twitter':
        # Twitter structure
        tweets = metadata.get('tweets', [])
        if tweets:
            # First tweet is the main post
            post_data = tweets[0]
            # Get replies/comments
            for tweet in tweets:
                replies = tweet.get('replies_data', [])
                comments.extend(replies)

    elif platform == 'facebook':
        # Facebook structure
        posts = metadata.get('posts', [])
        if posts:
            post_data = posts[0]
            for post in posts:
                post_comments = post.get('comments_data', []) or post.get('comments', [])
                comments.extend(post_comments)

    elif platform == 'instagram':
        # Instagram structure
        posts = metadata.get('posts', [])
        if posts:
            post_data = posts[0]
            for post in posts:
                post_comments = post.get('comments', [])
                comments.extend(post_comments)

    elif platform == 'reddit':
        # Reddit structure
        posts = metadata.get('posts', [])
        if posts:
            post_data = posts[0]
        # Reddit comments are separate
        reddit_comments = metadata.get('comments', [])
        comments.extend(reddit_comments)

    elif platform == 'linkedin':
        # LinkedIn structure
        posts = metadata.get('posts', [])
        if posts:
            post_data = posts[0]
            for post in posts:
                post_comments = post.get('comments', [])
                comments.extend(post_comments)

    return post_data, comments


async def get_post_status(post_id: str) -> PostStatusResponse:
    """Get post analysis status."""
    post = await Post.get(PydanticObjectId(post_id))
    if not post:
        raise ValueError("Post not found")

    from app.schemas.post import PostAnalysisResultResponse, CommentAnalysisResponse

    analysis_response = None
    if post.analysis:
        analysis_response = PostAnalysisResultResponse(
            post_id=post.analysis.post_id,
            post_url=post.analysis.post_url,
            post_text=post.analysis.post_text,
            author_username=post.analysis.author_username,
            author_name=post.analysis.author_name,
            author_url=post.analysis.author_url,
            timestamp=post.analysis.timestamp,
            comments_count=post.analysis.comments_count,
            comments_analyzed=post.analysis.comments_analyzed,
            toxic_comments_count=post.analysis.toxic_comments_count,
            anti_national_comments_count=post.analysis.anti_national_comments_count,
            flagged_commenters=post.analysis.flagged_commenters,
            comments=[
                CommentAnalysisResponse(**comment.dict())
                for comment in post.analysis.comments
            ],
        )

    return PostStatusResponse(
        id=str(post.id),
        postUrl=post.postUrl,
        postType=post.postType,
        platform=post.platform,
        status=post.status,
        analysis=analysis_response,
        errorMessage=post.errorMessage,
        externalRefId=post.externalRefId,
        createdAt=post.createdAt,
        updatedAt=post.updatedAt,
    )


async def list_posts(
    skip: int = 0,
    limit: int = 100,
    status: Optional[PostStatus] = None,
) -> List[PostListItem]:
    """List all posts with optional filtering."""
    query = {}
    if status:
        query["status"] = status

    posts = await Post.find(query).skip(skip).limit(limit).sort(-Post.createdAt).to_list()

    result = []
    for post in posts:
        comments_count = 0
        flagged_count = 0
        if post.analysis:
            comments_count = post.analysis.comments_analyzed
            flagged_count = len(post.analysis.flagged_commenters)

        result.append(
            PostListItem(
                id=str(post.id),
                postUrl=post.postUrl,
                postType=post.postType,
                platform=post.platform,
                status=post.status,
                errorMessage=post.errorMessage,
                externalRefId=post.externalRefId,
                createdAt=post.createdAt,
                updatedAt=post.updatedAt,
                comments_count=comments_count,
                flagged_commenters_count=flagged_count,
            )
        )

    return result
