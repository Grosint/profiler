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
    tasks: List[ScrapedData] = []

    insta = profile.urls.instagramUrl
    if insta:
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
    return tasks
