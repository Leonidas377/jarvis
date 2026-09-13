// ==========================================================================
// Assistant Orb: Animated Holographic Arc Reactor Sphere
// Adapts the central orb from ai_core_voice_command_hub
// ==========================================================================

import { store } from '../services/store.js';

export function renderAssistantOrb() {
  const state = store.state;
  const assistantState = state.assistantState;

  // State-specific styles & icons
  let stateIcon = 'neurology';
  let stateColor = 'var(--cyan-core)';
  let stateGlow = 'var(--glow-cyan-lg)';
  let spinSpeedCw = '20s';
  let spinSpeedCcw = '14s';

  if (assistantState === 'LISTENING') {
    stateIcon = 'mic';
    stateColor = 'var(--ice-flare)';
    stateGlow = '0 0 36px rgba(0, 240, 255, 0.85)';
    spinSpeedCw = '6s';
    spinSpeedCcw = '4s';
  } else if (assistantState === 'THINKING') {
    stateIcon = 'psychology';
    stateColor = 'var(--warning-amber)';
    stateGlow = '0 0 32px rgba(255, 184, 0, 0.75)';
    spinSpeedCw = '3s';
    spinSpeedCcw = '3s';
  } else if (assistantState === 'SPEAKING') {
    stateIcon = 'volume_up';
    stateColor = 'var(--success-green)';
    stateGlow = '0 0 36px rgba(0, 255, 178, 0.75)';
    spinSpeedCw = '8s';
    spinSpeedCcw = '6s';
  }

  return `
    <div class="assistant-orb-container" style="
      position: relative;
      width: 100%;
      min-height: 270px;
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 16px;
      background: radial-gradient(circle at center, rgba(0, 240, 255, 0.08) 0%, rgba(8, 18, 30, 0) 70%);
      border: var(--border-cyan);
      clip-path: var(--chamfer-clip-lg);
      overflow: hidden;
      cursor: pointer;
    " onclick="window.jarvisApp.triggerVoiceModal()" title="Tap to engage Voice Assistant">
      
      <!-- Top Sci-Fi Corner Badges -->
      <div style="position: absolute; top: 10px; left: 14px; display: flex; align-items: center; gap: 6px;">
        <span style="width: 5px; height: 5px; background: var(--cyan-core); display: inline-block;"></span>
        <span class="label-caps" style="font-size: 8px;">SYS.NEURAL // 3.8 GJ</span>
      </div>
      <div style="position: absolute; top: 10px; right: 14px; display: flex; align-items: center; gap: 6px;">
        <span class="label-caps" style="font-size: 8px;">QUANTUM COHERENCE: 99.4%</span>
        <span style="width: 5px; height: 5px; border-radius: 50%; background: var(--cyan-core); display: inline-block;"></span>
      </div>

      <!-- Concentric Kinetic Rings Container -->
      <div style="position: relative; width: 200px; height: 200px; display: flex; align-items: center; justify-content: center;">
        
        <!-- Outer Concentric Rotating Ring (Clockwise) -->
        <svg style="position: absolute; inset: 0; width: 100%; height: 100%; animation: spin-cw ${spinSpeedCw} linear infinite;" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="92" fill="none" stroke="rgba(0, 240, 255, 0.18)" stroke-width="1.5" stroke-dasharray="4 8"/>
          <circle cx="100" cy="100" r="84" fill="none" stroke="${stateColor}" stroke-width="2" stroke-dasharray="32 16 8 16" opacity="0.7"/>
          <circle cx="100" cy="100" r="76" fill="none" stroke="rgba(175, 198, 255, 0.25)" stroke-width="1" stroke-dasharray="2 6"/>
        </svg>

        <!-- Middle Concentric Rotating Ring (Counter-Clockwise) -->
        <svg style="position: absolute; inset: 0; width: 100%; height: 100%; animation: spin-ccw ${spinSpeedCcw} linear infinite;" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="66" fill="none" stroke="${stateColor}" stroke-width="2" stroke-dasharray="14 18" opacity="0.8"/>
          <circle cx="100" cy="34" r="3" fill="${stateColor}"/>
          <circle cx="166" cy="100" r="3" fill="${stateColor}"/>
          <circle cx="100" cy="166" r="3" fill="${stateColor}"/>
          <circle cx="34" cy="100" r="3" fill="${stateColor}"/>
        </svg>

        <!-- Inner Arc Segments -->
        <svg style="position: absolute; inset: 0; width: 100%; height: 100%; animation: spin-cw 8s ease-in-out infinite;" viewBox="0 0 200 200">
          <circle cx="100" cy="100" r="50" fill="none" stroke="${stateColor}" stroke-width="3" stroke-dasharray="24 12" opacity="0.6"/>
        </svg>

        <!-- Central Core Photon Bulb -->
        <div style="
          position: relative;
          z-index: 10;
          width: 82px;
          height: 82px;
          border-radius: 50%;
          background: rgba(14, 28, 48, 0.95);
          border: 2px solid ${stateColor};
          box-shadow: ${stateGlow};
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          transition: all 0.3s ease;
        ">
          <span class="material-symbols-outlined" style="font-size: 32px; color: ${stateColor};">
            ${stateIcon}
          </span>
          <span class="font-telemetry" style="font-size: 9px; font-weight: 700; color: ${stateColor}; letter-spacing: 0.15em; margin-top: 2px;">
            ${assistantState}
          </span>
        </div>
      </div>

      <!-- State Subtitle / Action Prompt -->
      <div style="margin-top: 10px; text-align: center;">
        <span class="label-caps" style="color: var(--cyan-core); font-size: 10px;">
          ${assistantState === 'READY' ? 'TAP TO INITIATE VOICE COMMAND' : assistantState + ' // AUDIO STREAM ACTIVE'}
        </span>
      </div>
    </div>
  `;
}
