/* ==========================================================================
   AURALAB - PC Telemetry & Running Process Inspector Modal
   ========================================================================== */

const InspectorModule = (function () {
  let activePcId = null;

  function openInspector(pc) {
    activePcId = pc.id;
    updateInspectorUI(pc);
    document.getElementById("modal-pc-inspector").classList.remove("hidden");
  }

  function updateInspectorUI(pc) {
    if (!pc || (activePcId && pc.id !== activePcId)) return;

    document.getElementById("inspector-pc-name").textContent = pc.name;
    document.getElementById("inspector-location-text").textContent = `${pc.zone} • ${pc.location || 'Row 1 - Rack 01'}`;
    
    // Status badge
    const badge = document.getElementById("inspector-status-badge");
    badge.textContent = pc.health_badge || pc.status;
    badge.className = "badge-status";
    
    // Host tag
    const hostTag = document.getElementById("inspector-host-tag");
    if (pc.is_host) {
      hostTag.classList.remove("hidden");
    } else {
      hostTag.classList.add("hidden");
    }

    // Scores
    document.getElementById("inspector-health-score").textContent = pc.health_score ?? '--';
    document.getElementById("inspector-vram-avail").textContent = `${roundVal(pc.vram_total - pc.vram_used)} GB`;
    document.getElementById("inspector-smart-explanation").textContent = pc.ai_explanation || "Operating normally.";
    document.getElementById("inspector-last-updated").textContent = pc.last_updated || "--:--:--";

    // Gauges
    setGauge("gpu", pc.gpu_usage, "%");
    document.getElementById("inspector-gpu-model").textContent = pc.gpu_name || "NVIDIA GPU";

    setGauge("temp", pc.gpu_temp, "°C", 85);
    
    setGauge("vram", pc.vram_pct, "%");
    document.getElementById("gauge-vram-val").textContent = `${pc.vram_used} / ${pc.vram_total} GB`;
    document.getElementById("gauge-vram-pct").textContent = `${pc.vram_pct}% Capacity`;

    setGauge("cpu", pc.cpu_usage, "%");

    setGauge("ram", pc.ram_pct, "%");
    document.getElementById("gauge-ram-val").textContent = `${pc.ram_used} / ${pc.ram_total} GB`;
    document.getElementById("gauge-ram-pct").textContent = `${pc.ram_pct}% Capacity`;

    // Process list
    renderProcessTable(pc.processes || []);
  }

  function setGauge(type, val, unit, maxRef = 100) {
    const valEl = document.getElementById(`gauge-${type}-val`);
    const fillEl = document.getElementById(`progress-${type}-fill`);
    if (!fillEl) return;

    if (valEl && (type === 'gpu' || type === 'temp' || type === 'cpu')) {
      valEl.textContent = `${val}${unit}`;
    }

    const pct = Math.min(100, Math.max(0, (val / maxRef) * 100));
    fillEl.style.width = `${pct}%`;

    // Color fill class
    fillEl.className = "progress-fill";
    if (pct >= 85) fillEl.classList.add("fill-red");
    else if (pct >= 70) fillEl.classList.add("fill-orange");
    else if (pct >= 50) fillEl.classList.add("fill-yellow");
    else fillEl.classList.add("fill-green");
  }

  function renderProcessTable(processes) {
    const tbody = document.getElementById("inspector-process-rows");
    if (!tbody) return;

    if (processes.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center; color:var(--text-muted);">No active background workloads running.</td></tr>`;
      return;
    }

    tbody.innerHTML = processes.map(p => `
      <tr>
        <td style="color:var(--text-muted);">${p.pid}</td>
        <td style="font-weight:600; color:var(--text-main);">${escapeHtml(p.name)}</td>
        <td>${p.memory_mb} MB</td>
        <td style="color:var(--color-accent-cyan); font-weight:700;">${p.cpu_pct}%</td>
      </tr>
    `).join('');
  }

  function closeInspector() {
    activePcId = null;
    document.getElementById("modal-pc-inspector").classList.add("hidden");
  }

  function roundVal(v) {
    return Math.max(0, roundTo(v, 1));
  }

  function roundTo(num, dec) {
    return Math.round(num * Math.pow(10, dec)) / Math.pow(10, dec);
  }

  function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return {
    openInspector,
    updateInspectorUI,
    closeInspector,
    getActivePcId: () => activePcId
  };
})();
