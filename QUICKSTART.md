# ⚡ Quick Start Guide

Hướng dẫn nhanh để chạy hệ thống từ đầu đến cuối.

---

## 📋 Prerequisites Checklist

Trước khi bắt đầu, đảm bảo bạn đã cài:
- [ ] Python 3.8+ (`python --version`)
- [ ] Docker Desktop (đang chạy)
- [ ] Git

---

## 🚀 Chạy hệ thống trong 5 phút

### 1️⃣ Setup môi trường

```bash
# Clone repo (nếu chưa có)
git clone <repo-url>
cd Retrieval_System

# Tạo virtual environment
python -m venv .venv

# Activate venv
.venv\Scripts\activate       # Windows
source .venv/bin/activate    # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Khởi động Docker

```bash
docker compose up -d
```

Chờ ~2 phút, kiểm tra:
```bash
docker compose ps
```

Tất cả phải **"Up"** hoặc **"healthy"**.

### 3️⃣ Verify môi trường

```bash
python -m scripts.setup_environment --all
```

Nếu có lỗi → Fix theo hướng dẫn hiển thị.

### 4️⃣ Thêm video

Copy video MP4 vào:
```
data/videos/L01_V001.mp4
data/videos/L01_V002.mp4
...
```

### 5️⃣ Ingest data

```bash
python -m backend.ingest_data
```

⏱️ **Thời gian:** ~1-2 phút cho 10 videos

### 6️⃣ Chạy web server

```bash
python -m backend.app
```

### 7️⃣ Mở trình duyệt

🌐 **http://localhost:5000**

---

## 🎯 Cấu hình Session ID

### Trước khi submit kết quả:

1. **Mở:** `backend/config.py`
2. **Sửa:**
   ```python
   SESSION_ID = "YOUR_SESSION_ID_HERE"
   EVALUATION_ID = "YOUR_EVALUATION_ID_HERE"
   EVALUATION_SERVER = "http://192.168.20.156:5601"
   ```
3. **Restart:** Server (`Ctrl+C` → chạy lại `python -m backend.app`)

---

## 🧪 Test hệ thống

### Kiểm tra Milvus:
```bash
curl http://localhost:9091/healthz
```

### Kiểm tra Elasticsearch:
```bash
curl http://localhost:9200/_cluster/health
```

### Kiểm tra Flask API:
```bash
curl http://localhost:5000/
```

---

## ❓ Gặp lỗi?

### Docker không chạy:
```bash
docker compose down
docker compose up -d --force-recreate
```

### Milvus connection failed:
```bash
docker compose restart milvus-standalone
docker compose logs milvus-standalone
```

### Elasticsearch yellow/red:
```bash
docker compose restart elasticsearch
# Chờ 30s
curl http://localhost:9200/_cluster/health
```

### Port đã được sử dụng:
Đổi port trong `docker-compose.yml`:
```yaml
ports:
  - "5001:5000"  # Thay 5000 thành 5001
```

---

## 📚 Đọc thêm

- **Full Documentation:** [README.md](README.md)
- **API Details:** [README.md#api-endpoints](README.md#api-endpoints)
- **Troubleshooting:** [README.md#troubleshooting](README.md#troubleshooting)

---

**Ready to search! 🎬**
