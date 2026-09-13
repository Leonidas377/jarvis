// ==========================================================================
// J.A.R.V.I.S. Main Application Controller & Router
// ==========================================================================

import { store } from './services/store.js';
import { jarvisApi } from './services/api.js';
import { renderHeader } from './components/Header.js';
import { renderBottomNav } from './components/BottomNav.js';
import { renderMoreModal } from './components/MoreModal.js';
import { renderVoiceModal } from './components/VoiceModal.js';
import { renderTaskModal } from './components/TaskModal.js';
import { renderApprovalModal } from './components/ApprovalModal.js';
import { renderAssetDetailModal } from './components/AssetDetailModal.js';
import { renderLLMConfigModal } from './components/LLMConfigModal.js';
import { initWaveformAnimation } from './components/VoiceWaveform.js';

import { renderCoreScreen } from './screens/CoreScreen.js';
import { renderChatScreen } from './screens/ChatScreen.js';
import { renderTasksScreen, setTaskFilter } from './screens/TasksScreen.js';
import { 
  renderResearchScreen, 
  executeSearch, 
  setResearchTab, 
  toggleSourceSelection, 
  generateCitedReport, 
  openReportDetail, 
  closeReportModal, 
  deleteReportAction, 
  summarizeSingleSource, 
  closeSummaryModal, 
  openExternalUrl, 
  loadSavedReports, 
  loadSavedBriefs,
  loadSearchHistory,
  triggerBriefAction,
  saveCurrentBrief,
  shareCurrentBrief,
  highlightCitation,
  toggleRelatedSources,
  askFollowUpPrompt,
  searchSavedBriefs,
  renameBriefAction,
  deleteBriefAction,
  exportBriefAction,
  openBriefDetail
} from './screens/ResearchScreen.js';


import { 
  renderNewsScreen, 
  setNewsCategory, 
  setNewsTopic,
  loadNewsData, 
  loadTopics, 
  subscribeTopicAction, 
  unsubscribeTopicAction, 
  toggleArticleRead, 
  toggleArticleSaved, 
  toggleClusterExpanded,
  summarizeClusterAction,
  generateNewsBriefing, 
  saveActiveBriefingAction,
  closeBriefingModal, 
  toggleTopicsModal, 
  toggleNotificationsModal,
  openArticleLink 
} from './screens/NewsScreen.js';
import { renderMarketsScreen, setMarketSubTab } from './screens/MarketsScreen.js';
import { renderCodeScreen } from './screens/CodeScreen.js';
import { renderDevicesScreen } from './screens/DevicesScreen.js';
import { renderFilesScreen, setViewingFile } from './screens/FilesScreen.js';
import { renderMemoryScreen, setMemoryFilter } from './screens/MemoryScreen.js';
import { renderSettingsScreen } from './screens/SettingsScreen.js';
import { renderIntegrationsScreen } from './screens/IntegrationsScreen.js';

class JarvisApp {
  constructor() {
    this.approvalConfig = null;
    this.selectedAssetSymbol = null;
    this.audioCtx = null;
    this.llmModalOpen = false;
    this.llmConfig = null;
    this.llmTestResult = null;
    this.llmLoading = false;
    this.llmTesting = false;
  }

  init() {
    // Subscribe to store updates to trigger re-renders
    store.subscribe(() => {
      this.render();
    });

    // Android / Browser Back navigation handler
    window.addEventListener('popstate', () => {
      this.handleBack();
    });

    // Initial render
    this.render();
    initWaveformAnimation();
  }

  // Audio / Haptic Feedback
  playHudBeep(freq = 880, duration = 0.04) {
    if (!store.state.settings.soundEffects) return;
    try {
      if (!this.audioCtx) {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (this.audioCtx.state === 'suspended') {
        this.audioCtx.resume();
      }
      const osc = this.audioCtx.createOscillator();
      const gain = this.audioCtx.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime);
      gain.gain.setValueAtTime(0.04, this.audioCtx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, this.audioCtx.currentTime + duration);
      osc.connect(gain);
      gain.connect(this.audioCtx.destination);
      osc.start();
      osc.stop(this.audioCtx.currentTime + duration);
    } catch (e) {
      // Audio not permitted yet
    }
  }

  triggerHaptic(duration = 20) {
    if (!store.state.settings.hapticFeedback) return;
    if (window.navigator && window.navigator.vibrate) {
      window.navigator.vibrate(duration);
    }
    // Native Android Bridge hook if present
    if (window.Android && window.Android.vibrate) {
      window.Android.vibrate(duration);
    }
  }

