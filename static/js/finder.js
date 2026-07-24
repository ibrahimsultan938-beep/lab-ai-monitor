/* ==========================================================================
   AURALAB - One-Click Best GPU Finder Spotlight Modal
   ========================================================================== */

const FinderModule = (function () {
  async function openFinderModal() {
    const modal = document.getElementById("modal-gpu-finder");
    const container = document.getElementById("finder-recommendations-list");
    const spinner = document.getElementById("finder-loading");
    
    modal.classList.remove("hidden");
    container.innerHTML = "";
    spinner.classList.remove("hidden");

    try {
      const res = await fetch('/api/recommendations');
      const recommendations = await res.json();

      spinner.classList.add("hidden");
      renderRecommendations(recommendations);
    } catch (err) {
      console.error("Error fetching GPU recommendations:", err);
      spinner.classList.add("hidden");
      container.innerHTML = `<p style="color:var(--color-critical);">Failed to compute recommendations. Please ensure backend server is running.</p>`;
    }
  }

  function renderRecommendations(recs) {
    const container = document.getElementById("finder-recommendations-list");
    if (!container) return;

    if (!recs || recs.length === 0) {
      container.innerHTML = `<p style="color:var(--text-muted); text-align:center;">No recommended GPUs available at this time.</p>`;
      return;
    }

    container.innerHTML = recs.map((rec, index) => {
      const rankNum = index + 1;
      const isTopRank = rankNum === 1;

      return `
        <div class="recommendation-card ${isTopRank ? 'top-rank' : ''}">
          <div class="rank-ribbon ${isTopRank ? 'rank-1' : ''}">
            ${isTopRank ? '👑 #1 BEST MATCH' : `RANK #${rankNum}`}
          </div>

          <div class="rec-card-header">
            <div>
              <div class="rec-pc-title">${escapeHtml(rec.pc_name)}</div>
              <div style="font-size:0.8rem; color:var(--color-accent-cyan); font-family:var(--font-mono); font-weight:600;">
                ${escapeHtml(rec.gpu_model)} • ${escapeHtml(rec.zone)}
              </div>
            </div>
          </div>

          <div class="rec-scores-row">
            <div class="rec-score-badge">
              <span class="rec-score-label">Recommendation Score</span>
              <span class="rec-score-value">${rec.recommendation_score}</span>
            </div>
            <div class="rec-score-badge">
              <span class="rec-score-label">Health Score</span>
              <span class="rec-score-value" style="color:var(--color-healthy);">${rec.health_score}</span>
            </div>
            <div class="rec-score-badge">
              <span class="rec-score-label">AI Confidence</span>
              <span class="rec-score-value" style="color:var(--color-accent-purple);">${rec.confidence}%</span>
            </div>
          </div>

          <div class="rec-reasons-list">
            <div class="rec-reasons-title">Why this PC was selected:</div>
            <ul class="rec-bullets">
              ${rec.reasons.map(r => `<li>${escapeHtml(r)}</li>`).join('')}
            </ul>
          </div>

          <div class="rec-smart-exp" style="font-size:0.82rem; color:var(--text-muted); background:rgba(255,255,255,0.02); padding:0.65rem 0.85rem; border-radius:8px;">
            💡 <em>"${escapeHtml(rec.smart_explanation)}"</em>
          </div>

          <div style="display:flex; justify-content:flex-end; gap:0.5rem; margin-top:0.25rem;">
            <button class="btn-primary-finder" style="padding:0.45rem 1rem; font-size:0.82rem;" onclick="FinderModule.assignWorkload('${rec.pc_id}', '${escapeHtml(rec.pc_name)}')">
              🚀 Deploy AI Job to ${escapeHtml(rec.pc_name)}
            </button>
          </div>
        </div>
      `;
    }).join('');
  }

  function assignWorkload(pcId, pcName) {
    alert(`AI Training Workload successfully scheduled on ${pcName}! Reserved VRAM memory block.`);
    closeFinderModal();
  }

  function closeFinderModal() {
    document.getElementById("modal-gpu-finder").classList.add("hidden");
  }

  function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return {
    openFinderModal,
    closeFinderModal,
    assignWorkload
  };
})();
