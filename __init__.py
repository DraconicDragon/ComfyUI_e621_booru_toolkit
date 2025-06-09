from .nodes.get_any_post_node import AnyBooruPostAdvanced
from .nodes.nodes import GetBooruPost
from .nodes.wiki_fetch_node import TagWikiFetch
from .pyserver import get_tag_wiki_data

NODE_CLASS_MAPPINGS = {
    "GetBooruPost": GetBooruPost,
    "GetAnyBooruPostAdv": AnyBooruPostAdvanced,
    "TagWikiFetch": TagWikiFetch,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruPost": "[OLD] Fetch e621/Booru Post",
    "GetAnyBooruPostAdv": "Get Booru Post Adv. (Any)",
    "TagWikiFetch": "[OLD] Tag Wiki Lookup",  # todo: i really need better names for these
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
