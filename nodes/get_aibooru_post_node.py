from ..nodes.get_post_node_base import BaseBooruNode


class AIBooruPostNode(BaseBooruNode):
    """
    A node specifically for fetching posts from AIBooru.
    """

    N_HANDLER_NAME = "AIBooru"  # This should match the HANDLER_NAME so it can find the correct handler

    EXPERIMENTAL = False

    DESCRIPTION = (
        "Fetches a post from AIBooru (aibooru.online) or any service with same JSON response structure.\n"
        "This node is optimized specifically for AIBooru-style APIs and will provide the most reliable results "
        "for these services, including proper handling of tag categories and media variants."
    )

    RETURN_INFO = {
        "IMAGE": "IMAGE",
        "GENERAL_TAGS": "STRING",
        "CHARACTER_TAGS": "STRING",
        "COPYRIGHT_TAGS": "STRING",
        "ARTIST_TAGS": "STRING",
        "META_TAGS": "STRING",
        "MODEL_TAGS": "STRING",  # aibooru
        "ORIGINAL_WIDTH": "INT",
        "ORIGINAL_HEIGHT": "INT",
    }
    RETURN_TYPES = tuple(RETURN_INFO.values())
    RETURN_NAMES = tuple(RETURN_INFO.keys())
