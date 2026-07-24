/**
 * AuraLab Admin Panel JavaScript Module
 * Handles Node Management (Add, Edit, Delete, Zone/Threshold change)
 * and Connected Agents Monitoring (UUID, Heartbeat, IP).
 */

document.addEventListener('DOMContentLoaded', () => {
  const btnOpenAdmin = document.getElementById('btn-open-admin');
  const modalAdmin = document.getElementById('modal-admin-panel');
  const btnCloseAdmin = document.getElementById('btn-close-admin');

  const tabPcsBtn = document.getElementById('admin-tab-pcs-btn');
  const tabAgentsBtn = document.getElementById('admin-tab-agents-btn');
  const tabPcsContent = document.getElementById('admin-tab-pcs');
  const tabAgentsContent = document.getElementById('admin-tab-agents');

  const adminPcsTableBody = document.getElementById('admin-pcs-tbody');
  const adminAgentsTableBody = document.getElementById('admin-agents-tbody');

  const btnAddPcModal = document.getElementById('btn-admin-add-pc');
  const formPc = document.getElementById('admin-pc-form');
  const formModal = document.getElementById('modal-admin-pc-form');
  const btnCloseForm = document.getElementById('btn-close-pc-form');
  const btnCancelForm = document.getElementById('btn-cancel-pc-form');
  const formTitle = document.getElementById('admin-pc-form-title');

  let editingPcId = null;

  if (btnOpenAdmin) {
    btnOpenAdmin.addEventListener('click', () => {
      openAdminModal();
    });
  }

  if (btnCloseAdmin) {
    btnCloseAdmin.addEventListener('click', () => {
      modalAdmin.classList.add('hidden');
    });
  }

  // Tab switching
  if (tabPcsBtn && tabAgentsBtn) {
    tabPcsBtn.addEventListener('click', () => {
      tabPcsBtn.classList.add('active');
      tabAgentsBtn.classList.remove('active');
      tabPcsContent.classList.add('active');
      tabAgentsContent.classList.remove('active');
      loadAdminPcs();
    });

    tabAgentsBtn.addEventListener('click', () => {
      tabAgentsBtn.classList.add('active');
      tabPcsBtn.classList.remove('active');
      tabAgentsContent.classList.add('active');
      tabPcsContent.classList.remove('active');
      loadAdminAgents();
    });
  }

  function openAdminModal() {
    modalAdmin.classList.remove('hidden');
    loadAdminPcs();
    loadAdminAgents();
  }

  async function loadAdminPcs() {
    try {
      const res = await fetch('/api/admin/pcs');
      const pcs = await res.json();
      renderAdminPcs(pcs);
    } catch (e) {
      console.error('Failed to load admin PCs:', e);
    }
  }

  function renderAdminPcs(pcs) {
    if (!adminPcsTableBody) return;
    adminPcsTableBody.innerHTML = pcs.map(p => `
      <tr>
        <td><strong>${p.id}</strong></td>
        <td>${p.name}</td>
        <td><span class="badge-status" style="background:rgba(59,130,246,0.15); color:#60a5fa; border:1px solid rgba(59,130,246,0.3); padding:0.2rem 0.5rem; border-radius:4px; font-size:0.75rem;">${p.zone}</span></td>
        <td>${p.gpu_name || 'NVIDIA GPU'}</td>
        <td>${p.vram_total} GB</td>
        <td>${p.ram_total} GB</td>
        <td><strong style="color:#f59e0b;">${p.temp_threshold || 85}°C</strong></td>
        <td>${p.uuid ? `<code style="font-size:0.7rem; color:#a78bfa;">${p.uuid.substring(0,8)}...</code>` : '<span style="color:#64748b;">Simulated / Pending</span>'}</td>
        <td>
          <button class="btn-action-sm edit" onclick="window.editAdminPc('${p.id}')">✏️ Edit</button>
          <button class="btn-action-sm delete" onclick="window.deleteAdminPc('${p.id}')">🗑️ Delete</button>
        </td>
      </tr>
    `).join('');
  }

  async function loadAdminAgents() {
    try {
      const res = await fetch('/api/admin/agents');
      const agents = await res.json();
      renderAdminAgents(agents);
    } catch (e) {
      console.error('Failed to load admin agents:', e);
    }
  }

  function renderAdminAgents(agents) {
    if (!adminAgentsTableBody) return;
    if (agents.length === 0) {
      adminAgentsTableBody.innerHTML = `
        <tr>
          <td colspan="6" style="text-align:center; color:#94a3b8; padding:2rem;">
            📡 No remote telemetry agents pinging currently.<br>
            <span style="font-size:0.8rem;">Run <code>python telemetry_agent.py --server http://&lt;SERVER_IP&gt;:8000 --pc-id PC-02</code> on remote PCs to connect live agents.</span>
          </td>
        </tr>
      `;
      return;
    }

    adminAgentsTableBody.innerHTML = agents.map(a => `
      <tr>
        <td><code style="color:#a78bfa;">${a.uuid}</code></td>
        <td><strong>${a.pc_id}</strong></td>
        <td>${a.client_ip}</td>
        <td>${a.gpu_name} (${a.gpu_temp}°C, ${a.gpu_usage}%)</td>
        <td>${a.last_seen}</td>
        <td>
          <span class="badge-status ${a.status === 'Online' ? 'badge-healthy' : 'badge-critical'}" style="padding:0.2rem 0.6rem; border-radius:4px; font-weight:700; font-size:0.75rem;">
            ${a.status === 'Online' ? '🟢 Online' : '⚫ Offline'}
          </span>
        </td>
      </tr>
    `).join('');
  }

  // Add PC Button
  if (btnAddPcModal) {
    btnAddPcModal.addEventListener('click', () => {
      editingPcId = null;
      formTitle.innerText = '➕ Add New PC Node';
      formPc.reset();
      document.getElementById('input-pc-id').readOnly = false;
      document.getElementById('input-temp-threshold').value = '85';
      formModal.classList.remove('hidden');
    });
  }

  if (btnCloseForm) {
    btnCloseForm.addEventListener('click', () => formModal.classList.add('hidden'));
  }
  if (btnCancelForm) {
    btnCancelForm.addEventListener('click', () => formModal.classList.add('hidden'));
  }

  // Window edit & delete handlers
  window.editAdminPc = async (pcId) => {
    try {
      const res = await fetch('/api/admin/pcs');
      const pcs = await res.json();
      const target = pcs.find(p => p.id === pcId);
      if (!target) return;

      editingPcId = pcId;
      formTitle.innerText = `✏️ Edit PC Node (${pcId})`;
      document.getElementById('input-pc-id').value = target.id;
      document.getElementById('input-pc-id').readOnly = true;
      document.getElementById('input-pc-name').value = target.name || target.id;
      document.getElementById('input-pc-zone').value = target.zone || 'Zone A (Training Cluster)';
      document.getElementById('input-pc-location').value = target.location || '';
      document.getElementById('input-pc-gpu').value = target.gpu_name || '';
      document.getElementById('input-pc-vram').value = target.vram_total || 8.0;
      document.getElementById('input-pc-ram').value = target.ram_total || 16.0;
      document.getElementById('input-temp-threshold').value = target.temp_threshold || 85;

      formModal.classList.remove('hidden');
    } catch (e) {
      console.error('Failed to edit PC:', e);
    }
  };

  window.deleteAdminPc = async (pcId) => {
    if (!confirm(`Are you sure you want to remove ${pcId} from the cluster?`)) return;
    try {
      const res = await fetch(`/api/admin/pcs/${pcId}`, { method: 'DELETE' });
      if (res.ok) {
        loadAdminPcs();
      } else {
        alert('Failed to delete PC');
      }
    } catch (e) {
      console.error('Error deleting PC:', e);
    }
  };

  // Form Submission
  if (formPc) {
    formPc.addEventListener('submit', async (e) => {
      e.preventDefault();
      const pcId = document.getElementById('input-pc-id').value.trim();
      const name = document.getElementById('input-pc-name').value.trim() || pcId;
      const zone = document.getElementById('input-pc-zone').value;
      const location = document.getElementById('input-pc-location').value.trim();
      const gpu_name = document.getElementById('input-pc-gpu').value.trim() || 'NVIDIA GPU';
      const vram_total = parseFloat(document.getElementById('input-pc-vram').value) || 8.0;
      const ram_total = parseFloat(document.getElementById('input-pc-ram').value) || 16.0;
      const temp_threshold = parseInt(document.getElementById('input-temp-threshold').value) || 85;

      const payload = { id: pcId, name, zone, location, gpu_name, vram_total, ram_total, temp_threshold };

      try {
        let res;
        if (editingPcId) {
          res = await fetch(`/api/admin/pcs/${editingPcId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        } else {
          res = await fetch('/api/admin/pcs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          });
        }

        if (res.ok) {
          formModal.classList.add('hidden');
          loadAdminPcs();
        } else {
          const err = await res.json();
          alert(`Error: ${err.error || 'Failed to save PC configuration'}`);
        }
      } catch (err) {
        console.error('Form submission error:', err);
      }
    });
  }
});
