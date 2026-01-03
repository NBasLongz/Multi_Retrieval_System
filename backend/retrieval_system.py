import csv
import json
import logging
from functools import lru_cache
from pathlib import Path

import torch

from elasticsearch import Elasticsearch
from pymilvus import Collection, connections

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import config
from utils.elasticsearch_client import get_elasticsearch_client
from utils.text_encoder import TextEncoder
from utils.video_metadata import load_video_metadata
# --- Setup Logging ---
logger = logging.getLogger(__name__)

_KEYFRAME_MAP_DIR = Path(config.KEYFRAMES_DIR) / "maps"


@lru_cache(maxsize=2048)
def _load_keyframe_seconds_map(video_id: str):
    """Load mapping of keyframe index to seconds for a given video."""
    map_path = _KEYFRAME_MAP_DIR / f"{video_id}_map.csv"
    if not map_path.exists():
        return None

    mapping = {}
    try:
        with map_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                try:
                    frame_id = int(row.get("FrameID", "").strip())
                    seconds = float(row.get("Seconds", "").strip())
                    original_frame_raw = row.get("OriginalFrame", "")
                    original_frame = (
                        int(original_frame_raw.strip()) if original_frame_raw is not None and original_frame_raw.strip() != "" else None
                    )
                except (ValueError, AttributeError):
                    continue
                mapping[frame_id] = (seconds, original_frame)
    except Exception as exc:  # noqa: BLE001 - log and fallback
        logger.warning("Failed to read keyframe map for %s: %s", video_id, exc)
        return None

    return mapping or None


