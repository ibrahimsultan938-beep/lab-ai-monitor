/* ==========================================================================
   AURALAB - Notification Drawer & Toast Alerts Controller
   ========================================================================== */

const NotificationsModule = (function () {
  let knownAlertIds = new Set();

  function renderNotificationList(notifications) {
    const listContainer = document.getElementById("notif-list");
    const badgeCounter = document.getElementById("notif-badge-count");
    if (!listContainer) return;

    badgeCounter.textContent = notifications.length;

    if (notifications.length === 0) {
      listContainer.innerHTML = `
        <div class="empty-notifs" style="text-align:center; padding:3rem 1rem; color:var(--text-muted);">
          <div style="font-size:2rem; margin-bottom:0.5rem;">🎉</div>
          <p>No critical system alerts.</p>
          <small>All cluster nodes operating normally.</small>
        </div>
      `;
      return;
    }

    listContainer.innerHTML = notifications.map(notif => `
      <div class="notif-card ${notif.severity.toLowerCase()}" id="notif-item-${notif.id}">
        <div class="notif-header">
          <div class="notif-title-row">
            <span class="severity-tag ${notif.severity.toLowerCase()}">${notif.severity}</span>
            <span class="notif-pc-name">${escapeHtml(notif.affected_pc)}</span>
          </div>
          <span class="notif-time">${notif.time}</span>
        </div>
        <div class="notif-desc"><strong>${escapeHtml(notif.title)}</strong>: ${escapeHtml(notif.description)}</div>
        <div class="notif-explanation">💡 <em>${escapeHtml(notif.explanation)}</em></div>
        <button class="btn-ack-notif" onclick="NotificationsModule.acknowledgeNotif(${notif.id})">Acknowledge</button>
      </div>
    `).join('');
  }

  function handleNewToasts(notifications) {
    notifications.forEach(notif => {
      if (!knownAlertIds.has(notif.id)) {
        knownAlertIds.add(notif.id);
        showToast(notif);
      }
    });
  }

  function showToast(notif) {
    const container = document.getElementById("toast-container");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast-item ${notif.severity.toLowerCase()}`;
    toast.id = `toast-${notif.id}`;
    
    toast.innerHTML = `
      <div class="toast-title">
        <span>🚨 ${escapeHtml(notif.title)} - ${escapeHtml(notif.affected_pc)}</span>
        <span style="font-size:0.75rem; color:var(--text-muted);">${notif.time}</span>
      </div>
      <div class="toast-body">${escapeHtml(notif.description)}</div>
    `;

    container.appendChild(toast);

    // Auto disappear after 6 seconds
    setTimeout(() => {
      toast.style.animation = "toast-slide-in 0.3s reverse ease";
      setTimeout(() => toast.remove(), 300);
    }, 6000);
  }

  async function acknowledgeNotif(id) {
    try {
      await fetch('/api/notifications/ack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: id })
      });
      const el = document.getElementById(`notif-item-${id}`);
      if (el) el.remove();
    } catch (err) {
      console.error("Error acknowledging notification:", err);
    }
  }

  function escapeHtml(str) {
    return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return {
    renderNotificationList,
    handleNewToasts,
    acknowledgeNotif
  };
})();
