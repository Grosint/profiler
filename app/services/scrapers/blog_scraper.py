from app.models.scraped_data import ScrapePlatform
from .base_scraper import BaseScraper


class BlogScraper(BaseScraper):
    platform: ScrapePlatform = ScrapePlatform.BLOG