  // Navigation
  navigate(screenId) {
    this.playHudBeep(700, 0.03);
    this.triggerHaptic(15);
    store.navigate(screenId);
    window.history.pushState({ screen: screenId }, '', `#${screenId}`);
    window.scrollTo(0, 0);
    if (screenId === 'news') {
      loadNewsData();
    } else if (screenId === 'research') {
      loadSavedReports();
    }
  }

  handleBack() {
    if (this.approvalConfig) {
      this.closeApprovalModal();
      return;
    }
    if (this.selectedAssetSymbol) {
      this.closeAssetDetailModal();
      return;
    }
    const isModalOpen = document.querySelector('.hud-modal-overlay.active');
    if (isModalOpen) {
      isModalOpen.classList.remove('active');
      return;
    }
    store.goBack();
  }

  goBack() {
    this.handleBack();
  }

  handleNavTab(tabId) {
    if (tabId === 'more') {
      this.openMoreModal();
    } else {
      this.navigate(tabId);
    }
  }

  // Modals
  openMoreModal() {
    this.playHudBeep(600, 0.04);
    const modal = document.getElementById('more-modal');
    if (modal) modal.classList.add('active');
  }

  closeMoreModal() {
    const modal = document.getElementById('more-modal');
    if (modal) modal.classList.remove('active');
  }

  openMoreScreen(screenId) {
    this.closeMoreModal();
    this.navigate(screenId);
  }

  triggerVoiceModal() {
    this.playHudBeep(900, 0.05);
    this.triggerHaptic(25);
    store.setAssistantState('LISTENING');
    const modal = document.getElementById('voice-modal');
    if (modal) modal.classList.add('active');
  }

  closeVoiceModal() {
    store.setAssistantState('READY');
    const modal = document.getElementById('voice-modal');
    if (modal) modal.classList.remove('active');
  }

  handleVoiceSimulate(commandText) {
    this.playHudBeep(850, 0.05);
    store.setAssistantState('THINKING');
    const statusText = document.getElementById('voice-status-text');
    if (statusText) {
      statusText.innerHTML = `
        <span class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--warning-amber); letter-spacing: 0.1em; display: block;">
          PROCESSING DIRECTIVE: "${commandText}"
        </span>
      `;
    }

    setTimeout(() => {
      store.setAssistantState('SPEAKING');
      this.closeVoiceModal();
      this.sendPrompt(commandText);
      setTimeout(() => {
        store.setAssistantState('READY');
      }, 2500);
    }, 900);
  }

  submitVoiceFallback() {
    const input = document.getElementById('voice-fallback-input');
    if (input && input.value.trim()) {
      const text = input.value.trim();
      input.value = '';
      this.handleVoiceSimulate(text);
    }
  }

  openTaskModal() {
    this.playHudBeep(650, 0.04);
    const modal = document.getElementById('task-modal');
    if (modal) modal.classList.add('active');
  }

  closeTaskModal() {
    const modal = document.getElementById('task-modal');
    if (modal) modal.classList.remove('active');
  }

  submitNewTask() {
    const title = document.getElementById('task-input-title').value.trim();
    const desc = document.getElementById('task-input-desc').value.trim();
    const priority = document.getElementById('task-input-priority').value;
    const category = document.getElementById('task-input-category').value;
    const due = document.getElementById('task-input-due').value.trim() || 'Tomorrow';

    if (!title) {
      alert('Please provide a directive title.');
      return;
    }

    this.playHudBeep(920, 0.06);
    this.triggerHaptic(30);
    store.addTask(title, desc || 'Standard operational task.', priority, category, due);
    this.closeTaskModal();
    if (store.state.activeScreen !== 'tasks') {
      this.navigate('tasks');
    }
  }

  // Approval Modal Actions
  showApprovalModal(title, message, riskLevel, onConfirmFn) {
    this.approvalConfig = { title, message, riskLevel, onConfirmFn };
    this.render();
  }

  closeApprovalModal() {
    this.approvalConfig = null;
    this.render();
  }

  // Asset Detail Modal
  openAssetDetail(symbol) {
    this.playHudBeep(750, 0.04);
    this.selectedAssetSymbol = symbol;
    this.render();
  }

  closeAssetDetailModal() {
    this.selectedAssetSymbol = null;
    this.render();
  }

  toggleWatchlistAction(symbol) {
    this.playHudBeep(880, 0.04);
    this.triggerHaptic(20);
    store.toggleWatchlist(symbol);
    this.render();
  }

