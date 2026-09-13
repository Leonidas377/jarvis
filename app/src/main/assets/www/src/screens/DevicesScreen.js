// ==========================================================================
// Devices Screen: Smart Home & Environmental Control
// ==========================================================================

import { store } from '../services/store.js';

export function renderDevicesScreen() {
  const state = store.state;
  const devices = state.devices;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">ENVIRONMENTAL TELEMETRY</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Smart Devices</h2>
          </div>
        </div>

        <button onclick="window.jarvisApp.simulateAddDevice()" class="hud-btn" style="padding: 6px 10px; font-size: 10px;">
          <span class="material-symbols-outlined" style="font-size: 14px;">add</span>
          Add Node
        </button>
      </div>

      <!-- Quick Summary Status -->
      <div class="hud-panel" style="padding: 10px 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--cyan-core); box-shadow: 0 0 6px var(--cyan-core);"></span>
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">${devices.length} NODES CONNECTED</span>
        </div>
        <span class="label-caps" style="font-size: 8px;">LOCAL ZIGBEE / MATTER BRIDGE</span>
      </div>

      <!-- Device Cards Grid -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${devices.map(dev => {
          const isOn = dev.state;
          const statusCol = isOn ? 'var(--cyan-core)' : 'var(--text-muted)';
          
          let icon = 'power';
          if (dev.type === 'light') icon = 'lightbulb';
          if (dev.type === 'thermostat') icon = 'thermostat';
          if (dev.type === 'speaker') icon = 'speaker';
          if (dev.type === 'camera') icon = 'videocam';

          return `
            <div class="hud-panel" style="
              padding: 12px;
              border-color: ${isOn ? 'var(--border-cyan)' : 'rgba(0, 240, 255, 0.1)'};
              background: ${isOn ? 'var(--surface-panel)' : 'rgba(8, 18, 30, 0.5)'};
            ">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                  <div style="
                    width: 36px;
                    height: 36px;
                    background: var(--surface-input);
                    border: 1px solid ${statusCol};
                    color: ${statusCol};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    clip-path: var(--chamfer-clip-sm);
                  ">
                    <span class="material-symbols-outlined" style="font-size: 20px;">${icon}</span>
                  </div>

                  <div>
                    <h3 style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${dev.name}</h3>
                    <span class="label-caps" style="font-size: 8px; color: var(--text-muted);">${dev.room}</span>
                  </div>
                </div>

                <!-- On/Off Toggle Button -->
                <button onclick="window.jarvisApp.toggleDeviceAction('${dev.id}')" style="
                  background: ${isOn ? 'var(--cyan-core)' : 'var(--surface-input)'};
                  color: ${isOn ? 'var(--bg-void)' : 'var(--text-muted)'};
                  border: 1px solid ${isOn ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.25)'};
                  font-family: var(--font-telemetry);
                  font-size: 10px;
                  font-weight: 700;
                  padding: 4px 10px;
                  cursor: pointer;
                  clip-path: var(--chamfer-clip-sm);
                  transition: all 0.15s ease;
                ">
                  ${isOn ? 'ACTIVE' : 'OFFLINE'}
                </button>
              </div>

              <!-- Value Slider / Readout if Active -->
              ${isOn && dev.unit ? `
                <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(0, 240, 255, 0.08);">
                  <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                    <span class="label-caps" style="font-size: 8px;">LEVEL OUTPUT</span>
                    <span class="font-telemetry" style="font-size: 11px; font-weight: 700; color: var(--cyan-core);">${dev.value} ${dev.unit}</span>
                  </div>
                  <input 
                    type="range" 
                    min="${dev.type === 'thermostat' ? 16 : 0}" 
                    max="${dev.type === 'thermostat' ? 30 : 100}" 
                    value="${dev.value}"
                    oninput="window.jarvisApp.handleDeviceSlider('${dev.id}', this.value)"
                    style="width: 100%; accent-color: var(--cyan-core);"
                  >
                </div>
              ` : ''}

            </div>
          `;
        }).join('')}
      </div>

    </div>
  `;
}
