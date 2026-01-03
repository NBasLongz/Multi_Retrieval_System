import { elements } from "./elements.js";
import { submitResultAPI } from "./api.js";

let currentOpenVideoId = null;

export function initVideoModal() {
  elements.closeModalBtn.addEventListener("click", closeModal);
  elements.modalOverlay.addEventListener("click", (e) => {
    if (e.target === elements.modalOverlay) {
      closeModal();
    }
  });
}

export function openModal(videoId, startTime, fps, keyframeIndex = 0) {
  closeModal(); // Dọn dẹp instance cũ trước khi mở mới
  currentOpenVideoId = videoId;
  
  console.log('[VIDEO PLAYER] Opening modal:', { videoId, startTime, fps, keyframeIndex });

  elements.modalOverlay.classList.remove("hidden");
  
  // Update video info overlay
  updateVideoInfo(videoId, keyframeIndex, startTime, fps);

  const hlsUrl = `/hls/${videoId}/playlist.m3u8`;
  const mp4Url = `/videos/${videoId}`;
  let mainHls = null;

  // Consumer helpers will populate these after availability check

  // --- Video Wrapper styling ---
  const videoWrapper = elements.modalVideoPlayer.parentElement;
  if (getComputedStyle(videoWrapper).position === "static") {
    videoWrapper.style.position = "relative";
  }

  // --- Xóa timeline và info bar cũ nếu có ---
  const oldTimeline = videoWrapper.querySelector('.video-timeline');
  if (oldTimeline) oldTimeline.remove();
  
  const oldInfoBar = videoWrapper.querySelector('.video-info-bar');
  if (oldInfoBar) oldInfoBar.remove();

  // --- Create Timeline UI (Giữ nguyên logic cũ) ---
  const timelineBar = document.createElement("div");
  timelineBar.className = "video-timeline";
  Object.assign(timelineBar.style, {
    position: "relative",
    height: "8px",
    background: "#444",
    marginTop: "8px",
    cursor: "pointer",
  });

  const progressFill = document.createElement("div");
  Object.assign(progressFill.style, {
    position: "absolute",
    left: "0",
    top: "0",
    bottom: "0",
    width: "0%",
    background: "#1db954",
  });
  timelineBar.appendChild(progressFill);

  const timelinePreview = document.createElement("div");
  timelinePreview.className = "timeline-preview";
  Object.assign(timelinePreview.style, {
    display: "none",
    position: "absolute",
    bottom: "120%",
    transform: "translateX(-50%)",
    zIndex: "999",
    pointerEvents: "none",
  });
  timelinePreview.innerHTML = `
        <img src="" alt="Preview" style="max-width: 150px; border: 1px solid #fff; display:none;">
        <div class="time-label" style="background: rgba(0,0,0,0.7); color: #fff; padding: 2px 5px; text-align: center;">0:00</div>
    `;
  timelineBar.appendChild(timelinePreview);
  videoWrapper.appendChild(timelineBar);

  const previewImg = timelinePreview.querySelector("img");
  const timeLabel = timelinePreview.querySelector(".time-label");

  // --- HLS Preview Setup (Hidden Video for Hover) ---
  const previewVideo = document.createElement("video");
  previewVideo.muted = true;
  previewVideo.preload = "auto";
  previewVideo.style.display = "none";
  videoWrapper.appendChild(previewVideo);

  let previewHls = null;

  const ensureStartPosition = () => {
    const targetTime = Math.max(0, startTime);
    let seekRetries = 0;

    const playAfterSeek = () => {
      if (
        elements.modalOverlay.classList.contains("hidden") ||
        currentOpenVideoId !== videoId
      ) {
        return;
      }
      elements.modalVideoPlayer
        .play()
        .catch((e) => console.warn("Auto-play blocked:", e));
    };

    const seekToTarget = () => {
      const onSeeked = () => {
        elements.modalVideoPlayer.removeEventListener("seeked", onSeeked);
        playAfterSeek();
      };

      try {
        elements.modalVideoPlayer.currentTime = targetTime;
      } catch (err) {
        elements.modalVideoPlayer.addEventListener(
          "canplay",
          () => {
            seekToTarget();
          },
          { once: true },
        );
        return;
      }

      if (Math.abs(elements.modalVideoPlayer.currentTime - targetTime) < 0.05) {
        playAfterSeek();
      } else {
        elements.modalVideoPlayer.addEventListener("seeked", onSeeked, {
          once: true,
        });
      }
    };

    const enforceTargetDuringPlayback = () => {
      const video = elements.modalVideoPlayer;
      if (
        elements.modalOverlay.classList.contains("hidden") ||
        currentOpenVideoId !== videoId
      ) {
        video.removeEventListener("timeupdate", enforceTargetDuringPlayback);
        return;
      }

      if (Math.abs(video.currentTime - targetTime) > 0.25 && seekRetries < 4) {
        seekRetries += 1;
        try {
          video.currentTime = targetTime;
        } catch (err) {
          // ignore; we'll retry on next timeupdate if needed
        }
        return;
      }

      video.removeEventListener("timeupdate", enforceTargetDuringPlayback);
    };

    elements.modalVideoPlayer.addEventListener(
      "timeupdate",
      enforceTargetDuringPlayback,
    );

    const onReady = () => {
      elements.modalVideoPlayer.pause();
      seekToTarget();
    };

    if (elements.modalVideoPlayer.readyState >= 1) {
      onReady();
    } else {
      elements.modalVideoPlayer.addEventListener("loadedmetadata", onReady, {
        once: true,
      });
    }
  };

  const updateCleanupRefs = () => {
    if (elements.modalOverlay._cleanupHandlers) {
      elements.modalOverlay._cleanupHandlers.mainHls = mainHls;
      elements.modalOverlay._cleanupHandlers.previewHls = previewHls;
    }
  };

  const setupMp4Playback = (logFallback = false) => {
    if (mainHls) {
      mainHls.destroy();
      mainHls = null;
    }
    if (previewHls) {
      previewHls.destroy();
      previewHls = null;
    }
    updateCleanupRefs();

    if (logFallback) {
      console.warn(`Falling back to MP4 playback for ${videoId}`);
    }

    elements.modalVideoPlayer.src = mp4Url;
    elements.modalVideoPlayer.load();
    ensureStartPosition();

    previewVideo.src = mp4Url;
    previewVideo.load();
  };

  const setupNativeHlsPlayback = () => {
    elements.modalVideoPlayer.src = hlsUrl;
    elements.modalVideoPlayer.load();
    ensureStartPosition();

    previewVideo.src = hlsUrl;
    previewVideo.load();
  };

  const setupHlsPlayback = () => {
    if (Hls.isSupported()) {
      mainHls = new Hls({
        debug: false,
        enableWorker: true,
      });
      mainHls.loadSource(hlsUrl);
      mainHls.attachMedia(elements.modalVideoPlayer);
      mainHls.on(Hls.Events.MANIFEST_PARSED, ensureStartPosition);

      mainHls.on(Hls.Events.ERROR, function (_, data) {
        if (data.fatal) {
          if (
            data.type === Hls.ErrorTypes.NETWORK_ERROR &&
            Hls.ErrorDetails &&
            data.details === Hls.ErrorDetails.MANIFEST_LOAD_ERROR
          ) {
            console.error("HLS manifest could not be loaded, using MP4 fallback");
            mainHls.destroy();
            mainHls = null;
            setupMp4Playback(true);
            return;
          }

          switch (data.type) {
            case Hls.ErrorTypes.NETWORK_ERROR:
              console.error(
                "Fatal network error encountered, trying to recover",
              );
              mainHls.startLoad();
              break;
            case Hls.ErrorTypes.MEDIA_ERROR:
              console.error(
                "Fatal media error encountered, trying to recover",
              );
              mainHls.recoverMediaError();
              break;
            default:
              mainHls.destroy();
              mainHls = null;
          }
        }
      });

      previewHls = new Hls({
        maxBufferLength: 1,
        maxMaxBufferLength: 2,
        enableWorker: true,
      });
      previewHls.loadSource(hlsUrl);
      previewHls.attachMedia(previewVideo);

      updateCleanupRefs();
      return;
    }

    if (elements.modalVideoPlayer.canPlayType("application/vnd.apple.mpegurl")) {
      setupNativeHlsPlayback();
      updateCleanupRefs();
      return;
    }

    setupMp4Playback(true);
  };

  const verifyAndInitializePlayback = () => {
    // Tắt HLS, chỉ dùng MP4
    console.log(`Using MP4 playback for ${videoId}`);
    setupMp4Playback(false);
  };

  verifyAndInitializePlayback();

  // --- Hover Logic ---
  const previewCanvas = document.createElement("canvas");
  const previewCtx = previewCanvas.getContext("2d");
  let hoverTargetTime = null;
  let hoverScheduled = false;

  const runHoverPreview = () => {
    hoverScheduled = false;
    if (hoverTargetTime === null || !elements.modalVideoPlayer.duration) return;

    const targetTime = hoverTargetTime;
    hoverTargetTime = null;

    const onSeeked = () => {
      if (Math.abs(previewVideo.currentTime - targetTime) > 0.5) return;

      const vw = previewVideo.videoWidth || previewVideo.clientWidth;
      const vh = previewVideo.videoHeight || previewVideo.clientHeight;
      if (!vw || !vh) return;

      previewCanvas.width = vw;
      previewCanvas.height = vh;
      try {
        previewCtx.drawImage(previewVideo, 0, 0, vw, vh);
        previewImg.src = previewCanvas.toDataURL("image/jpeg", 0.6);
        previewImg.style.display = "block";
      } catch (err) {
        previewImg.style.display = "none";
      }
    };

    previewVideo.removeEventListener("seeked", onSeeked);
    previewVideo.addEventListener("seeked", onSeeked, { once: true });
    previewVideo.currentTime = targetTime;
  };

  const scheduleHoverPreview = () => {
    if (!hoverScheduled) {
      hoverScheduled = true;
      setTimeout(runHoverPreview, 50);
    }
  };

  const handleMouseMove = (e) => {
    if (!elements.modalVideoPlayer.duration) return;
    const rect = timelineBar.getBoundingClientRect();
    const percent = Math.max(
      0,
      Math.min(1, (e.clientX - rect.left) / rect.width),
    );
    const hoverTime = percent * elements.modalVideoPlayer.duration;

    timelinePreview.style.display = "block";
    let previewLeft = percent * rect.width - timelinePreview.offsetWidth / 2;
    previewLeft = Math.max(
      0,
      Math.min(previewLeft, rect.width - timelinePreview.offsetWidth),
    );
    timelinePreview.style.left = `${percent * 100}%`;

    const minutes = Math.floor(hoverTime / 60);
    const seconds = Math.floor(hoverTime % 60);
    timeLabel.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;

    hoverTargetTime = hoverTime;
    scheduleHoverPreview();
  };

  // --- Controls & Listeners ---
  const handleTimelineClick = (e) => {
    if (!elements.modalVideoPlayer.duration) return;
    const rect = timelineBar.getBoundingClientRect();
    const percent = Math.max(
      0,
      Math.min(1, (e.clientX - rect.left) / rect.width),
    );
    elements.modalVideoPlayer.currentTime =
      percent * elements.modalVideoPlayer.duration;
  };

  const updateProgress = () => {
    if (!elements.modalVideoPlayer.duration) return;
    const p =
      (elements.modalVideoPlayer.currentTime /
        elements.modalVideoPlayer.duration) *
      100;
    progressFill.style.width = `${p}%`;
  };

  timelineBar.addEventListener("mousemove", handleMouseMove);
  timelineBar.addEventListener("mouseleave", () => {
    timelinePreview.style.display = "none";
    hoverTargetTime = null;
  });
  timelineBar.addEventListener("click", handleTimelineClick);
  elements.modalVideoPlayer.addEventListener("timeupdate", updateProgress);

  // --- Video Info Bar (Trên video) ---
  const videoInfoBar = document.createElement("div");
  videoInfoBar.className = "video-info-bar";
  videoInfoBar.innerHTML = `
    <span class="video-name" id="video-name-display"></span>
    <span class="frame-counter" id="frame-counter-display">Frame: 0 / 0</span>
    <span class="fps-display" id="fps-display">FPS: ${fps.toFixed(2)}</span>
  `;
  videoWrapper.insertBefore(videoInfoBar, videoWrapper.firstChild);

  // Frame controls are already in HTML (no need to create dynamically)
  const frameRate = fps;
  const videoNameDisplay = videoInfoBar.querySelector("#video-name-display");
  const frameCounterDisplay = videoInfoBar.querySelector("#frame-counter-display");
  
  console.log(`[VIDEO-PLAYER] Opening ${currentOpenVideoId} with FPS=${frameRate}`);
  videoNameDisplay.textContent = currentOpenVideoId;

  const getCurrentFrame = () => {
    // Tính frame hiện tại từ thời gian
    const currentTime = elements.modalVideoPlayer.currentTime;
    return Math.floor(currentTime * frameRate);
  };

  const updateFrameInfo = () => {
    if (!elements.modalVideoPlayer.duration) return;
    const currentFrame = getCurrentFrame();
    const totalFrames = Math.floor(elements.modalVideoPlayer.duration * frameRate);
    frameCounterDisplay.textContent = `Frame: ${currentFrame} / ${totalFrames}`;
    
    // Cập nhật FPS hiển thị
    const fpsDisplay = videoInfoBar.querySelector('#fps-display');
    if (fpsDisplay) {
      fpsDisplay.textContent = `FPS: ${frameRate.toFixed(2)}`;
    }

    // Đồng bộ overlay thông tin bên trái
    updateVideoInfoFromPlayer(elements.modalVideoPlayer, frameRate);
  };

  elements.modalVideoPlayer.addEventListener("timeupdate", updateFrameInfo);
  elements.modalVideoPlayer.addEventListener("loadedmetadata", updateFrameInfo);
  
  // Gọi ngay để hiển thị ban đầu
  if (elements.modalVideoPlayer.duration) {
    updateFrameInfo();
  }

  const handleFrameStep = (direction) => {
    elements.modalVideoPlayer.pause();
    const currentTime = elements.modalVideoPlayer.currentTime;
    // Di chuyển đúng 1 frame: 1/fps giây
    const oneFrameTime = 1.0 / frameRate;
    const newTime = currentTime + (direction * oneFrameTime);
    elements.modalVideoPlayer.currentTime = Math.max(0, Math.min(newTime, elements.modalVideoPlayer.duration || Infinity));
    updateFrameInfo();
    updateVideoInfoFromPlayer(elements.modalVideoPlayer, frameRate);
  };

  const prevBtn = document.getElementById("prev-frame-btn");
  const nextBtn = document.getElementById("next-frame-btn");
  const submitBtn = document.getElementById("modal-submit-btn");

  if (prevBtn) {
    prevBtn.onclick = () => handleFrameStep(-1);
  }
  if (nextBtn) {
    nextBtn.onclick = () => handleFrameStep(1);
  }
  
  // Submit button handler
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit Frame";
    submitBtn.onclick = async () => {
      if (!currentOpenVideoId) return;

      // Dừng video để tránh trôi khung hình khi xác nhận
      elements.modalVideoPlayer.pause();

      // Lấy frame hiện tại từ video player
      const currentFrame = getCurrentFrame();
      
      // Tính thời gian milliseconds
      // Formula: timeMs = (frame / fps) × 1000
      const timeSeconds = currentFrame / frameRate;
      const timeMs = Math.round(timeSeconds * 1000);

      // Hiển thị thông tin trước khi submit
      const confirmMsg = `Submit Frame ${currentFrame} (${timeSeconds.toFixed(2)}s = ${timeMs}ms) of video ${currentOpenVideoId}?`;
      if (!window.confirm(confirmMsg)) {
        return;
      }

      const sessionId = localStorage.getItem("sessionId");
      const evaluationId = localStorage.getItem("evaluationId");

      if (!sessionId || !evaluationId) {
        alert("Please connect first to submit!");
        return;
      }

      console.log('[SUBMIT] Modal submit:', {
        videoId: currentOpenVideoId,
        currentFrame,
        timeSeconds,
        timeMs,
        fps: frameRate
      });

      const previousText = "Submit Frame";

      try {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Submitting...';

        await submitResultAPI(
          sessionId,
          evaluationId,
          currentOpenVideoId,
          timeMs,
        );

        alert(`✅ Submit thành công!\nVideo: ${currentOpenVideoId}\nFrame: ${currentFrame}\nTime: ${timeMs}ms`);
        closeModal();  // Đóng modal sau khi submit thành công
      } catch (err) {
        alert(`❌ Submit thất bại: ${err.message}`);
      } finally {
        if (!elements.modalOverlay.classList.contains("hidden")) {
          submitBtn.disabled = false;
          submitBtn.textContent = previousText;
        }
      }
    };
  }

  const handleKeyPress = (e) => {
    if (elements.modalOverlay.classList.contains("hidden")) return;
    if (e.key === "ArrowLeft") handleFrameStep(-1);
    if (e.key === "ArrowRight") handleFrameStep(1);
    if (e.key === " ") {
      e.preventDefault();
      elements.modalVideoPlayer.paused
        ? elements.modalVideoPlayer.play()
        : elements.modalVideoPlayer.pause();
    }
    if (e.key === "Escape") closeModal();
  };
  document.addEventListener("keydown", handleKeyPress);

  // --- Store Handlers for Cleanup ---
  elements.modalOverlay.dataset.handlersAttached = "true";
  elements.modalOverlay._cleanupHandlers = {
    handleKeyPress,
    timelineBar,
    videoInfoBar,
    previewVideo,
    previewHls,
    mainHls, // LƯU MAIN HLS ĐỂ CLEANUP
    updateProgress,
    updateFrameInfo,
  };

  updateCleanupRefs();
}

