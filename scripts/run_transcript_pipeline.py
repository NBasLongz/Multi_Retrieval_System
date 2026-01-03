"""
Script pipeline hoàn chỉnh để:
1. Extract transcripts từ video (chỉ video chưa có transcript)
2. Ingest transcript data vào Elasticsearch
3. Đảm bảo tích hợp với keyframes để tìm kiếm và hiển thị video

Usage:
    python scripts/run_transcript_pipeline.py --all
    python scripts/run_transcript_pipeline.py --video L01_V001
    python scripts/run_transcript_pipeline.py --extract-only
    python scripts/run_transcript_pipeline.py --ingest-only
"""

import argparse
import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import config
from backend.ingest_data import ingest_transcript_data
from scripts.extract_transcripts import WhisperTranscriptExtractor
from utils.elasticsearch_client import get_elasticsearch_client, recreate_transcript_index

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


def check_existing_transcripts(transcripts_dir: str) -> set:
    """
    Lấy danh sách video_id đã có transcript
    
    Returns:
        Set các video_id đã có file transcript JSON
    """
    transcripts_path = Path(transcripts_dir)
    if not transcripts_path.exists():
        return set()
    
    existing = set()
    for json_file in transcripts_path.glob("*.json"):
        existing.add(json_file.stem)
    
    logger.info(f"Found {len(existing)} existing transcript files")
    return existing


def extract_transcripts(
    model_size: str = "base",
    language: str = None,
    device: str = None,
    videos_dir: str = None,
    output_dir: str = None,
    video_pattern: str = "*.mp4",
    single_video: str = None,
    skip_existing: bool = True
):
    """
    Extract transcripts từ video sử dụng Whisper
    """
    logger.info("=" * 60)
    logger.info("STEP 1: Extracting Transcripts from Videos")
    logger.info("=" * 60)
    
    videos_dir = videos_dir or config.VIDEOS_DIR
    output_dir = output_dir or config.TRANSCRIPTS_DIR
    
    # Initialize Whisper extractor
    extractor = WhisperTranscriptExtractor(
        model_size=model_size,
        language=language,
        device=device
    )
    
    # Single video mode
    if single_video:
        video_path = Path(videos_dir) / f"{single_video}.mp4"
        if not video_path.exists():
            video_path = Path(single_video)
        
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return []
        
        output_json = Path(output_dir) / f"{video_path.stem}.json"
        
        # Check if already exists
        if skip_existing and output_json.exists():
            logger.info(f"Transcript already exists for {video_path.stem}, skipping...")
            return []
        
        extractor.extract_transcript(
            video_path=str(video_path),
            output_json_path=str(output_json)
        )
        
        logger.info(f"✅ Transcript extracted for {video_path.stem}")
        return [video_path.stem]
    
    # Batch mode
    else:
        processed = extractor.batch_extract(
            videos_dir=videos_dir,
            output_dir=output_dir,
            video_pattern=video_pattern,
            skip_existing=skip_existing
        )
        
        logger.info(f"✅ Extracted {len(processed)} transcripts")
        return processed


def ingest_to_elasticsearch(
    transcripts_dir: str = None,
    recreate_index: bool = False
):
    """
    Ingest transcript data vào Elasticsearch
    """
    logger.info("=" * 60)
    logger.info("STEP 2: Ingesting Transcripts to Elasticsearch")
    logger.info("=" * 60)
    
    transcripts_dir = transcripts_dir or config.TRANSCRIPTS_DIR
    
    # Connect to Elasticsearch
    es_client = get_elasticsearch_client()
    
    # Recreate index nếu cần
    if recreate_index:
        logger.info("Recreating transcript index...")
        recreate_transcript_index(es_client)
    
    # Ingest data
    ingest_transcript_data(es_client, transcripts_dir)
    
    logger.info("✅ Transcript ingestion complete")


