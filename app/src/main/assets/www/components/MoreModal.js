// ==========================================================================
// More Tools Drawer / Sheet Component
// Exposes Code, Devices, Files, Memory, Settings, and Integrations
// ==========================================================================

export function renderMoreModal() {
  const tools = [
    { id: 'code', label: 'Code Assistant', icon: 'terminal', desc: 'Workspaces, patches, tests' },
    { id: 'devices', label: 'Smart Devices', icon: 'home_iot_device', desc: 'Lighting, climate, sensors' },
    { id: 'files', label: 'Files Workspace', icon: 'folder_open', desc: 'Secure local storage' },
    { id: 'memory', label: 'Personal Memory', icon: 'psychology', desc: 'Saved preferences & facts' },
    { id: 'integrations', label: 'Integrations', icon: 'hub', desc: 'Providers & API gateways' },
    { id: 'settings', label: 'Settings', icon: 'tune', desc: 'Audio, haptics, theme glow' }
  ];

  return `
    <div id="more-modal" class="hud-modal-overlay">
      <div class="hud-modal-content" style="padding: 20px 16px 28px 16px;">
        
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">EXTENDED SUB-ROUTINES</span>
            <h3 class="hud-title" style="font-size: 16px; margin-top: 2px;">Tools & Modules</h3>
          </div>
          <button onclick="window.jarvisApp.closeMoreModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Tool Grid -->
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
          ${tools.map(tool => `
            <button onclick="window.jarvisApp.openMoreScreen('${tool.id}')" class="hud-panel" style="
              text-align: left;
              background: var(--surface-card);
              border: 1px solid rgba(0, 240, 255, 0.2);
              padding: 12px;
              cursor: pointer;
              display: flex;
              flex-direction: column;
              gap: 6px;
            ">
              <div style="display: flex; align-items: center; justify-content: space-between;">
                <span class="material-symbols-outlined" style="font-size: 24px; color: var(--cyan-core);">
                  ${tool.icon}
                </span>
                <span class="label-caps" style="font-size: 8px;">ACTIVE</span>
              </div>
              <span style="font-size: 13px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">
                ${tool.label}
              </span>
              <span style="font-size: 11px; color: var(--text-muted); line-height: 1.2;">
                ${tool.desc}
              </span>
            </button>
          `).join('')}
        </div>
      </div>
    </div>
  `;
}