export function closeModal() {
  if (elements.modalOverlay.classList.contains("hidden")) return;

  if (elements.modalOverlay.dataset.handlersAttached === "true") {
    const h = elements.modalOverlay._cleanupHandlers;
    if (h) {
      document.removeEventListener("keydown", h.handleKeyPress);
      if (h.timelineBar) h.timelineBar.remove();
      if (h.videoInfoBar) h.videoInfoBar.remove();

      elements.modalVideoPlayer.removeEventListener(
        "timeupdate",
        h.updateProgress,
      );
      elements.modalVideoPlayer.removeEventListener(
        "timeupdate",
        h.updateFrameInfo,
      );
      elements.modalVideoPlayer.removeEventListener(
        "loadedmetadata",
        h.updateFrameInfo,
      );

      // Destroy Preview HLS
      if (h.previewHls) h.previewHls.destroy();

      // Destroy Main Player HLS
      if (h.mainHls) {
        h.mainHls.destroy();
      }

      if (h.previewVideo) {
        h.previewVideo.removeAttribute("src");
        h.previewVideo.load();
        h.previewVideo.remove();
      }
    }
    delete elements.modalOverlay._cleanupHandlers;
    delete elements.modalOverlay.dataset.handlersAttached;
  }

  currentOpenVideoId = null;

  elements.modalOverlay.classList.add("hidden");
  elements.modalVideoPlayer.pause();
  elements.modalVideoPlayer.removeAttribute("src");
  elements.modalVideoPlayer.load();
}

