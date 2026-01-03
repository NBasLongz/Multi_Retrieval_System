# 📂 Project Structure

```
Retrieval_System/
│
├── 📁 backend/                     # Core application backend
│   ├── app.py                     # 🚀 Flask web server (MAIN ENTRY POINT)
│   ├── retrieval_system.py        # 🔍 Search engine (Milvus + Elasticsearch)
│   ├── ingest_data.py             # 📥 Data ingestion pipeline
│   ├── config.py                  # ⚙️  Configuration settings
│   └── submit.py                  # 📤 Submit API helper
│
├── 📁 utils/                       # Utility modules
│   ├── __init__.py
│   ├── elasticsearch_client.py    # Elasticsearch connection helper
│   ├── text_encoder.py            # CLIP text encoder wrapper
│   └── video_metadata.py          # Video FPS/metadata loader
│
├── 📁 scripts/                     # Setup & processing scripts
│   ├── __init__.py
│   ├── setup_environment.py       # 🔧 Environment verification
│   ├── extract_keyframes.py       # 🎞️  Keyframe extraction
│   ├── compute_embeddings.py      # 🧠 CLIP embedding computation
│   └── test_ingest_one_video.py   # 🧪 Test single video ingest
│
├── 📁 tools/                       # Optional utilities
│   ├── hls.py                     # HLS converter (not used)
│   ├── open_clip_torch.py         # CLIP import compatibility shim
│   └── run_ingest.bat             # Windows batch for ingest
│
├── 📁 templates/                   # HTML templates
│   └── index.html                 # 🌐 Main web UI
│
├── 📁 static/                      # Frontend assets
│   ├── style.css                  # 🎨 Global CSS styles
│   └── 📁 js/
│       ├── main.js                # Main app controller
│       ├── video-player.js        # Video modal & frame controls
│       ├── results.js             # Search results rendering
│       ├── api.js                 # API communication
│       └── elements.js            # DOM element references
│
├── 📁 data/                        # Data storage (gitignored)
│   ├── 📁 videos/                 # 🎥 Source MP4 files
│   ├── 📁 keyframes/              # 🖼️  Extracted keyframe images (webp)
│   │   └── 📁 maps/               # CSV: frame_id → seconds
│   ├── 📁 transcripts/            # 📝 JSON transcript files
│   ├── 📁 embeddings/             # 🔢 CLIP embeddings (NPZ)
│   └── 📁 hls/                    # HLS segments (not used)
│
├── 📁 volumes/                     # Docker persistent storage
│   ├── milvus/                    # Milvus vector database
│   ├── es_data/                   # Elasticsearch indices
│   └── mongo_data/                # MongoDB (Milvus metadata)
│
├── 📄 docker-compose.yml           # Docker services definition
├── 📄 requirements.txt             # Python dependencies
├── 📄 README.md                    # 📚 Full documentation
├── 📄 QUICKSTART.md                # ⚡ Quick start guide
├── 📄 .gitignore                   # Git ignore rules
└── 📄 STRUCTURE.md                 # 📂 This file
```

---

## 🔗 File Dependencies

```
app.py
  ├── imports: backend/config.py
  ├── imports: backend/retrieval_system.py
  ├── imports: utils/video_metadata.py
  └── serves: templates/index.html
              └── loads: static/js/main.js
                         ├── static/js/video-player.js
                         ├── static/js/results.js
                         ├── static/js/api.js
                         └── static/js/elements.js

retrieval_system.py
  ├── imports: backend/config.py
  ├── imports: utils/text_encoder.py
  ├── imports: utils/elasticsearch_client.py
  ├── connects: Milvus (localhost:19530)
  └── connects: Elasticsearch (localhost:9200)

ingest_data.py
  ├── imports: backend/config.py
  ├── imports: utils/elasticsearch_client.py
  ├── calls: scripts/extract_keyframes.py
  ├── calls: scripts/compute_embeddings.py
  └── writes: data/keyframes/, data/embeddings/
```

---

## 🎯 Key Files Explained

### **Backend Core**

