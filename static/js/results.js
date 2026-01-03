/**
 * Results Display Module
 * Handles rendering and filtering of search results
 */

import { appState, getVideoList, filterByVideo, setSearchResults } from './appState.js';
import {
  createResultCard,
  createFilterItem,
  showLoading,
  showError,
  showEmptyResults,
  updateFilterLabel,
  toggleDropdown,
  closeDropdown,
} from './uiComponents.js';
import { openModal } from './video-player.js';
import { submitResultAPI } from './api.js';

/**
 * Display search results
 */
export function displayResults(results) {
  const container = document.getElementById('results-container');
  const filterToggle = document.getElementById('filter-toggle');
  const filterDropdown = document.getElementById('filter-dropdown');
  const filterList = document.getElementById('filter-list');

  container.innerHTML = '';
  container.classList.remove('has-results');

  if (!results || results.length === 0) {
    showEmptyResults(container);
    if (filterToggle) filterToggle.disabled = true;
    return;
  }

  // Update app state
  setSearchResults(results);

  // Render results
  container.classList.add('has-results');
  
  results.forEach((item) => {
    const card = createResultCard(item);
    container.appendChild(card);
  });

  // Setup card click handlers
  setupCardHandlers(container);

  // Enable and populate video filter
  if (filterToggle) {
    filterToggle.disabled = false;
    populateVideoFilter(filterList);
  }
}

/**
 * Populate video filter dropdown
 */
function populateVideoFilter(filterList) {
  if (!filterList) return;
  
  filterList.innerHTML = '';

  // Add "All videos" option
  const allItem = createFilterItem('all', appState.allResults.length, !appState.selectedVideoId);
  allItem.querySelector('.video-name').textContent = 'Tất cả video';
  filterList.appendChild(allItem);

  // Add individual video options
  const videoList = getVideoList();
  videoList.forEach(({ videoId, count }) => {
    const item = createFilterItem(
      videoId,
      count,
      appState.selectedVideoId === videoId
    );
    filterList.appendChild(item);
  });

  // Setup filter item click handlers
  filterList.querySelectorAll('li').forEach((li) => {
    li.addEventListener('click', () => {
      const videoId = li.dataset.videoId;
      handleFilterChange(videoId);
    });
  });
}

/**
 * Handle filter change
 */
function handleFilterChange(videoId) {
  const container = document.getElementById('results-container');
  const filterToggle = document.getElementById('filter-toggle');
  const filterDropdown = document.getElementById('filter-dropdown');

  // Filter results
  const filtered = filterByVideo(videoId);

  // Update filter label
  if (videoId === 'all') {
    updateFilterLabel(null, appState.allResults.length);
  } else {
    const count = appState.videoStats.get(videoId) || 0;
    updateFilterLabel(videoId, count);
  }

  // Re-render results
  container.innerHTML = '';
  filtered.forEach((item) => {
    const card = createResultCard(item);
    container.appendChild(card);
  });

  // Setup card handlers
  setupCardHandlers(container);

  // Close dropdown
  closeDropdown(filterDropdown, filterToggle);

  // Update filter list selection
  const filterList = document.getElementById('filter-list');
  filterList.querySelectorAll('li').forEach((li) => {
    if (li.dataset.videoId === videoId) {
      li.classList.add('selected');
    } else {
      li.classList.remove('selected');
    }
  });
}

/**
 * Setup card click and submit handlers
 */
function setupCardHandlers(container) {
  // Card click - open video modal
  container.querySelectorAll('.result-item').forEach((card) => {
    const thumbnail = card.querySelector('.result-thumbnail');
    const submitBtn = card.querySelector('.submit-card-btn');

    // Click on thumbnail/card opens modal
    if (thumbnail) {
      thumbnail.addEventListener('click', () => {
        const videoId = card.dataset.videoId;
        const startSeconds = parseFloat(card.dataset.startSeconds) || 0;
        const fps = parseFloat(card.dataset.fps) || 25;
        const keyframeIndex = parseInt(card.dataset.keyframeIndex) || 0;

        openModal(videoId, startSeconds, fps, keyframeIndex);
      });
    }

    // Submit button
    if (submitBtn) {
      submitBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        const videoId = submitBtn.dataset.videoId;
        const timeMs = parseInt(submitBtn.dataset.timeMs);

        console.log('[SUBMIT] Button clicked:', { videoId, timeMs, raw: submitBtn.dataset.timeMs });

        if (!videoId || isNaN(timeMs) || timeMs === null) {
          alert(`Invalid submit data: videoId=${videoId}, timeMs=${timeMs}`);
          console.error('[SUBMIT] Invalid data:', submitBtn.dataset);
          return;
        }

        const sessionId = localStorage.getItem("sessionId");
        const evaluationId = localStorage.getItem("evaluationId");

        if (!sessionId || !evaluationId) {
          alert("Please login first to submit!");
          return;
        }

        try {
          submitBtn.disabled = true;
          submitBtn.textContent = 'Submitting...';

          const res = await submitResultAPI(sessionId, evaluationId, videoId, timeMs);

          submitBtn.textContent = '✓ Submitted';
          submitBtn.style.background = '#4caf50';

          setTimeout(() => {
            submitBtn.disabled = false;
            submitBtn.textContent = 'Submit';
            submitBtn.style.background = '';
          }, 2000);
        } catch (error) {
          alert(`Submit failed: ${error.message}`);
          submitBtn.disabled = false;
          submitBtn.textContent = 'Submit';
        }
      });
    }
  });
}

/**
 * Initialize filter dropdown handlers
 */
export function initFilterDropdown() {
  const filterToggle = document.getElementById('filter-toggle');
  const filterDropdown = document.getElementById('filter-dropdown');
  const filterSearchInput = document.getElementById('filter-search-input');

  if (!filterToggle || !filterDropdown) return;

  // Toggle dropdown
  filterToggle.addEventListener('click', (e) => {
    e.stopPropagation();
    toggleDropdown(filterDropdown, filterToggle);
  });

  // Close dropdown when clicking outside
  document.addEventListener('click', (e) => {
    if (!filterDropdown.contains(e.target) && e.target !== filterToggle) {
      closeDropdown(filterDropdown, filterToggle);
    }
  });

  // Filter search
  if (filterSearchInput) {
    filterSearchInput.addEventListener('input', (e) => {
      const query = e.target.value.toLowerCase();
      const filterList = document.getElementById('filter-list');

      filterList.querySelectorAll('li').forEach((li) => {
        const videoId = li.dataset.videoId;
        const videoName = li.querySelector('.video-name').textContent.toLowerCase();

        if (videoId === 'all' || videoName.includes(query)) {
          li.style.display = '';
        } else {
          li.style.display = 'none';
        }
      });
    });
  }
}
