from typing import Dict, Optional, Tuple

from ..booru_post_handlers.handler_base import BooruHandlerBase


class DanbooruHandler(BooruHandlerBase):
    """Handler for Danbooru APIs."""

    SUPPORTED_DOMAINS = ["danbooru.donmai.us", "safebooru.donmai.us", "donmai.moe"]
    HANDLER_NAME = "Danbooru"

    def parse(self, response: Dict, img_size: str) -> Tuple[Dict[str, str], int, int, Optional[str]]:
        """Parse Danbooru API response."""
        tags_dict = {
            "general_tags": self._normalize_tags(response.get("tag_string_general", "")),
            "character_tags": self._normalize_tags(response.get("tag_string_character", "")),
            "copyright_tags": self._normalize_tags(response.get("tag_string_copyright", "")),
            "artist_tags": self._normalize_tags(response.get("tag_string_artist", "")),
            "meta_tags": self._normalize_tags(response.get("tag_string_meta", "")),
        }

        img_width = response.get("image_width", 0)
        img_height = response.get("image_height", 0)
        image_url = None

        if img_size != "none - don't download image":
            variants = response.get("media_asset", {}).get("variants", [])
            selected = next((v for v in variants if v["type"] == img_size), None)
            image_url = selected["url"] if selected else response.get("file_url")

        return tags_dict, img_width, img_height, image_url
