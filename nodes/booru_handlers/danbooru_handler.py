import requests

from ..booru_handlers.handler_base import BooruHandlerBase


class DanbooruHandler(BooruHandlerBase):
    def fetch(self, url, img_size, headers):
        if ".json" not in url:
            url = url.split("?")[0] + ".json"
        return requests.get(url, headers=headers).json()

    def parse(self, response, img_size):
        tags_dict = {
            "general_tags": response.get("tag_string_general", "").replace(" ", ", "),
            "character_tags": response.get("tag_string_character", "").replace(" ", ", "),
            "copyright_tags": response.get("tag_string_copyright", "").replace(" ", ", "),
            "artist_tags": response.get("tag_string_artist", "").replace(" ", ", "),
            "model_tags": response.get("tag_string_model", "").replace(" ", ", "), # unused
            "species_tags": "",
        }

        img_width = response.get("image_width", 0)
        img_height = response.get("image_height", 0)
        image_url = None

        if img_size != "none - don't download image":
            variants = response.get("media_asset", {}).get("variants", [])
            selected = next((v for v in variants if v["type"] == img_size), None)
            image_url = selected["url"] if selected else response.get("file_url")

        return tags_dict, img_width, img_height, image_url
