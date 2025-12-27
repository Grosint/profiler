import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from bs4 import BeautifulSoup

from app.core.http_client import http_client
from app.models.scraped_data import ScrapePlatform, ScrapeStatus, ScrapedData
from app.models.profile import Profile

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base scraper interface. Implementations should override `platform` and
    may customize `extract_text` if necessary.
    """

    platform: ScrapePlatform = ScrapePlatform.UNKNOWN

    async def scrape(self, profile: Profile, url: str) -> ScrapedData:
        try:
            response = await http_client.get(url)
            response.raise_for_status()
            text, metadata = self.extract_text(response.text, response.headers)
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
                "Scrape succeeded",
                extra={"profile_id": str(profile.id), "platform": self.platform, "url": url},
            )
            return scraped
        except Exception as exc:  # pragma: no cover - defensive
            logger.exception(
                "Scrape failed",
                extra={"profile_id": str(getattr(profile, "id", "")), "platform": self.platform, "url": url},
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

    def extract_text(self, html: str, headers: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Generic HTML → text extractor. Platform-specific scrapers can override.
        """
        soup = BeautifulSoup(html, "html.parser")
        # Basic readable text heuristic; can be improved later.
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        text = " ".join(soup.stripped_strings)
        metadata: Dict[str, Any] = {
            "content_length": len(html),
            "text_length": len(text),
            "headers": dict(headers),
        }
        return text, metadata
