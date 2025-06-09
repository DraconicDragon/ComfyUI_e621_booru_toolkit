import requests

from ..booru_handlers.handler_base import BooruHandlerBase


class E621Handler(BooruHandlerBase):
    def fetch(self, url, img_size, headers):
        if ".json" not in url:
            url = url.split("?")[0] + ".json"
        return requests.get(url, headers=headers).json()

    def parse(self, response, img_size):
        post = response.get("post", {})
        tags = post.get("tags", {})

        tags_dict = {
            "general_tags": ", ".join(tags.get("general", [])),
            "character_tags": ", ".join(tags.get("character", [])),
            "copyright_tags": ", ".join(tags.get("copyright", [])),
            "artist_tags": ", ".join(
                tags.get("artist", []) if tags.get("artist") else tags.get("director", [])
            ),  # director is e6ai's 'artist'
            "species_tags": ", ".join(tags.get("species", [])),
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
