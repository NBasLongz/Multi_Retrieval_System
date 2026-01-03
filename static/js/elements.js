export const elements = {
  searchForm: document.getElementById("search-form"),

  loginBtn: document.getElementById("login-btn"),

  // Results & Controls
  resultsContainer: document.getElementById("results-container"),
  // sortBySelect: Removed from HTML, so removing reference here prevents errors if accessed
  sortBySelect: { value: "clip_score" }, // Mock object to keep result.js working without refactor

  // Modal
  modalOverlay: document.getElementById("video-modal"),
  closeModalBtn: document.getElementById("close-modal-btn"),
  modalVideoPlayer: document.getElementById("modal-video-player"),
  modalContent: document.querySelector(".modal-content"),
};
