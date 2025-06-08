import io

import numpy as np
import requests
from utils import calculate_dimensions_for_diffusion, to_tensor
import torch
from PIL import Image

headers = {"User-Agent": "ComfyUI_e621_booru_toolkit/1.0 (by draconicdragon on GitHub)"}

# create a blank image tensor to use as a placeholder
blank_img_tensor = torch.from_numpy(np.zeros((512, 512, 3), dtype=np.float32) / 255.0).unsqueeze(0)


def get_e621_post_data(response, img_size):
    post = response.get("post", {})
    # NOTE: e621 has contributor key in tags since 18th dec., not useful for image gen
    # Get tags, e6 tags are in a list instead of space separated string like dbr
    tags = post.get("tags", {})
    tags_dict = {
        "general_tags": ", ".join(tags.get("general", [])),
        "character_tags": ", ".join(tags.get("character", [])),
        "copyright_tags": ", ".join(tags.get("copyright", [])),
        "artist_tags": ", ".join(tags.get("artist", [])),
        "species_tags": ", ".join(tags.get("species", [])),
    }

    # Get image size of original image | "file" key in json response
    img_width = post.get("file", {}).get("width", 0)
    img_height = post.get("file", {}).get("height", 0)

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor

    else:
        if img_size not in ["original", "sample"]:
            img_size = "preview"
        if img_size == "original":
            img_size = "file"

        image_url = post.get(img_size, {}).get("url")

        if not image_url:  # fallback
            image_url = post.get("file", {}).get("url")

        img_data = requests.get(image_url).content
        img_stream = io.BytesIO(img_data)
        image_ = Image.open(img_stream)
        img_tensor = to_tensor(image_)

    return (
        img_tensor,
        tags_dict,
        img_width,
        img_height,
    )


def get_danbooru_post_data(response, img_size):

    # Get tags
    tags_dict = {
        "general_tags": response.get("tag_string_general", "").replace(" ", ", "),
        "character_tags": response.get("tag_string_character", "").replace(" ", ", "),
        "copyright_tags": response.get("tag_string_copyright", "").replace(" ", ", "),
        "artist_tags": response.get("tag_string_artist", "").replace(" ", ", "),
        "species_tags": "",  # danbooru doesn't have this
    }

    # Get image size and dimensions of original image
    original_img_width = response.get("image_width", 0)
    original_img_height = response.get("image_height", 0)

    if img_size == "none - don't download image":
        img_tensor = blank_img_tensor

    else:
        # Get image size variant for selected variant and output desired image size
        variants = response.get("media_asset", {}).get("variants", [])
        selected_variant = next((variant for variant in variants if variant["type"] == img_size), None)

        if selected_variant:
            image_url = selected_variant["url"]
        else:  # fallback to original image
            image_url = response.get("file_url")

        img_data = requests.get(image_url).content
        img_stream = io.BytesIO(img_data)
        image_ = Image.open(img_stream)
        img_tensor = to_tensor(image_)

    return (
        img_tensor,
        tags_dict,
        original_img_width,
        original_img_height,
    )


