import numpy as np
import torch
from PIL import Image


def to_tensor(image: Image) -> torch.Tensor:
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def calculate_dimensions_for_diffusion(
    img_width: int, img_height: int, scale_target_avg: int, multiples_of: int = 64
) -> tuple:
    # Calculate the average of the original dimensions.
    # This average will be scaled to be near the scale_target_avg.
    original_avg = (img_width + img_height) / 2.0

    # Determine the scaling factor to get the average near the target.
    scale_factor = scale_target_avg / original_avg

    # Scale the dimensions while preserving the aspect ratio.
    new_width = round(img_width * scale_factor)  # rounding because output can be 1023.9999999999
    new_height = round(img_height * scale_factor)

    # Adjust the scaled dimensions to be multiples of
    new_width = (new_width // multiples_of) * multiples_of
    new_height = (new_height // multiples_of) * multiples_of

    return int(new_width), int(new_height)


def format_tags(tags: str) -> str:
    return tags.replace("_", " ").replace("(", "\\(").replace(")", "\\)")


def exclude_tags_from_string(tags: str, exclude_list) -> str:
    return ", ".join([tag for tag in tags.split(", ") if tag not in exclude_list])
