from ..nodes.get_post_node_base import BaseBooruNode


class AnyBooruPostAdvanced(BaseBooruNode):
    """
    A node for fetching posts from any supported booru service.
    Inherits BaseBooruNode and provides access to all supported services.
    """

    DESCRIPTION = (
        "Fetches a post from any supported booru service with automatic detection or manual selection.\n"
        "Supports e621/e6ai, Danbooru/Aibooru, and maybe more.\n"
        "It is recommended to use the specific nodes for the service you are using for the best experience.\n"
        "Use this node when you need flexibility to work with multiple different booru services, or just find it more convenient."
    )

    EXPERIMENTAL = False
