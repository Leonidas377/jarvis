// ==========================================================================
// Voice Command Bottom-Sheet Modal Component
// ==========================================================================

import { store } from '../services/store.js';

export function renderVoiceModal() {
  const state = store.state;
  const aState = state.assistantState;

  return `
    <div id="voice-modal" class="hud-modal-overlay">
      <div class="hud-modal-content" style="padding: 24px 16px 32px 16px; text-align: center;">
        
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
          <div style="text-align: left;">
            <span class="label-caps" style="color: var(--cyan-core);">VOICE PROTOCOL INTERFACE</span>
            <div style="display: flex; align-items: center; gap: 6px; margin-top: 2px;">
              <span class="badge badge-cyan" style="font-size: 8px;">PROTOTYPE SPEECH ENGINE</span>
              <span class="badge badge-amber" style="font-size: 8px;">SIMULATED RECOGNITION</span>
            </div>
          </div>
          <button onclick="window.jarvisApp.closeVoiceModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Large Mic Button & Pulse Orb -->
        <div style="margin: 10px auto 20px auto; width: 90px; height: 90px; position: relative; display: flex; align-items: center; justify-content: center;">
          <div style="
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background: rgba(0, 240, 255, 0.15);
            animation: pulse-glow 2s infinite;
          "></div>
          <button id="modal-mic-btn" onclick="window.jarvisApp.handleVoiceSimulate('Run full diagnostics and summarize schedule')" style="
            position: relative;
            z-index: 2;
            width: 76px;
            height: 76px;
            border-radius: 50%;
            background: var(--cyan-core);
            border: none;
            color: var(--bg-void);
            box-shadow: 0 0 24px var(--cyan-core);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.15s ease;
          ">
            <span class="material-symbols-outlined" style="font-size: 38px;">mic</span>
          </button>
        </div>

        <!-- Dynamic Status Text -->
        <div id="voice-status-text" style="margin-bottom: 16px;">
          <span class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--cyan-core); letter-spacing: 0.1em; display: block;">
            ${aState === 'LISTENING' ? 'LISTENING TO SPEECH...' : 'READY FOR VOICE INPUT'}
          </span>
          <span style="font-size: 12px; color: var(--text-muted); margin-top: 4px; display: block;">
            Tap microphone above or select a simulated command below:
          </span>
        </div>

        <!-- Mock Voice Prompt Chips -->
        <div style="display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin-bottom: 20px;">
          <button onclick="window.jarvisApp.handleVoiceSimulate('Show my active tasks and progress')" class="hud-btn-ghost" style="font-size: 11px; padding: 6px 10px;">
            “Show my active tasks”
          </button>
          <button onclick="window.jarvisApp.handleVoiceSimulate('Show market summary and top movers')" class="hud-btn-ghost" style="font-size: 11px; padding: 6px 10px;">
            “Show market summary”
          </button>
          <button onclick="window.jarvisApp.handleVoiceSimulate('Search for quantum computing chips')" class="hud-btn-ghost" style="font-size: 11px; padding: 6px 10px;">
            “Search for quantum chips”
          </button>
        </div>

        <!-- Text Fallback Input -->
        <div style="display: flex; gap: 8px; align-items: center;">
          <input type="text" id="voice-fallback-input" class="hud-input" placeholder="Or type voice command..." onkeydown="if(event.key === 'Enter') window.jarvisApp.submitVoiceFallback()">
          <button onclick="window.jarvisApp.submitVoiceFallback()" class="hud-btn" style="padding: 10px 14px;">
            <span class="material-symbols-outlined" style="font-size: 18px;">send</span>
          </button>
        </div>

      </div>
    </div>
  `;
}
