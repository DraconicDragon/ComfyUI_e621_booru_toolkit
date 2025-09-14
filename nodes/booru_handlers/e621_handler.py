from typing import Dict, Optional, Tuple

from ..booru_handlers.handler_base import BooruHandlerBase


class E621Handler(BooruHandlerBase):
    """Handler for e621 and e6ai APIs."""

    # NOTE: for now e6ai seems to have same json keys besides artis > director
    SUPPORTED_DOMAINS = ["e621.net", "e926.net", "e6ai.net"]
    HANDLER_NAME = "e621/e6ai"

    def parse(self, response: Dict, img_size: str) -> Tuple[Dict[str, str], int, int, Optional[str]]:
        """Parse e621/e6ai API response."""
        post = response.get("post", {})
        tags = post.get("tags", {})

        # NOTE: e621 has contributor key in tags since 18th dec., not useful for image gen but added anyway
        tags_dict = {
            "general_tags": self._normalize_tags(tags.get("general", [])),
            "character_tags": self._normalize_tags(tags.get("character", [])),
            "contributor_tags": self._normalize_tags(tags.get("contributor", [])),
            "copyright_tags": self._normalize_tags(tags.get("copyright", [])),
            "artist_tags": self._normalize_tags(
                tags.get("artist", []) if tags.get("artist") else tags.get("director", [])
            ),  # director is e6ai's 'artist' tag
            "species_tags": self._normalize_tags(tags.get("species", [])),
            "meta_tags": self._normalize_tags(tags.get("meta", [])),
        }

        img_width = post.get("file", {}).get("width", 0)
        img_height = post.get("file", {}).get("height", 0)
        image_url = None

        if img_size != "none - don't download image":
            if img_size not in ["original", "sample"]:
                img_size = "preview"
            if img_size == "original":
                img_size = "file"
            image_url = post.get(img_size, {}).get("url") or post.get("file", {}).get("url")

        return tags_dict, img_width, img_height, image_url