/**
 * Update video info overlay
 */
function updateVideoInfo(videoId, frameIndex, timeSeconds, fps) {
  const currentVideoIdEl = document.getElementById('current-video-id');
  const currentFrameEl = document.getElementById('current-frame');
  const currentTimeEl = document.getElementById('current-time');
  const currentFpsEl = document.getElementById('current-fps');
  
  if (currentVideoIdEl) currentVideoIdEl.textContent = videoId || '-';
  if (currentFrameEl) currentFrameEl.textContent = frameIndex || '-';
  if (currentTimeEl) currentTimeEl.textContent = formatTime(timeSeconds || 0);
  if (currentFpsEl && fps) currentFpsEl.textContent = fps.toFixed(2);
}

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds) {
  if (seconds === undefined || seconds === null || isNaN(seconds)) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Update video info from current player state
 */
function updateVideoInfoFromPlayer(videoPlayer, fps) {
  const currentTime = videoPlayer.currentTime || 0;
  const currentFrame = Math.floor(currentTime * fps);
  
  const currentFrameEl = document.getElementById('current-frame');
  const currentTimeEl = document.getElementById('current-time');
  const currentFpsEl = document.getElementById('current-fps');
  
  if (currentFrameEl) currentFrameEl.textContent = currentFrame;
  if (currentTimeEl) currentTimeEl.textContent = formatTime(currentTime);
  if (currentFpsEl) currentFpsEl.textContent = fps.toFixed(2);
}
