import io
import logging
from typing import Dict, Optional, Tuple

import numpy as np
import requests
import torch
from PIL import Image

from ..nodes.booru_handlers.handler_registry import registry
from ..nodes.utils import (
    adjust_tags,
    exclude_tags_from_string,
    to_tensor,
)


class BaseBooruNode:
    """
    Base class for all booru nodes.
    Provides common functionality for fetching and processing booru posts.
    """

    # todo: make format_tags input a string to select which tag category to format/not format?
    # may be overridden by child classes to customize behavior
    ALLOW_FORMAT_TAGS = True
    ALLOW_TRAILING_COMMA = True
    ALLOW_EXCLUDE_TAGS = True
    N_HANDLER_NAME = None  # Set this in subclasses, must match HANDLER_NAME of a handler
    # todo: this could probably be better, since both this and HANDLER_NAME have to be the same for N_HANDLER_NAME to find HANDLER_NAME of a handler
    # though then again idk right now how to make better so i just call this one N_HANDLER_NAME (N = Node) which is used to get a matching handler

    CATEGORY = "Booru Toolkit/Posts"
    FUNCTION = "get_data"

    # Set to False in child classes when they are stable
    EXPERIMENTAL = True

    DESCRIPTION = "Base booru node for fetching posts from various booru services."

    RETURN_INFO = {  # this way is just clearer for me
        "IMAGE": "IMAGE",
        "GENERAL_TAGS": "STRING",
        "CHARACTER_TAGS": "STRING",
        "CONTRIBUTOR_TAGS": "STRING",
        "COPYRIGHT_TAGS": "STRING",
        "ARTIST_TAGS": "STRING",
        "SPECIES_TAGS": "STRING",
        "META_TAGS": "STRING",
        "MODEL_TAGS": "STRING",
        "ORIGINAL_WIDTH": "INT",
        "ORIGINAL_HEIGHT": "INT",
    }
    RETURN_TYPES = tuple(RETURN_INFO.values())
    RETURN_NAMES = tuple(RETURN_INFO.keys())

    @classmethod
    def INPUT_TYPES(cls):
        inputs = {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the booru post URL"}),
            }
        }

        if not cls.N_HANDLER_NAME:
            inputs["required"]["api_type"] = (
                registry.get_handler_choices(),
                {"default": "auto", "tooltip": "Select booru api type. 'auto' should generally be OK to use"},
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
                },
            )

        if cls.ALLOW_TRAILING_COMMA:
            inputs["required"]["trailing_comma"] = (
                "BOOLEAN",
                {
                    "default": False,
                    "tooltip": "Appends a comma to the last tag in each output",
                },
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

    def get_data(
        self,
        url: str,
        img_size: str,
        format_tags: bool = True,
        trailing_comma: bool = False,
        exclude_tags: bool = True,
        user_excluded_tags: str = "",
        api_type: str = "auto",
    ) -> Tuple:
        """Main function to fetch and process booru data."""
        headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on GitHub)"}
        blank_img_tensor = torch.from_numpy(np.zeros((64, 64, 3), dtype=np.float32) / 255.0).unsqueeze(0)

        # Raise error if URL is empty after trimming
        if not url.strip():
            raise ValueError("URL cannot be empty.")

        # Determine which handler to use
        # todo: this fails when theres a domain that isnt added
        # todo: might not be desirable when theres a domain with supported api format, yet errors because domain isnt hardcoded in handler
        # todo: allow adding custom domains? in some config file?
        # todo: or have a "brute force" mode that goes through every handler. Or can add both ig
        # NOTE: the todos above only apply to the any node, image board specific nodes will try to fetch and parse regardless of domain
        handler = self._get_handler(url, api_type)
        if not handler:
            raise ValueError(f"No suitable handler found for URL: {url}")
        try:
            # Fetch and parse data
            response = handler.fetch(url, img_size, headers)
            tags_dict, img_width, img_height, image_url = handler.parse(response, img_size)

            logging.info(f"Successfully fetched data using {handler.HANDLER_NAME} handler")

        except Exception as e:
            logging.error(f"Failed to fetch data: {e}")
            raise ValueError(f"Failed to fetch data: {e}")

        # Download image
        img_tensor = self._download_image(image_url, img_size, blank_img_tensor)

        # Process tags
        tags_dict = self._process_tags(tags_dict, exclude_tags, user_excluded_tags, format_tags, trailing_comma)

        # Build return tuple dynamically based on the class's RETURN_NAMES
        return self._build_return_tuple(img_tensor, tags_dict, img_width, img_height)

    def _get_handler(self, url: str, api_type: str):
        """Get the appropriate handler for the URL and API type."""
        # If this node forces a specific API type, use that
        if self.N_HANDLER_NAME:
            return registry.get_handler_by_name(self.N_HANDLER_NAME)

        # If auto mode, try to detect from URL
        if api_type == "auto":
            return registry.get_handler_for_url(url)

        # Otherwise, use the specified handler
        return registry.get_handler_by_name(api_type)

    def _download_image(self, image_url: Optional[str], img_size: str, blank_img_tensor: torch.Tensor) -> torch.Tensor:
        """Download and process the image."""
        if img_size == "none - don't download image" or not image_url:
            return blank_img_tensor

        try:
            img_data = requests.get(image_url, timeout=10)
            img_data.raise_for_status()
            img_stream = io.BytesIO(img_data.content)
            image_ = Image.open(img_stream)
            return to_tensor(image_)
        except requests.RequestException as req_exc:
            logging.error(f"Image download failed: {req_exc}")
            return blank_img_tensor
        except (OSError, ValueError) as img_exc:
            logging.error(f"Image processing failed: {img_exc}")
            return blank_img_tensor
        except Exception as exc:
            logging.error(f"Unexpected error during image download: {exc}")
            return blank_img_tensor

    def _process_tags(
        self,
        tags_dict: Dict[str, str],
        exclude_tags: bool,
        user_excluded_tags: str,
        format_tags: bool,
        trailing_comma: bool,
    ) -> Dict[str, str]:
        """Process tags according to user preferences."""
        # Exclude tags
        if self.ALLOW_EXCLUDE_TAGS and exclude_tags:
            exclude_list = [
                tag.strip().replace(" ", "_").replace("\\(", "(").replace("\\)", ")")
                for tag in user_excluded_tags.replace(", ", ",").split(",")
            ]
            for key in tags_dict:
                tags_dict[key] = exclude_tags_from_string(tags_dict[key], exclude_list)

        # Format tags
        if self.ALLOW_FORMAT_TAGS and format_tags:
            for key in tags_dict:
                if tags_dict[key]:
                    tags_dict[key] = adjust_tags(tags_dict[key])

        # Append comma
        if self.ALLOW_TRAILING_COMMA and trailing_comma:
            for key in tags_dict:
                if tags_dict[key]:
                    tags_dict[key] += ","

        return tags_dict

    def _build_return_tuple(
        self, img_tensor: torch.Tensor, tags_dict: Dict[str, str], img_width: int, img_height: int
    ) -> Tuple:
        """
        Build return tuple dynamically based on the class's RETURN_NAMES.

        This allows child classes to define their own return/output structure.
        """
        # non-tag category values
        special_values = {
            "IMAGE": img_tensor,
            "ORIGINAL_WIDTH": img_width,
            "ORIGINAL_HEIGHT": img_height,
        }

        # Build return tuple based on this class's RETURN_NAMES
        return_values = []
        for return_name in self.RETURN_NAMES:
            if return_name in special_values:
                return_values.append(special_values[return_name])
            elif return_name.endswith("_TAGS"):
                # Convert RETURN_NAME to tags_dict key (e.g., "GENERAL_TAGS" -> "general_tags")
                tags_key = return_name.lower()
                return_values.append(tags_dict.get(tags_key, ""))
            else:
                # Fallback for unknown return types
                logging.warning(f"Unknown return type '{return_name}' in {self.__class__.__name__}")
                return_values.append("")

        return tuple(return_values)
