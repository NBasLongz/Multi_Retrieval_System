"""
Script để extract transcripts từ video sử dụng OpenAI Whisper.
Hỗ trợ:
- Tự động detect ngôn ngữ hoặc chỉ định ngôn ngữ cụ thể
- Xuất ra JSON format với timestamps
- Hỗ trợ batch processing
- Tùy chọn model size (tiny, base, small, medium, large)
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import whisper
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)


class WhisperTranscriptExtractor:
    """Class để extract transcripts từ video sử dụng Whisper"""
    
    def __init__(
        self,
        model_size: str = "base",
        language: Optional[str] = None,
        device: Optional[str] = None
    ):
        """
        Args:
            model_size: Kích thước model ('tiny', 'base', 'small', 'medium', 'large')
            language: Mã ngôn ngữ (VD: 'en', 'vi', 'ja'). None = auto detect
            device: 'cuda', 'cpu', hoặc None (auto detect)
        """
        self.model_size = model_size
        self.language = language
        self.device = device
        
        logger.info(f"Loading Whisper model '{model_size}'...")
        self.model = whisper.load_model(model_size, device=device)
        logger.info(f"Model loaded successfully. Device: {self.model.device}")
    
    @staticmethod
    def _seconds_to_timestamp(seconds: float) -> str:
        """Chuyển đổi seconds thành HH:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def extract_transcript(
        self,
        video_path: str,
        output_json_path: Optional[str] = None
    ) -> Dict:
        """
        Extract transcript từ một video file
        
        Args:
            video_path: Đường dẫn đến file video
            output_json_path: Đường dẫn output JSON. None = không lưu file
            
        Returns:
            Dictionary chứa transcript data với format:
            {
                "video_id": str,
                "language": str,
                "segments": [
                    {
                        "id": int,
                        "start": float,
                        "end": float,
                        "text": str
                    },
                    ...
                ]
            }
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        video_id = video_path.stem
        logger.info(f"Transcribing video: {video_id}")
        
        # Whisper transcription options
        transcribe_options = {
            "verbose": False,
            "language": self.language,
            "task": "transcribe",  # 'transcribe' hoặc 'translate'
        }
        
        # Run Whisper
        result = self.model.transcribe(str(video_path), **transcribe_options)
        
        # Format output
        transcript_data = {
            "video_id": video_id,
            "language": result.get("language", "unknown"),
            "duration": round(result.get("duration", 0), 3),
            "segments": []
        }
        
        for segment in result["segments"]:
            transcript_data["segments"].append({
                "id": segment["id"],
                "start": round(segment["start"], 3),
                "end": round(segment["end"], 3),
                "text": segment["text"].strip(),
                "timestamp": self._seconds_to_timestamp(segment["start"])
            })
        
        # Save to JSON if output path provided
        if output_json_path:
            output_path = Path(output_json_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(transcript_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Transcript saved to: {output_path}")
        
        return transcript_data
    
    def batch_extract(
        self,
        videos_dir: str,
        output_dir: str,
        video_pattern: str = "*.mp4",
        skip_existing: bool = True
    ) -> List[str]:
        """
        Batch extract transcripts từ nhiều video
        
        Args:
            videos_dir: Thư mục chứa video files
            output_dir: Thư mục output cho JSON files
            video_pattern: Glob pattern cho video files
            skip_existing: Bỏ qua video đã có transcript
            
        Returns:
            List các video_id đã được xử lý
        """
        videos_dir = Path(videos_dir)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        video_files = sorted(videos_dir.glob(video_pattern))
        
        if not video_files:
            logger.warning(f"No video files found in {videos_dir} matching '{video_pattern}'")
            return []
        
        logger.info(f"Found {len(video_files)} video files to process")
        
        processed_ids = []
        
        for video_file in tqdm(video_files, desc="Extracting transcripts"):
            video_id = video_file.stem
            output_json = output_dir / f"{video_id}.json"
            
            # Skip if already exists
            if skip_existing and output_json.exists():
                logger.info(f"Skipping {video_id} (transcript already exists)")
                continue
            
            try:
                self.extract_transcript(
                    video_path=str(video_file),
                    output_json_path=str(output_json)
                )
                processed_ids.append(video_id)
                
            except Exception as e:
                logger.error(f"Error processing {video_id}: {e}")
                continue
        
        logger.info(f"Batch extraction complete. Processed {len(processed_ids)} videos.")
        return processed_ids


def main():
    parser = argparse.ArgumentParser(
        description="Extract transcripts từ video sử dụng Whisper"
    )
    
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
        default=None,
        help="Language code (e.g., 'en', 'vi', 'ja'). None = auto detect"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        choices=["cuda", "cpu"],
        help="Device to run on. None = auto detect"
    )
    
    parser.add_argument(
        "--videos-dir",
        type=str,
        default=config.VIDEOS_DIR,
        help=f"Directory containing video files (default: {config.VIDEOS_DIR})"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default=config.TRANSCRIPTS_DIR,
        help=f"Output directory for JSON files (default: {config.TRANSCRIPTS_DIR})"
    )
    
    parser.add_argument(
        "--video-pattern",
        type=str,
        default="*.mp4",
        help="Glob pattern for video files (default: *.mp4)"
    )
    
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip videos that already have transcripts"
    )
    
    parser.add_argument(
        "--single-video",
        type=str,
        default=None,
        help="Process only a single video (video_id or full path)"
    )
    
    args = parser.parse_args()
    
    # Initialize extractor
    extractor = WhisperTranscriptExtractor(
        model_size=args.model,
        language=args.language,
        device=args.device
    )
    
    # Single video mode
    if args.single_video:
        video_path = Path(args.single_video)
        
        # If only video_id provided, construct full path
        if not video_path.exists():
            video_path = Path(args.videos_dir) / f"{args.single_video}.mp4"
        
        if not video_path.exists():
            logger.error(f"Video not found: {video_path}")
            return
        
        output_json = Path(args.output_dir) / f"{video_path.stem}.json"
        
        extractor.extract_transcript(
            video_path=str(video_path),
            output_json_path=str(output_json)
        )
        
        logger.info(f"✅ Transcript extracted successfully for {video_path.stem}")
    
    # Batch mode
    else:
        processed = extractor.batch_extract(
            videos_dir=args.videos_dir,
            output_dir=args.output_dir,
            video_pattern=args.video_pattern,
            skip_existing=args.skip_existing
        )
        
        logger.info(f"✅ Batch extraction complete. {len(processed)} videos processed.")


if __name__ == "__main__":
    main()
