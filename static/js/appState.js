/**
 * Application State Management
 * Centralized state for the video retrieval system
 */

export const appState = {
  // Current search mode: 'visual' or 'transcript'
  mode: 'visual',
  
  // All search results from API
  allResults: [],
  
  // Filtered results based on video filter
  filteredResults: [],
  
  // Current selected video filter (null = all videos)
  selectedVideoId: null,
  
  // Video statistics for filter dropdown
  videoStats: new Map(), // videoId -> count
  
  // Current video player state
  currentVideo: {
    videoId: null,
    fps: 25,
    startSeconds: 0,
    keyframeIndex: 0,
  },
  
  // Login state
  session: {
    sessionId: null,
    evaluationId: null,
    connected: false,
  },
};

/**
 * Update search mode
 */
export function setSearchMode(mode) {
  if (mode !== 'visual' && mode !== 'transcript') {
    console.error('Invalid search mode:', mode);
    return;
  }
  appState.mode = mode;
  console.log('[State] Search mode changed to:', mode);
}

/**
 * Update search results and calculate video stats
 */
export function setSearchResults(results) {
  appState.allResults = results;
  appState.filteredResults = results;
  appState.selectedVideoId = null;
  
  // Calculate video statistics
  appState.videoStats.clear();
  results.forEach(item => {
    const videoId = item.video_id;
    const count = appState.videoStats.get(videoId) || 0;
    appState.videoStats.set(videoId, count + 1);
  });
  
  console.log('[State] Search results updated:', results.length, 'items');
  console.log('[State] Video stats:', Array.from(appState.videoStats.entries()));
}

/**
 * Filter results by video ID
 */
export function filterByVideo(videoId) {
  if (!videoId || videoId === 'all') {
    appState.selectedVideoId = null;
    appState.filteredResults = appState.allResults;
  } else {
    appState.selectedVideoId = videoId;
    appState.filteredResults = appState.allResults.filter(
      item => item.video_id === videoId
    );
  }
  
  console.log('[State] Filtered results:', appState.filteredResults.length, 'items');
  return appState.filteredResults;
}

/**
 * Get sorted list of videos for dropdown
 */
export function getVideoList() {
  return Array.from(appState.videoStats.entries())
    .sort((a, b) => {
      // Sort by video ID
      return a[0].localeCompare(b[0]);
    })
    .map(([videoId, count]) => ({ videoId, count }));
}

/**
 * Update current video player state
 */
export function setCurrentVideo(videoId, fps, startSeconds, keyframeIndex) {
  appState.currentVideo = {
    videoId,
    fps: fps || 25,
    startSeconds: startSeconds || 0,
    keyframeIndex: keyframeIndex || 0,
  };
  console.log('[State] Current video updated:', appState.currentVideo);
}

/**
 * Update session state
 */
export function setSession(sessionId, evaluationId) {
  appState.session = {
    sessionId,
    evaluationId,
    connected: !!(sessionId && evaluationId),
  };
  console.log('[State] Session updated:', appState.session);
}

/**
 * Clear all state
 */
export function clearState() {
  appState.allResults = [];
  appState.filteredResults = [];
  appState.selectedVideoId = null;
  appState.videoStats.clear();
  console.log('[State] State cleared');
}
