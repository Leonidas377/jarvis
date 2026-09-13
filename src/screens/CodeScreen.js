// ==========================================================================
// Code Screen: Coding Assistant & Workspace Subroutines
// ==========================================================================

import { store } from '../services/store.js';

export function renderCodeScreen() {
  const state = store.state;
  const project = state.codeProjects[0];

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">AUTOMATED SOFTWARE MATRIX</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Coding Assistant</h2>
          </div>
        </div>

        <button onclick="window.jarvisApp.simulateNewCodeTask()" class="hud-btn" style="padding: 6px 10px; font-size: 10px;">
          <span class="material-symbols-outlined" style="font-size: 14px;">add_circle</span>
          New Task
        </button>
      </div>

      <!-- Project Health Card -->
      <div class="hud-panel" style="padding: 12px; display: flex; align-items: center; justify-content: space-between;">
        <div>
          <div style="display: flex; align-items: center; gap: 6px;">
            <span class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--text-primary);">${project.name}</span>
            <span class="badge badge-cyan" style="font-size: 8px;">BRANCH: ${project.branch}</span>
          </div>
          <span style="font-size: 11px; color: var(--text-muted); display: block; margin-top: 2px;">
            STACK: ${project.language} · SANDBOX ACTIVE
          </span>
        </div>

        <span class="badge badge-green" style="font-size: 9px;">
          ${project.status.toUpperCase()}
        </span>
      </div>

      <!-- Active Tasks & Diff Review -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        <span class="label-caps" style="color: var(--text-secondary);">WORKSPACE CODE DIRECTIVES</span>

        ${project.tasks.map(task => `
          <div class="hud-panel" style="padding: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 6px;">
              <h3 style="font-size: 13px; font-weight: 700; color: var(--text-primary);">
                ${task.title}
              </h3>
              <span class="badge ${task.status === 'applied' ? 'badge-green' : 'badge-amber'}" style="font-size: 8px;">
                ${task.status.toUpperCase()}
              </span>
            </div>

            <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 8px;">
              ${task.description}
            </p>

            <!-- Code Diff View -->
            <div style="
              background: var(--surface-input);
              border: 1px solid rgba(0, 240, 255, 0.18);
              padding: 10px;
              font-family: var(--font-telemetry);
              font-size: 11px;
              color: var(--success-green);
              white-space: pre-wrap;
              clip-path: var(--chamfer-clip-sm);
              margin-bottom: 10px;
            ">
              ${task.diff}
            </div>

            <!-- Test Results Line -->
            <div style="display: flex; align-items: center; justify-content: space-between; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px;">
              <div style="display: flex; align-items: center; gap: 6px;">
                <span class="material-symbols-outlined" style="font-size: 14px; color: var(--success-green);">check_circle</span>
                <span class="font-telemetry" style="font-size: 10px; color: var(--text-muted);">${task.testResults}</span>
              </div>

              <div style="display: flex; gap: 6px;">
                <button onclick="window.jarvisApp.simulateRunTests('${task.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
                  Run Tests
                </button>
                ${task.status !== 'applied' ? `
                  <button onclick="window.jarvisApp.confirmApplyCodePatch('${task.id}')" class="hud-btn" style="font-size: 9px; padding: 4px 8px;">
                    Apply Patch
                  </button>
                ` : ''}
              </div>
            </div>

          </div>
        `).join('')}
      </div>

    </div>
  `;
}
