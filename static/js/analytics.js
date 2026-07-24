/* ==========================================================================
   AURALAB - Historical Telemetry Analytics & SVG Sparkline Charts
   ========================================================================== */

const AnalyticsModule = (function () {
  let currentTimeframe = "hour";

  async function fetchAndRenderAnalytics(timeframe = "hour") {
    currentTimeframe = timeframe;
    try {
      const res = await fetch(`/api/analytics?timeframe=${timeframe}`);
      const data = await res.json();
      renderAnalyticsUI(data);
    } catch (err) {
      console.error("Error loading analytics:", err);
    }
  }

  function renderAnalyticsUI(data) {
    document.getElementById("an-avg-gpu").textContent = `${data.avg_gpu}%`;
    document.getElementById("an-peak-gpu").textContent = `${data.peak_gpu}%`;
    document.getElementById("an-avg-cpu").textContent = `${data.avg_cpu}%`;
    document.getElementById("an-avg-temp").textContent = `${data.avg_temp}°C`;
    document.getElementById("an-avg-ram").textContent = `${data.avg_ram}%`;
    document.getElementById("an-avg-health").textContent = `${data.avg_health}/100`;
    document.getElementById("an-total-alerts").textContent = data.total_alerts ?? 0;
    document.getElementById("an-most-active").textContent = data.most_active_pc;
    document.getElementById("an-least-active").textContent = data.least_active_pc;

    // Render SVG Line Charts
    renderGpuCpuChart(data.trends || []);
    renderTempRamChart(data.trends || []);
  }

  function renderGpuCpuChart(trends) {
    const container = document.getElementById("chart-gpu-svg-container");
    if (!container) return;

    if (trends.length < 2) {
      container.innerHTML = `<div style="color:var(--text-dim); font-size:0.8rem;">Gathering historical trend samples...</div>`;
      return;
    }

    const width = 500;
    const height = 160;
    const padding = 20;

    const gpuPoints = trends.map((t, idx) => {
      const x = padding + (idx / (trends.length - 1)) * (width - 2 * padding);
      const y = height - padding - (t.avg_gpu / 100) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(" ");

    const cpuPoints = trends.map((t, idx) => {
      const x = padding + (idx / (trends.length - 1)) * (width - 2 * padding);
      const y = height - padding - (t.avg_cpu / 100) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(" ");

    container.innerHTML = `
      <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <line x1="${padding}" y1="${height/2}" x2="${width-padding}" y2="${height/2}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4"/>
        <polyline fill="none" stroke="#3b82f6" stroke-width="2.5" points="${gpuPoints}" />
        <polyline fill="none" stroke="#06b6d4" stroke-width="2" stroke-dasharray="3" points="${cpuPoints}" />
        <text x="${padding}" y="${height - 5}" fill="#64748b" font-size="10">Avg GPU (Blue) vs CPU (Cyan)</text>
      </svg>
    `;
  }

  function renderTempRamChart(trends) {
    const container = document.getElementById("chart-temp-svg-container");
    if (!container) return;

    if (trends.length < 2) {
      container.innerHTML = `<div style="color:var(--text-dim); font-size:0.8rem;">Gathering historical trend samples...</div>`;
      return;
    }

    const width = 500;
    const height = 160;
    const padding = 20;

    const tempPoints = trends.map((t, idx) => {
      const x = padding + (idx / (trends.length - 1)) * (width - 2 * padding);
      const y = height - padding - (t.avg_temp / 100) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(" ");

    const ramPoints = trends.map((t, idx) => {
      const x = padding + (idx / (trends.length - 1)) * (width - 2 * padding);
      const y = height - padding - (t.avg_ram / 100) * (height - 2 * padding);
      return `${x},${y}`;
    }).join(" ");

    container.innerHTML = `
      <svg width="100%" height="100%" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none">
        <line x1="${padding}" y1="${height/2}" x2="${width-padding}" y2="${height/2}" stroke="rgba(255,255,255,0.05)" stroke-dasharray="4"/>
        <polyline fill="none" stroke="#f97316" stroke-width="2.5" points="${tempPoints}" />
        <polyline fill="none" stroke="#8b5cf6" stroke-width="2" stroke-dasharray="3" points="${ramPoints}" />
        <text x="${padding}" y="${height - 5}" fill="#64748b" font-size="10">Temp (Orange) vs RAM (Purple)</text>
      </svg>
    `;
  }

  return {
    fetchAndRenderAnalytics
  };
})();
