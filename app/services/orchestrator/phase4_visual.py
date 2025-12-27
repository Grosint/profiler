"""
Phase 4: Image & Video Context

YOLO/Detectron, CLIP, OCR analysis for images/videos.
"""

import logging
from typing import Any, Dict, List

from app.models.scraped_data import ScrapedData

logger = logging.getLogger(__name__)


class Phase4Visual:
    """Handles image and video context analysis."""

    async def execute(self, scraped_items: List[ScrapedData]) -> Dict[str, Any]:
        """YOLO/Detectron, CLIP, OCR analysis for images/videos."""
        # Check if any scraped data has image/video references
        has_visual_data = False
        image_urls = []
        video_urls = []

        for item in scraped_items:
            if item.metadata:
                if "images" in item.metadata:
                    image_urls.extend(item.metadata.get("images", []))
                    has_visual_data = True
                if "videos" in item.metadata:
                    video_urls.extend(item.metadata.get("videos", []))
                    has_visual_data = True
                if "media_urls" in item.metadata:
                    media = item.metadata.get("media_urls", [])
                    image_urls.extend(
                        [
                            m
                            for m in media
                            if isinstance(m, str)
                            and any(ext in m.lower() for ext in [".jpg", ".png", ".gif", ".jpeg"])
                        ]
                    )
                    video_urls.extend(
                        [
                            m
                            for m in media
                            if isinstance(m, str)
                            and any(ext in m.lower() for ext in [".mp4", ".mov", ".avi"])
                        ]
                    )
                    if media:
                        has_visual_data = True

        if not has_visual_data:
            return {
                "hasVisualData": False,
                "dominantContexts": [],
                "symbolsDetected": [],
            }

        # In production, this would:
        # 1. Download and process images with YOLO/Detectron
        # 2. Use CLIP to match image-text relevance
        # 3. Run OCR on images
        # For now, return placeholder structure

        return {
            "hasVisualData": True,
            "dominantContexts": [],  # Would contain scene tags from YOLO/CLIP
            "symbolsDetected": [],  # Would contain repeated symbols/motifs
            "imageCount": len(image_urls),
            "videoCount": len(video_urls),
        }