class GetBooruPost:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "url": ("STRING", {"multiline": False, "tooltip": "Enter the URL of the Danbooru/e621 post"}),
                "scale_target_avg": (
                    "INT",
                    {
                        "default": 1024,
                        "min": 64,
                        "max": 16384,
                        "step": 64,  # add multiples_of option and then allow different step sizes although usually not needed
                        "tooltip": "[BETA] Calculates the image's width and height so it's average is close to the scale_target_avg value while keeping the aspect ratio as close to original as possible. Use 1024 for SDXL",
                    },
                ),
                "img_size": (
                    [
                        "none - don't download image",
                        "180x180",
                        "360x360",
                        "720x720",
                        "sample",
                        "original",
                    ],
                    {
                        "default": "sample",
                        "tooltip": "Select the image size variant to output through 'IMAGE'. Choose 'none' to output a blank image. For e6, anything below sample will be 'preview'",
                    },
                ),
                "format_tags": (
                    "BOOLEAN",
                    {"default": True, "tooltip": "Removes underscores and adds backslashes to brackets if set to True"},
                ),
                "exclude_tags": (
                    "BOOLEAN",
                    {
                        "default": True,
                        "tooltip": "Removes tags before output based on textbox content below",
                    },
                ),
                "user_excluded_tags": (
                    "STRING",
                    {  # todo: load defaults from file maybe
                        "default": "conditional dnp, sound_warning, unknown_artist, third-party_edit, anonymous_artist, e621, e621 post recursion, e621_comment, patreon, patreon logo, patreon username, instagram username, text, dialogue",
                        "multiline": True,
                        "tooltip": "Enter tags you don't want outputted. Input should be comma separated like prompts (they can include underscore or spaces, with or without backslashes)",
                    },
                ),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING", "STRING", "STRING", "STRING", "STRING", "INT", "INT", "INT", "INT")
    RETURN_NAMES = (
        "IMAGE",
        "GENERAL_TAGS",
        "CHARACTER_TAGS",
        "COPYRIGHT_TAGS",
        "ARTIST_TAGS",
        "E6_SPECIES_TAGS",
        "SCALED_WIDTH",
        "SCALED_HEIGHT",
        "ORIGINAL_WIDTH",
        "ORIGINAL_HEIGHT",
    )
    FUNCTION = "get_data"
    CATEGORY = "E621 Booru Toolkit"

    def get_data(self, url, scale_target_avg, img_size, format_tags, exclude_tags, user_excluded_tags):
        # Check if URL already ends with .json
        # todo: doesnt work for gelbooru, safebooru, similar
        # NOTE: these sites are cringe, the tags are in a singular string. Char/artist/general tags, all merged. WHY?
        # gelbooru api url https://gelbooru.com/index.php?page=dapi&s=post&q=index&id=1&json=1
        if ".json" not in url:
            # Split URL into base and query parts if it contains a query
            if "?" in url:
                base_url, sep, query = url.partition("?")  # sep = "?"
            else:
                base_url = url
                sep = ""
                query = ""

            json_url = base_url + ".json"

            # Remake full URL with query part, if any, maybe not needed
            if query:
                json_url = json_url + sep + query
        else:
            json_url = url

        # todo: check if e6 api format or dbr, or other, needs to get api response first
        if any(keyword in json_url for keyword in ["e621", "e926", "e6ai"]):
            response = requests.get(json_url, headers=headers).json()
            img_tensor, tags_dict, og_img_width, og_img_height = get_e621_post_data(response, img_size)

        # elif: # for other sites

        else:  # danbooru used / used as fallback for now
            response = requests.get(json_url, headers=headers).json()
            img_tensor, tags_dict, og_img_width, og_img_height = get_danbooru_post_data(response, img_size)

        # print(f"E621 Booru Toolkit DEBUG - Possibly unsupported site? Using danbooru as fallback. URL: {json_url}")

        # scale image to diffusion-compatible size
        scaled_img_width, scaled_img_height = calculate_dimensions_for_diffusion(
            og_img_width, og_img_height, scale_target_avg
        )

        if exclude_tags:
            # convert user_excluded_tags to a list and format it properly to match tags_dict
            user_excluded_tags = user_excluded_tags.replace(", ", ",").split(",")
            exclude_tags_list = [
                tag.replace(" ", "_").replace("\\(", "(").replace("\\)", ")") for tag in user_excluded_tags
            ]

            # remove tags in tags_dict that match the exclude_tags_list
            for key in tags_dict:
                tags_dict[key] = ", ".join([tag for tag in tags_dict[key].split(", ") if tag not in exclude_tags_list])

        if format_tags:  # should run last
            for key in tags_dict:
                tags_dict[key] = tags_dict[key].replace("_", " ").replace("(", "\\(").replace(")", "\\)")

        return (
            img_tensor,
            tags_dict["general_tags"],
            tags_dict["character_tags"],
            tags_dict["copyright_tags"],
            tags_dict["artist_tags"],
            tags_dict["species_tags"],
            scaled_img_width,
            scaled_img_height,
            og_img_width,
            og_img_height,
        )
