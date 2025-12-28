import logging
from typing import List

from app.models.profile import Profile
from app.models.scraped_data import ScrapedData
from app.services.scrapers.blog_scraper import BlogScraper
from app.services.scrapers.facebook_scraper import FacebookScraper
from app.services.scrapers.instagram_scraper import InstagramScraper
from app.services.scrapers.twitter_scraper import TwitterScraper
from app.services.scrapers.linkedin_scraper import LinkedInScraper
from app.services.scrapers.reddit_scraper import RedditScraper

logger = logging.getLogger(__name__)


async def scrape_profile(profile: Profile) -> List[ScrapedData]:
    """
    Scrape all URLs associated with a profile using platform-specific scrapers.
    """
    # #region agent log
    import json
    import os
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "scraping-service", "hypothesisId": "F", "location": "scraping_service.py:scrape_profile", "message": "Starting scrape_profile", "data": {"profile_id": str(profile.id), "urls": {"instagram": bool(profile.urls.instagramUrl), "facebook": bool(profile.urls.facebookUrl), "twitter": bool(profile.urls.twitterUrl), "linkedin": bool(profile.urls.linkedinUrl), "reddit": bool(profile.urls.redditUrl), "blogs": len(profile.urls.blogUrls or [])}}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    tasks: List[ScrapedData] = []

    insta = profile.urls.instagramUrl
    if insta:
        # #region agent log
        try:
            with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
                f.write(json.dumps({"sessionId": "debug-session", "runId": "scraping-service", "hypothesisId": "F", "location": "scraping_service.py:scrape_profile", "message": "Scraping Instagram URL", "data": {"profile_id": str(profile.id), "url": insta}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
        except:
            pass
        # #endregion
        scraper = InstagramScraper()
        tasks.append(await scraper.scrape(profile, insta))

    fb = profile.urls.facebookUrl
    if fb:
        scraper = FacebookScraper()
        tasks.append(await scraper.scrape(profile, fb))

    tw = profile.urls.twitterUrl
    if tw:
        scraper = TwitterScraper()
        tasks.append(await scraper.scrape(profile, tw))

    linkedin = profile.urls.linkedinUrl
    if linkedin:
        scraper = LinkedInScraper()
        tasks.append(await scraper.scrape(profile, linkedin))

    reddit = profile.urls.redditUrl
    if reddit:
        scraper = RedditScraper()
        tasks.append(await scraper.scrape(profile, reddit))

    blogs = profile.urls.blogUrls or []
    if blogs:
        scraper = BlogScraper()
        for url in blogs:
            tasks.append(await scraper.scrape(profile, url))

    logger.info(
        "Scraping phase finished",
        extra={"profile_id": str(profile.id), "scraped_count": len(tasks)},
    )
    # #region agent log
    try:
        with open("/Users/navitas28/Work/grosint/profiler/.cursor/debug.log", "a") as f:
            f.write(json.dumps({"sessionId": "debug-session", "runId": "scraping-service", "hypothesisId": "F", "location": "scraping_service.py:scrape_profile", "message": "Scraping phase finished", "data": {"profile_id": str(profile.id), "scraped_count": len(tasks), "scraped_ids": [str(item.id) for item in tasks]}, "timestamp": int(__import__("time").time() * 1000)}) + "\n")
    except:
        pass
    # #endregion
    return tasks
