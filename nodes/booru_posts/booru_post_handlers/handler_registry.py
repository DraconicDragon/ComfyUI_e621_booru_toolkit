import importlib
import logging
import os
import pkgutil
from typing import Dict, List, Optional, Type

from ..booru_post_handlers.handler_base import BooruHandlerBase


class HandlerRegistry:
    """
    Registry for automatically discovering and managing booru handlers.
    """

    def __init__(self):
        self._handlers: Dict[str, Type[BooruHandlerBase]] = {}
        self._instances: Dict[str, BooruHandlerBase] = {}
        self._auto_discover()

    def _auto_discover(self):
        """Automatically discover all handler classes in the files in the booru_handlers folder.
        Checks for files ending with '_handler.py'."""
        current_dir = os.path.dirname(__file__)

        # Iterate through all Python files in the handlers directory
        for finder, name, ispkg in pkgutil.iter_modules([current_dir]):
            if name.endswith("_handler") and name != "handler_base":
                try:
                    module = importlib.import_module(f".{name}", package=__package__)

                    # Find all classes that inherit from BooruHandlerBase
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BooruHandlerBase) and attr != BooruHandlerBase:

                            handler_instance = attr()
                            handler_key = attr.HANDLER_NAME.lower().replace("/", "_").replace(" ", "_")

                            self._handlers[handler_key] = attr
                            self._instances[handler_key] = handler_instance
                            logging.info(f"Registered handler: {attr.HANDLER_NAME} ({handler_key})")

                except Exception as e:
                    logging.error(f"Failed to load handler from {name}: {e}")

    def get_handler_for_url(self, url: str) -> Optional[BooruHandlerBase]:
        """Get the appropriate handler for a given URL."""
        for handler in self._instances.values():
            if handler.can_handle(url):
                return handler
        return None

    def get_handler_by_name(self, name: str) -> Optional[BooruHandlerBase]:
        """Get a handler by its registered HANDLER_NAME."""
        return self._instances.get(name.lower().replace("/", "_").replace(" ", "_"))

    def get_all_handlers(self) -> Dict[str, BooruHandlerBase]:
        """Get all registered handlers."""
        return self._instances.copy()

    def get_supported_sites(self) -> List[str]:
        """Get list of all supported site names."""
        return [handler.HANDLER_NAME for handler in self._instances.values()]

    def get_handler_choices(self) -> List[str]:
        """Get list of choices for ComfyUI dropdown including 'auto'."""
        choices = ["auto"]
        choices.extend(sorted(self.get_supported_sites()))
        return choices


registry = HandlerRegistry()
