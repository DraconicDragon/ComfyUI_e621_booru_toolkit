from ..nodes.get_post_node_base import BaseBooruNode


class AnyBooruPostAdvanced(BaseBooruNode):
    """
    A node for fetching posts from any supported booru service.
    Inherits BaseBooruNode and doesn't change anything from it.
    """

    DESCRIPTION = (
        "Fetches a post from any booru service so long as the api response type is supported, such as e621/e6ai or Danbooru/aibooru.\n"
        "It is recommended to use the specific nodes for the service you are using so far one exists.\n"
        "Use this node as a last resort only. There may not be any outputs for character/artist/copyright tags "
        "because it's possible the api response puts those tags as 'general' tags. Confirm the outputs if you use this node."
    )
    pass
