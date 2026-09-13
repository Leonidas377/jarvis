// ==========================================================================
// Integrations Screen: Provider & Service Gateway Configuration
// ==========================================================================

import { store } from '../services/store.js';

export function renderIntegrationsScreen() {
  const state = store.state;
  const integrations = state.integrations;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">FEDERATED ADAPTERS</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Service Gateways</h2>
          </div>
        </div>

        <span class="badge badge-cyan" style="font-size: 8px;">SECURE CHANNELS</span>
      </div>

      <!-- Dedicated BYOK Neural Core Gateway Banner -->
      <div class="hud-panel" style="padding: 14px; border: 1px solid var(--cyan-core); background: rgba(0, 240, 255, 0.05); display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
        <div style="padding-right: 10px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">neurology</span>
            <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin: 0;">Cloud LLM Provider (BYOK)</h3>
            <span class="badge badge-cyan" style="font-size: 8px;">AES-256-GCM</span>
          </div>
          <span style="font-size: 11px; color: var(--text-secondary); margin-top: 4px; display: block;">
            Configure your own NVIDIA NIM, OpenAI, or Groq API key. Zero client-side key storage.
          </span>
        </div>
        <button onclick="window.jarvisApp.openLLMModal()" class="hud-btn-primary" style="font-size: 11px; padding: 8px 14px; white-space: nowrap;">
          <span class="material-symbols-outlined" style="font-size: 14px;">vpn_key</span>
          Configure Key
        </button>
      </div>

      <!-- Notice Banner -->
      <div class="hud-panel" style="padding: 10px 12px; border-color: rgba(0, 240, 255, 0.3);">
        <div style="display: flex; align-items: flex-start; gap: 8px;">
          <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core); margin-top: 1px;">info</span>
          <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.4;">
            All integrations operate under strict local prototype sandbox limits. No financial orders or unencrypted keys are stored.
          </p>
        </div>
      </div>

      <!-- Integrations Cards List -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${integrations.map(item => `
          <div class="hud-panel" style="padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <div style="width: 32px; height: 32px; background: var(--surface-input); border: 1px solid var(--cyan-core); color: var(--cyan-core); display: flex; align-items: center; justify-content: center; clip-path: var(--chamfer-clip-sm);">
                  <span class="material-symbols-outlined" style="font-size: 18px;">${item.icon}</span>
                </div>
                <div>
                  <h4 style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${item.name}</h4>
                  <span class="label-caps" style="font-size: 8px; color: var(--text-muted);">${item.category}</span>
                </div>
              </div>

              <span class="badge ${item.status.includes('Disabled') ? 'badge-amber' : 'badge-cyan'}" style="font-size: 8px;">
                ${item.status}
              </span>
            </div>

            <div style="display: flex; justify-content: flex-end; margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(0, 240, 255, 0.08);">
              <button onclick="${item.category === 'AI / Neural' || item.name.toLowerCase().includes('llm') || item.name.toLowerCase().includes('gemini') ? 'window.jarvisApp.openLLMModal()' : `window.jarvisApp.simulateConfigureIntegration('${item.name}')`}" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
                ${item.category === 'AI / Neural' ? 'Configure BYOK Key' : 'Configure Adapter'}
              </button>
            </div>
          </div>
        `).join('')}
      </div>

    </div>
  `;
}
