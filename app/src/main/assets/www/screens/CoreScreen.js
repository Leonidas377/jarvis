// ==========================================================================
// Core Screen: Home AI Assistant Dashboard
// Reproduces ai_core_voice_command_hub with personal assistant semantics
// ==========================================================================

import { store } from '../services/store.js';
import { renderAssistantOrb } from '../components/AssistantOrb.js';
import { renderVoiceWaveform } from '../components/VoiceWaveform.js';

export function renderCoreScreen() {
  const state = store.state;
  const t = state.telemetry;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Status Banner -->
      <div class="hud-panel" style="padding: 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 10px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: var(--cyan-core); box-shadow: 0 0 8px var(--cyan-core);" class="animate-pulse-glow"></span>
          <div>
            <span class="label-caps" style="color: var(--cyan-core); font-size: 9px; display: block;">J.A.R.V.I.S. // NEURAL CORE ACTIVATED</span>
            <span style="font-size: 11px; color: var(--text-muted); font-family: var(--font-telemetry);">SUB-ROUTINE 04.99 · ALL NODES NOMINAL</span>
          </div>
        </div>
        <div style="text-align: right;">
          <span class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--cyan-core);">99.4%</span>
          <span class="label-caps" style="font-size: 8px; display: block;">COHERENCE</span>
        </div>
      </div>

      <!-- Centerpiece: Holographic Arc Sphere -->
      ${renderAssistantOrb()}

      <!-- Voice Equalizer Waveform -->
      ${renderVoiceWaveform()}

      <!-- Telemetry Tiles (4 Metrics) -->
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
        <!-- Metric 1: Core Temp -->
        <div class="hud-panel" style="padding: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="label-caps" style="font-size: 8px;">CORE TEMP</span>
            <span class="material-symbols-outlined" style="font-size: 14px; color: var(--cyan-core);">thermostat</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 4px;">
            <span class="font-telemetry" style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${t.coreTemp}</span>
            <span class="font-telemetry" style="font-size: 9px; color: var(--text-muted);">NOMINAL</span>
          </div>
          <div style="width: 100%; height: 3px; background: var(--surface-dim); border-radius: 2px; margin-top: 6px; overflow: hidden;">
            <div style="width: 42%; height: 100%; background: var(--cyan-core);"></div>
          </div>
        </div>

        <!-- Metric 2: Compute -->
        <div class="hud-panel" style="padding: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="label-caps" style="font-size: 8px;">COMPUTE LOAD</span>
            <span class="material-symbols-outlined" style="font-size: 14px; color: var(--plasma-cobalt);">memory</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 4px;">
            <span class="font-telemetry" style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${t.computeLoad}</span>
            <span class="font-telemetry" style="font-size: 9px; color: var(--text-muted);">ASYNC</span>
          </div>
          <div style="width: 100%; height: 3px; background: var(--surface-dim); border-radius: 2px; margin-top: 6px; overflow: hidden;">
            <div style="width: 68%; height: 100%; background: var(--plasma-cobalt);"></div>
          </div>
        </div>

        <!-- Metric 3: Memory -->
        <div class="hud-panel" style="padding: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="label-caps" style="font-size: 8px;">RAM BUFFER</span>
            <span class="material-symbols-outlined" style="font-size: 14px; color: var(--cyan-core);">storage</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 4px;">
            <span class="font-telemetry" style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${t.memoryUsage}</span>
            <span class="font-telemetry" style="font-size: 9px; color: var(--text-muted);">ACTIVE</span>
          </div>
          <div style="width: 100%; height: 3px; background: var(--surface-dim); border-radius: 2px; margin-top: 6px; overflow: hidden;">
            <div style="width: 64%; height: 100%; background: var(--cyan-core);"></div>
          </div>
        </div>

        <!-- Metric 4: Latency -->
        <div class="hud-panel" style="padding: 10px;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span class="label-caps" style="font-size: 8px;">LINK LATENCY</span>
            <span class="material-symbols-outlined" style="font-size: 14px; color: var(--warning-amber);">speed</span>
          </div>
          <div style="display: flex; align-items: baseline; gap: 4px;">
            <span class="font-telemetry" style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${t.neuralLatency}</span>
            <span class="font-telemetry" style="font-size: 9px; color: var(--text-muted);">SYNC</span>
          </div>
          <div style="width: 100%; height: 3px; background: var(--surface-dim); border-radius: 2px; margin-top: 6px; overflow: hidden;">
            <div style="width: 25%; height: 100%; background: var(--warning-amber);"></div>
          </div>
        </div>
      </div>

      <!-- Quick Actions Grid (8 Actions) -->
      <div>
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; padding: 0 2px;">
          <span class="label-caps" style="color: var(--text-secondary);">TACTICAL COMMAND OVERRIDES</span>
          <span class="label-caps" style="color: var(--cyan-core);">8 SHORTCUTS</span>
        </div>
        
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px;">
          <button onclick="window.jarvisApp.navigate('chat')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">forum</span>
              <span class="label-caps" style="font-size: 8px;">01</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Ask J.A.R.V.I.S.</span>
            <span style="font-size: 10px; color: var(--text-muted);">Conversational Stream</span>
          </button>

          <button onclick="window.jarvisApp.navigate('research')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">travel_explore</span>
              <span class="label-caps" style="font-size: 8px;">02</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Web Research</span>
            <span style="font-size: 10px; color: var(--text-muted);">Verified Citations</span>
          </button>

          <button onclick="window.jarvisApp.openTaskModal()" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">add_task</span>
              <span class="label-caps" style="font-size: 8px;">03</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Create Task</span>
            <span style="font-size: 10px; color: var(--text-muted);">Schedule Directive</span>
          </button>

          <button onclick="window.jarvisApp.navigate('markets')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">trending_up</span>
              <span class="label-caps" style="font-size: 8px;">04</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Analyze Market</span>
            <span style="font-size: 10px; color: var(--text-muted);">Watchlist & Insights</span>
          </button>

          <button onclick="window.jarvisApp.navigate('code')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">terminal</span>
              <span class="label-caps" style="font-size: 8px;">05</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Coding Task</span>
            <span style="font-size: 10px; color: var(--text-muted);">Diffs & Tests</span>
          </button>

          <button onclick="window.jarvisApp.navigate('devices')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">home_iot_device</span>
              <span class="label-caps" style="font-size: 8px;">06</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Smart Devices</span>
            <span style="font-size: 10px; color: var(--text-muted);">Lab Environment</span>
          </button>

          <button onclick="window.jarvisApp.navigate('files')" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">folder_open</span>
              <span class="label-caps" style="font-size: 8px;">07</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Files Storage</span>
            <span style="font-size: 10px; color: var(--text-muted);">Workspace Explorer</span>
          </button>

          <button onclick="window.jarvisApp.triggerVoiceModal()" class="hud-panel" style="text-align: left; padding: 10px; cursor: pointer; display: flex; flex-direction: column; gap: 4px;">
            <div style="display: flex; justify-content: space-between;">
              <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">mic</span>
              <span class="label-caps" style="font-size: 8px;">08</span>
            </div>
            <span style="font-size: 12px; font-weight: 700; color: var(--text-primary); text-transform: uppercase;">Voice Command</span>
            <span style="font-size: 10px; color: var(--text-muted);">Quantum Speech Link</span>
          </button>
        </div>
      </div>

      <!-- Comms Transcript Preview -->
      <div class="hud-panel" style="padding: 12px;">
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
          <div style="display: flex; align-items: center; gap: 6px;">
            <span style="width: 6px; height: 6px; background: var(--cyan-core); display: inline-block;"></span>
            <span class="label-caps" style="color: var(--text-primary);">RECENT COMMS TRANSCRIPT</span>
          </div>
          <button onclick="window.jarvisApp.navigate('chat')" class="hud-btn-ghost" style="font-size: 9px; padding: 2px 8px;">VIEW FULL CHAT</button>
        </div>

        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${state.chatMessages.slice(-2).map(msg => `
            <div style="background: var(--surface-input); border: 1px solid rgba(0, 240, 255, 0.15); padding: 8px 10px; clip-path: var(--chamfer-clip-sm);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span class="label-caps" style="font-size: 8px; color: ${msg.sender === 'user' ? 'var(--cyan-core)' : 'var(--plasma-cobalt)'};">
                  ${msg.sender === 'user' ? 'T. STARK // USER' : 'J.A.R.V.I.S. // CORE'}
                </span>
                <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">${msg.timestamp}</span>
              </div>
              <p style="font-size: 12px; color: var(--text-primary); line-height: 1.4;">
                ${msg.text}
              </p>
            </div>
          `).join('')}
        </div>
      </div>

    </div>
  `;
}
