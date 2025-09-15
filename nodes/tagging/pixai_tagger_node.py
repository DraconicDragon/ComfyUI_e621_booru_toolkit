import logging
import os

import numpy as np
import torch
from PIL import Image

from .inference.pixai_tagger_pth import EndpointHandler

# todo: make this like post nodes where theres one central one that can execute evry one of them (might not work? consider RRTagger steps thingy?? idkw hat it does)
class PixAITaggerNode:
    MODELS_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "..", "..", "models"))

    @classmethod
    def scan_models(cls):
        models = []
        if not os.path.isdir(cls.MODELS_DIR):
            logging.warning(f"Models directory not found: {cls.MODELS_DIR}")
            return models
        for folder in os.listdir(cls.MODELS_DIR):
            folder_path = os.path.join(cls.MODELS_DIR, folder)
            if not os.path.isdir(folder_path):
                continue
            # Look for .pth file, tags json, and mapping json
            weights = None
            tags = None
            mapping = None
            for f in os.listdir(folder_path):
                if f.lower().endswith((".pth", ".safetensors")):
                    weights = f
                elif f.lower().startswith("tags_") and f.lower().endswith(".json"):
                    tags = f
                elif f.lower().startswith("char_ip_map") and f.lower().endswith(".json"):
                    mapping = f
            if weights and tags and mapping:
                # Show as folder/model.pth
                models.append(
                    {
                        "label": f"{folder}/{weights}",
                        "weights": os.path.join(folder_path, weights),
                        "tags": os.path.join(folder_path, tags),
                        "mapping": os.path.join(folder_path, mapping),
                    }
                )
        return models

    """
    A ComfyUI node that uses the PixAI Tagger model to generate general,
    character, and IP/copyright/franchise tags for a given image.
    """

    _handler_cache = {}

    @classmethod
    def INPUT_TYPES(cls):
        models = cls.scan_models()
        model_choices = [m["label"] for m in models] if models else ["No valid models found"]
        return {
            "required": {
                "model": (model_choices,),
                "image": ("IMAGE",),
                "general_threshold": ("FLOAT", {"default": 0.35, "min": 0.0, "max": 1.0, "step": 0.01}),
                "character_threshold": ("FLOAT", {"default": 0.85, "min": 0.0, "max": 1.0, "step": 0.01}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("general_tags", "character_tags", "ip_tags")
    FUNCTION = "tag_image"
    CATEGORY = "Tagging"

    def tag_image(self, model: str, image: torch.Tensor, general_threshold: float, character_threshold: float):
        # Find model info from scanned models
        models = self.scan_models()
        model_info = next((m for m in models if m["label"] == model), None)
        if not model_info:
            logging.error(f"Selected model '{model}' not found in available models.")
            return ("", "", "")

        cache_key = model_info["weights"]
        handler = self._handler_cache.get(cache_key)
        if handler is None:
            try:
                handler = EndpointHandler(
                    weights_file=model_info["weights"], tags_file=model_info["tags"], mapping_file=model_info["mapping"]
                )
                self._handler_cache[cache_key] = handler
                logging.info(f"Loaded model handler for {model}")
            except Exception as e:
                logging.error(f"Failed to load model handler for {model}: {e}")
                return ("", "", "")

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
        predicted_tags = handler(data)

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