  deepDiveResearch(query) {
    this.closeAssetDetailModal();
    this.navigate('research');
    executeSearch(query);
  }

  // Chat Actions
  async sendPrompt(text) {
    store.addMessage('user', text);
    this.playHudBeep(720, 0.03);
    await this.processCommand(text);
  }

  submitChatInput() {
    const input = document.getElementById('chat-input');
    if (input && input.value.trim()) {
      const text = input.value.trim();
      input.value = '';
      this.sendPrompt(text);
    }
  }

  async processCommand(rawText) {
    store.setAssistantState('THINKING');

    try {
      // Send chat command to Python FastAPI AI Orchestrator
      const chatResult = await jarvisApi.sendChat(rawText);

      // 1. Check if backend policy triggered an explicit approval gate
      if (chatResult.approval_required && chatResult.approval_request) {
        const appReq = chatResult.approval_request;
        store.addMessage('jarvis', chatResult.response, ['POLICY_GATE', appReq.risk_level], 'Authorization Pending');
        store.setAssistantState('READY');

        this.showApprovalModal(
          `Directive Authorization Required: ${appReq.tool_name}`,
          `The cognitive core requested: ${appReq.summary}\n\nSecurity Risk: ${appReq.risk_level}\nDo you explicitly authorize J.A.R.V.I.S. to execute this directive?`,
          appReq.risk_level,
          async () => {
            try {
              store.setAssistantState('THINKING');
              this.closeApprovalModal();
              // User confirmed: decide and execute on backend
              await jarvisApi.decideApproval(appReq.id, 'approve');
              const execRes = await jarvisApi.executeApproval(appReq.id);
              store.addMessage('jarvis', `Directive authorized and executed successfully, sir.\nResult: ${JSON.stringify(execRes.result || 'Success')}`, ['USER_AUTHORIZED', 'AUDIT_LOGGED'], 'Verified 100%');
              store.setAssistantState('SPEAKING');
              setTimeout(() => store.setAssistantState('READY'), 1500);
            } catch (err) {
              store.addMessage('jarvis', `Failed to execute approved directive: ${err.message}`, ['SECURITY_ALERT'], 'Execution Fault');
              store.setAssistantState('READY');
            }
          }
        );
        return;
      }

      // 2. Safe tool or conversational response
      let citations = ['JARVIS_CORE', 'AI_ORCHESTRATOR'];
      if (chatResult.tool_executed) {
        citations.push(chatResult.tool_executed.tool.toUpperCase());
        // Sync tasks if task was created
        if (chatResult.tool_executed.tool === 'create_task') {
          const res = chatResult.tool_executed.result;
          store.addTask(res.title, res.summary || '', res.priority || 'medium', 'general', res.due_date || 'Today');
        } else if (chatResult.tool_executed.tool === 'save_memory') {
          const res = chatResult.tool_executed.result;
          store.addMemory(res.category || 'General', res.key || 'Fact', res.value || '');
        }
      }

      store.addMessage('jarvis', chatResult.response, citations, 'Verified with 99.4% confidence');
      store.setAssistantState('SPEAKING');

      // Scroll chat to bottom
      const stream = document.getElementById('chat-stream');
      if (stream) {
        stream.scrollTop = stream.scrollHeight;
      }

      setTimeout(() => {
        store.setAssistantState('READY');
      }, 1500);

    } catch (err) {
      console.warn('Backend API connection failed, executing fallback:', err);
      this.runLocalFallbackCommand(rawText);
    }
  }

