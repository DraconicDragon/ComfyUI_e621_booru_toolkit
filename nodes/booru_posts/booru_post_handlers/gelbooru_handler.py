from typing import Dict, Optional, Tuple

from .handler_base import BooruHandlerBase


class GelbooruHandler(BooruHandlerBase):
    """Handler for Gelbooru API."""

    # safebooru.org is a gelbooru fork, unrelated to safebooru.donmai.us
    SUPPORTED_DOMAINS = ["gelbooru.com", "safebooru.org"]
    HANDLER_NAME = "Gelbooru"

    @classmethod
    def get_api_url(cls, url: str) -> str:
        """Convert Gelbooru post URL to API URL."""
        # Example: https://gelbooru.com/index.php?page=post&s=view&id=12345
        # to: https://gelbooru.com/index.php?page=dapi&s=post&q=index&id=12345&json=1
        if "gelbooru.com" in url and "id=" in url:
            post_id = url.split("id=")[1].split("&")[0]
            api_key = url.lower().split("api_key=")[1].split("&")[0] if "api_key=" in url.lower() else None
            user_id = url.lower().split("user_id=")[1].split("&")[0] if "user_id=" in url.lower() else None
            if api_key and user_id:
                return f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&id={post_id}&json=1&api_key={api_key}&user_id={user_id}"
            return f"https://gelbooru.com/index.php?page=dapi&s=post&q=index&id={post_id}&json=1"
            # todo: thanks to UK spamming gelbooru with 10k requests per sec it now requires user id and api key added to query
        return url

    def parse(self, response: Dict, img_size: str) -> Tuple[Dict[str, str], int, int, Optional[str]]:
        """Parse Gelbooru API response."""

        post = response.get("post", [{}])[0] if isinstance(response.get("post"), list) else response.get("post", {})

        # Gelbooru does not put tags into separate categories in api response
        # todo: either filter out tags with tags list or try to scrape site
        all_tags = post.get("tags", "")
        tags_dict = {
            "all_tags": self._normalize_tags(all_tags),
        }

        img_width = int(post.get("width", 0))
        img_height = int(post.get("height", 0))
        image_url = None

        if img_size != "none - don't download image":
            if img_size == "original":
                image_url = post.get("file_url")
            elif img_size == "sample":
                image_url = post.get("sample_url") or post.get("file_url")
            else:  # preview or other sizes
                image_url = post.get("preview_url") or post.get("file_url")

        return tags_dict, img_width, img_height, image_url
