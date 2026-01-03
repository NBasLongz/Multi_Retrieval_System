"""
Script wrapper để chạy toàn bộ pipeline extract transcripts
Tự động extract transcripts từ video chưa có transcript
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import config

# Load environment variables from whisper_config.env if exists
env_file = Path(__file__).parent.parent / "whisper_config.env"
if env_file.exists():
    load_dotenv(env_file)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


def run_transcript_extraction(
    model_size: str = "base",
    language: str = None,
    skip_existing: bool = True
):
    """
    Chạy script extract_transcripts.py
    
    Args:
        model_size: Whisper model size
        language: Language code (None = auto detect)
        skip_existing: Skip videos that already have transcripts
    """
    from scripts.extract_transcripts import WhisperTranscriptExtractor
    
    logger.info("=" * 60)
    logger.info("STEP 1: EXTRACTING TRANSCRIPTS WITH WHISPER")
    logger.info("=" * 60)
    
    extractor = WhisperTranscriptExtractor(
        model_size=model_size,
        language=language
    )
    
    processed = extractor.batch_extract(
        videos_dir=config.VIDEOS_DIR,
        output_dir=config.TRANSCRIPTS_DIR,
        video_pattern="*.mp4",
        skip_existing=skip_existing
    )
    
    logger.info(f"✅ Extracted {len(processed)} transcripts")
    return processed


def run_ingest_data():
    """Chạy backend.ingest_data để index vào Elasticsearch và Milvus"""
    logger.info("=" * 60)
    logger.info("STEP 2: INGESTING DATA TO ELASTICSEARCH & MILVUS")
    logger.info("=" * 60)
    
    from backend.ingest_data import main as ingest_main
    
    ingest_main()
    
    logger.info("✅ Data ingestion complete")


def main():
    parser = argparse.ArgumentParser(
        description="Extract transcripts và ingest vào database"
    )
    
    # Get defaults from environment if available
    default_model = os.getenv("WHISPER_MODEL", "base")
    default_language = os.getenv("WHISPER_LANGUAGE", "vi")  # Mặc định tiếng Việt
    default_skip = os.getenv("WHISPER_SKIP_EXISTING", "true").lower() == "true"
    
    parser.add_argument(
        "--model",
        type=str,
        default=default_model,
        choices=["tiny", "base", "small", "medium", "large"],
        help=f"Whisper model size (default: {default_model})"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        default=default_language,
        help=f"Language code (e.g., 'en', 'vi'). None = auto detect (default: {default_language})"
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=default_skip,
        help=f"Skip videos that already have transcripts (default: {default_skip})"
    )
    
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Only extract transcripts, don't run ingestion"
    )
    
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Only run ingestion, skip transcript extraction"
    )
    
    args = parser.parse_args()
    
    try:
        # Step 1: Extract transcripts
        if not args.ingest_only:
            run_transcript_extraction(
                model_size=args.model,
                language=args.language,
                skip_existing=args.skip_existing
            )
        
        # Step 2: Ingest data
        if not args.extract_only:
            run_ingest_data()
        
        logger.info("=" * 60)
        logger.info("✅ ALL STEPS COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


if __name__ == "__main__":
    main()
