// ==========================================================================
// Files Screen: Controlled Workspace Explorer
// ==========================================================================

import { store } from '../services/store.js';

let viewingFile = null;

export function setViewingFile(file) {
  viewingFile = file;
  window.jarvisApp.render();
}

export function renderFilesScreen() {
  const state = store.state;
  const files = state.files;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Back Button -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">WORKSPACE ENCLAVE</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">Files Storage</h2>
          </div>
        </div>

        <button onclick="window.jarvisApp.promptNewFile()" class="hud-btn" style="padding: 6px 10px; font-size: 10px;">
          <span class="material-symbols-outlined" style="font-size: 14px;">note_add</span>
          New File
        </button>
      </div>

      <!-- Workspace Path Info -->
      <div class="hud-panel" style="padding: 10px 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 6px;">
          <span class="material-symbols-outlined" style="font-size: 16px; color: var(--cyan-core);">folder</span>
          <span class="font-telemetry" style="font-size: 11px; color: var(--text-primary);">/sandbox/workspace_alpha/</span>
        </div>
        <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">${files.length} ITEMS</span>
      </div>

      <!-- File List -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${files.map(f => {
          let icon = 'description';
          if (f.type === 'python') icon = 'code';
          if (f.type === 'json') icon = 'data_object';
          if (f.type === 'markdown') icon = 'text_snippet';

          return `
            <div class="hud-panel" style="
              padding: 10px 12px;
              display: flex;
              align-items: center;
              justify-content: space-between;
              cursor: pointer;
            " onclick="window.jarvisApp.openFilePreview('${f.id}')">
              <div style="display: flex; align-items: center; gap: 10px; min-width: 0;">
                <span class="material-symbols-outlined" style="font-size: 22px; color: var(--cyan-core); shrink-0;">${icon}</span>
                <div style="min-width: 0;">
                  <span style="font-size: 13px; font-weight: 600; color: var(--text-primary); font-family: var(--font-telemetry); display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    ${f.name}
                  </span>
                  <div style="display: flex; gap: 8px; align-items: center; margin-top: 1px;">
                    <span class="label-caps" style="font-size: 8px;">${f.size}</span>
                    <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">${f.modifiedAt}</span>
                  </div>
                </div>
              </div>

              <!-- Delete Action -->
              <button onclick="event.stopPropagation(); window.jarvisApp.confirmDeleteFile('${f.id}', '${f.name}')" class="hud-btn-ghost" style="width: 28px; height: 28px; padding: 0; display: flex; align-items: center; justify-content: center; color: var(--alert-red);" title="Delete File">
                <span class="material-symbols-outlined" style="font-size: 16px;">delete</span>
              </button>
            </div>
          `;
        }).join('')}
      </div>

      <!-- File Preview Modal (if active) -->
      ${viewingFile ? `
        <div id="file-preview-modal" class="hud-modal-overlay active">
          <div class="hud-modal-content" style="padding: 20px 16px 28px 16px; max-height: 80vh;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
              <div>
                <span class="label-caps" style="color: var(--cyan-core);">FILE INSPECTOR</span>
                <h3 class="font-telemetry" style="font-size: 14px; color: var(--text-primary); margin-top: 2px;">${viewingFile.name}</h3>
              </div>
              <button onclick="window.jarvisApp.closeFilePreview()" class="hud-btn-ghost" style="width: 30px; height: 30px; padding: 0; display: flex; align-items: center; justify-content: center;">
                <span class="material-symbols-outlined" style="font-size: 16px;">close</span>
              </button>
            </div>

            <div style="
              flex: 1;
              background: var(--surface-input);
              border: var(--border-cyan);
              padding: 12px;
              font-family: var(--font-telemetry);
              font-size: 12px;
              color: var(--text-primary);
              overflow-y: auto;
              white-space: pre-wrap;
              clip-path: var(--chamfer-clip-sm);
              margin-bottom: 14px;
              max-height: 340px;
            ">
              ${viewingFile.content || '// Empty document buffer.'}
            </div>

            <button onclick="window.jarvisApp.closeFilePreview()" class="hud-btn" style="width: 100%;">
              Dismiss Preview
            </button>
          </div>
        </div>
      ` : ''}

    </div>
  `;
}
