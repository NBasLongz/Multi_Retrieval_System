import { appState, setSearchMode, setSession, clearState } from './appState.js';
import { searchAPI, loginAPI } from './api.js';
import { displayResults, initFilterDropdown } from './results.js';
import { initVideoModal } from './video-player.js';
import { updatePlaceholder, updateSearchPlaceholder } from './uiComponents.js';

document.addEventListener("DOMContentLoaded", () => {
  console.log('[MAIN] Application initializing...');
  
  // Initialize UI Logic
  initVideoModal();
  initFilterDropdown();

  // === LOGIN/CONNECTION LOGIC ===
  const loginBtn = document.getElementById('login-btn');
  const loginStatus = document.getElementById("login-status");
  const statusText = document.getElementById("status-text");
  const statusDetails = document.getElementById("status-details");

  // Kiểm tra connection status khi load trang
  const checkLoginStatus = () => {
    const sessionId = localStorage.getItem("sessionId");
    const evaluationId = localStorage.getItem("evaluationId");

    if (sessionId && evaluationId) {
      setSession(sessionId, evaluationId);
      loginBtn.classList.add("logged-in");
      loginBtn.textContent = `✓ Connected`;
      loginStatus.classList.remove("hidden");
      loginStatus.classList.add("logged-in");
      statusText.textContent = `Evaluation: ${evaluationId.substring(0, 20)}...`;
      statusDetails.textContent = `Session: ${sessionId.substring(0, 20)}...`;
    } else {
      setSession(null, null);
      loginBtn.classList.remove("logged-in");
      loginBtn.textContent = "Connect";
      loginStatus.classList.add("hidden");
      statusText.textContent = "Not connected";
      statusDetails.textContent = "";
    }
  };

  checkLoginStatus();

  if (loginBtn) {
    loginBtn.addEventListener("click", async () => {
      loginBtn.textContent = "Connecting...";
      loginBtn.disabled = true;
      try {
        console.log("[MAIN] Starting connection...");
        const data = await loginAPI();
        console.log("[MAIN] Connection successful, data:", data);
        console.log("[MAIN] SessionId:", data.sessionId);
        console.log("[MAIN] EvaluationId:", data.evaluationId);
        
        localStorage.setItem("sessionId", data.sessionId);
        localStorage.setItem("evaluationId", data.evaluationId);
        
        console.log("[MAIN] Stored in localStorage:");
        console.log("  sessionId:", localStorage.getItem("sessionId"));
        console.log("  evaluationId:", localStorage.getItem("evaluationId"));
        
        checkLoginStatus();
        alert(
          `Connected Successfully!\nEvaluation: ${data.evaluationId}\nSession: ${data.sessionId.substring(0, 30)}...`,
        );
      } catch (error) {
        console.error("[MAIN] Connection failed:", error);
        alert(`Connection Failed: ${error.message}`);
        loginBtn.textContent = "Connect";
        loginBtn.disabled = false;
      }
    });
  }

  // Disconnect khi click vào status
  if (loginStatus) {
    loginStatus.addEventListener("click", () => {
      if (confirm("Disconnect from server?")) {
        localStorage.removeItem("sessionId");
        localStorage.removeItem("evaluationId");
        checkLoginStatus();
      }
    });
  }

  // === SEARCH MODE TABS ===
  const tabBtns = document.querySelectorAll('.tab-btn');
  const searchInput = document.getElementById('main-query');

  tabBtns.forEach((btn) => {
    btn.addEventListener('click', () => {
      const mode = btn.dataset.mode;
      
      // Update active tab
      tabBtns.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');
      
      // Update app state
      setSearchMode(mode);
      
      // Clear results and reset filter
      clearState();
      const container = document.getElementById('results-container');
      container.innerHTML = '';
      container.classList.remove('has-results');
      
      // Update placeholders
      updatePlaceholder(mode);
      updateSearchPlaceholder(mode);
      
      // Reset filter
      const filterToggle = document.getElementById('filter-toggle');
      const filterLabel = filterToggle ? filterToggle.querySelector('.filter-label') : null;
      if (filterToggle) {
        filterToggle.disabled = true;
        if (filterLabel) filterLabel.textContent = 'Tất cả video';
      }
      
      // Clear search input
      if (searchInput) {
        searchInput.value = '';
        searchInput.focus();
      }
      
      console.log('[MAIN] Search mode changed to:', mode);
    });
  });

  // === SEARCH FORM HANDLER ===
  const searchForm = document.getElementById('search-form');
  const searchBtn = document.getElementById('search-btn');

  if (searchForm) {
    searchForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      
      const query = searchInput ? searchInput.value.trim() : '';
      if (!query) {
        alert('Vui lòng nhập từ khóa tìm kiếm');
        return;
      }

      const container = document.getElementById('results-container');
      container.innerHTML = '<div class="loading-content"><div class="loading-spinner"></div><p class="loading-text">Đang tìm kiếm...</p></div>';
      
      if (searchBtn) {
        searchBtn.disabled = true;
        searchBtn.textContent = 'Đang tìm...';
      }

      try {
        console.log('[MAIN] Searching:', { mode: appState.mode, query });
        
        // Prepare search data based on mode
        const searchData = {};
        if (appState.mode === 'visual') {
          searchData.description = query;
        } else if (appState.mode === 'transcript') {
          searchData.transcript = query;
        }

        // Call search API
        const results = await searchAPI(searchData);
        console.log('[MAIN] Search results:', results.length, 'items');
        
        // Display results
        displayResults(results);
        
      } catch (error) {
        console.error('[MAIN] Search failed:', error);
        container.innerHTML = `<div class="error-content"><div class="error-icon">⚠️</div><p class="error-text">Tìm kiếm thất bại: ${error.message}</p></div>`;
      } finally {
        if (searchBtn) {
          searchBtn.disabled = false;
          searchBtn.textContent = 'Tìm kiếm';
        }
      }
    });
  }

  console.log('[MAIN] Application initialized successfully');
});
