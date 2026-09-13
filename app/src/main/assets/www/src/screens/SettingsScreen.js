// ==========================================================================
// Settings Screen: System Preferences & Configuration
// ==========================================================================

import { store } from '../services/store.js';

export function renderSettingsScreen() {
  const s = store.state.settings;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">SYSTEM CONFIGURATION</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Preferences</h2>
          </div>
        </div>

        <span class="badge badge-cyan" style="font-size: 8px;">STARK SEC-5</span>
      </div>

      <!-- Settings Groups -->
      <div style="display: flex; flex-direction: column; gap: 12px;">
        
        <!-- Group 1: Visual Atmosphere -->
        <div class="hud-panel" style="padding: 14px; display: flex; flex-direction: column; gap: 12px;">
          <span class="label-caps" style="color: var(--cyan-core);">HUD OPTIC INTENSITY</span>

          <div>
            <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
              <span style="font-size: 13px; font-weight: 600; color: var(--text-primary);">Photonic Glow Factor</span>
              <span class="font-telemetry" style="font-size: 11px; color: var(--cyan-core);">${s.visualGlowIntensity}%</span>
            </div>
            <input 
              type="range" 
              min="20" 
              max="100" 
              value="${s.visualGlowIntensity}" 
              oninput="window.jarvisApp.handleGlowSlider(this.value)"
              style="width: 100%; accent-color: var(--cyan-core);"
            >
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px;">
            <div>
              <span style="font-size: 13px; font-weight: 600; color: var(--text-primary); display: block;">Reduced Motion</span>
              <span style="font-size: 11px; color: var(--text-muted);">Suppress continuous ambient scanlines</span>
            </div>
            <input 
              type="checkbox" 
              ${s.reducedMotion ? 'checked' : ''} 
              onchange="window.jarvisApp.handleSettingToggle('reducedMotion', this.checked)"
              style="width: 18px; height: 18px; accent-color: var(--cyan-core);"
            >
          </div>
        </div>

        <!-- Group 2: Audio & Haptics -->
        <div class="hud-panel" style="padding: 14px; display: flex; flex-direction: column; gap: 12px;">
          <span class="label-caps" style="color: var(--cyan-core);">TACTILE & ACOUSTICS</span>

          <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
              <span style="font-size: 13px; font-weight: 600; color: var(--text-primary); display: block;">Haptic Feedback</span>
              <span style="font-size: 11px; color: var(--text-muted);">Vibration pulse on critical taps</span>
            </div>
            <input 
              type="checkbox" 
              ${s.hapticFeedback ? 'checked' : ''} 
              onchange="window.jarvisApp.handleSettingToggle('hapticFeedback', this.checked)"
              style="width: 18px; height: 18px; accent-color: var(--cyan-core);"
            >
          </div>

          <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px;">
            <div>
              <span style="font-size: 13px; font-weight: 600; color: var(--text-primary); display: block;">Tactical Sound Effects</span>
              <span style="font-size: 11px; color: var(--text-muted);">HUD audio clicks and telemetry chimes</span>
            </div>
            <input 
              type="checkbox" 
              ${s.soundEffects ? 'checked' : ''} 
              onchange="window.jarvisApp.handleSettingToggle('soundEffects', this.checked)"
              style="width: 18px; height: 18px; accent-color: var(--cyan-core);"
            >
          </div>

          <div style="border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px;">
            <label class="label-caps" style="display: block; margin-bottom: 4px;">Assistant Synthesizer Voice</label>
            <select class="hud-input" onchange="window.jarvisApp.handleSettingToggle('ttsVoice', this.value)" style="background: var(--surface-input); color: var(--text-primary);">
              <option value="British Male (JARVIS Synthetic)" selected>British Male (JARVIS Synthetic)</option>
              <option value="Standard Technical Voice">Standard Technical Voice</option>
              <option value="Crisp Minimalist Female">Crisp Minimalist Female</option>
            </select>
          </div>
        </div>

        <!-- Group 3: LLM & Integrations Gateway -->
        <button onclick="window.jarvisApp.openLLMModal()" class="hud-panel" style="padding: 14px; text-align: left; cursor: pointer; display: flex; align-items: center; justify-content: space-between; border-color: rgba(0, 240, 255, 0.4);">
          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">neurology</span>
              <span style="font-size: 14px; font-weight: 700; color: var(--text-primary);">Cloud LLM Provider (BYOK)</span>
            </div>
            <span style="font-size: 11px; color: var(--text-muted); margin-top: 2px; display: block;">
              Configure NVIDIA NIM, OpenAI, Groq (AES-256-GCM encrypted)
            </span>
          </div>
          <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core);">chevron_right</span>
        </button>

        <button onclick="window.jarvisApp.navigate('integrations')" class="hud-panel" style="padding: 14px; text-align: left; cursor: pointer; display: flex; align-items: center; justify-content: space-between;">
          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">hub</span>
              <span style="font-size: 14px; font-weight: 700; color: var(--text-primary);">External Service Gateways</span>
            </div>
            <span style="font-size: 11px; color: var(--text-muted); margin-top: 2px; display: block;">
              Configure Broker, Search, and IoT provider adapters
            </span>
          </div>
          <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core);">chevron_right</span>
        </button>

        <!-- Group 4: Reset Demo Data -->
        <div class="hud-panel" style="padding: 14px; border-color: rgba(255, 42, 85, 0.35);">
          <span class="label-caps" style="color: var(--alert-red);">DEVELOPER RE-CALIBRATION</span>
          <p style="font-size: 12px; color: var(--text-secondary); margin: 6px 0 12px 0;">
            Restore factory default directives, mock watchlist, smart device states, and comms buffer.
          </p>
          <button onclick="window.jarvisApp.confirmResetAllData()" class="hud-btn-danger" style="width: 100%; padding: 10px;">
            <span class="material-symbols-outlined" style="font-size: 16px;">restart_alt</span>
            Reset All Demo Data
          </button>
        </div>

      </div>

    </div>
  `;
}
