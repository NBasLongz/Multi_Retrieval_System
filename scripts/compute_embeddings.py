"""
Script to compute CLIP embeddings for keyframe images.

Usage:
    python scripts/compute_embeddings.py --video L01_V001
    python scripts/compute_embeddings.py  # Process all videos
    python scripts/compute_embeddings.py --batch-size 32
"""

import argparse
import logging
from pathlib import Path

import numpy as np
import open_clip
import torch
import torch.nn.functional as F
from PIL import Image
from tqdm import tqdm
import concurrent.futures

from backend import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
)
logger = logging.getLogger(__name__)


class ImageEncoder:
    """CLIP image encoder for computing keyframe embeddings.

    This encoder can use a thread pool to preprocess images in parallel
    (image decoding + transforms) which helps when CPU or disk I/O is the bottleneck.
    """
    
    def __init__(self, device: str = None, num_workers: int = 4):
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            # If user requested cuda but PyTorch/CUDA not available, fallback to cpu
            if device == "cuda" and not torch.cuda.is_available():
                logger.warning("CUDA requested but not available in this Python environment. Falling back to CPU.")
                self.device = "cpu"
            else:
                self.device = device
        
        logger.info(f"Loading CLIP model '{config.CLIP_MODEL_NAME}' on device '{self.device}'...")
        
        # Create model and preprocess
        self.model, _, self.preprocess = open_clip.create_model_and_transforms(
            config.CLIP_MODEL_NAME,
            pretrained=config.CLIP_PRETRAINED,
        )

        # Move model to device
        try:
            self.model = self.model.to(self.device)
        except Exception:
            # fallback: if .to fails, try .cuda() when requested
            if self.device == "cuda" and torch.cuda.is_available():
                self.model = self.model.cuda()
            else:
                self.model = self.model.cpu()
        
        # Remove text encoder to save memory
        del self.model.transformer
        del self.model.token_embedding
        del self.model.ln_final
        del self.model.text_projection
        del self.model.attn_mask
        del self.model.positional_embedding
        
        self.model.eval()
        # Number of worker threads for preprocessing (image decoding + transform)
        self.num_workers = max(1, int(num_workers))
        logger.info(f"CLIP model loaded successfully on {self.device}")
    
    @torch.no_grad()
    def encode_image(self, image_path: Path) -> np.ndarray:
        """
        Encode a single image to embedding vector.
        
        Args:
            image_path: Path to image file
        
        Returns:
            Normalized embedding vector (numpy array, float32)
        """
        try:
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
            
            image_features = self.model.encode_image(image_tensor)
            
            # Move to CPU and normalize
            if self.device == "cuda":
                image_features = image_features.cpu()
            
            image_features = F.normalize(image_features, p=2, dim=-1)
            return image_features.numpy().astype(np.float32)
        
        except Exception as e:
            logger.error(f"Error encoding {image_path}: {e}")
            return None
    
    @torch.no_grad()
    def encode_batch(self, image_paths: list) -> list:
        """
        Encode a batch of images.
        
        Args:
            image_paths: List of image file paths
        
        Returns:
            List of embedding vectors
        """
        # Preprocess images in parallel to reduce CPU I/O bottleneck
        images = []
        paths = []

        def _load_and_preprocess(p):
            try:
                img = Image.open(p).convert("RGB")
                return self.preprocess(img)
            except Exception as e:
                logger.error(f"Error loading {p}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.num_workers) as ex:
            for result, p in zip(ex.map(_load_and_preprocess, image_paths), image_paths):
                if result is not None:
                    images.append(result)
                    paths.append(p)

        if not images:
            return []

        image_batch = torch.stack(images).to(self.device)
        image_features = self.model.encode_image(image_batch)
        
        # Move to CPU and normalize
        if self.device == "cuda":
            image_features = image_features.cpu()
        
        image_features = F.normalize(image_features, p=2, dim=-1)
        return image_features.numpy().astype(np.float32)


def compute_embeddings_for_video(
    video_id: str, 
    encoder: ImageEncoder, 
    batch_size: int = 16
):
    """
    Compute embeddings for all keyframes of a video.
    
    Args:
        video_id: Video ID (e.g., L01_V001)
        encoder: ImageEncoder instance
        batch_size: Batch size for processing
    """
    keyframes_dir = Path(config.KEYFRAMES_DIR) / video_id
    embeddings_dir = Path(config.CLIP_FEATURES_DIR) / video_id
    
    if not keyframes_dir.exists():
        logger.error(f"Keyframes directory not found: {keyframes_dir}")
        return False
    
    # Get all keyframe images
    keyframe_files = sorted(
        keyframes_dir.glob("keyframe_*.webp"),
        key=lambda x: int(x.stem.split("_")[-1])
    )
    
    if not keyframe_files:
        logger.warning(f"No keyframes found in {keyframes_dir}")
        return False
    
    logger.info(f"Processing {len(keyframe_files)} keyframes for video {video_id}")
    
    # Create output directory
    embeddings_dir.mkdir(parents=True, exist_ok=True)
    
    # Process in batches
    for i in tqdm(range(0, len(keyframe_files), batch_size), desc=f"Encoding {video_id}"):
        batch_files = keyframe_files[i:i + batch_size]
        
        if batch_size == 1:
            # Process single image
            keyframe_file = batch_files[0]
            frame_idx = int(keyframe_file.stem.split("_")[-1])
            embedding = encoder.encode_image(keyframe_file)
            
            if embedding is not None:
                # Convert to torch tensor and save
                embedding_tensor = torch.from_numpy(embedding)
                output_path = embeddings_dir / f"keyframe_{frame_idx}.pt"
                torch.save(embedding_tensor, output_path)
        else:
            # Process batch
            embeddings = encoder.encode_batch(batch_files)
            
            if len(embeddings) > 0:
                for j, keyframe_file in enumerate(batch_files):
                    if j < len(embeddings):
                        frame_idx = int(keyframe_file.stem.split("_")[-1])
                        embedding_tensor = torch.from_numpy(embeddings[j:j+1])
                        output_path = embeddings_dir / f"keyframe_{frame_idx}.pt"
                        torch.save(embedding_tensor, output_path)
    
    logger.info(f"Embeddings saved to {embeddings_dir}")
    return True


def process_all_videos(batch_size: int = 16, device: str = None, num_workers: int = None):
    """Process all videos with keyframes."""
    keyframes_root = Path(config.KEYFRAMES_DIR)
    
    if not keyframes_root.exists():
        logger.error(f"Keyframes directory not found: {keyframes_root}")
        return
    
    # Get all video directories
    video_dirs = [d for d in keyframes_root.iterdir() if d.is_dir() and d.name != "maps"]
    
    if not video_dirs:
        logger.warning(f"No video keyframe directories found in {keyframes_root}")
        return
    
    logger.info(f"Found {len(video_dirs)} videos to process")
    
    # Initialize encoder once
    # Default workers: use provided num_workers or min(8, cpu_count)
    import os
    if num_workers is None:
        default_workers = min(8, max(1, (os.cpu_count() or 4)))
    else:
        default_workers = max(1, int(num_workers))
    encoder = ImageEncoder(device=device, num_workers=default_workers)
    
    for video_dir in video_dirs:
        video_id = video_dir.name
        compute_embeddings_for_video(video_id, encoder, batch_size)


def main():
    parser = argparse.ArgumentParser(
        description="Compute CLIP embeddings for keyframe images"
    )
    parser.add_argument(
        "--video",
        type=str,
        help="Process only specific video ID (e.g., L01_V001). If not provided, processes all videos.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=16,
        help="Batch size for processing (default: 16)",
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["cuda", "cpu"],
        help="Device to use (default: auto-detect)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=4,
        help="Number of worker threads for image preprocessing (default: 4)",
    )
    
    args = parser.parse_args()
    
    if args.video:
        encoder = ImageEncoder(device=args.device, num_workers=args.workers)
        compute_embeddings_for_video(args.video, encoder, args.batch_size)
    else:
        # Pass worker count into the global encoder creation
        process_all_videos(args.batch_size, device=args.device, num_workers=args.workers)


if __name__ == "__main__":
    main()