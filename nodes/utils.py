import numpy as np
import torch # type: ignore
from PIL.Image import Image as PILImage


def to_tensor(image: PILImage) -> torch.Tensor:
    """Converts a PIL Image to a PyTorch tensor with an added batch dimension as ComfyUI expects it."""
    return torch.from_numpy(np.array(image).astype(np.float32) / 255.0).unsqueeze(0)


def calculate_dimensions_for_diffusion(
    img_width: int, img_height: int, scale_target_avg: int, multiples_of: int = 64
) -> tuple:
    """
    Calculates new image dimensions scaled to a target average size (E.g.: 1024) while preserving aspect ratio,
    rounding each dimension down to the nearest multiple of a specified value (usually 64).
    Args:
        img_width (int): Original image width.
        img_height (int): Original image height.
        scale_target_avg (int): Target average for the new dimensions.
        multiples_of (int, optional): Value to which dimensions are rounded down. Defaults to 64.
    Returns:
        tuple: (new_width, new_height) scaled and rounded dimensions.
    """
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
    """Removes underscores and escape parentheses."""
    return tags.replace("_", " ").replace("(", "\\(").replace(")", "\\)")


def exclude_tags_from_string(tags: str, exclude_list) -> str:
    """Excludes specified tags from the tag string."""
    return ", ".join([tag for tag in tags.split(", ") if tag not in exclude_list])
