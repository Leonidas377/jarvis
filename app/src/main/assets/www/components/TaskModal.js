// ==========================================================================
// Add Task Modal Component
// ==========================================================================

export function renderTaskModal() {
  return `
    <div id="task-modal" class="hud-modal-overlay">
      <div class="hud-modal-content" style="padding: 24px 16px 28px 16px;">
        
        <!-- Header -->
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">TASK SCHEDULER</span>
            <h3 class="hud-title" style="font-size: 16px; margin-top: 2px;">Create New Directive</h3>
          </div>
          <button onclick="window.jarvisApp.closeTaskModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Form -->
        <div style="display: flex; flex-direction: column; gap: 12px; margin-bottom: 20px;">
          <div>
            <label class="label-caps" style="display: block; margin-bottom: 4px;">Task Title</label>
            <input type="text" id="task-input-title" class="hud-input" placeholder="e.g. Backtest Quantum Trailing Model">
          </div>

          <div>
            <label class="label-caps" style="display: block; margin-bottom: 4px;">Specification / Description</label>
            <textarea id="task-input-desc" class="hud-input" rows="3" placeholder="Detail subroutines and objectives..." style="resize: none;"></textarea>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <div>
              <label class="label-caps" style="display: block; margin-bottom: 4px;">Priority Level</label>
              <select id="task-input-priority" class="hud-input" style="background: var(--surface-input); color: var(--text-primary);">
                <option value="high">High (P1)</option>
                <option value="medium" selected>Medium (P2)</option>
                <option value="low">Low (P3)</option>
              </select>
            </div>

            <div>
              <label class="label-caps" style="display: block; margin-bottom: 4px;">Category Domain</label>
              <select id="task-input-category" class="hud-input" style="background: var(--surface-input); color: var(--text-primary);">
                <option value="research">Research</option>
                <option value="code">Code</option>
                <option value="markets">Markets</option>
                <option value="devices">Devices</option>
                <option value="general" selected>General</option>
              </select>
            </div>
          </div>

          <div>
            <label class="label-caps" style="display: block; margin-bottom: 4px;">Due Date / Window</label>
            <input type="text" id="task-input-due" class="hud-input" placeholder="e.g. Today, 06:00 PM">
          </div>
        </div>

        <!-- Submit Button -->
        <button onclick="window.jarvisApp.submitNewTask()" class="hud-btn" style="width: 100%; padding: 12px;">
          <span class="material-symbols-outlined" style="font-size: 18px;">add_task</span>
          Deploy Directive
        </button>

      </div>
    </div>
  `;
}
