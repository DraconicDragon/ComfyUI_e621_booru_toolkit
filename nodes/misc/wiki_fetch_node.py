class TagWikiFetch:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "tags": (
                    "STRING",
                    {
                        "multiline": False,
                        "tooltip": "Enter the tags to search for, separated by commas."
                        + "Input tags are normalized meaning you don't need to pay attention to using underscores or backslashes or having to worry about too many spaces."
                        + "(Important: currently only supports a single tag. If multiple are supplied then one before first comma is chosen.)",
                    },
                ),
                "booru": (
                    ["danbooru", "e621, e6ai, e926"],
                    {"default": "danbooru", "tooltip": "Select the booru to search for the tag wiki page."},
                ),
                "extended_info": (
                    ["yes", "no", "only_extended"],
                    {
                        "default": "no",
                        "tooltip": "Include extended info of the wiki page response, mostly useless for now.",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "get_wiki_data"
    OUTPUT_NODE = True

    CATEGORY = "E621 Booru Toolkit/Tags"

    def get_wiki_data(self, tags, booru, extended_info):

        import asyncio

        from ..pyserver import get_tag_wiki_data

        response = asyncio.run(get_tag_wiki_data.fetch_wiki_data(tags, booru, extended_info))

        data = response.get("data", "")
        return {"ui": {"text": data}, "result": (data,)}
