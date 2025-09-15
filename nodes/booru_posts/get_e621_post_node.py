from ..booru_posts.booru_post_handlers.e621_handler import E621Handler
from ..booru_posts.get_post_node_base import BaseBooruNode


class E621PostNode(BaseBooruNode):
    """
    A node specifically for fetching posts from e621.net and e6ai.net.
    """

    HANDLER_CLASS = E621Handler

    EXPERIMENTAL = False

    DESCRIPTION = (
        "Fetches a post from e621.net or e6ai.net.\n"
        "This node is optimized specifically for e621 and e6ai APIs and will provide the most reliable results "
        "for these services, including proper handling of species tags and other e621-specific features."
    )

    RETURN_INFO = {
        "IMAGE": "IMAGE",
        "GENERAL_TAGS": "STRING",
        "CHARACTER_TAGS": "STRING",
        "CONTRIBUTOR_TAGS": "STRING",
        "COPYRIGHT_TAGS": "STRING",
        "ARTIST_TAGS": "STRING",
        "SPECIES_TAGS": "STRING",
        "META_TAGS": "STRING",
        "ORIGINAL_WIDTH": "INT",
        "ORIGINAL_HEIGHT": "INT",
    }
    RETURN_TYPES = tuple(RETURN_INFO.values())
    RETURN_NAMES = tuple(RETURN_INFO.keys())
