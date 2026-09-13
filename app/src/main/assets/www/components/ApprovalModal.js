// ==========================================================================
// Approval Modal Component
// Universal confirmation dialog for consequential / destructive actions
// ==========================================================================

export function renderApprovalModal(title, message, riskLevel, onConfirmCallbackName) {
  const isDanger = riskLevel === 'R3_HIGH' || riskLevel === 'R4_CRITICAL';
  const badgeClass = isDanger ? 'badge-red' : 'badge-amber';
  const btnClass = isDanger ? 'hud-btn-danger' : 'hud-btn';

  return `
    <div id="approval-modal" class="hud-modal-overlay active">
      <div class="hud-modal-content" style="padding: 24px; max-width: 440px; margin: auto;">
        
        <!-- Header -->
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px;">
          <div>
            <span class="badge ${badgeClass}" style="margin-bottom: 6px;">
              <span class="material-symbols-outlined" style="font-size: 14px;">security</span>
              ${riskLevel || 'ACTION APPROVAL REQUIRED'}
            </span>
            <h3 style="font-size: 18px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">
              ${title}
            </h3>
          </div>
          <button onclick="window.jarvisApp.closeApprovalModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Description -->
        <div style="background: var(--surface-input); border: 1px solid rgba(0, 240, 255, 0.18); padding: 14px; margin-bottom: 20px; clip-path: var(--chamfer-clip-sm);">
          <p style="font-size: 13px; color: var(--text-secondary); line-height: 1.5;">
            ${message}
          </p>
        </div>

        <!-- Action Controls -->
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
          <button onclick="window.jarvisApp.closeApprovalModal()" class="hud-btn-ghost" style="flex: 1;">
            Cancel
          </button>
          <button onclick="${onConfirmCallbackName}()" class="${btnClass}" style="flex: 1.2;">
            Authorize
          </button>
        </div>
      </div>
    </div>
  `;
}
