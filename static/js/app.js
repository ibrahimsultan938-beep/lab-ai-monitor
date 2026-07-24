/* ==========================================================================
   AURALAB - Main Application Entrypoint & WebSocket Manager
   Developed for AI Innovation Hackathon 2026 by Team DIU_Elite_Noob
   ========================================================================== */

document.addEventListener("DOMContentLoaded", () => {
  console.log("Initializing AuraLab AI Cluster Dashboard...");

  initWebSocket();
  initEventListeners();

  // Live Header Clock (Updates every second)
  setInterval(updateHeaderClock, 1000);
  updateHeaderClock();

  // Load initial analytics for Last Hour
  AnalyticsModule.fetchAndRenderAnalytics("hour");
});

let socket = null;

function updateHeaderClock() {
  const clockEl = document.getElementById("header-clock");
  if (clockEl) {
    const now = new Date();
    const timeStr = new Intl.DateTimeFormat("en-GB", {
      timeZone: "Asia/Dhaka",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false
    }).format(now);
    clockEl.textContent = timeStr;
  }
}

function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws`;

  const statusText = document.getElementById("ws-status-text");

  socket = new WebSocket(wsUrl);

  socket.onopen = () => {
    console.log("WebSocket connected to live telemetry stream.");
    if (statusText) {
      statusText.textContent = "WS Connected";
      statusText.parentElement.style.borderColor = "rgba(16, 185, 129, 0.4)";
    }
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.type === "TELEMETRY_UPDATE") {
        // 1. Render floor map & PC cards
        FloorMapModule.renderFloorMap(data.pcs);

        // 2. Update notification drawer & toasts
        NotificationsModule.renderNotificationList(data.notifications || []);
        NotificationsModule.handleNewToasts(data.notifications || []);

        // 3. Update inspector if modal is open
        const activeInspectorPcId = InspectorModule.getActivePcId();
        if (activeInspectorPcId) {
          const currentPc = data.pcs.find(p => p.id === activeInspectorPcId);
          if (currentPc) {
            InspectorModule.updateInspectorUI(currentPc);
          }
        }

        // 4. Update Safe Demo Mode button UI
        updateSafeDemoBtnState(data.demo_mode_active);
      }
    } catch (err) {
      console.error("Error processing WebSocket message:", err);
    }
  };

  socket.onerror = (err) => {
    console.error("WebSocket error:", err);
    if (statusText) {
      statusText.textContent = "WS Offline";
      statusText.parentElement.style.borderColor = "rgba(239, 68, 68, 0.4)";
    }
  };

  socket.onclose = () => {
    console.warn("WebSocket closed. Attempting reconnect in 3 seconds...");
    if (statusText) {
      statusText.textContent = "Reconnecting...";
    }
    setTimeout(initWebSocket, 3000);
  };
}

function initEventListeners() {
  // Live Search Input Listener
  const searchInput = document.getElementById("pc-search-input");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      FloorMapModule.setSearchQuery(e.target.value.trim());
    });
  }

  // One-Click Best GPU Finder Button
  const btnFinder = document.getElementById("btn-open-finder");
  if (btnFinder) {
    btnFinder.addEventListener("click", () => FinderModule.openFinderModal());
  }

  const btnCloseFinder = document.getElementById("btn-close-finder");
  if (btnCloseFinder) {
    btnCloseFinder.addEventListener("click", () => FinderModule.closeFinderModal());
  }

  // Inspector Close Button
  const btnCloseInspector = document.getElementById("btn-close-inspector");
  if (btnCloseInspector) {
    btnCloseInspector.addEventListener("click", () => InspectorModule.closeInspector());
  }

  // Notification Bell Toggle
  const btnNotifs = document.getElementById("btn-toggle-notifs");
  const drawer = document.getElementById("notif-drawer");
  if (btnNotifs && drawer) {
    btnNotifs.addEventListener("click", () => drawer.classList.toggle("hidden"));
  }

  const btnCloseNotif = document.getElementById("btn-close-notif");
  if (btnCloseNotif && drawer) {
    btnCloseNotif.addEventListener("click", () => drawer.classList.add("hidden"));
  }

  // Zone Filter Buttons
  const zoneBtns = document.querySelectorAll(".zone-btn");
  zoneBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      zoneBtns.forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      const zone = e.target.getAttribute("data-zone");
      FloorMapModule.setZoneFilter(zone);
    });
  });

  // View Mode Buttons (Map vs Grid)
  const viewMapBtn = document.getElementById("view-map");
  const viewGridBtn = document.getElementById("view-grid");

  if (viewMapBtn && viewGridBtn) {
    viewMapBtn.addEventListener("click", () => {
      viewMapBtn.classList.add("active");
      viewGridBtn.classList.remove("active");
      FloorMapModule.setViewMode("map");
    });

    viewGridBtn.addEventListener("click", () => {
      viewGridBtn.classList.add("active");
      viewMapBtn.classList.remove("active");
      FloorMapModule.setViewMode("grid");
    });
  }

  // Analytics Timeframe Buttons (Last Hour vs Last 24 Hours vs Last 7 Days)
  const timeBtns = document.querySelectorAll(".time-btn");
  timeBtns.forEach(btn => {
    btn.addEventListener("click", (e) => {
      timeBtns.forEach(b => b.classList.remove("active"));
      e.target.classList.add("active");
      const timeframe = e.target.getAttribute("data-timeframe");
      AnalyticsModule.fetchAndRenderAnalytics(timeframe);
    });
  });

  // SAFE DEMO MODE Button
  const btnDemo = document.getElementById("btn-demo-mode");
  if (btnDemo) {
    btnDemo.addEventListener("click", async () => {
      try {
        const res = await fetch('/api/demomode', { method: 'POST' });
        const data = await res.json();
        updateSafeDemoBtnState(data.demo_mode_active);
      } catch (err) {
        console.error("Error toggling Safe Demo Mode:", err);
      }
    });
  }
}

function updateSafeDemoBtnState(isActive) {
  const btn = document.getElementById("btn-demo-mode");
  const btnText = document.getElementById("demo-btn-text");
  if (!btn || !btnText) return;

  if (isActive) {
    btn.style.background = "rgba(239, 68, 68, 0.25)";
    btn.style.borderColor = "var(--color-critical)";
    btnText.textContent = "🛡️ DEMO ALERT ACTIVE (Click to Reset)";
  } else {
    btn.style.background = "rgba(16, 185, 129, 0.15)";
    btn.style.borderColor = "rgba(16, 185, 129, 0.4)";
    btnText.textContent = "Safe Demo Mode";
  }
}
