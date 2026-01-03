import os
import json
from pathlib import Path
import easyocr

# Đường dẫn thư mục keyframes và thư mục lưu kết quả OCR
KEYFRAMES_DIR = "data/keyframes"
OCR_RESULTS_DIR = "data/ocr_result"

# Tạo thư mục lưu kết quả OCR nếu chưa tồn tại
os.makedirs(OCR_RESULTS_DIR, exist_ok=True)

def extract_text_from_keyframes():
    # Khởi tạo EasyOCR reader với GPU (nếu khả dụng)
    try:
        reader = easyocr.Reader(['en', 'vi'], gpu=True)  # Bắt buộc sử dụng GPU
        print("[INFO] GPU được sử dụng để tăng tốc OCR.")
    except Exception as e:
        print("[WARNING] Không thể sử dụng GPU. Chuyển sang CPU.")
        reader = easyocr.Reader(['en', 'vi'], gpu=False)  # Dùng CPU nếu GPU không khả dụng

    # Duyệt qua các thư mục con trong keyframes
    for video_id in os.listdir(KEYFRAMES_DIR):
        video_dir = os.path.join(KEYFRAMES_DIR, video_id)

        if not os.path.isdir(video_dir):
            continue

        print(f"Processing video: {video_id}")

        # Tạo thư mục kết quả cho video
        video_result_dir = os.path.join(OCR_RESULTS_DIR, video_id)
        os.makedirs(video_result_dir, exist_ok=True)

        # Kiểm tra nếu video đã được OCR xong
        if os.path.exists(video_result_dir):
            existing_files = set(os.listdir(video_result_dir))
            keyframe_files = set(f"{Path(f).stem}.json" for f in os.listdir(video_dir) if f.endswith(('.jpg', '.png', '.webp')))

            # Nếu tất cả keyframes đã có kết quả OCR, bỏ qua video này
            if keyframe_files.issubset(existing_files):
                print(f"[INFO] Video {video_id} đã được OCR xong. Bỏ qua.")
                continue

        # Duyệt qua các file keyframe trong thư mục video
        for keyframe_file in os.listdir(video_dir):
            if not keyframe_file.endswith(('.jpg', '.png', '.webp')):
                continue

            keyframe_path = os.path.join(video_dir, keyframe_file)
            print(f"  Extracting text from: {keyframe_file}")

            # Tính toán thời gian của keyframe (2 giây mỗi keyframe)
            keyframe_index = int(Path(keyframe_file).stem.split('_')[-1])  # Lấy chỉ số keyframe từ tên file
            time_seconds = keyframe_index * 2

            # Thực hiện OCR trên keyframe
            results = reader.readtext(keyframe_path)

            # Chuyển kết quả OCR thành danh sách
            extracted_text = {
                "keyframe": keyframe_file,
                "time_seconds": time_seconds,
                "ocr_results": [
                    {
                        "text": result[1],
                        "confidence": result[2]
                    }
                    for result in results
                ]
            }

            # Lưu kết quả OCR vào file JSON
            result_file = Path(video_result_dir) / f"{Path(keyframe_file).stem}.json"
            with open(result_file, "w", encoding="utf-8") as f:
                json.dump(extracted_text, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    extract_text_from_keyframes()