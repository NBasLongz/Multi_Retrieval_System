# 🧠 Memory Optimization Guide

## Current Memory Usage
- **Total RAM:** 15.69 GB
- **Used:** 13.46 GB (86%)
- **Free:** 2.23 GB ⚠️

## Major Memory Consumers

### 1. Elasticsearch (1.58 GB)
**Cause:** ES loads indices and caches queries
**Fix:**
```yaml
# docker-compose.yml
services:
  elasticsearch:
    environment:
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"  # Reduce from 1.5GB to 512MB
```

### 2. Milvus (972 MB)
**Cause:** Collection loaded into memory with all vectors
**Fix:**
```python
# backend/retrieval_system.py
# Option 1: Don't preload collection
# self.keyframes_collection.load()  # Comment this out
# Will auto-load on first query

# Option 2: Release collection when idle
def cleanup(self):
    self.keyframes_collection.release()
```

### 3. CLIP Model (~400 MB)
**Already optimized:**
- ✅ Lazy loading (loads only when needed)
- ✅ Visual encoder deleted (`del self._model.visual`)
- ✅ Set to eval mode (no gradients)

**Further optimization:**
```python
# utils/text_encoder.py
import torch
with torch.no_grad():  # Ensure no gradient tracking
    embeddings = self.encode([query])
```

### 4. VS Code (2.4 GB)
**Cause:** Multiple extensions, language servers, terminals

**Fix:**
1. **Disable unused extensions:**
   - Settings → Extensions → Disable workspace-only
   - Keep only: Python, Pylance, Docker, GitLens

2. **Reduce terminal instances:**
   - Close unused terminals (you have 4 active)
   - Use 1-2 max

3. **Add to `.vscode/settings.json`:**
```json
{
  "files.watcherExclude": {
    "**/.venv/**": true,
    "**/.git/objects/**": true,
    "**/data/embeddings/**": true,
    "**/data/keyframes/**": true,
    "**/data/videos/**": true,
    "**/volumes/**": true
  },
  "search.exclude": {
    "**/data/**": true,
    "**/.venv/**": true,
    "**/volumes/**": true
  },
  "python.analysis.exclude": [
    "**/data/**",
    "**/.venv/**"
  ]
}
```

## Quick Wins (Apply Now)

### 1. Reduce Elasticsearch Memory
```bash
# Edit docker-compose.yml, then restart
docker compose down
docker compose up -d
```

### 2. Close VS Code Extensions
- **Ctrl+Shift+P** → "Developer: Reload Window"
- Disable extensions you don't use

### 3. Release Milvus Collection After Use
Add to `backend/app.py`:
```python
import atexit

def cleanup():
    if search_system:
        search_system.keyframes_collection.release()
        logger.info("Released Milvus collection from memory")

atexit.register(cleanup)
```

### 4. Clear Python Cache
```bash
cd F:\Retrieval_System
python -m pip cache purge
find . -type d -name "__pycache__" -exec rm -rf {} +  # Linux/Mac
# Windows:
powershell -Command "Get-ChildItem -Path . -Include __pycache__ -Recurse -Force | Remove-Item -Recurse -Force"
```

## Expected Memory After Optimization

| Component | Before | After | Saved |
|-----------|--------|-------|-------|
| Elasticsearch | 1.58 GB | 512 MB | -1.07 GB |
| VS Code | 2.4 GB | 1.5 GB | -900 MB |
| Python | 577 MB | 577 MB | 0 |
| Milvus | 972 MB | 500 MB* | -472 MB |
| **Total Saved** | | | **~2.4 GB** |

*Milvus will auto-release if not using `collection.load()`

## Long-term Solutions

### 1. Increase Virtual Memory (Page File)
**Windows:**
1. Search "View advanced system settings"
2. Performance → Settings → Advanced → Virtual Memory
3. Set custom size: **Initial: 8192 MB, Maximum: 16384 MB**
4. Restart

### 2. Upgrade RAM
- Current: 16 GB
- Recommended: 32 GB (if working with large datasets)

### 3. Use Swap Space (Linux)
```bash
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## Monitoring Memory

### Real-time Monitor
```bash
# Windows
powershell -Command "while($true) { Get-Process | Where-Object {$_.ProcessName -match 'python|docker|code'} | Sort-Object -Property WS -Descending | Select-Object -First 5 ProcessName, @{Name='Memory(MB)';Expression={[math]::Round($_.WS/1MB,2)}} | Format-Table -AutoSize; Start-Sleep 5; Clear-Host }"

# Docker containers
docker stats
```

### Check Before Starting
```python
# Add to backend/app.py at startup
import psutil
mem = psutil.virtual_memory()
print(f"Available: {mem.available / (1024**3):.2f} GB")
if mem.available < 3 * (1024**3):
    print("⚠️ WARNING: Less than 3GB free RAM!")
```

---

**Apply these changes and you should have ~4-5 GB free RAM! 🎉**
