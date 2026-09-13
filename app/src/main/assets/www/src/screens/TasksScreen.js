// ==========================================================================
// Tasks Screen: Directive Management & Scheduler
// ==========================================================================

import { store } from '../services/store.js';

let currentFilter = 'all'; // 'all' | 'active' | 'scheduled' | 'completed'

export function setTaskFilter(filter) {
  currentFilter = filter;
  window.jarvisApp.render();
}

export function renderTasksScreen() {
  const state = store.state;
  let filtered = state.tasks;
  if (currentFilter !== 'all') {
    filtered = state.tasks.filter(t => t.status === currentFilter);
  }

  const activeCount = state.tasks.filter(t => t.status === 'active').length;
  const totalCount = state.tasks.length;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title & Action Bar -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <span class="label-caps" style="color: var(--cyan-core);">TACTICAL DIRECTIVES</span>
          <h2 class="hud-title" style="font-size: 18px; margin-top: 2px;">Task Matrix</h2>
        </div>

        <button onclick="window.jarvisApp.openTaskModal()" class="hud-btn" style="padding: 8px 12px; font-size: 11px;">
          <span class="material-symbols-outlined" style="font-size: 16px;">add</span>
          New Task
        </button>
      </div>

      <!-- Filters & Counter Bar -->
      <div class="hud-panel" style="padding: 10px; display: flex; align-items: center; justify-content: space-between; gap: 8px; flex-wrap: wrap;">
        <!-- Segmented Filter Buttons -->
        <div style="display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none;">
          ${['all', 'active', 'scheduled', 'completed'].map(f => {
            const isActive = currentFilter === f;
            const bg = isActive ? 'var(--cyan-core)' : 'transparent';
            const col = isActive ? 'var(--bg-void)' : 'var(--text-secondary)';
            return `
              <button onclick="window.jarvisApp.filterTasks('${f}')" style="
                background: ${bg};
                color: ${col};
                border: 1px solid ${isActive ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
                font-family: var(--font-telemetry);
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                padding: 4px 10px;
                cursor: pointer;
                transition: all 0.15s ease;
                clip-path: var(--chamfer-clip-sm);
              ">
                ${f}
              </button>
            `;
          }).join('')}
        </div>

        <!-- Task Count Badge -->
        <span class="badge badge-cyan" style="font-size: 9px;">
          ${activeCount} ACTIVE / ${totalCount} TOTAL
        </span>
      </div>

      <!-- Task List Container -->
      <div style="display: flex; flex-direction: column; gap: 10px;">
        ${filtered.length === 0 ? `
          <div class="hud-panel" style="padding: 30px 20px; text-align: center;">
            <span class="material-symbols-outlined" style="font-size: 36px; color: var(--cyan-core); opacity: 0.5;">assignment_turned_in</span>
            <h4 class="hud-title" style="font-size: 14px; margin-top: 8px;">No Directives Match Filter</h4>
            <p style="font-size: 11px; color: var(--text-muted); margin-top: 4px;">
              All tasks in this category have been cleared or have not yet been initialized.
            </p>
          </div>
        ` : filtered.map(task => {
          const isDone = task.status === 'completed';
          const pCol = task.priority === 'high' ? 'var(--alert-red)' : (task.priority === 'medium' ? 'var(--warning-amber)' : 'var(--cyan-core)');

          return `
            <div class="hud-panel" style="
              padding: 12px;
              opacity: ${isDone ? '0.75' : '1'};
              border-color: ${isDone ? 'rgba(0, 255, 178, 0.3)' : 'rgba(0, 240, 255, 0.22)'};
            ">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; margin-bottom: 6px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <!-- Checkbox Status Toggle -->
                  <button onclick="window.jarvisApp.toggleTask('${task.id}')" style="
                    width: 22px;
                    height: 22px;
                    background: ${isDone ? 'var(--success-green)' : 'var(--surface-input)'};
                    border: 1.5px solid ${isDone ? 'var(--success-green)' : 'var(--cyan-core)'};
                    color: var(--bg-void);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    cursor: pointer;
                    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 4px), calc(100% - 4px) 100%, 0 100%);
                  ">
                    ${isDone ? '<span class="material-symbols-outlined" style="font-size: 16px;">check</span>' : ''}
                  </button>

                  <h3 style="
                    font-size: 14px;
                    font-weight: 700;
                    color: ${isDone ? 'var(--text-muted)' : 'var(--text-primary)'};
                    text-decoration: ${isDone ? 'line-through' : 'none'};
                  ">
                    ${task.title}
                  </h3>
                </div>

                <!-- Priority Badge -->
                <span class="badge" style="border: 1px solid ${pCol}; color: ${pCol}; background: rgba(0,0,0,0.3); font-size: 9px;">
                  ${task.priority.toUpperCase()}
                </span>
              </div>

              <!-- Description -->
              <p style="font-size: 12px; color: var(--text-secondary); margin-bottom: 10px; line-height: 1.4; padding-left: 30px;">
                ${task.description}
              </p>

              <!-- Progress Bar -->
              <div style="padding-left: 30px; margin-bottom: 8px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 3px;">
                  <span class="label-caps" style="font-size: 8px;">EXECUTION PROGRESS</span>
                  <span class="font-telemetry" style="font-size: 9px; color: var(--cyan-core);">${task.progress}%</span>
                </div>
                <div style="width: 100%; height: 4px; background: var(--surface-dim); overflow: hidden; border-radius: 2px;">
                  <div style="width: ${task.progress}%; height: 100%; background: ${isDone ? 'var(--success-green)' : 'var(--cyan-core)'}; transition: width 0.3s ease;"></div>
                </div>
              </div>

              <!-- Footer: Due Date, Category, and Delete Action -->
              <div style="display: flex; justify-content: space-between; align-items: center; padding-left: 30px; padding-top: 6px; border-top: 1px solid rgba(0, 240, 255, 0.08);">
                <div style="display: flex; align-items: center; gap: 8px;">
                  <span class="label-caps" style="font-size: 8px;">DUE: ${task.dueDate}</span>
                  <span class="badge badge-cyan" style="font-size: 8px;">${task.category}</span>
                </div>

                <button onclick="window.jarvisApp.confirmDeleteTask('${task.id}')" style="background: none; border: none; cursor: pointer; color: var(--alert-red); display: flex; align-items: center; gap: 2px;">
                  <span class="material-symbols-outlined" style="font-size: 14px;">delete</span>
                  <span style="font-size: 9px;" class="label-caps">PURGE</span>
                </button>
              </div>

            </div>
          `;
        }).join('')}
      </div>

    </div>
  `;
}
