import io
import logging

import numpy as np
import requests
import torch  # type: ignore
from PIL import Image

from ..nodes.booru_handlers.danbooru_handler import DanbooruHandler
from ..nodes.booru_handlers.e621_handler import E621Handler
from ..nodes.utils import (
    adjust_tags,
    calculate_dimensions_for_diffusion,
    exclude_tags_from_string,
    to_tensor,
)

BOORU_HANDLERS = {
    "auto": [E621Handler(), DanbooruHandler()],  # Try in order
    "e621/e6ai": [E621Handler()],
    "danbooru/aibooru": [DanbooruHandler()],
}


class BaseBooruNode:
    # may be overridden by child classes
    ALLOW_SERVICE_SELECT = True
    ALLOW_SCALE = True
    ALLOW_FORMAT_TAGS = True
    ALLOW_APPEND_COMMA = True
    ALLOW_EXCLUDE_TAGS = True

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the booru post URL"}),
            }
        }
        if cls.ALLOW_SERVICE_SELECT:
            inputs["required"]["api_type"] = (
                ["auto", "e621/e6ai", "danbooru/aibooru"],
                {"default": "auto", "tooltip": "Select booru api type. 'auto' should generally be OK to use"},
            )
        if cls.ALLOW_SCALE:
            inputs["required"]["scale_target_avg"] = (
                "INT",
                {
                    "default": 1024,
                    "min": 64,
                    "max": 16384,
                    "step": 64,
                    "tooltip": (
                        "Calculates the image's width and height so it's average is close to the "
                        "scale_target_avg value while keeping the aspect ratio as close to original "
                        "as possible and making the output dimensions multiples of 64"
                    ),
                },
            )
        inputs["required"]["img_size"] = (
            [
                "none - don't download image",
                "180x180",
                "360x360",
                "720x720",
                "sample",
                "original",
            ],
            {
                "default": "sample",
                "tooltip": (
                    "Select the image size variant to output through 'IMAGE'.\n"
                    "Choose 'none' to output a blank image. For e6, anything below sample will be 'preview'"
                ),
            },
        )
        if cls.ALLOW_FORMAT_TAGS:
            inputs["required"]["format_tags"] = (
                "BOOLEAN",
                {
                    "default": True,
                    "tooltip": "Format tags for prompt use. Removes underscores and adds backslashes to brackets",
                },  # "" if cls.ALLOW_FORMAT_TAGS else "Disabled"
            )
        if cls.ALLOW_APPEND_COMMA:
            inputs["required"]["append_comma"] = (
                "BOOLEAN",
                {
                    "default": False,
                    "tooltip": "Appends a comma to the last tag in each output",
                },  # todo: with or without extra space? not that it matters for CLIP but you never know
            )
        if cls.ALLOW_EXCLUDE_TAGS:
            inputs["required"]["exclude_tags"] = (
                "BOOLEAN",
                {"default": True, "tooltip": "Toggle exclusion of tags from output"},
            )
            inputs["required"]["user_excluded_tags"] = (
                "STRING",
                {
                    "default": "conditional dnp, sound_warning, unknown_artist, third-party_edit, anonymous_artist, e621, e621 post recursion, e621_comment, patreon, patreon logo, patreon username, instagram username, text, dialogue",
                    "multiline": True,
                    "tooltip": "Comma separated list of tags to exclude for output (they can include underscores or spaces, with or without backslashes)",
                },
            )
        return inputs

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "SPECIES_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
        "ORIGINAL_WIDTH",
        "ORIGINAL_HEIGHT",
    )
    CATEGORY = "E621 Booru Toolkit/Posts"
    FUNCTION = "get_data"

    # DEPRECATED = True
    # BETA would be CATEGORY = "_for_testing"  or
    # EXPERIMENTAL = True

    DESCRIPTION = "aaa"

    def get_data(
        self,
        url,
        img_size,
        scale_target_avg=1024,
        format_tags=True,
        append_comma=False,
        exclude_tags=True,
        user_excluded_tags="",
        api_type="auto",
    ):
        headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on GitHub)"}
        blank_img_tensor = torch.from_numpy(np.zeros((64, 64, 3), dtype=np.float32) / 255.0).unsqueeze(0)

        # Select handler(s)
        handlers = BOORU_HANDLERS.get(api_type, BOORU_HANDLERS["auto"])
        tags_dict = {}
        img_width = img_height = 0
        image_url = None

        # Try handlers in order (for auto)
        last_error = None
        for handler in handlers:
            try:
                response = handler.fetch(url, img_size, headers)

                # todo: maybe move validation to handlers
                # Validate response format before parsing
                if isinstance(handler, E621Handler):
                    # E621/E6AI: expect dict with top-level "Post" key, and tags as lists
                    if not (isinstance(response, dict) and "post" in response):
                        raise ValueError("Response does not match E621/E6AI format (no top-level 'Post' key).")
                    tags = response["post"].get("tags", {})
                    if not isinstance(tags, dict) or not all(isinstance(v, list) for v in tags.values()):
                        raise ValueError("E621/E6AI tags are not lists as expected.")

                elif isinstance(handler, DanbooruHandler):
                    # Danbooru/Aibooru: expect dict with tag_string_* keys as strings
                    if not (isinstance(response, dict) and "tag_string_general" in response):
                        raise ValueError("Response does not match Danbooru/Aibooru format (no 'tag_string_general').")

                    if not all(
                        isinstance(response.get(k, ""), str)
                        for k in [
                            "tag_string_general",
                            "tag_string_character",
                            "tag_string_copyright",
                            "tag_string_artist",
                        ]
                    ):
                        raise ValueError("Danbooru/Aibooru tag strings in API response are not strings as expected.")

                else:
                    raise ValueError(f"Unknown handler type: {handler.__class__.__name__}")

                tags_dict, img_width, img_height, image_url = handler.parse(response, img_size)
                print(f"Using handler: {handler.__class__.__name__} for API type: {api_type}")
                print(f"Fetching data from URL: {url} with image size: {img_size}")

                if tags_dict and (img_width or img_height):
                    break
            except Exception as e:
                last_error = e
                continue

        if (not image_url or img_width == 0 or img_height == 0) and not img_size == "none - don't download image":
            raise ValueError(
                f"No valid image found for the given URL with the selected API type ({api_type}). "
                f"Check if the URL matches the API type, or try 'auto' mode.\n"
                # f"API Response: \n{response if 'response' in locals() else 'No response available'}\n"
                f"Last error: {last_error}"
            )

        # Image download
        if img_size == "none - don't download image" or not image_url:
            img_tensor = blank_img_tensor
        else:
            try:
                img_data = requests.get(image_url, timeout=10)
                img_data.raise_for_status()
                img_stream = io.BytesIO(img_data.content)
                image_ = Image.open(img_stream)
                img_tensor = to_tensor(image_)
            except requests.RequestException as req_exc:
                logging.error(f"Image download failed: {req_exc}")
                img_tensor = blank_img_tensor
            except (OSError, ValueError) as img_exc:
                logging.error(f"Image processing failed: {img_exc}")
                img_tensor = blank_img_tensor
            except Exception as exc:
                logging.error(f"Unexpected error: {exc}")
                img_tensor = blank_img_tensor

        # Scale
        # print(f"Original image dimensions: {img_width}x{img_height}")
        scaled_img_width, scaled_img_height = (
            calculate_dimensions_for_diffusion(img_width, img_height, scale_target_avg)
            if self.ALLOW_SCALE
            else (img_width, img_height)
        )

        # Exclude tags
        if self.ALLOW_EXCLUDE_TAGS and exclude_tags:
            exclude_list = [
                tag.replace(" ", "_").replace("\\(", "(").replace("\\)", ")")
                for tag in user_excluded_tags.replace(", ", ",").split(",")
            ]
            for key in tags_dict:
                tags_dict[key] = exclude_tags_from_string(tags_dict[key], exclude_list)

        # Format tags
        if self.ALLOW_FORMAT_TAGS and format_tags:
            for key in tags_dict:
                tags_dict[key] = adjust_tags(tags_dict[key])

        # Append comma
        if self.ALLOW_APPEND_COMMA and append_comma:
            for key in tags_dict:
                if tags_dict[key]:
                    tags_dict[key] += ","

        return (
            img_tensor,
            tags_dict.get("general_tags", ""),
            tags_dict.get("character_tags", ""),
            tags_dict.get("copyright_tags", ""),
            tags_dict.get("artist_tags", ""),
            tags_dict.get("species_tags", ""),
            scaled_img_width,
            scaled_img_height,
            img_width,
            img_height,
        )
