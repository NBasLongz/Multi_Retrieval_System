import { elements } from "./elements.js";

export async function searchAPI(queryData) {
  elements.resultsContainer.innerHTML = "<p>Searching...</p>";

  try {
    const response = await fetch("/search", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(queryData),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(
        errorData.error || `HTTP error! status: ${response.status}`,
      );
    }

    return await response.json();
  } catch (error) {
    console.error("Search failed:", error);
    elements.resultsContainer.innerHTML = `<p style="color: red;">An error occurred: ${error.message}</p>`;
    return [];
  }
}

export async function loginAPI() {
  try {
    console.log("[LOGIN] Sending request to /api/login");
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}), // Dùng default credentials trong config.py
    });

    console.log("[LOGIN] Response status:", response.status);
    console.log("[LOGIN] Response headers:", Object.fromEntries(response.headers.entries()));
    
    const data = await response.json();
    console.log("[LOGIN] Response data:", data);
    console.log("[LOGIN] SessionId:", data.sessionId);
    console.log("[LOGIN] SessionId type:", typeof data.sessionId);
    console.log("[LOGIN] SessionId length:", data.sessionId?.length);
    
    if (!response.ok) {
      throw new Error(data.error || "Login failed");
    }
    return data;
  } catch (error) {
    console.error("[LOGIN] Error:", error);
    throw error;
  }
}

export async function submitResultAPI(
  sessionId,
  evaluationId,
  videoId,
  timeMs,
) {
  try {
    const response = await fetch("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionId,
        evaluationId,
        videoId,
        timeMs,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Submit failed");
    }
    return data;
  } catch (error) {
    console.error("Submit error:", error);
    throw error;
  }
}
