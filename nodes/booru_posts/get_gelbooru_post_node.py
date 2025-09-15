from ..booru_posts.booru_post_handlers.gelbooru_handler import GelbooruHandler
from ..booru_posts.get_post_node_base import BaseBooruNode


class GelbooruPostNode(BaseBooruNode):

    HANDLER_CLASS = GelbooruHandler

    EXPERIMENTAL = True

    DESCRIPTION = (
        "Fetches a post from Gelbooru (gelbooru.com).\n"
        "This node is optimized specifically for Gelbooru's API. Note that Gelbooru doesn't categorize tags, "
        "so all tags will be returned in the ALL_TAGS output."
        "Gelbooru also only has preview and original file urls, sample and every other option is remapped to preview."
        "IMPORTANT: needs api key and user id added to query; it can be copied from account options page at the bottom."
    )

    # todo: check gelbooru handler for stuff on making this better
    RETURN_INFO = {
        "IMAGE": "IMAGE",
        "ALL_TAGS": "STRING",
        "ORIGINAL_WIDTH": "INT",
        "ORIGINAL_HEIGHT": "INT",
    }
    RETURN_TYPES = tuple(RETURN_INFO.values())
    RETURN_NAMES = tuple(RETURN_INFO.keys())
