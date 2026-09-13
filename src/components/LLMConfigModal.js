// ==========================================================================
// JARVIS LLM Configuration Modal (Bring Your Own Key)
// Secure client interface for configuring cloud LLM providers
// Zero plaintext exposure, instant presets, test diagnostics
// ==========================================================================

export function renderLLMConfigModal(config, testResult = null, isLoading = false, isTesting = false) {
  const currentStatus = config ? config.status.toUpperCase() : 'NOT CONFIGURED';
  const isConnected = currentStatus === 'CONNECTED';
  const isEnabled = config ? config.is_enabled : false;
  const fingerprint = config ? config.key_fingerprint : 'No key stored';

  return `
    <div id="llm-config-modal" class="hud-modal-overlay" style="z-index: 10000; overflow-y: auto;">
      <div class="hud-modal-content" style="padding: 24px 18px 30px 18px; max-width: 520px; width: 92%; margin: 40px auto;">
        
        <!-- Header -->
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 14px;">
          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core);">neurology</span>
              <span class="label-caps" style="color: var(--cyan-core); letter-spacing: 1px;">NEURAL COGNITIVE CORE</span>
            </div>
            <h3 class="hud-title" style="font-size: 18px; margin-top: 2px;">Provider Gateway (BYOK)</h3>
          </div>
          <button onclick="window.jarvisApp.closeLLMModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 20px;">close</span>
          </button>
        </div>

        <!-- Security Disclosure Banner -->
        <div class="hud-panel" style="padding: 10px 12px; margin-bottom: 14px; border-left: 3px solid var(--cyan-core); background: rgba(0, 240, 255, 0.04);">
          <div style="display: flex; align-items: flex-start; gap: 8px;">
            <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core); margin-top: 2px;">lock</span>
            <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.4; margin: 0;">
              <strong style="color: var(--cyan-core);">MIL-SPEC AES-256-GCM ENCRYPTED STORAGE.</strong> Your API key is encrypted at rest using a 256-bit Key Encryption Key outside the database. Credentials are decrypted only in backend memory at execution time and never exposed to the client or Android bundle.
            </p>
          </div>
        </div>

        <!-- Current Status Telemetry Strip -->
        <div class="hud-panel" style="padding: 12px 14px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center;">
          <div>
            <span class="label-caps" style="font-size: 9px; color: var(--text-muted); display: block;">ACTIVE LINK STATUS</span>
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 2px;">
              <span style="width: 8px; height: 8px; border-radius: 50%; background: ${isConnected ? 'var(--cyan-core)' : (config ? 'var(--alert-amber)' : 'var(--alert-red)')}; box-shadow: 0 0 8px ${isConnected ? 'var(--cyan-core)' : 'transparent'};"></span>
              <span style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${config ? config.display_name : 'No Provider Active'}</span>
              <span class="badge ${isConnected ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">${currentStatus}</span>
            </div>
          </div>

          <div style="text-align: right;">
            <span class="label-caps" style="font-size: 8px; color: var(--text-muted); display: block;">KEY FINGERPRINT</span>
            <span class="font-telemetry" style="font-size: 11px; color: var(--cyan-core); font-weight: 600;">${fingerprint}</span>
          </div>
        </div>

        <!-- Provider Quick Presets -->
        <div style="margin-bottom: 14px;">
          <span class="label-caps" style="font-size: 9px; color: var(--text-muted); display: block; margin-bottom: 6px;">QUICK-CONFIG PRESETS</span>
          <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px;">
            <button onclick="window.jarvisApp.applyLLMPreset('nvidia')" class="hud-btn-ghost" style="font-size: 10px; padding: 6px; border-color: rgba(0, 240, 255, 0.4); text-align: center;">
              ⚡ NVIDIA NIM
            </button>
            <button onclick="window.jarvisApp.applyLLMPreset('openai')" class="hud-btn-ghost" style="font-size: 10px; padding: 6px; border-color: rgba(0, 240, 255, 0.4); text-align: center;">
              🤖 OpenAI
            </button>
            <button onclick="window.jarvisApp.applyLLMPreset('groq')" class="hud-btn-ghost" style="font-size: 10px; padding: 6px; border-color: rgba(0, 240, 255, 0.4); text-align: center;">
              🚀 Groq LPU
            </button>
          </div>
        </div>

        <!-- Configuration Form -->
        <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 18px;">
          
          <!-- Protocol & Display Name -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div>
              <label class="label-caps" style="display: block; margin-bottom: 4px;">Provider Protocol</label>
              <select id="llm-input-provider" class="hud-input" style="background: var(--surface-input); color: var(--text-primary);" onchange="window.jarvisApp.handleProviderProtocolChange(this.value)">
                <option value="openai-compatible" ${config && config.provider === 'openai-compatible' ? 'selected' : ''}>OpenAI-Compatible</option>
                <option value="openai" ${config && config.provider === 'openai' ? 'selected' : ''}>OpenAI Direct</option>
                <option value="google" ${config && config.provider === 'google' ? 'selected' : ''}>Google Gemini</option>
                <option value="custom" ${config && config.provider === 'custom' ? 'selected' : ''}>Custom Gateway</option>
              </select>
            </div>

            <div>
              <label class="label-caps" style="display: block; margin-bottom: 4px;">Display Name</label>
              <input type="text" id="llm-input-name" class="hud-input" value="${config ? config.display_name : 'NVIDIA NIM'}" placeholder="e.g. NVIDIA NIM">
            </div>
          </div>

          <!-- Base URL -->
          <div id="llm-base-url-container">
            <label class="label-caps" style="display: block; margin-bottom: 4px;">API Base URL</label>
            <input type="text" id="llm-input-url" class="hud-input" value="${config ? (config.base_url || '') : 'https://integrate.api.nvidia.com/v1'}" placeholder="e.g. https://integrate.api.nvidia.com/v1">
          </div>

          <!-- Model Identifier -->
          <div>
            <label class="label-caps" style="display: block; margin-bottom: 4px;">Model Name / Identifier</label>
            <input type="text" id="llm-input-model" class="hud-input" value="${config ? config.model : 'meta/llama-3.2-11b-vision-instruct'}" placeholder="e.g. meta/llama-3.2-11b-vision-instruct">
          </div>

          <!-- Secret API Key Input (Never Pre-filled) -->
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <label class="label-caps">Secret API Key</label>
              ${config ? `<span style="font-size: 10px; color: var(--cyan-core);">Key is stored encrypted (${fingerprint})</span>` : ''}
            </div>
            
            <div style="position: relative; display: flex; align-items: center;">
              <input 
                type="password" 
                id="llm-input-key" 
                class="hud-input" 
                placeholder="${config ? 'Enter new key to replace existing' : 'Paste your API key (e.g. nvapi-...)'}" 
                style="padding-right: 42px;"
                autocomplete="off"
                spellcheck="false"
              >
              <button 
                type="button" 
                onclick="window.jarvisApp.toggleKeyVisibility()" 
                class="hud-btn-ghost" 
                style="position: absolute; right: 4px; width: 34px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center; border: none;"
                title="Toggle key visibility"
              >
                <span id="llm-key-eye-icon" class="material-symbols-outlined" style="font-size: 18px; color: var(--text-muted);">visibility</span>
              </button>
            </div>
            <span style="font-size: 10px; color: var(--text-muted); margin-top: 3px; display: block;">
              For security, raw keys are wiped from memory immediately upon save and never pre-filled.
            </span>
          </div>

          <!-- Temperature & Max Tokens Slider -->
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 10px;">
            <div>
              <div style="display: flex; justify-content: space-between;">
                <label class="label-caps">Temperature</label>
                <span id="llm-temp-val" class="font-telemetry" style="font-size: 10px; color: var(--cyan-core);">${config ? config.temperature : 0.7}</span>
              </div>
              <input 
                type="range" 
                id="llm-input-temp" 
                min="0.0" 
                max="1.5" 
                step="0.05" 
                value="${config ? config.temperature : 0.7}" 
                oninput="document.getElementById('llm-temp-val').innerText = this.value"
                style="width: 100%; accent-color: var(--cyan-core); margin-top: 4px;"
              >
            </div>

            <div>
              <label class="label-caps" style="display: block; margin-bottom: 4px;">Max Tokens</label>
              <input type="number" id="llm-input-tokens" class="hud-input" value="${config ? config.max_output_tokens : 1024}" min="64" max="4096">
            </div>
          </div>

        </div>

        <!-- Diagnostic Feedback Result Box -->
        ${testResult ? `
          <div class="hud-panel" style="padding: 10px 12px; margin-bottom: 16px; border-color: ${testResult.status === 'CONNECTED' ? 'var(--cyan-core)' : 'var(--alert-red)'}; background: ${testResult.status === 'CONNECTED' ? 'rgba(0, 240, 255, 0.06)' : 'rgba(255, 42, 85, 0.06)'};">
            <div style="display: flex; align-items: flex-start; gap: 8px;">
              <span class="material-symbols-outlined" style="font-size: 18px; color: ${testResult.status === 'CONNECTED' ? 'var(--cyan-core)' : 'var(--alert-red)'};">
                ${testResult.status === 'CONNECTED' ? 'check_circle' : 'error'}
              </span>
              <div>
                <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); display: block;">
                  ${testResult.status === 'CONNECTED' ? 'JARVIS LLM CONNECTED' : `DIAGNOSTIC ${testResult.status}`}
                  ${testResult.latency_ms ? `<span style="font-size: 10px; color: var(--cyan-core); font-weight: normal; margin-left: 6px;">(${testResult.latency_ms} ms)</span>` : ''}
                </span>
                <span style="font-size: 11px; color: var(--text-secondary); margin-top: 2px; display: block; line-height: 1.3;">
                  ${testResult.message}
                </span>
              </div>
            </div>
          </div>
        ` : ''}

        <!-- Action Buttons -->
        <div style="display: flex; flex-direction: column; gap: 10px;">
          
          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <button 
              onclick="window.jarvisApp.testLLMConnection()" 
              class="hud-btn-ghost" 
              style="padding: 10px; justify-content: center; font-size: 12px;"
              ${isTesting || isLoading ? 'disabled' : ''}
            >
              <span class="material-symbols-outlined" style="font-size: 16px;">${isTesting ? 'sync' : 'network_check'}</span>
              ${isTesting ? 'Testing Link...' : 'Test Connection'}
            </button>

            <button 
              onclick="window.jarvisApp.saveLLMConfiguration()" 
              class="hud-btn-primary" 
              style="padding: 10px; justify-content: center; font-size: 12px;"
              ${isLoading || isTesting ? 'disabled' : ''}
            >
              <span class="material-symbols-outlined" style="font-size: 16px;">save</span>
              ${isLoading ? 'Saving...' : 'Save Configuration'}
            </button>
          </div>

          <!-- Secondary Actions (Enable / Disable & Delete) -->
          ${config ? `
            <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.1); padding-top: 10px; margin-top: 4px;">
              <button 
                onclick="window.jarvisApp.toggleLLMActiveStatus(${!isEnabled})" 
                class="hud-btn-ghost" 
                style="font-size: 11px; padding: 6px 12px; border-color: ${isEnabled ? 'var(--alert-amber)' : 'var(--cyan-core)'};"
              >
                <span class="material-symbols-outlined" style="font-size: 14px;">${isEnabled ? 'pause' : 'play_arrow'}</span>
                ${isEnabled ? 'Disable Provider' : 'Enable Provider'}
              </button>

              <button 
                onclick="window.jarvisApp.confirmDeleteLLMConfig()" 
                class="hud-btn-ghost" 
                style="font-size: 11px; padding: 6px 12px; color: var(--alert-red); border-color: rgba(255, 42, 85, 0.4);"
              >
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--alert-red);">delete</span>
                Delete Key & Config
              </button>
            </div>
          ` : ''}

        </div>

      </div>
    </div>
  `;
}
