// ==========================================================================
// J.A.R.V.I.S. Top HUD Status Header Component
// ==========================================================================

import { store } from '../services/store.js';

export function renderHeader() {
  const state = store.state;
  return `
    <header class="hud-header" style="
      position: sticky;
      top: 0;
      left: 0;
      right: 0;
      height: var(--header-height);
      background: rgba(4, 8, 15, 0.92);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: var(--border-cyan);
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 0 16px;
      z-index: 50;
    ">
      <!-- Left: Arc Reactor Branding & Title -->
      <div class="flex-row items-center gap-sm cursor-pointer" onclick="window.jarvisApp.navigate('core')" style="display: flex; align-items: center; gap: 10px;">
        <svg width="28" height="28" viewBox="0 0 100 100" fill="none" style="filter: drop-shadow(0 0 6px var(--cyan-core));">
          <circle cx="50" cy="50" r="46" stroke="#00F0FF" stroke-width="2" stroke-dasharray="6 3" opacity="0.6"/>
          <circle cx="50" cy="50" r="38" stroke="#00F0FF" stroke-width="1.5" opacity="0.8"/>
          <circle cx="50" cy="50" r="28" stroke="#00F0FF" stroke-width="2"/>
          <circle cx="50" cy="50" r="16" fill="#00F0FF" fill-opacity="0.2" stroke="#A6EFFF" stroke-width="2"/>
          <polygon points="50,26 56,42 72,42 59,52 64,68 50,58 36,68 41,52 28,42 44,42" stroke="#00F0FF" stroke-width="1.5" fill="none"/>
          <circle cx="50" cy="50" r="7" fill="#00F0FF"/>
          <line x1="50" y1="4" x2="50" y2="12" stroke="#00F0FF" stroke-width="2"/>
          <line x1="50" y1="88" x2="50" y2="96" stroke="#00F0FF" stroke-width="2"/>
          <line x1="4" y1="50" x2="12" y2="50" stroke="#00F0FF" stroke-width="2"/>
          <line x1="88" y1="50" x2="96" y2="50" stroke="#00F0FF" stroke-width="2"/>
        </svg>

        <div>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 15px; font-weight: 700; letter-spacing: 0.12em; color: var(--cyan-core);">J.A.R.V.I.S.</span>
            <span class="badge badge-cyan" style="font-size: 8px; padding: 1px 4px;">OS 14.8</span>
          </div>
          <span class="label-caps" style="font-size: 9px; color: var(--text-muted); display: block;">CORE AI ASSISTANT</span>
        </div>
      </div>

      <!-- Right: System Vitals & Profile Action -->
      <div style="display: flex; align-items: center; gap: 12px;">
        <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end;">
          <div style="display: flex; align-items: center; gap: 5px;">
            <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--cyan-core); box-shadow: 0 0 6px var(--cyan-core); display: inline-block;"></span>
            <span class="font-telemetry" style="font-size: 10px; color: var(--text-secondary);">${state.connectionStatus}</span>
          </div>
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">${state.telemetry.neuralLatency} LINK</span>
        </div>

        <button onclick="window.jarvisApp.navigate('settings')" class="hud-btn-ghost" style="
          width: 34px;
          height: 34px;
          border-radius: 4px;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        " title="System Settings">
          <span class="material-symbols-outlined" style="font-size: 18px; color: var(--cyan-core);">settings</span>
        </button>
      </div>
    </header>
  `;
}
