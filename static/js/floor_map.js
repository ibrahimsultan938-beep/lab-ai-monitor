/* ==========================================================================
   AURALAB - Interactive Lab Floor Map & PC Status Grid Renderer
   ========================================================================== */

const FloorMapModule = (function () {
  let currentZoneFilter = "all";
  let currentSearchQuery = "";
  let currentViewMode = "map";
  let cachedPcs = [];

  function renderFloorMap(pcs) {
    cachedPcs = pcs;
    const gridContainer = document.getElementById("floor-map-grid");
    if (!gridContainer) return;

    let filtered = pcs;
    if (currentZoneFilter !== "all") {
      filtered = filtered.filter(p => p.zone === currentZoneFilter);
    }
    if (currentSearchQuery) {
      const q = currentSearchQuery.toLowerCase();
      filtered = filtered.filter(p => 
        p.name.toLowerCase().includes(q) ||
        p.gpu_name.toLowerCase().includes(q) ||
        p.status.toLowerCase().includes(q) ||
        p.zone.toLowerCase().includes(q)
      );
    }

    updateHeaderCounters(pcs);

    if (filtered.length === 0) {
      gridContainer.innerHTML = `<div style="grid-column:1/-1; text-align:center; padding:4rem; color:var(--text-muted);">No PC nodes found matching current filters.</div>`;
      return;
    }

    if (currentViewMode === "map" && currentZoneFilter === "all" && !currentSearchQuery) {
      gridContainer.innerHTML = renderZoneGroupedCards(pcs);
    } else {
      gridContainer.innerHTML = filtered.map(pc => renderPcCardHtml(pc)).join('');
    }

    const cards = gridContainer.querySelectorAll(".pc-card");
    cards.forEach(card => {
      card.addEventListener("click", () => {
        const pcId = card.getAttribute("data-pc-id");
        const pc = cachedPcs.find(p => p.id === pcId);
        if (pc) {
          InspectorModule.openInspector(pc);
        }
      });
    });
  }

  function renderZoneGroupedCards(pcs) {
    const zones = [
      "Zone A (Training Cluster)",
      "Zone B (Inference Racks)",
      "Zone C (Student Workstations)",
      "Zone D (Edge AI Nodes)"
    ];

    let html = "";
    zones.forEach(zoneName => {
      const zonePcs = pcs.filter(p => p.zone === zoneName);
      if (zonePcs.length === 0) return;

      html += `
        <div class="zone-divider">
          <span class="zone-divider-title">📍 ${zoneName}</span>
          <span style="font-size:0.75rem; color:var(--text-muted); font-family:var(--font-mono);">${zonePcs.length} Nodes</span>
        </div>
      `;
      html += zonePcs.map(pc => renderPcCardHtml(pc)).join('');
    });
    return html;
  }

  function renderPcCardHtml(pc) {
    const statusClass = `status-${pc.status.toLowerCase()}`;
    const gpuFillClass = getFillClass(pc.gpu_usage);
    const tempFillClass = getFillClass((pc.gpu_temp / 85) * 100);

    return `
      <div class="pc-card ${statusClass}" data-pc-id="${pc.id}" style="--card-accent-color: ${pc.health_color || '#10b981'}; --card-glow-color: ${pc.health_color}33;">
        <div class="pc-card-header">
          <div class="pc-name-group">
            <div class="pc-title">
              ${escapeHtml(pc.name)}
              ${pc.is_host ? '<span class="host-badge-tiny">HOST HARDWARE</span>' : ''}
            </div>
            <div class="pc-gpu-spec">${escapeHtml(pc.gpu_name)}</div>
          </div>
          <div class="pc-health-badge">
            ${pc.health_badge || pc.status}
          </div>
        </div>

        <div class="pc-rec-ratings-row">
          <div class="rec-rating-item">
            <span>AI Rec:</span>
            <strong>${pc.rec_score ?? 85}/100</strong>
          </div>
          <div class="rec-rating-item">
            <span>Conf:</span>
            <strong style="color:var(--color-accent-purple);">${pc.confidence ?? 95}%</strong>
          </div>
          <div class="rec-rating-item" style="color:var(--text-dim);">
            🕒 <span>${pc.last_updated || 'Live'}</span>
          </div>
        </div>

        <div class="pc-metrics-mini">
          <div class="metric-box-mini">
            <div class="metric-title-mini">
              <span>GPU Usage</span>
              <span style="font-family:var(--font-mono);">${pc.gpu_usage}%</span>
            </div>
            <div class="mini-bar-track">
              <div class="mini-bar-fill ${gpuFillClass}" style="width: ${pc.gpu_usage}%;"></div>
            </div>
          </div>

          <div class="metric-box-mini">
            <div class="metric-title-mini">
              <span>GPU Temp</span>
              <span style="font-family:var(--font-mono);">${pc.gpu_temp}°C</span>
            </div>
            <div class="mini-bar-track">
              <div class="mini-bar-fill ${tempFillClass}" style="width: ${Math.min(100, (pc.gpu_temp / 85) * 100)}%;"></div>
            </div>
          </div>

          <div class="metric-box-mini">
            <div class="metric-title-mini">
              <span>CPU Load</span>
              <span style="font-family:var(--font-mono);">${pc.cpu_usage}%</span>
            </div>
            <div class="mini-bar-track">
              <div class="mini-bar-fill ${getFillClass(pc.cpu_usage)}" style="width: ${pc.cpu_usage}%;"></div>
            </div>
          </div>

          <div class="metric-box-mini">
            <div class="metric-title-mini">
              <span>RAM Used</span>
              <span style="font-family:var(--font-mono);">${pc.ram_pct}%</span>
            </div>
            <div class="mini-bar-track">
              <div class="mini-bar-fill ${getFillClass(pc.ram_pct)}" style="width: ${pc.ram_pct}%;"></div>
            </div>
          </div>
        </div>

        <div class="pc-card-footer">
          <div class="click-hint">
            <span>🔍 Inspect PC</span>
          </div>
          <div class="score-pill">
            Health: <span style="color:${pc.health_color};">${pc.health_score ?? '--'}</span>
          </div>
        </div>
      </div>
    `;
  }

  function updateHeaderCounters(pcs) {
    const total = pcs.length;
    const healthy = pcs.filter(p => p.status === "Healthy").length;
    const moderate = pcs.filter(p => p.status === "Moderate").length;
    const heavy = pcs.filter(p => p.status === "Heavy").length;
    const critical = pcs.filter(p => p.status === "Critical").length;

    document.getElementById("stat-total-pcs").textContent = total;
    document.getElementById("stat-healthy-pcs").textContent = healthy;
    document.getElementById("stat-moderate-pcs").textContent = moderate;
    document.getElementById("stat-heavy-pcs").textContent = heavy;
    document.getElementById("stat-critical-pcs").textContent = critical;
  }

  function getFillClass(pct) {
    if (pct >= 85) return "fill-red";
    if (pct >= 70) return "fill-orange";
    if (pct >= 50) return "fill-yellow";
    return "fill-green";
  }

  function setZoneFilter(zone) {
    currentZoneFilter = zone;
    renderFloorMap(cachedPcs);
  }

  function setSearchQuery(q) {
    currentSearchQuery = q;
    renderFloorMap(cachedPcs);
  }

  function setViewMode(mode) {
    currentViewMode = mode;
    renderFloorMap(cachedPcs);
  }

  function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return {
    renderFloorMap,
    setZoneFilter,
    setSearchQuery,
    setViewMode
  };
})();
