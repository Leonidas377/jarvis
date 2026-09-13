// ==========================================================================
// Chat Screen: Conversational Interface with Local Mock Engine
// ==========================================================================

import { store } from '../services/store.js';

export function renderChatScreen() {
  const state = store.state;
  const messages = state.chatMessages;

  return `
    <div class="screen-container" style="flex: 1; display: flex; flex-direction: column; height: calc(100vh - var(--header-height) - var(--nav-height));">
      
      <!-- Top Action Bar -->
      <div style="
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 8px 14px;
        background: rgba(8, 18, 30, 0.75);
        border-bottom: var(--border-cyan);
      ">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--cyan-core);" class="animate-pulse-glow"></span>
          <span class="label-caps" style="color: var(--cyan-core);">NEURAL CHAT MATRIX // DEMO ENGINE</span>
        </div>

        <button onclick="window.jarvisApp.confirmClearChat()" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
          <span class="material-symbols-outlined" style="font-size: 13px;">delete_sweep</span>
          CLEAR LOG
        </button>
      </div>

      <!-- Scrollable Message Stream -->
      <div id="chat-stream" class="hud-scroll" style="flex: 1; padding: 14px; display: flex; flex-direction: column; gap: 12px;">
        ${messages.length === 0 ? `
          <div style="text-align: center; margin: auto; padding: 30px 20px;">
            <span class="material-symbols-outlined" style="font-size: 42px; color: var(--cyan-core); opacity: 0.6;">forum</span>
            <h4 class="hud-title" style="font-size: 14px; margin-top: 8px;">Comms Buffer Empty</h4>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">
              Transmit a command, tap a suggested prompt, or use voice input to initiate a dialogue with J.A.R.V.I.S.
            </p>
          </div>
        ` : messages.map(msg => {
          const isUser = msg.sender === 'user';
          const align = isUser ? 'flex-end' : 'flex-start';
          const bg = isUser ? 'var(--surface-high)' : 'var(--surface-card)';
          const border = isUser ? '1px solid rgba(0, 114, 255, 0.4)' : 'var(--border-cyan)';
          const nameColor = isUser ? 'var(--plasma-cobalt)' : 'var(--cyan-core)';

          return `
            <div style="display: flex; flex-direction: column; align-items: ${align}; max-width: 88%; align-self: ${align};">
              <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 2px; padding: 0 4px;">
                <span class="label-caps" style="font-size: 8px; color: ${nameColor};">
                  ${isUser ? 'T. STARK // USER' : 'J.A.R.V.I.S.'}
                </span>
                <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">${msg.timestamp}</span>
              </div>

              <div class="hud-panel" style="background: ${bg}; border: ${border}; padding: 10px 14px; clip-path: var(--chamfer-clip-sm);">
                <p style="font-size: 13px; color: var(--text-primary); line-height: 1.5; white-space: pre-wrap;">
                  ${msg.text}
                </p>

                ${msg.citations && msg.citations.length > 0 ? `
                  <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 8px; padding-top: 6px; border-top: 1px solid rgba(0, 240, 255, 0.1);">
                    ${msg.citations.map(c => `
                      <span class="badge badge-cyan" style="font-size: 8px;">
                        <span class="material-symbols-outlined" style="font-size: 10px;">verified</span>
                        ${c}
                      </span>
                    `).join('')}
                  </div>
                ` : ''}

                ${msg.uncertainty ? `
                  <div style="margin-top: 4px;">
                    <span class="label-caps" style="font-size: 8px; color: var(--text-muted);">
                      CONFIDENCE: ${msg.uncertainty}
                    </span>
                  </div>
                ` : ''}
              </div>

              <!-- Message Controls (Copy / Retry) -->
              <div style="display: flex; gap: 6px; margin-top: 2px; padding: 0 4px;">
                <button onclick="window.jarvisApp.copyToClipboard('${encodeURIComponent(msg.text)}')" style="background: none; border: none; cursor: pointer; color: var(--text-muted); display: flex; align-items: center; gap: 2px;">
                  <span class="material-symbols-outlined" style="font-size: 12px;">content_copy</span>
                  <span style="font-size: 9px;">Copy</span>
                </button>
                ${!isUser ? `
                  <button onclick="window.jarvisApp.retryLastPrompt()" style="background: none; border: none; cursor: pointer; color: var(--text-muted); display: flex; align-items: center; gap: 2px;">
                    <span class="material-symbols-outlined" style="font-size: 12px;">refresh</span>
                    <span style="font-size: 9px;">Regenerate</span>
                  </button>
                ` : ''}
              </div>
            </div>
          `;
        }).join('')}
      </div>

      <!-- Suggested Prompts Strip -->
      <div style="
        display: flex;
        gap: 6px;
        overflow-x: auto;
        padding: 6px 14px;
        background: rgba(4, 8, 15, 0.9);
        border-top: 1px solid rgba(0, 240, 255, 0.1);
        scrollbar-width: none;
      ">
        <button onclick="window.jarvisApp.sendPrompt('show my tasks')" class="hud-btn-ghost" style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
          “show my tasks”
        </button>
        <button onclick="window.jarvisApp.sendPrompt('show market summary')" class="hud-btn-ghost" style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
          “show market summary”
        </button>
        <button onclick="window.jarvisApp.sendPrompt('search for next-gen photonics')" class="hud-btn-ghost" style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
          “search for photonics”
        </button>
        <button onclick="window.jarvisApp.sendPrompt('create a task review architecture')" class="hud-btn-ghost" style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
          “create a task...”
        </button>
        <button onclick="window.jarvisApp.sendPrompt('start a coding task')" class="hud-btn-ghost" style="font-size: 10px; padding: 4px 8px; white-space: nowrap;">
          “start a coding task”
        </button>
      </div>

      <!-- Input Bar -->
      <div style="
        padding: 10px 14px;
        background: rgba(8, 18, 30, 0.92);
        border-top: var(--border-cyan);
        display: flex;
        align-items: center;
        gap: 8px;
      ">
        <!-- Attachment Button -->
        <button onclick="window.jarvisApp.handleAttachmentClick()" class="hud-btn-ghost" style="width: 38px; height: 38px; padding: 0; display: flex; align-items: center; justify-content: center;" title="Attach workspace file">
          <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">attach_file</span>
        </button>

        <!-- Voice Button -->
        <button onclick="window.jarvisApp.triggerVoiceModal()" class="hud-btn-ghost" style="width: 38px; height: 38px; padding: 0; display: flex; align-items: center; justify-content: center;" title="Voice mode">
          <span class="material-symbols-outlined" style="font-size: 20px; color: var(--cyan-core);">mic</span>
        </button>

        <!-- Text Input Field -->
        <input 
          type="text" 
          id="chat-input" 
          class="hud-input" 
          placeholder="Command J.A.R.V.I.S. (e.g. search, tasks, markets)..." 
          style="flex: 1;"
          onkeydown="if(event.key === 'Enter') window.jarvisApp.submitChatInput()"
        >

        <!-- Send Button -->
        <button onclick="window.jarvisApp.submitChatInput()" class="hud-btn" style="padding: 10px 14px;">
          <span class="material-symbols-outlined" style="font-size: 18px;">send</span>
        </button>
      </div>

    </div>
  `;
}