class VideoRetrievalSystem:
    def __init__(self, re_ingest=False):
        if re_ingest:
            from backend.ingest_data import main

            main()

        logger.info("Initializing Video Retrieval System...")

        self.video_fps = load_video_metadata(config.VIDEOS_DIR)

        # --- Milvus ---
        connections.connect("default", host=config.MILVUS_HOST, port=config.MILVUS_PORT)
        logger.info("Successfully connected to Milvus.")
        self.keyframes_collection = Collection(config.KEYFRAME_COLLECTION_NAME)
        # Lazy load: collection will auto-load on first query (saves ~500MB RAM at startup)
        # self.keyframes_collection.load()  # Uncomment if you prefer preloading
        logger.info("Milvus collection ready (lazy loading enabled to save memory)")

        # --- Elasticsearch ---
        self.es_client: Elasticsearch = get_elasticsearch_client()
        logger.info("Successfully connected to Elasticsearch.")

        # Initialize the text encoder
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.encoder = TextEncoder(device=self.device)

    def _resolve_frame_info(self, video_id: str, keyframe_index: int) -> tuple[float, int]:
        try:
            key_idx = int(keyframe_index)
        except (TypeError, ValueError):
            key_idx = keyframe_index

        mapping = _load_keyframe_seconds_map(video_id)
        seconds_value = None
        original_frame_value = None
        if mapping and key_idx in mapping:
            try:
                seconds_candidate, original_candidate = mapping[key_idx]
                if seconds_candidate is not None:
                    seconds_value = float(seconds_candidate)
                if original_candidate is not None:
                    original_frame_value = int(original_candidate)
            except (TypeError, ValueError):
                seconds_value = None
                original_frame_value = None

        fps = self.video_fps.get(video_id, 25.0)
        try:
            fps_value = float(fps)
        except (TypeError, ValueError):
            fps_value = 25.0

        if fps_value <= 0:
            fps_value = 25.0

        if seconds_value is None:
            try:
                seconds_value = float(key_idx) / fps_value
            except (TypeError, ValueError):
                seconds_value = 0.0

        if original_frame_value is None:
            try:
                original_frame_value = int(round(seconds_value * fps_value))
            except (TypeError, ValueError):
                original_frame_value = 0

        return seconds_value, original_frame_value

    def _resolve_start_seconds(self, video_id: str, keyframe_index: int) -> float:
        seconds_value, _ = self._resolve_frame_info(video_id, keyframe_index)
        return seconds_value

    def clip_search(self, query: str = "", max_results: int = 200) -> list:
        """
        Searching on CLIP embeddings.
        """
        logger.info(f"--- Start searching on CLIP embeddings with query: '{query}' ---")

        if not query:
            logger.warning("Search initiated with no query data.")
            return []

        query_vector = self.encoder.encode(query)

        search_params = {"metric_type": "COSINE", "params": {"nprobe": 10}}

        search_results = self.keyframes_collection.search(
            data=query_vector,
            anns_field="keyframe_vector",
            param=search_params,
            limit=max_results,
            output_fields=["video_id", "keyframe_index"],
        )

        keyframe_scores = []
        if search_results:
            for hit in search_results[0]:
                video_id = hit.entity.get("video_id")
                keyframe_index = hit.entity.get("keyframe_index")
                start_seconds, original_frame = self._resolve_frame_info(video_id, keyframe_index)
                keyframe_scores.append(
                    {
                        "video_id": video_id,
                        "keyframe_index": keyframe_index,
                        "frame_number": original_frame,
                        "start": start_seconds,
                        "start_seconds": start_seconds,  # Add alias for frontend consistency
                        "clip_score": hit.distance,
                    }
                )

        logger.info(f"CLIP: Found {len(keyframe_scores)} potential keyframes.")
        return keyframe_scores

    def transcript_search(self, query: str = "", max_results: int = 200) -> list[dict]:
        if not query:
            return []

        try:
            response = self.es_client.search(
                index=config.TRANSCRIPT_INDEX,
                size=max_results,
                query={
                    "bool": {
                        "should": [
                            {"match": {"text": {"query": query, "fuzziness": "AUTO"}}},
                            {"match_phrase": {"text": {"query": query}}},
                            {"match": {"text.as_you_type": {"query": query}}},
                        ],
                        "minimum_should_match": 1,
                    }
                },
                _source=["video_id", "keyframe_index", "start", "end", "text"],
            )

            hits = []
            for hit in response.get("hits", {}).get("hits", []):
                source = hit.get("_source", {})
                start_time = source.get("start", 0)
                hits.append(
                    {
                        "video_id": source.get("video_id"),
                        "keyframe_index": source.get("keyframe_index"),
                        "start": start_time,
                        "start_seconds": start_time,  # Alias for frontend consistency
                        "end": source.get("end"),
                        "transcript_text": source.get("text"),
                        "transcript_score": hit.get("_score"),
                    }
                )

            logger.info(f"Elasticsearch: Found {len(hits)} transcript matches.")
            return hits
        except Exception as e:
            logger.error(f"An error occurred during transcript search: {e}")
            return []

    def intersect(self, list_results: list[list[dict]]) -> list[dict]:
        logger.info(f"Intersecting {len(list_results)} result sets.")
        if not list_results:
            return []

        if len(list_results) == 1:
            return list_results[0]

        # --- Step 1: Create a lookup map and an initial set of identifiers ---
        # We use the first list as our baseline. Any keyframe in the final
        # intersection MUST be present in this first list.
        # The lookup map allows us to reconstruct the full dictionary at the end.

        first_list = list_results[0]
        # The key is a tuple (video_id, keyframe_index), which is hashable.
        # The value is the original keyframe dictionary.
        lookup_map = {(kf["video_id"], kf["keyframe_index"]): kf for kf in first_list}

        # This set contains the unique identifiers from the first list.
        # This will be our "running intersection".
        intersecting_ids = set(lookup_map.keys())

        # --- Step 2: Iterate and intersect with the rest of the lists ---
        # We start from the second list (index 1).
        for other_list in list_results[1:]:
            # Convert the current list into a set of its unique identifiers.
            other_list_ids = set(
                (kf["video_id"], kf["keyframe_index"]) for kf in other_list
            )

            # Perform the core intersection logic.
            # The "&=" operator updates a set with the intersection of itself
            # and another set. It's highly efficient.
            intersecting_ids &= other_list_ids

            # Optimization: If the intersection ever becomes empty,
            # we can stop early as the final result will also be empty.
            if not intersecting_ids:
                break

        # --- Step 3: Convert the final set of identifiers back to a list of dicts ---
        # We use our lookup_map to retrieve the original, full dictionary
        # for each identifier that survived the intersection process.
        final_results = [lookup_map[id_tuple] for id_tuple in intersecting_ids]

        return final_results


# --- Example Usage ---
if __name__ == "__main__":
    searcher = VideoRetrievalSystem()
    query1 = [
        {"label": "car", "confidence": 0.5, "min_instances": 1, "max_instances": 3},
        {"label": "person", "confidence": 0.7, "min_instances": 1},
    ]
    import time

    print("Start searching")
    start = time.time()
    matching_frames = searcher.object_search(
        query1, projection={"_id": 1, "video_id": 1, "keyframe_id": 1}
    )
    print("Filter take: ", time.time() - start)

