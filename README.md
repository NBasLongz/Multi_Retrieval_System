# 🎥 Video Retrieval System

Hệ thống tìm kiếm và truy xuất video thông minh sử dụng **CLIP embedding** và **Elasticsearch** cho tìm kiếm transcript. Hỗ trợ nộp kết quả lên evaluation server.

---

## 📋 Mục Lục

- [Tổng quan](#tổng-quan)
- [Kiến trúc hệ thống](#kiến-trúc-hệ-thống)
- [Yêu cầu hệ thống](#yêu-cầu-hệ-thống)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Sử dụng](#sử-dụng)
- [Cấu trúc thư mục](#cấu-trúc-thư-mục)
- [API Endpoints](#api-endpoints)
- [Troubleshooting](#troubleshooting)

---

## 🎯 Tổng quan

Hệ thống cho phép:
- ✅ **Tìm kiếm video** bằng mô tả văn bản (text query)
- ✅ **Tìm kiếm transcript** trong nội dung video
- ✅ **Auto-extract transcripts** bằng OpenAI Whisper (99 ngôn ngữ)
- ✅ **Xem preview video** khi hover chuột
- ✅ **Điều hướng frame-by-frame** chính xác
- ✅ **Nộp kết quả** lên evaluation server với session ID
- ✅ **Quản lý metadata** video (FPS, duration, keyframes)

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────┐
│   Web UI        │  ← Flask + Vanilla JavaScript
│  (templates/)   │
└────────┬────────┘
         │
┌────────▼────────┐
│   Backend       │
│   (Flask API)   │  ← app.py, retrieval_system.py
└────────┬────────┘
         │
    ┌────┴────┬─────────────┬──────────────┐
    ▼         ▼             ▼              ▼
┌───────┐ ┌────────┐ ┌──────────┐ ┌──────────────┐
│Milvus │ │Elastic │ │Video     │ │Evaluation    │
│Vector │ │Search  │ │Storage   │ │Server        │
│  DB   │ │(Trans) │ │(MP4)     │ │(Submit API)  │
└───────┘ └────────┘ └──────────┘ └──────────────┘
```

**Công nghệ sử dụng:**
- **Frontend:** HTML5, CSS3, Vanilla JavaScript (ES6 modules)
- **Backend:** Flask (Python 3.8+)
- **Vector DB:** Milvus (CLIP embeddings)
- **Text Search:** Elasticsearch (transcript search)
- **Video Processing:** OpenCV, FFmpeg
- **ML Model:** OpenCLIP (ViT-B/32)
- **Transcript Extraction:** OpenAI Whisper (multi-language ASR)

---

## 💻 Yêu cầu hệ thống

### Phần mềm bắt buộc:
- **Python 3.8+** 
- **Docker Desktop** (Milvus, Elasticsearch containers)
- **Git** (để clone repository)
- **8GB RAM** tối thiểu (khuyến nghị 16GB)
- **10GB dung lượng** trống (cho models và data)

### Hệ điều hành:
- ✅ Windows 10/11
- ✅ Linux (Ubuntu 20.04+)
- ✅ macOS (Intel/Apple Silicon)

---

## 📦 Cài đặt

### Bước 1: Clone repository

```bash
git clone <repository-url>
cd Retrieval_System
```

### Bước 2: Tạo môi trường ảo Python

**Windows (cmd):**
```cmd
python -m venv .venv
.venv\Scripts\activate
python -m scripts.run_whisper_pipeline --language vi
```

**Linux/macOS:**
```bash
python3 -m venv .venv
source .venv/bin/activate

python -m backend.app
```

### Bước 3: Cài đặt dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Bước 4: Khởi động Docker services

```bash
docker compose up -d
```

**Chờ ~2-5 phút** để các containers khởi động hoàn tất. Kiểm tra status:

```bash
docker compose ps
```

Tất cả services phải ở trạng thái **"Up"** hoặc **"healthy"**.

### Bước 5: Setup môi trường

```bash
python -m scripts.setup_environment --all
```

Lệnh này sẽ:
- ✅ Kiểm tra Python packages
- ✅ Kiểm tra Docker containers
- ✅ Tạo các thư mục cần thiết
- ✅ Download CLIP model weights

---

## ⚙️ Cấu hình

### File: `backend/config.py`

Các cấu hình quan trọng:

```python
# Video & Data Paths
VIDEOS_DIR = "data/videos"           # Thư mục chứa video MP4
KEYFRAMES_DIR = "data/keyframes"     # Thư mục keyframes
TRANSCRIPTS_DIR = "data/transcripts" # Thư mục JSON transcripts
EMBEDDINGS_DIR = "data/embeddings"   # Vector embeddings

# Database Connections
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
ELASTICSEARCH_HOST = "localhost:9200"

# CLIP Model
CLIP_MODEL = "ViT-B/32"
CLIP_PRETRAINED = "openai"

# Evaluation Server
SESSION_ID = "CXTDKFpWUS8QDARbbM6n61yJJ7Yiu9eL"  # Session ID của bạn
EVALUATION_ID = "76f9d8a8-e30d-4840-9865-a09ad24859a6"
EVALUATION_SERVER = "http://192.168.20.156:5601"
```

**⚠️ Quan trọng:** 
- Đổi `SESSION_ID` và `EVALUATION_ID` thành giá trị của bạn
- Kiểm tra `EVALUATION_SERVER` có đúng IP không

---

## 🚀 Sử dụng

### 1. Extract transcripts từ video (Whisper)

**Cách đơn giản nhất:**

```cmd
python -m scripts.run_whisper_pipeline
```

Hoặc dùng batch file (Windows):

```cmd
tools\run_whisper.bat
```

Script này sẽ:
1. ✅ Extract transcripts từ video bằng Whisper
2. ✅ Tự động detect ngôn ngữ (hoặc chỉ định cụ thể)
3. ✅ Lưu transcripts với timestamps chính xác
4. ✅ Index vào Elasticsearch để search

**Tùy chọn nâng cao:**

```cmd
# Chọn model size (tiny/base/small/medium/large)
python -m scripts.run_whisper_pipeline --model small

# Chỉ định ngôn ngữ (tăng tốc độ và độ chính xác)
python -m scripts.run_whisper_pipeline --language en

# Test với 1 video
python -m scripts.extract_transcripts --single-video L01_V001
```

📖 **Chi tiết:** Xem [WHISPER_GUIDE.md](WHISPER_GUIDE.md)

### 2. Ingest data (Chỉ chạy 1 lần hoặc khi có video mới)

**Nếu đã có transcripts (CSV hoặc Whisper JSON):**

```bash
python -m backend.ingest_data
```

**Quá trình này sẽ:**
1. ✅ Extract keyframes từ video (mỗi X giây)
2. ✅ Tính CLIP embeddings cho keyframes
3. ✅ Index embeddings vào Milvus
4. ✅ Index transcripts (CSV hoặc JSON) vào Elasticsearch
5. ✅ Lưu metadata (FPS, duration, frame mapping)

**Thời gian:** ~5-10 phút cho 100 videos (tùy thuộc hardware)

**Lưu ý:** Backend tự động hỗ trợ cả hai format transcript:
- **CSV** (legacy): `Start`, `End`, `Text`
- **JSON** (Whisper): `video_id`, `language`, `segments[]`

📌 **Muốn bổ sung transcript mới mà vẫn giữ dữ liệu cũ?**

```bash
python -m backend.ingest_data --append-transcripts
```

Chế độ này chỉ thêm hoặc cập nhật transcript mới (dựa trên `_id` của Elasticsearch) và không xóa index cũ.

### 3. Chạy web server

```bash
python -m backend.app
```

Server sẽ chạy tại: **http://localhost:5000**

### 4. Sử dụng giao diện web

1. **Mở trình duyệt:** http://localhost:5000
2. **Click "Connect"** → Kết nối đến evaluation server (hiển thị session ID)
3. **Nhập query:** Mô tả video cần tìm (VD: "person walking on the street")
4. **Click "Search"** → Xem kết quả
5. **Hover chuột** lên card → Xem video preview
6. **Click card** → Mở video player modal
7. **Dùng ◀ ▶** → Điều chỉnh frame chính xác
8. **Click "SubmitFrame"** → Nộp lên server

---

## 📁 Cấu trúc thư mục

```
Retrieval_System/
│
├── backend/                    # Core Python backend
│   ├── app.py                 # Flask web server (main entry)
│   ├── retrieval_system.py    # Search engine logic
│   ├── ingest_data.py         # Data ingestion pipeline
│   ├── config.py              # Configuration settings
│   └── submit.py              # Submit API helper
│
├── utils/                      # Utility modules
│   ├── elasticsearch_client.py
│   ├── text_encoder.py        # CLIP text encoder
│   └── video_metadata.py      # Video metadata helpers
│
├── scripts/                    # Setup & processing scripts
│   ├── setup_environment.py   # Environment verification
│   ├── extract_keyframes.py   # Keyframe extraction
│   └── compute_embeddings.py  # CLIP embedding computation
│
├── tools/                      # Optional tools
│   ├── hls.py                 # HLS streaming converter (unused)
│   ├── open_clip_torch.py     # CLIP import shim
│   └── run_ingest.bat         # Windows batch script
│
├── templates/                  # HTML templates
│   └── index.html             # Main web UI
│
├── static/                     # Frontend assets
│   ├── style.css              # Global styles
│   └── js/
│       ├── main.js            # Main app logic
│       ├── video-player.js    # Video modal & controls
│       ├── results.js         # Search results display
│       ├── api.js             # API communication
│       └── elements.js        # DOM element references
│
├── data/                       # Data storage (gitignored)
│   ├── videos/                # MP4 video files
│   ├── keyframes/             # Extracted keyframes (webp)
│   │   └── maps/              # Frame→seconds mapping (CSV)
│   ├── transcripts/           # JSON transcript files
│   └── embeddings/            # CLIP embeddings (NPZ)
│
├── volumes/                    # Docker persistent volumes
│   ├── milvus/
│   ├── es_data/
│   └── mongo_data/
│
├── docker-compose.yml          # Docker services definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 🔌 API Endpoints

### 1. `/` (GET)
- **Mục đích:** Hiển thị giao diện web chính
- **Response:** HTML page

### 2. `/search` (POST)
- **Mục đích:** Tìm kiếm video
- **Request body:**
  ```json
  {
    "description": "person walking",
    "top_k": 100
  }
  ```
- **Response:**
  ```json
  [
    {
      "video_id": "L01_V001",
      "keyframe_index": 150,
      "clip_score": 0.8542,
      "fps": 25.0,
      "start_seconds": 6.0
    }
  ]
  ```

### 3. `/api/login` (POST)
- **Mục đích:** Kết nối evaluation server, lấy session info
- **Request body:** `{}`
- **Response:**
  ```json
  {
    "sessionId": "CXTDKFpWUS8QDARbbM6n61yJJ7Yiu9eL",
    "evaluationId": "76f9d8a8-e30d-4840-9865-a09ad24859a6"
  }
  ```

### 4. `/api/submit` (POST)
- **Mục đích:** Nộp kết quả lên evaluation server
- **Request body:**
  ```json
  {
    "sessionId": "xxx",
    "evaluationId": "yyy",
    "videoId": "L01_V001",
    "timeMs": 6000
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "remote_response": {...}
  }
  ```

### 5. `/videos/<video_id>` (GET)
- **Mục đích:** Stream video MP4
- **Response:** Video file (binary)

### 6. `/keyframes/<video_id>/keyframe_<index>.webp` (GET)
- **Mục đích:** Lấy ảnh keyframe
- **Response:** Image file (webp)

---

## 🐛 Troubleshooting

### ❌ Lỗi: "Milvus connection failed"

**Nguyên nhân:** Docker container chưa khởi động hoặc port bị chặn

**Giải pháp:**
```bash
# Kiểm tra container status
docker compose ps

# Restart containers
docker compose restart

# Xem logs
docker compose logs milvus-standalone
```

---

### ❌ Lỗi: "Elasticsearch not available"

**Giải pháp:**
```bash
# Kiểm tra Elasticsearch health
curl http://localhost:9200/_cluster/health

# Restart nếu cần
docker compose restart elasticsearch
```

---

### ❌ Lỗi: "No videos found"

**Nguyên nhân:** Chưa có video trong `data/videos/`

**Giải pháp:**
1. Copy video MP4 vào `data/videos/`
2. Chạy lại ingest: `python -m backend.ingest_data`

---

### ❌ Lỗi: "Frame counter not updating"

**Nguyên nhân:** JavaScript cache hoặc event listener issue

**Giải pháp:**
1. Hard refresh: **Ctrl+Shift+R** (Windows) hoặc **Cmd+Shift+R** (Mac)
2. Mở Console (F12) → Kiểm tra errors
3. Kiểm tra `video-player.js` có log `updateFrameInfo called` không

---

### ❌ Lỗi: "Submit failed: 401 Unauthorized"

**Nguyên nhân:** Session ID không đúng hoặc đã expire

**Giải pháp:**
1. Click **"Connect"** lại để refresh session
2. Kiểm tra `backend/config.py` → `SESSION_ID` có đúng không
3. Kiểm tra evaluation server có online không:
   ```bash
   curl http://192.168.20.156:5601/api/health
   ```

---

### ❌ Video không play trong modal

**Giải pháp:**
1. Kiểm tra video file tồn tại: `data/videos/L01_V001.mp4`
2. Kiểm tra format: Phải là MP4 (H.264)
3. Convert nếu cần:
   ```bash
   ffmpeg -i input.mp4 -c:v libx264 -c:a aac output.mp4
   ```

---

## 📊 Performance Tips

### 1. Tăng tốc ingest
```python
# Trong backend/ingest_data.py
BULK_CHUNK_SIZE = 2000  # Tăng lên 5000 nếu RAM đủ
```

### 2. Giảm keyframe density
```python
# Trong scripts/extract_keyframes.py
KEYFRAME_INTERVAL = 1.0  # Tăng lên 2.0 để giảm số frame
```

### 3. Optimize Docker
```bash
# Tăng memory cho Docker Desktop
# Settings → Resources → Memory: 8GB+
```

---

## 🤝 Contributing

Contributions are welcome! Vui lòng:
1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

---

## 📝 License

Dự án này chỉ phục vụ mục đích học tập và nghiên cứu.

---

## 👨‍💻 Technical Details

### Frame Timing Logic

**Cách tính thời gian từ keyframe index:**
```python
start_seconds = keyframe_index / fps
time_ms = round(start_seconds * 1000)
```

**Ví dụ:**
- Video FPS: 25
- Keyframe index: 150
- → Start time: 150 / 25 = **6.0 seconds** = **6000 ms**

### Submit Flow

```
User clicks "Submit"
    ↓
JavaScript gets currentTime from <video>
    ↓
timeMs = Math.round(currentTime * 1000)
    ↓
POST /api/submit with {sessionId, evaluationId, videoId, timeMs}
    ↓
Flask backend forwards to evaluation server
    ↓
Response displayed to user
```

---

## 📞 Support

Nếu gặp vấn đề:
1. Kiểm tra [Troubleshooting](#troubleshooting) section
2. Xem logs: `docker compose logs -f`
3. Mở Console (F12) → Tab Console để xem JavaScript errors
4. Check backend logs trong terminal đang chạy `python -m backend.app`

---

**Happy Searching! 🎬🔍**
