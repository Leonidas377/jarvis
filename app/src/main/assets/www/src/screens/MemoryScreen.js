// ==========================================================================
// Memory Screen: Explicit Personal Memory & Context Store
// ==========================================================================

import { store } from '../services/store.js';

let memFilter = '';

export function setMemoryFilter(query) {
  memFilter = query;
  window.jarvisApp.render();
}

export function renderMemoryScreen() {
  const state = store.state;
  let memories = state.memories;
  if (memFilter) {
    memories = memories.filter(m => 
      m.key.toLowerCase().includes(memFilter.toLowerCase()) || 
      m.value.toLowerCase().includes(memFilter.toLowerCase()) ||
      m.category.toLowerCase().includes(memFilter.toLowerCase())
    );
  }

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">EPISODIC CONTEXT STORE</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Personal Memory</h2>
          </div>
        </div>

        <button onclick="window.jarvisApp.promptAddMemory()" class="hud-btn" style="padding: 6px 10px; font-size: 10px;">
          <span class="material-symbols-outlined" style="font-size: 14px;">add</span>
          Add Fact
        </button>
      </div>

      <!-- Search & Purge Bar -->
      <div class="hud-panel" style="padding: 10px 12px; display: flex; flex-direction: column; gap: 8px;">
        <input 
          type="text" 
          class="hud-input" 
          placeholder="Filter memories, preferences, facts..." 
          value="${memFilter}"
          oninput="window.jarvisApp.filterMemory(this.value)"
        >

        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="label-caps" style="font-size: 8px;">${memories.length} FACTS REGISTERED</span>
          <button onclick="window.jarvisApp.confirmPurgeAllMemory()" style="background: none; border: none; cursor: pointer; color: var(--alert-red); font-size: 9px;" class="label-caps">
            PURGE ALL MEMORY
          </button>
        </div>
      </div>

      <!-- Memory Cards List -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${memories.map(m => `
          <div class="hud-panel" style="padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
              <div>
                <span class="badge badge-cyan" style="font-size: 8px; margin-bottom: 2px;">${m.category}</span>
                <h4 style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${m.key}</h4>
              </div>
              <button onclick="window.jarvisApp.confirmDeleteMemory('${m.id}', '${m.key}')" class="hud-btn-ghost" style="width: 26px; height: 26px; padding: 0; display: flex; align-items: center; justify-content: center; color: var(--alert-red);" title="Delete Memory">
                <span class="material-symbols-outlined" style="font-size: 14px;">close</span>
              </button>
            </div>

            <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.4; margin-top: 4px;">
              ${m.value}
            </p>

            <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted); display: block; margin-top: 6px;">
              RECORDED: ${m.updatedAt} · EXPLICIT PERMISSION
            </span>
          </div>
        `).join('')}
      </div>

    </div>
  `;
}