def verify_setup(transcripts_dir: str = None):
    """
    Verify rằng transcript data đã được setup đúng
    """
    logger.info("=" * 60)
    logger.info("VERIFICATION: Checking Transcript Setup")
    logger.info("=" * 60)
    
    transcripts_dir = transcripts_dir or config.TRANSCRIPTS_DIR
    transcripts_path = Path(transcripts_dir)
    
    # Check transcript files
    if not transcripts_path.exists():
        logger.error(f"❌ Transcripts directory not found: {transcripts_path}")
        return False
    
    json_files = list(transcripts_path.glob("*.json"))
    logger.info(f"✅ Found {len(json_files)} transcript JSON files")
    
    if json_files:
        # Check first file format
        sample_file = json_files[0]
        import json
        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Sample transcript: {sample_file.name}")
        logger.info(f"  - Video ID: {data.get('video_id')}")
        logger.info(f"  - Language: {data.get('language')}")
        logger.info(f"  - Duration: {data.get('duration', 0):.2f}s")
        logger.info(f"  - Segments: {len(data.get('segments', []))}")
        
        if data.get('segments'):
            sample_seg = data['segments'][0]
            logger.info(f"  - Sample segment:")
            logger.info(f"    * Start: {sample_seg.get('start')}s")
            logger.info(f"    * End: {sample_seg.get('end')}s")
            logger.info(f"    * Timestamp: {sample_seg.get('timestamp')}")
            logger.info(f"    * Text: {sample_seg.get('text', '')[:50]}...")
    
    # Check Elasticsearch
    try:
        es_client = get_elasticsearch_client()
        if es_client.indices.exists(index=config.TRANSCRIPT_INDEX):
            count = es_client.count(index=config.TRANSCRIPT_INDEX)
            logger.info(f"✅ Elasticsearch index '{config.TRANSCRIPT_INDEX}' exists")
            logger.info(f"  - Total documents: {count['count']}")
        else:
            logger.warning(f"⚠️ Elasticsearch index '{config.TRANSCRIPT_INDEX}' does not exist")
    except Exception as e:
        logger.error(f"❌ Failed to connect to Elasticsearch: {e}")
        return False
    
    logger.info("=" * 60)
    logger.info("✅ Verification complete!")
    logger.info("=" * 60)
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Pipeline hoàn chỉnh để extract và ingest transcripts"
    )
    
    # Mode selection
    parser.add_argument(
        "--all",
        action="store_true",
        help="Chạy cả extract và ingest (mặc định)"
    )
    
    parser.add_argument(
        "--extract-only",
        action="store_true",
        help="Chỉ extract transcripts, không ingest"
    )
    
    parser.add_argument(
        "--ingest-only",
        action="store_true",
        help="Chỉ ingest transcripts có sẵn, không extract"
    )
    
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Chỉ verify setup, không làm gì khác"
    )
    
    # Whisper options
    parser.add_argument(
        "--model",
        type=str,
        default="base",
        choices=["tiny", "base", "small", "medium", "large"],
        help="Whisper model size (default: base)"
    )
    
    parser.add_argument(
        "--language",
        type=str,
        default="vi",
        help="Language code (default: vi for Vietnamese)"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cuda", "cpu"],
        help="Device to run on (default: auto detect)"
    )
    
    # Path options
    parser.add_argument(
        "--videos-dir",
        type=str,
        default=config.VIDEOS_DIR,
        help=f"Videos directory (default: {config.VIDEOS_DIR})"
    )
    
    parser.add_argument(
        "--transcripts-dir",
        type=str,
        default=config.TRANSCRIPTS_DIR,
        help=f"Transcripts directory (default: {config.TRANSCRIPTS_DIR})"
    )
    
    parser.add_argument(
        "--video-pattern",
        type=str,
        default="*.mp4",
        help="Video file pattern (default: *.mp4)"
    )
    
    # Processing options
    parser.add_argument(
        "--video",
        type=str,
        default=None,
        help="Process only a single video (video_id)"
    )
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-extract transcripts cho video đã có"
    )
    
    parser.add_argument(
        "--recreate-index",
        action="store_true",
        help="Recreate Elasticsearch index trước khi ingest"
    )
    
    args = parser.parse_args()
    
    # Determine mode
    extract = args.all or args.extract_only or (not args.ingest_only and not args.verify_only)
    ingest = args.all or args.ingest_only or (not args.extract_only and not args.verify_only)
    verify = args.verify_only
    
    try:
        # Verify only mode
        if verify:
            verify_setup(args.transcripts_dir)
            return
        
        # Extract transcripts
        if extract:
            processed = extract_transcripts(
                model_size=args.model,
                language=args.language,
                device=args.device,
                videos_dir=args.videos_dir,
                output_dir=args.transcripts_dir,
                video_pattern=args.video_pattern,
                single_video=args.video,
                skip_existing=not args.force
            )
            
            if not processed and not args.video:
                logger.info("No new transcripts extracted. All videos already processed.")
        
        # Ingest to Elasticsearch
        if ingest:
            ingest_to_elasticsearch(
                transcripts_dir=args.transcripts_dir,
                recreate_index=args.recreate_index
            )
        
        # Final verification
        logger.info("\n")
        verify_setup(args.transcripts_dir)
        
        logger.info("\n" + "=" * 60)
        logger.info("🎉 PIPELINE HOÀN THÀNH!")
        logger.info("=" * 60)
        logger.info("Bạn có thể:")
        logger.info("1. Tìm kiếm transcript qua giao diện web")
        logger.info("2. Kết quả sẽ hiển thị video với keyframe")
        logger.info("3. Nhấn vào để xem video tại thời điểm chính xác")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
