import logging
import os

import numpy as np
import torch
from PIL import Image

from .inference.pixai_tagger_pth import EndpointHandler


class PixAITaggerNode:
    """
    A ComfyUI node that uses the PixAI Tagger model to generate general,
    character, and IP tags for a given image.
    """

    def __init__(self):
        # current dir of this script
        current_dir = os.path.dirname(os.path.realpath(__file__))

        # Try both hyphen and underscore versions of the model directory
        model_dir_hyphen = os.path.normpath(os.path.join(current_dir, "..", "..", "models", "pixai-tagger-v0.9"))
        model_dir_underscore = os.path.normpath(os.path.join(current_dir, "..", "..", "models", "pixai_tagger_v0.9"))

        if os.path.isdir(model_dir_hyphen):
            model_dir = model_dir_hyphen
        elif os.path.isdir(model_dir_underscore):
            model_dir = model_dir_underscore
        else:
            model_dir = model_dir_hyphen

        if not os.path.isdir(model_dir):
            raise FileNotFoundError(
                f"Model directory not found at {model_dir}. Please ensure the 'models' folder with model files exists. If it doesn't, create it."
            )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logging.info(f"PixAI Tagger: Model will be loaded onto device: {device.upper()}")
        logging.info(f"PixAI Tagger: Loading model from: {model_dir}")
        self.handler = EndpointHandler(path=model_dir)
        logging.info(f"PixAI Tagger: Model loaded successfully on device: {self.handler.device.upper()}")

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "general_threshold": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.01}),
                "character_threshold": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("general_tags", "character_tags", "ip_tags")
    FUNCTION = "tag_image"
    CATEGORY = "Tagging"

    def tag_image(self, image: torch.Tensor, general_threshold: float, character_threshold: float):
        # 1. Convert the input tensor (shape: BHWC) to a PIL Image (first one in batch)
        img_tensor = image[0]
        i = 255.0 * img_tensor.cpu().numpy()
        pil_image = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

        # 2. Prepare the data payload for the handler
        data = {
            "inputs": pil_image,
            "parameters": {
                "general_threshold": float(general_threshold),
                "character_threshold": float(character_threshold),
            },
        }

        # 3. Run inference using the handler
        predicted_tags = self.handler(data)

        # 4. Format the output tags into comma-separated strings
        general_tags_list = sorted(predicted_tags.get("feature", []))
        character_tags_list = sorted(predicted_tags.get("character", []))
        ip_tags_list = sorted(predicted_tags.get("ip", []))

        # Replace underscores with spaces
        # todo: make optional

        # todo: use logic from utils
        general_tags = ", ".join(tag.replace("_", " ") for tag in general_tags_list)
        character_tags = ", ".join(tag.replace("_", " ") for tag in character_tags_list)
        ip_tags = ", ".join(tag.replace("_", " ") for tag in ip_tags_list)

        # Replace parenthesises with escaped versions
        general_tags = general_tags.replace("(", "\\(").replace(")", "\\)")
        character_tags = character_tags.replace("(", "\\(").replace(")", "\\)")
        ip_tags = ip_tags.replace("(", "\\(").replace(")", "\\)")

        return (general_tags, character_tags, ip_tags)
