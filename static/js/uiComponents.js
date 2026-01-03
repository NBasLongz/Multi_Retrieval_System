/**
 * UI Components Module
 * Reusable UI component builders
 */

import { appState } from './appState.js';

/**
 * Create a result card element
 */
export function createResultCard(item) {
  const card = document.createElement('div');
  card.className = 'result-item';
  card.dataset.videoId = item.video_id;
  card.dataset.keyframeIndex = item.keyframe_index || 0;
  card.dataset.startSeconds = item.start_seconds || item.start || 0;  // Fallback to 'start' field
  card.dataset.fps = item.fps || 25;

  const mode = appState.mode;
  
  if (mode === 'visual') {
    // Visual search mode
    const fps = Number(item.fps) || 25;
    const frameNumber = item.frame_number || item.keyframe_index || 0;
    
    // Công thức: timeMs = (frame / fps) × 1000
    const timeSeconds = frameNumber / fps;
    const timeMs = Math.round(timeSeconds * 1000);
    
    card.innerHTML = `
      <img 
        src="/keyframes/${item.video_id}/keyframe_${item.keyframe_index}.webp" 
        alt="Keyframe ${item.keyframe_index}"
        class="result-thumbnail"
        loading="lazy"
      >
      <div class="result-info">
        <div class="result-title">${item.video_id}</div>
        <div class="result-meta">
          <span>Frame: ${frameNumber}</span>
          <span>Time: ${formatTime(timeSeconds)}</span>
          <span>FPS: ${fps.toFixed(2)}</span>
        </div>
        ${item.clip_score ? `<div class="result-score">Score: ${(item.clip_score * 100).toFixed(1)}%</div>` : ''}
      </div>
      <button class="submit-card-btn" data-video-id="${item.video_id}" data-time-ms="${timeMs}">
        Submit
      </button>
    `;
  } else {
    // Transcript search mode
    const startSeconds = item.start_seconds || item.start || 0;
    const fps = Number(item.fps) || 25;
    const timeMs = Math.round(startSeconds * 1000);
    
    card.innerHTML = `
      <img 
        src="/keyframes/${item.video_id}/keyframe_${item.keyframe_index || 0}.webp" 
        alt="${item.video_id}"
        class="result-thumbnail"
        loading="lazy"
      >
      <div class="result-info">
        <div class="result-title">${item.video_id}</div>
        <div class="result-meta">
          <span>Time: ${formatTime(startSeconds)}</span>
          <span>FPS: ${fps.toFixed(2)}</span>
        </div>
        ${item.transcript_text ? `<div class="result-transcript">"${truncateText(item.transcript_text, 100)}"</div>` : ''}
      </div>
      <button class="submit-card-btn" data-video-id="${item.video_id}" data-time-ms="${timeMs}">
        Submit
      </button>
    `;
  }

  return card;
}

/**
 * Create video filter dropdown item
 */
export function createFilterItem(videoId, count, isSelected = false) {
  const li = document.createElement('li');
  li.dataset.videoId = videoId;
  if (isSelected) {
    li.classList.add('selected');
  }
  
  li.innerHTML = `
    <span class="video-name">${videoId}</span>
    <span class="video-count">${count}</span>
  `;
  
  return li;
}

/**
 * Update placeholder content based on mode
 */
export function updatePlaceholder(mode) {
  const container = document.getElementById('results-container');
  const placeholderContent = container.querySelector('.placeholder-content');
  
  if (placeholderContent) {
    if (mode === 'visual') {
      placeholderContent.innerHTML = `
        <div class="placeholder-icon">🎬</div>
        <p class="placeholder-text">Nhập mô tả hình ảnh để tìm kiếm video.</p>
      `;
    } else {
      placeholderContent.innerHTML = `
        <div class="placeholder-icon">💬</div>
        <p class="placeholder-text">Nhập lời thoại/phụ đề để tìm kiếm video.</p>
      `;
    }
  }
}

/**
 * Update search input placeholder based on mode
 */
export function updateSearchPlaceholder(mode) {
  const input = document.getElementById('main-query');
  if (input) {
    if (mode === 'visual') {
      input.placeholder = 'Nhập mô tả hình ảnh...';
    } else {
      input.placeholder = 'Nhập lời thoại/âm thanh...';
    }
  }
}

/**
 * Show loading state
 */
export function showLoading(container) {
  container.innerHTML = `
    <div class="loading-content">
      <div class="loading-spinner"></div>
      <p class="loading-text">Đang tìm kiếm...</p>
    </div>
  `;
}

/**
 * Show error message
 */
export function showError(container, message) {
  container.innerHTML = `
    <div class="error-content">
      <div class="error-icon">⚠️</div>
      <p class="error-text">${message}</p>
    </div>
  `;
}

/**
 * Show empty results message
 */
export function showEmptyResults(container) {
  container.innerHTML = `
    <div class="empty-content">
      <div class="empty-icon">🔍</div>
      <p class="empty-text">Không tìm thấy kết quả phù hợp.</p>
    </div>
  `;
}

/**
 * Format seconds to MM:SS
 */
function formatTime(seconds) {
  if (seconds === undefined || seconds === null) return '00:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Truncate text to max length
 */
function truncateText(text, maxLength) {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
}

/**
 * Toggle dropdown visibility
 */
export function toggleDropdown(dropdown, toggle) {
  const isHidden = dropdown.classList.contains('hidden');
  
  if (isHidden) {
    dropdown.classList.remove('hidden');
    toggle.classList.add('open');
  } else {
    dropdown.classList.add('hidden');
    toggle.classList.remove('open');
  }
}

/**
 * Close dropdown
 */
export function closeDropdown(dropdown, toggle) {
  dropdown.classList.add('hidden');
  toggle.classList.remove('open');
}

/**
 * Update filter toggle label
 */
export function updateFilterLabel(videoId, count) {
  const toggle = document.getElementById('filter-toggle');
  const label = toggle.querySelector('.filter-label');
  
  if (!videoId || videoId === 'all') {
    label.textContent = 'Tất cả video';
  } else {
    label.textContent = `${videoId} (${count})`;
  }
}