  runLocalFallbackCommand(rawText) {
    const text = rawText.toLowerCase().trim();
    setTimeout(() => {
      let response = '';
      let citations = ['OFFLINE_CLIENT'];
      let uncertainty = 'Local Fallback Simulation';

      if (text.startsWith('search for') || text.startsWith('search')) {
        const query = text.replace(/^search(\s+for)?\s*/i, '');
        response = `Understood, sir. Initiated deep web analysis for "${query}". Found 2 authoritative papers and official benchmarks. Data summarized and saved to your Research Portal.`;
        citations = ['RESEARCH_GATEWAY_V1', 'SEMICONDUCTOR_CONSORTIUM'];
        executeSearch(query || 'Photonic Clusters');
      } else if (text.startsWith('create a task') || text.startsWith('create task')) {
        const taskName = text.replace(/^create(\s+a)?\s+task\s*/i, '') || 'New Directive';
        store.addTask(taskName, 'Generated autonomously via chat command.', 'medium', 'general', 'Tomorrow');
        response = `Directive registered: "${taskName}". Priority set to Medium. Added to your active task scheduler.`;
        citations = ['TASK_ENGINE_V1'];
      } else if (text.includes('show my tasks') || text.includes('show tasks')) {
        const activeTasks = store.state.tasks.filter(t => t.status === 'active');
        response = `You have ${activeTasks.length} active directives in the matrix:\n` + 
          activeTasks.map(t => `• ${t.title} [${t.priority.toUpperCase()}] (${t.progress}%)`).join('\n');
        citations = ['TASK_SCHEDULER'];
      } else if (text.includes('show market summary') || text.includes('market summary')) {
        response = `Market Snapshot (Simulated Data):\n• S&P 500: $5,842.10 (+0.59%)\n• NASDAQ: $18,410.50 (+0.78%)\n• NVDA: $138.45 (+2.33%)\n• BTC Core: $68,420.00 (+2.73%)\nOverall trajectory is bullish with strong semiconductor volume.`;
        citations = ['FINANCIAL_TELEMETRY', 'MARKET_RADAR'];
      } else {
        response = `Command received: "${rawText}". All local subroutines operating in client sandbox mode.`;
      }

      store.addMessage('jarvis', response, citations, uncertainty);
      store.setAssistantState('SPEAKING');

      const stream = document.getElementById('chat-stream');
      if (stream) {
        stream.scrollTop = stream.scrollHeight;
      }

      setTimeout(() => {
        store.setAssistantState('READY');
      }, 1500);
    }, 400);
  }

  confirmClearChat() {
    this.showApprovalModal(
      'Purge Comms Buffer',
      'This will erase all active messages and dialogue history from this session. This action cannot be reversed.',
      'R1_LOW',
      () => {
        store.clearChat();
        this.closeApprovalModal();
      }
    );
  }

  copyToClipboard(encodedText) {
    const text = decodeURIComponent(encodedText);
    navigator.clipboard.writeText(text).then(() => {
      this.playHudBeep(950, 0.03);
      alert('Copied to clipboard.');
    });
  }

