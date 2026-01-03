"""
Script để cải thiện chất lượng transcript bằng cách chạy lại Whisper với model tốt hơn (large).
Script này sẽ ghi đè lên các file transcript cũ.
"""

import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import config
from scripts.extract_transcripts import WhisperTranscriptExtractor

# Load environment variables
env_file = Path(__file__).parent.parent / "whisper_config.env"
if env_file.exists():
    load_dotenv(env_file)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    # Lấy cấu hình từ env
    model_size = os.getenv("WHISPER_MODEL", "large")
    language = os.getenv("WHISPER_LANGUAGE", "vi")
    device = os.getenv("WHISPER_DEVICE")
    
    logger.info(f"Starting transcript improvement with model: {model_size}")
    logger.info("This process may take a long time depending on your hardware.")
    
    # Initialize extractor
    extractor = WhisperTranscriptExtractor(
        model_size=model_size,
        language=language,
        device=device
    )
    
    # Paths
    videos_dir = config.DATA_DIR / "videos"
    transcripts_dir = config.DATA_DIR / "transcripts"
    
    # Run batch extraction with skip_existing=False to overwrite old files
    processed_files = extractor.batch_extract(
        videos_dir=str(videos_dir),
        output_dir=str(transcripts_dir),
        skip_existing=False  # Quan trọng: Ghi đè file cũ
    )
    
    logger.info(f"Completed! Processed {len(processed_files)} videos.")

if __name__ == "__main__":
    main()
