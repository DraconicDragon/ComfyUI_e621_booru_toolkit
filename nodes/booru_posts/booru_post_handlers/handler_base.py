import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

import requests


class BooruHandlerBase(ABC):
    """
    Abstract base class for all booru handlers. Subclasses must define parse() function.

    Provides common functionality and defines the interface for site-specific handlers.
    """

    # these are, and should be defined by child classes
    SUPPORTED_DOMAINS: List[str] = []
    HANDLER_NAME: str = ""

    @classmethod
    def can_handle(cls, url: str) -> bool:
        """Check if this handler can process the given URL."""
        host = urlparse(url).hostname or ""
        host = host.lower()
        return any(host == d or host.endswith("." + d) for d in cls.SUPPORTED_DOMAINS)

    @classmethod
    def get_api_url(cls, url: str) -> str:
        """Convert a post URL to its API URL (by appending '.json')"""
        # add .json if not present and remove any extra params, they probably aren't needed
        if ".json" not in url:
            url = url.split("?")[0] + ".json"
        return url

    def fetch(self, url: str, img_size: str, headers: Dict[str, str]) -> Dict:
        """
        Fetch data from the API.
        Handles common errors and provides fallbacks.
        """
        try:
            api_url = self.get_api_url(url)
            logging.info(f"Fetching from {self.HANDLER_NAME}: {api_url}")

            response = requests.get(api_url, headers=headers, timeout=10)
            response.raise_for_status()

            # Try JSON first
            try:
                return response.json()
            except ValueError:
                # todo: todo
                raise ValueError("Invalid JSON response: " + response.text)
                # If JSON fails, try XML
                return self._parse_xml_response(response.text)

        except requests.RequestException as e:
            logging.error(f"Failed to fetch from {self.HANDLER_NAME}: {e}")
            raise ValueError(f"Failed to fetch data from {self.HANDLER_NAME}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error fetching from {self.HANDLER_NAME}: {e}")
            raise ValueError(f"Unexpected error: {e}")

    def _parse_xml_response(self, xml_text: str) -> Dict:
        """Parse XML response (some boorus seem to use it) UNFINISHED.

        Override in child classes if needed.
        """
        import xml.etree.ElementTree as ET

        try:
            ET.fromstring(xml_text)
            # convert XML to dict-like structure
            # todo: implement XML parsing
            return {"error": "XML parsing not implemented for this handler"}
        except ET.ParseError:
            raise ValueError("Invalid XML response: " + xml_text)

    @abstractmethod
    def parse(self, response: Dict, img_size: str) -> Tuple[Dict[str, str], int, int, Optional[str]]:
        """
        Parse the API response and extract tag data, dimensions, and image URL.

        Returns:
            Tuple of (tags_dict, img_width, img_height, image_url)
        """
        pass

    def _normalize_tags(self, tags: Union[str, List[str]]) -> str:
        """Convert tags to comma-separated string format.

        Example: Danbooru tags come as space-separated string, e621 as list of strings.
        (most responses will likely come as danbooru-like)
        """
        if isinstance(tags, list):
            return ", ".join(tags)
        elif isinstance(tags, str):
            return tags.replace(" ", ", ") if tags else ""
        return ""
