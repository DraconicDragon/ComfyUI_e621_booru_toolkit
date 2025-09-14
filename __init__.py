from .nodes.get_aibooru_post_node import AIBooruPostNode
from .nodes.get_any_post_node import AnyBooruPostAdvanced
from .nodes.get_danbooru_post_node import DanbooruPostNode
from .nodes.get_e621_post_node import E621PostNode

# from .nodes.get_gelbooru_post_node import GelbooruPostNode
from .nodes.old_nodes import GetBooruPost
from .nodes.tagging.pixai_tagger_node import PixAITaggerNode
from .nodes.wiki_fetch_node import TagWikiFetch
from .pyserver import get_tag_wiki_data  # noqa: F401

NODE_CLASS_MAPPINGS = {
    "GetBooruPost": GetBooruPost,
    "GetAnyBooruPostAdv": AnyBooruPostAdvanced,
    "GetAIBooruPost": AIBooruPostNode,
    "GetDanbooruPost": DanbooruPostNode,
    "GetE621Post": E621PostNode,
    # "GetGelbooruPost": GelbooruPostNode,
    "TagWikiFetch": TagWikiFetch,
    # tagging
    "BTK_PixAITaggerNode": PixAITaggerNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetBooruPost": "[OLD] Fetch e621/Booru Post",
    "GetAnyBooruPostAdv": "Get Booru Post (Any Service)",
    "GetAIBooruPost": "Get AIBooru Post",
    "GetDanbooruPost": "Get Danbooru Post",
    "GetE621Post": "Get e621/e6ai Post",
    # "GetGelbooruPost": "Get Gelbooru Post",
    "TagWikiFetch": "[OLD] Tag Wiki Lookup",
    # tagging
    "BTK_PixAITaggerNode": "PixAI Tagger v0.9",
}

WEB_DIRECTORY = "./js"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
