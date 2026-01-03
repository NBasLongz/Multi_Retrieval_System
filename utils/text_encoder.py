import logging

import numpy as np
import open_clip
import torch
import torch.nn.functional as F

from backend import config

logger = logging.getLogger(__name__)


class TextEncoder:
    def __init__(self, device: str = "cuda"):
        self.device = device
        self._model = None
        self._tokenizer = None
        self._precomputed_tokens = None
        logger.info(f"TextEncoder created (lazy loading enabled for '{config.CLIP_MODEL_NAME}')")

    def _ensure_loaded(self):
        """Lazy load the model only when needed."""
        if self._model is not None:
            return
            
        logger.info(f"Loading CLIP model '{config.CLIP_MODEL_NAME}' to device '{self.device}'...")
        self._model, _, _ = open_clip.create_model_and_transforms(
            config.CLIP_MODEL_NAME,
            pretrained=config.CLIP_PRETRAINED
        )
        
        # Remove visual encoder to save memory (we only need text encoder)
        del self._model.visual
        
        self._model = self._model.to(self.device)
        self._model.eval()
        self._tokenizer = open_clip.get_tokenizer(config.CLIP_MODEL_NAME)

        # Precompute common query tokens for performance
        common_queries = ["person", "car", "building"]
        self._precomputed_tokens = {
            query: self._tokenizer([query]).to(self.device)
            for query in common_queries
        }
        logger.info("CLIP model loaded successfully.")
    
    @property
    def model(self):
        self._ensure_loaded()
        return self._model
    
    @property
    def tokenizer(self):
        self._ensure_loaded()
        return self._tokenizer
    
    @property
    def precomputed_tokens(self):
        self._ensure_loaded()
        return self._precomputed_tokens

    def encode(self, query: str):
        text_inputs = self.tokenizer([query]).to(self.device)

        with torch.no_grad():
            text_features = self.model.encode_text(text_inputs)
            if self.device  == "cuda":
                text_features = text_features.cpu()
            return F.normalize(text_features, p=2, dim=-1).detach().numpy().astype(np.float32)