  retryLastPrompt() {
    const msgs = store.state.chatMessages;
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].sender === 'user') {
        this.processCommand(msgs[i].text);
        break;
      }
    }
  }

  handleAttachmentClick() {
    this.playHudBeep(780, 0.04);
    alert('Workspace File Attachment: Select a file from /sandbox/workspace_alpha/ or upload via Android storage.');
  }

  // Task Actions
  filterTasks(filter) {
    this.playHudBeep(750, 0.03);
    setTaskFilter(filter);
  }

  toggleTask(taskId) {
    this.playHudBeep(880, 0.04);
    this.triggerHaptic(20);
    store.toggleTaskStatus(taskId);
  }

  confirmDeleteTask(taskId) {
    this.showApprovalModal(
      'Delete Directive',
      'Are you sure you want to permanently delete this task from the directive matrix?',
      'R1_LOW',
      () => {
        store.deleteTask(taskId);
        this.closeApprovalModal();
      }
    );
  }

  // Research Actions (Phase 3)
  handleSearchSubmit() {
    const input = document.getElementById('research-search-input');
    if (input && input.value.trim()) {
      this.playHudBeep(820, 0.04);
      executeSearch(input.value.trim());
    }
  }

  runQuickSearch(query) {
    const input = document.getElementById('research-search-input');
    if (input) input.value = query;
    this.playHudBeep(820, 0.04);
    executeSearch(query);
  }

  setResearchTab(tab) {
    this.playHudBeep(700, 0.03);
    setResearchTab(tab);
  }

  toggleSourceSelection(url) {
    this.playHudBeep(800, 0.02);
    toggleSourceSelection(url);
  }

  generateCitedReport() {
    this.playHudBeep(900, 0.05);
    generateCitedReport();
  }

  openReportDetail(id) {
    this.playHudBeep(750, 0.03);
    openReportDetail(id);
  }

  closeReportModal() {
    closeReportModal();
  }

  deleteReportAction(id) {
    this.playHudBeep(650, 0.04);
    deleteReportAction(id);
  }

  summarizeSingleSource(url, encTitle) {
    const title = decodeURIComponent(encTitle);
    summarizeSingleSource(url, title);
  }

  closeSummaryModal() {
    closeSummaryModal();
  }

  openExternalUrl(url) {
    openExternalUrl(url);
  }

  loadSavedReports() {
    loadSavedReports();
  }

  loadSearchHistory() {
    loadSearchHistory();
  }

  loadSavedBriefs() {
    loadSavedBriefs();
  }

  triggerBriefAction(action) {
    triggerBriefAction(action);
  }

  saveCurrentBrief() {
    saveCurrentBrief();
  }

  shareCurrentBrief() {
    shareCurrentBrief();
  }

  highlightCitation(id) {
    highlightCitation(id);
  }

  toggleRelatedSources() {
    toggleRelatedSources();
  }

  askFollowUpPrompt() {
    askFollowUpPrompt();
  }

  searchSavedBriefs(query) {
    searchSavedBriefs(query);
  }

  renameBriefAction(briefId, title) {
    this.playHudBeep(700, 0.03);
    renameBriefAction(briefId, title);
  }

  deleteBriefAction(briefId) {
    this.playHudBeep(600, 0.04);
    deleteBriefAction(briefId);
  }

  exportBriefAction(briefId) {
    this.playHudBeep(900, 0.04);
    exportBriefAction(briefId);
  }

  openBriefDetail(briefId) {
    this.playHudBeep(780, 0.03);
    openBriefDetail(briefId);
  }


  // News Actions (Phase 5)
  filterNews(cat) {
    this.playHudBeep(750, 0.03);
    setNewsCategory(cat);
  }

  filterNewsTopic(topicId) {
    this.playHudBeep(780, 0.03);
    setNewsTopic(topicId);
  }

  refreshNewsFeed() {
    this.playHudBeep(720, 0.03);
    loadNewsData();
  }

  loadNewsData() {
    loadNewsData();
  }

  toggleClusterExpanded(clusterId) {
    this.playHudBeep(700, 0.02);
    toggleClusterExpanded(clusterId);
  }

  summarizeClusterAction(clusterId) {
    this.playHudBeep(880, 0.04);
    summarizeClusterAction(clusterId);
  }

  generateNewsBriefing(type = 'on_demand', window = '24h') {
    this.playHudBeep(920, 0.05);
    generateNewsBriefing(type, window);
  }

  saveActiveBriefingAction() {
    this.playHudBeep(850, 0.04);
    saveActiveBriefingAction();
  }

  closeBriefingModal() {
    closeBriefingModal();
  }

  toggleTopicsModal(show) {
    this.playHudBeep(750, 0.03);
    toggleTopicsModal(show);
  }

  toggleNotificationsModal(show) {
    this.playHudBeep(750, 0.03);
    toggleNotificationsModal(show);
  }

  subscribeTopicAction(name, type, ticker, notif, thresh) {
    this.playHudBeep(880, 0.04);
    subscribeTopicAction(name, type, ticker, notif, thresh);
  }

  unsubscribeTopicAction(id) {
    this.playHudBeep(700, 0.03);
    unsubscribeTopicAction(id);
  }

  toggleArticleRead(id, current) {
    this.playHudBeep(700, 0.03);
    toggleArticleRead(id, current);
  }

  toggleArticleSaved(id, current) {
    this.playHudBeep(880, 0.04);
    this.triggerHaptic(15);
    toggleArticleSaved(id, current);
  }

  openArticleLink(url) {
    openArticleLink(url);
  }

  // Markets Actions
  setMarketTab(tab) {
    this.playHudBeep(720, 0.03);
    setMarketSubTab(tab);
  }

  // Code Actions
  simulateRunTests(taskId) {
    this.playHudBeep(800, 0.05);
    alert('Simulated Test Runner Executing: Running 10 unit test suites in sandbox container... All 10 passed [84ms].');
  }

  confirmApplyCodePatch(taskId) {
    this.showApprovalModal(
      'Apply Code Patch',
      'This will commit and merge the simulated diff into the active workspace branch. Continue?',
      'R2_MEDIUM',
      () => {
        const project = store.state.codeProjects[0];
        const t = project.tasks.find(x => x.id === taskId);
        if (t) t.status = 'applied';
        store.notify(['codeProjects']);
        this.closeApprovalModal();
        alert('Patch successfully merged into active branch.');
      }
    );
  }

  simulateNewCodeTask() {
    const title = prompt('Enter coding directive objective:');
    if (title) {
      store.state.codeProjects[0].tasks.unshift({
        id: 'ctask-' + Date.now(),
        title,
        description: 'Autonomously scheduled code maintenance.',
        status: 'ready_for_test',
        diff: '+ // Automated subroutine patch\n+ def execute_optimizer():\n+     return True',
        testResults: 'Pending execution'
      });
      store.notify(['codeProjects']);
    }
  }

  // Device Actions
  toggleDeviceAction(devId) {
    this.playHudBeep(840, 0.04);
    this.triggerHaptic(25);
    store.toggleDevice(devId);
  }

  handleDeviceSlider(devId, val) {
    store.setDeviceValue(devId, val);
  }

  simulateAddDevice() {
    const name = prompt('Enter new Smart Device name (e.g. Workshop Exhaust):');
    if (name) {
      store.state.devices.push({
        id: 'dev-' + Date.now(),
        name,
        type: 'light',
        room: 'Workshop',
        isOnline: true,
        state: true,
        value: 100,
        unit: '%'
      });
      store.notify(['devices']);
    }
  }

  // Files Actions
  openFilePreview(fileId) {
    const f = store.state.files.find(x => x.id === fileId);
    if (f) {
      this.playHudBeep(760, 0.04);
      setViewingFile(f);
    }
  }

  closeFilePreview() {
    setViewingFile(null);
  }

  promptNewFile() {
    const name = prompt('Enter file name (e.g. notes_sept_10.md):');
    if (name) {
      store.addFile(name, 'markdown', '# New Document\n\nCreated in JARVIS Workspace.');
    }
  }

  confirmDeleteFile(fileId, fileName) {
    this.showApprovalModal(
      'Permanent File Removal',
      `Are you sure you want to permanently delete "${fileName}" from the sandbox storage?`,
      'R3_HIGH',
      () => {
        store.deleteFile(fileId);
        this.closeApprovalModal();
      }
    );
  }

  // Memory Actions
  filterMemory(query) {
    setMemoryFilter(query);
  }

  promptAddMemory() {
    const key = prompt('Enter preference or fact key:');
    const value = prompt('Enter fact details:');
    if (key && value) {
      store.addMemory('User Fact', key, value);
    }
  }

  confirmDeleteMemory(memId, memKey) {
    this.showApprovalModal(
      'Delete Memory Fact',
      `Erase memory item "${memKey}" from episodic memory?`,
      'R1_LOW',
      () => {
        store.deleteMemory(memId);
        this.closeApprovalModal();
      }
    );
  }

  confirmPurgeAllMemory() {
    this.showApprovalModal(
      'Purge Entire Memory Store',
      'CAUTION: This will permanently wipe all stored user facts, preferences, and trading boundaries. This action is irreversible.',
      'R4_CRITICAL',
      () => {
        store.clearAllMemory();
        this.closeApprovalModal();
        alert('All memory items have been purged.');
      }
    );
  }

  // Settings Actions
  handleGlowSlider(val) {
    store.updateSetting('visualGlowIntensity', Number(val));
    const factor = Number(val) / 100;
    document.documentElement.style.setProperty('--cyan-glow', `rgba(0, 240, 255, ${0.45 * factor})`);
  }

  handleSettingToggle(key, val) {
    this.playHudBeep(750, 0.03);
    store.updateSetting(key, val);
  }

  confirmResetAllData() {
    this.showApprovalModal(
      'Reset All Demo Data',
      'Restore application to initial factory state? All custom tasks, files, memories, and chat history will be reset.',
      'R3_HIGH',
      () => {
        store.resetAllData();
        this.closeApprovalModal();
        alert('Factory demo data restored.');
      }
    );
  }

  simulateConfigureIntegration(name) {
    if (name.toLowerCase().includes('llm') || name.toLowerCase().includes('neural') || name.toLowerCase().includes('gemini') || name.toLowerCase().includes('language')) {
      this.openLLMModal();
    } else {
      alert(`Adapter Gateway for "${name}": OAuth and API credentials will be configurable via the Python backend bridge.`);
    }
  }

  // LLM Configuration Modal Lifecycle & Actions
  async openLLMModal() {
    this.playHudBeep(880, 0.04);
    this.llmLoading = true;
    this.llmModalOpen = true;
    this.llmTestResult = null;
    this.render();

    try {
      this.llmConfig = await jarvisApi.getLLMConfig();
    } catch (e) {
      console.warn('Could not load LLM config:', e);
      this.llmConfig = null;
    } finally {
      this.llmLoading = false;
      this.render();
    }
  }

  closeLLMModal() {
    this.playHudBeep(440, 0.04);
    this.llmModalOpen = false;
    this.llmTestResult = null;
    this.render();
  }

  applyLLMPreset(preset) {
    this.playHudBeep(980, 0.04);
    const providerEl = document.getElementById('llm-input-provider');
    const nameEl = document.getElementById('llm-input-name');
    const urlEl = document.getElementById('llm-input-url');
    const modelEl = document.getElementById('llm-input-model');
    const urlContainer = document.getElementById('llm-base-url-container');

    if (preset === 'nvidia') {
      if (providerEl) providerEl.value = 'openai-compatible';
      if (nameEl) nameEl.value = 'NVIDIA NIM';
      if (urlEl) urlEl.value = 'https://integrate.api.nvidia.com/v1';
      if (modelEl) modelEl.value = 'meta/llama-3.2-11b-vision-instruct';
      if (urlContainer) urlContainer.style.display = 'block';
    } else if (preset === 'openai') {
      if (providerEl) providerEl.value = 'openai';
      if (nameEl) nameEl.value = 'OpenAI Direct';
      if (urlEl) urlEl.value = 'https://api.openai.com/v1';
      if (modelEl) modelEl.value = 'gpt-4o-mini';
      if (urlContainer) urlContainer.style.display = 'block';
    } else if (preset === 'groq') {
      if (providerEl) providerEl.value = 'openai-compatible';
      if (nameEl) nameEl.value = 'Groq LPU';
      if (urlEl) urlEl.value = 'https://api.groq.com/openai/v1';
      if (modelEl) modelEl.value = 'llama-3.3-70b-versatile';
      if (urlContainer) urlContainer.style.display = 'block';
    }
  }

  handleProviderProtocolChange(val) {
    const urlContainer = document.getElementById('llm-base-url-container');
    const nameEl = document.getElementById('llm-input-name');
    const urlEl = document.getElementById('llm-input-url');
    const modelEl = document.getElementById('llm-input-model');

    if (val === 'google') {
      if (urlContainer) urlContainer.style.display = 'none';
      if (nameEl) nameEl.value = 'Google Gemini';
      if (modelEl) modelEl.value = 'gemini-1.5-flash';
    } else {
      if (urlContainer) urlContainer.style.display = 'block';
      if (val === 'openai') {
        if (nameEl) nameEl.value = 'OpenAI Direct';
        if (urlEl) urlEl.value = 'https://api.openai.com/v1';
        if (modelEl) modelEl.value = 'gpt-4o-mini';
      }
    }
  }

  toggleKeyVisibility() {
    const input = document.getElementById('llm-input-key');
    const icon = document.getElementById('llm-key-eye-icon');
    if (!input || !icon) return;
    if (input.type === 'password') {
      input.type = 'text';
      icon.innerText = 'visibility_off';
    } else {
      input.type = 'password';
      icon.innerText = 'visibility';
    }
  }

  async testLLMConnection() {
    this.playHudBeep(700, 0.04);
    const providerEl = document.getElementById('llm-input-provider');
    const nameEl = document.getElementById('llm-input-name');
    const urlEl = document.getElementById('llm-input-url');
    const modelEl = document.getElementById('llm-input-model');
    const keyEl = document.getElementById('llm-input-key');

    const provider = providerEl ? providerEl.value : 'openai-compatible';
    const displayName = nameEl ? nameEl.value : 'Provider';
    const baseUrl = urlEl ? urlEl.value : '';
    const model = modelEl ? modelEl.value.trim() : '';
    const apiKey = keyEl ? keyEl.value.trim() : '';

    if (!model) {
      alert('Model identifier is required for connection testing.');
      return;
    }

    if (!apiKey && !this.llmConfig) {
      alert('Please enter an API key to test connection.');
      return;
    }

    this.llmTesting = true;
    this.llmTestResult = null;
    this.render();

    try {
      const payload = {
        provider,
        display_name: displayName,
        base_url: baseUrl,
        model,
        api_key: apiKey || null
      };
      const res = await jarvisApi.testLLMConfig(payload);
      this.llmTestResult = res;
      this.playHudBeep(res.status === 'CONNECTED' ? 1200 : 300, 0.08);
    } catch (e) {
      this.llmTestResult = {
        status: 'FAILED',
        message: e.message || 'Diagnostic connection failed.',
        provider: displayName,
        model: model
      };
      this.playHudBeep(250, 0.1);
    } finally {
      this.llmTesting = false;
      this.render();
    }
  }

  async saveLLMConfiguration() {
    this.playHudBeep(880, 0.05);
    const providerEl = document.getElementById('llm-input-provider');
    const nameEl = document.getElementById('llm-input-name');
    const urlEl = document.getElementById('llm-input-url');
    const modelEl = document.getElementById('llm-input-model');
    const keyEl = document.getElementById('llm-input-key');
    const tempEl = document.getElementById('llm-input-temp');
    const tokensEl = document.getElementById('llm-input-tokens');

    const provider = providerEl ? providerEl.value : 'openai-compatible';
    const displayName = nameEl ? nameEl.value.trim() : 'LLM Provider';
    const baseUrl = urlEl ? urlEl.value.trim() : '';
    const model = modelEl ? modelEl.value.trim() : '';
    const apiKey = keyEl ? keyEl.value.trim() : '';
    const temperature = tempEl ? parseFloat(tempEl.value) : 0.7;
    const maxTokens = tokensEl ? parseInt(tokensEl.value, 10) : 1024;

    if (!apiKey && !this.llmConfig) {
      alert('API Key is required to save configuration.');
      return;
    }

    if (!model) {
      alert('Model identifier is required.');
      return;
    }

    this.llmLoading = true;
    this.render();

    try {
      const payload = {
        provider,
        display_name: displayName,
        base_url: baseUrl,
        model,
        api_key: apiKey || (this.llmConfig ? 'RETAIN_EXISTING_KEY' : ''),
        temperature,
        max_output_tokens: maxTokens
      };
      const saved = await jarvisApi.saveLLMConfig(payload);
      this.llmConfig = saved;
      this.llmTestResult = {
        status: saved.status === 'connected' ? 'CONNECTED' : 'CONFIGURED',
        message: 'Configuration and API key encrypted with AES-256-GCM and saved.',
        provider: saved.display_name,
        model: saved.model
      };
      this.playHudBeep(1200, 0.08);
      alert('LLM Configuration securely saved & encrypted at rest.');
    } catch (e) {
      alert(`Save failed: ${e.message}`);
    } finally {
      this.llmLoading = false;
      this.render();
    }
  }

  async toggleLLMActiveStatus(enable) {
    this.playHudBeep(700, 0.04);
    try {
      const updated = await jarvisApi.updateLLMStatus(enable);
      this.llmConfig = updated;
      this.render();
    } catch (e) {
      alert(`Status update failed: ${e.message}`);
    }
  }

  confirmDeleteLLMConfig() {
    this.showApprovalModal(
      'Delete LLM Key',
      'Permanently delete your encrypted API key and provider configuration? J.A.R.V.I.S. will revert to unconfigured status.',
      'R3_HIGH',
      async () => {
        try {
          await jarvisApi.deleteLLMConfig();
          this.llmConfig = null;
          this.llmTestResult = null;
          this.closeApprovalModal();
          this.render();
          alert('Configuration and encrypted key permanently removed.');
        } catch (e) {
          alert(`Delete failed: ${e.message}`);
        }
      }
    );
  }

  // Main Render Pipeline
  render() {
    const current = store.state.activeScreen;
    const appEl = document.getElementById('app');
    if (!appEl) return;

    let screenHtml = '';
    switch (current) {
      case 'core':
        screenHtml = renderCoreScreen();
        break;
      case 'chat':
        screenHtml = renderChatScreen();
        break;
      case 'tasks':
        screenHtml = renderTasksScreen();
        break;
      case 'research':
        screenHtml = renderResearchScreen();
        break;
      case 'news':
        screenHtml = renderNewsScreen();
        break;
      case 'markets':
        screenHtml = renderMarketsScreen();
        break;
      case 'code':
        screenHtml = renderCodeScreen();
        break;
      case 'devices':
        screenHtml = renderDevicesScreen();
        break;
      case 'files':
        screenHtml = renderFilesScreen();
        break;
      case 'memory':
        screenHtml = renderMemoryScreen();
        break;
      case 'settings':
        screenHtml = renderSettingsScreen();
        break;
      case 'integrations':
        screenHtml = renderIntegrationsScreen();
        break;
      default:
        screenHtml = renderCoreScreen();
    }

    appEl.innerHTML = `
      ${renderHeader()}
      ${screenHtml}
      ${renderBottomNav()}
      ${renderMoreModal()}
      ${renderVoiceModal()}
      ${renderTaskModal()}
      ${this.selectedAssetSymbol ? renderAssetDetailModal(this.selectedAssetSymbol) : ''}
      ${this.approvalConfig ? renderApprovalModal(this.approvalConfig.title, this.approvalConfig.message, this.approvalConfig.riskLevel, 'window.jarvisApp.approvalConfig.onConfirmFn') : ''}
      ${this.llmModalOpen ? renderLLMConfigModal(this.llmConfig, this.llmTestResult, this.llmLoading, this.llmTesting) : ''}
    `;
  }
}

window.jarvisApp = new JarvisApp();
document.addEventListener('DOMContentLoaded', () => {
  window.jarvisApp.init();
});
