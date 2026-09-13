// ==========================================================================
// Bottom Navigation Bar Component
// 5 Primary Tabs: Core, Tasks, Research, Markets, More
// ==========================================================================

import { store } from '../services/store.js';

export function renderBottomNav() {
  const current = store.state.activeScreen;

  const tabs = [
    { id: 'core', label: 'Core', icon: 'neurology' },
    { id: 'tasks', label: 'Tasks', icon: 'fact_check' },
    { id: 'research', label: 'Research', icon: 'travel_explore' },
    { id: 'markets', label: 'Markets', icon: 'monitoring' },
    { id: 'more', label: 'More', icon: 'grid_view' }
  ];

  return `
    <nav class="hud-bottom-nav" style="
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      height: var(--nav-height);
      background: rgba(4, 8, 15, 0.94);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-top: var(--border-cyan);
      display: flex;
      justify-content: space-around;
      align-items: center;
      padding-bottom: var(--safe-bottom);
      z-index: 50;
      box-shadow: 0 -4px 20px rgba(0, 240, 255, 0.08);
    ">
      ${tabs.map(tab => {
        // Tab is active if current matches id, OR if current is sub-screen of more (code, devices, files, memory, settings)
        const isMoreActive = tab.id === 'more' && ['code', 'devices', 'files', 'memory', 'settings', 'integrations'].includes(current);
        const isActive = current === tab.id || isMoreActive;
        const color = isActive ? 'var(--cyan-core)' : 'var(--text-muted)';
        const glow = isActive ? 'filter: drop-shadow(0 0 8px var(--cyan-core));' : '';
        const fontW = isActive ? '700' : '500';

        return `
          <button onclick="window.jarvisApp.handleNavTab('${tab.id}')" class="nav-tab-btn" style="
            background: none;
            border: none;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 4px;
            width: 64px;
            height: 52px;
            cursor: pointer;
            transition: all 0.15s ease;
          ">
            <span class="material-symbols-outlined" style="font-size: 24px; color: ${color}; ${glow}">
              ${tab.icon}
            </span>
            <span class="label-caps" style="font-size: 9px; color: ${color}; font-weight: ${fontW};">
              ${tab.label}
            </span>
          </button>
        `;
      }).join('')}
    </nav>
  `;
}