| File | Purpose | When to edit |
|------|---------|-------------|
| `backend/app.py` | Flask server, API routes | Add new endpoints |
| `backend/retrieval_system.py` | Search logic | Change ranking/scoring |
| `backend/ingest_data.py` | Data pipeline | Modify ingest process |
| `backend/config.py` | Settings | Change paths, IDs, servers |

### **Utilities**

| File | Purpose | Dependencies |
|------|---------|-------------|
| `utils/text_encoder.py` | CLIP text encoding | open_clip, torch |
| `utils/elasticsearch_client.py` | ES connection | elasticsearch |
| `utils/video_metadata.py` | Load video FPS | cv2 |

### **Scripts**

| File | Purpose | Usage |
|------|---------|-------|
| `scripts/setup_environment.py` | Verify setup | `python -m scripts.setup_environment --all` |
| `scripts/extract_keyframes.py` | Extract frames | Called by ingest_data.py |
| `scripts/compute_embeddings.py` | Compute CLIP embeddings | Called by ingest_data.py |

### **Frontend**

| File | Purpose | Exports |
|------|---------|---------|
| `static/js/main.js` | App init, search logic | - |
| `static/js/video-player.js` | Modal, frame controls | `openModal()`, `closeModal()` |
| `static/js/results.js` | Display search results | `displayResults()` |
| `static/js/api.js` | HTTP requests | `searchAPI()`, `submitResultAPI()` |
| `static/js/elements.js` | DOM references | `elements` object |

---

## 🗂️ Data Flow

```
1. USER UPLOADS VIDEO
   data/videos/L01_V001.mp4
         ↓
2. INGEST PROCESS
   scripts/extract_keyframes.py
         ↓ generates
   data/keyframes/L01_V001/keyframe_0.webp
   data/keyframes/maps/L01_V001_map.csv
         ↓
   scripts/compute_embeddings.py
         ↓ generates
   data/embeddings/L01_V001.npz
         ↓
3. INDEX TO DATABASES
   Milvus: vector embeddings
   Elasticsearch: transcript text
         ↓
4. USER SEARCHES
   Web UI → app.py → retrieval_system.py
         ↓ queries
   Milvus + Elasticsearch
         ↓ returns
   Ranked results → Web UI
         ↓
5. USER SUBMITS
   video-player.js → api.js → app.py
         ↓ forwards to
   Evaluation Server (192.168.20.156:5601)
```

---

## 🔄 Module Import Chain

```python
# app.py startup
import backend.config              # Load settings
import backend.retrieval_system    # Init search engine
  ├── import utils.text_encoder    # Load CLIP
  ├── import utils.elasticsearch_client
  └── connect to Milvus

# retrieval_system.py startup
connect_to_milvus()
  └── pymilvus.connections.connect()

get_elasticsearch_client()
  └── elasticsearch.Elasticsearch()

TextEncoder()
  └── open_clip.create_model_and_transforms()
```

---

## 📦 External Dependencies

| Service | Port | Purpose | Container |
|---------|------|---------|-----------|
| **Milvus** | 19530 | Vector search | milvus-standalone |
| **Elasticsearch** | 9200 | Text search | elasticsearch |
| **Etcd** | 2379 | Milvus metadata | etcd |
| **MinIO** | 9000 | Milvus storage | minio |
| **Flask** | 5000 | Web server | (local Python) |

---

## 🛠️ When to Edit What

### **Add new feature:**
1. Backend logic → `backend/retrieval_system.py`
2. API endpoint → `backend/app.py`
3. Frontend UI → `templates/index.html` + `static/js/`

### **Change search ranking:**
→ `backend/retrieval_system.py` → `search()` method

### **Modify video processing:**
→ `scripts/extract_keyframes.py` or `scripts/compute_embeddings.py`

### **Update session/evaluation IDs:**
→ `backend/config.py`

### **Change UI styling:**
→ `static/style.css`

### **Fix frame navigation:**
→ `static/js/video-player.js`

---

**Understanding the structure helps you navigate and contribute! 🧭**
