// ==========================================================================
// Research Screen: 10-15 Line Synthesized Briefs & Verified Citations
// Autonomous Multi-Source Extraction, Anti-Hallucination & Follow-Up Controls
// ==========================================================================

import { store } from '../services/store.js';
import { jarvisApi } from '../services/api.js';

let activeTab = 'search'; // 'search' | 'reports' | 'history'
let searchQuery = '';
let searchResults = [];
let searchMetadata = null;
let isSearching = false;
let researchStage = 'READY'; // 'SEARCHING' | 'READING SOURCES' | 'SYNTHESIZING' | 'READY' | 'ERROR'
let activeBrief = null; // Currently generated 10-15 line research brief
let isGeneratingReport = false;
let activeReport = null; // Currently opened full legacy report modal
let activeSummary = null; // Single-source summary modal
let savedReports = [];
let savedBriefs = [];
let searchHistory = [];
let selectedUrlsForReport = new Set();
let providerStatus = 'ONLINE';
let showRelatedSources = false;
let highlightedCitationId = null;

export function setResearchTab(tab) {
  activeTab = tab;
  if (tab === 'reports') {
    loadSavedReports();
    loadSavedBriefs();
  } else if (tab === 'history') {
    loadSearchHistory();
  }
  window.jarvisApp.render();
}

export async function executeSearch(query, answerMode = 'brief') {
  if (!query || !query.trim()) return;
  searchQuery = query.trim();
  isSearching = true;
  activeTab = 'search';
  researchStage = 'SEARCHING';
  highlightedCitationId = null;
  window.jarvisApp.render();

  // Progressive telemetry stage simulation
  const stageTimer1 = setTimeout(() => {
    if (isSearching) {
      researchStage = 'SELECTING SOURCES';
      window.jarvisApp.render();
    }
  }, 400);

  const stageTimer2 = setTimeout(() => {
    if (isSearching) {
      researchStage = 'READING SOURCES';
      window.jarvisApp.render();
    }
  }, 900);

  const stageTimer3 = setTimeout(() => {
    if (isSearching) {
      researchStage = 'EXTRACTING EVIDENCE';
      window.jarvisApp.render();
    }
  }, 1500);

  const stageTimer4 = setTimeout(() => {
    if (isSearching) {
      researchStage = 'SYNTHESIZING';
      window.jarvisApp.render();
    }
  }, 2300);

  const stageTimer5 = setTimeout(() => {
    if (isSearching) {
      researchStage = 'VALIDATING CITATIONS';
      window.jarvisApp.render();
    }
  }, 3200);

  try {
    // 1. Generate autonomous research brief
    const brief = await jarvisApi.generateResearchBrief(searchQuery, answerMode);
    clearTimeout(stageTimer1);
    clearTimeout(stageTimer2);
    clearTimeout(stageTimer3);
    clearTimeout(stageTimer4);
    clearTimeout(stageTimer5);

    activeBrief = brief;
    researchStage = 'READY';

    // 2. Also fetch search results to populate collapsible related sources
    try {
      const data = await jarvisApi.searchWeb(searchQuery, null, 'us-en', 6);
      searchResults = data.results || [];
      searchMetadata = {
        query: data.query,
        provider: data.provider,
        count: data.count,
        timestamp: new Date().toLocaleTimeString()
      };
    } catch (_) {
      // If direct search fails, construct results from brief citations
      searchResults = (brief.citations || []).map((c, i) => ({
        id: c.id,
        rank: i + 1,
        title: c.title,
        url: c.url,
        publisher: c.publisher,
        domain: (c.url.split('/')[2] || c.publisher).replace('www.', ''),
        snippet: c.excerpt || 'Verified citation document.',
        published_at: c.publication_date || 'Date unavailable'
      }));
    }

    providerStatus = brief.coverage_status === 'FULL'
      ? 'FULL COVERAGE'
      : brief.coverage_status.includes('PARTIAL')
        ? 'PARTIAL SOURCE COVERAGE'
        : 'PROVIDER NOT CONFIGURED';

    selectedUrlsForReport.clear();
    searchResults.slice(0, 3).forEach(r => selectedUrlsForReport.add(r.url));
  } catch (err) {
    clearTimeout(stageTimer1);
    clearTimeout(stageTimer2);
    clearTimeout(stageTimer3);
    clearTimeout(stageTimer4);
    clearTimeout(stageTimer5);
    console.error('Research brief generation failed:', err);

    if (typeof navigator !== 'undefined' && !navigator.onLine) {
      researchStage = 'OFFLINE';
      providerStatus = 'OFFLINE';
    } else if (err.message.includes('NOT_CONFIGURED') || err.message.includes('PROVIDER_NOT_CONFIGURED')) {
      researchStage = 'PROVIDER NOT CONFIGURED';
      providerStatus = 'PROVIDER NOT CONFIGURED';
    } else {
      researchStage = 'FAILED';
      providerStatus = 'FAILED';
    }
    searchMetadata = { query: searchQuery, error: err.message };
  } finally {
    isSearching = false;
    window.jarvisApp.render();
  }
}

export async function triggerBriefAction(action) {
  if (!activeBrief) return;
  window.jarvisApp.playHudBeep(850, 0.04);
  isSearching = true;
  researchStage = 'SYNTHESIZING';
  window.jarvisApp.render();

  try {
    const updated = await jarvisApi.executeBriefAction(activeBrief.id, action);
    activeBrief = updated;
    researchStage = 'READY';
  } catch (err) {
    alert(`Follow-up action failed: ${err.message}`);
    researchStage = 'READY';
  } finally {
    isSearching = false;
    window.jarvisApp.render();
  }
}

export async function saveCurrentBrief() {
  if (!activeBrief) return;
  window.jarvisApp.playHudBeep(920, 0.05);
  try {
    await jarvisApi.saveResearchBrief(activeBrief.id);
    activeBrief.saved = true;
    alert('Research Brief committed to permanent research vault.');
    loadSavedBriefs();
  } catch (err) {
    alert(`Could not save brief: ${err.message}`);
  }
  window.jarvisApp.render();
}

export function shareCurrentBrief() {
  if (!activeBrief) return;
  window.jarvisApp.playHudBeep(780, 0.03);

  const lines = [
    `# ${activeBrief.title}`,
    `Subject: ${activeBrief.query}`,
    '',
    `## Direct Answer`,
    activeBrief.direct_answer,
    '',
    `## Research Brief`,
    activeBrief.brief_paragraphs.join('\n\n'),
    '',
    `## Concluding Takeaway`,
    activeBrief.takeaway,
    '',
    `## Verified Sources`,
    activeBrief.citations.map(c => `[${c.id}] ${c.title} (${c.publisher}) - ${c.url}`).join('\n')
  ];
  const markdownText = lines.join('\n');

  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(markdownText);
    alert('Formatted Research Brief with sources copied to clipboard!');
  } else {
    alert('Brief text prepared. Copying not supported on this device.');
  }
}

export function highlightCitation(citId) {
  window.jarvisApp.playHudBeep(900, 0.03);
  highlightedCitationId = highlightedCitationId === citId ? null : citId;
  window.jarvisApp.render();
}

export function toggleRelatedSources() {
  showRelatedSources = !showRelatedSources;
  window.jarvisApp.render();
}

export function askFollowUpPrompt() {
  const input = document.getElementById('research-search-input');
  if (input) {
    input.value = '';
    input.placeholder = `Ask follow-up on "${activeBrief ? activeBrief.query : 'this topic'}"...`;
    input.focus();
  }
}

export async function loadSavedReports() {
  try {
    const data = await jarvisApi.getResearchReports();
    savedReports = data.reports || [];
  } catch (err) {
    console.warn('Failed to load saved reports:', err);
  }
  window.jarvisApp.render();
}

export async function loadSavedBriefs(query = null) {
  try {
    const data = await jarvisApi.getSavedBriefs(query);
    savedBriefs = data || [];
  } catch (err) {
    console.warn('Failed to load saved briefs:', err);
  }
  window.jarvisApp.render();
}

export async function searchSavedBriefs(query) {
  await loadSavedBriefs(query);
}

export async function renameBriefAction(briefId, currentTitle) {
  const newTitle = prompt('Enter new descriptive title for research brief:', currentTitle);
  if (!newTitle || !newTitle.trim() || newTitle.trim() === currentTitle) return;
  try {
    await jarvisApi.renameResearchBrief(briefId, newTitle.trim());
    await loadSavedBriefs();
  } catch (err) {
    alert(`Rename failed: ${err.message}`);
  }
}

export async function deleteBriefAction(briefId) {
  if (!confirm('Are you sure you want to delete this research brief from the vault?')) return;
  try {
    await jarvisApi.deleteResearchBrief(briefId);
    await loadSavedBriefs();
  } catch (err) {
    alert(`Delete failed: ${err.message}`);
  }
}

export async function exportBriefAction(briefId) {
  try {
    const res = await jarvisApi.exportResearchBrief(briefId);
    if (navigator.clipboard && navigator.clipboard.writeText) {
      await navigator.clipboard.writeText(res.content);
      alert(`Exported brief "${res.title}" copied to clipboard as Markdown!`);
    } else {
      alert(`Exported Markdown:\n\n${res.content.substring(0, 300)}...`);
    }
  } catch (err) {
    alert(`Export failed: ${err.message}`);
  }
}

export async function loadSearchHistory() {
  try {
    const data = await jarvisApi.getSearchHistory();
    searchHistory = data.history || [];
  } catch (err) {
    console.warn('Failed to load search history:', err);
  }
  window.jarvisApp.render();
}

export function toggleSourceSelection(url) {
  if (selectedUrlsForReport.has(url)) {
    selectedUrlsForReport.delete(url);
  } else {
    selectedUrlsForReport.add(url);
  }
  window.jarvisApp.render();
}

export async function generateCitedReport() {
  if (selectedUrlsForReport.size === 0 && searchResults.length === 0) {
    alert('Please execute a search and select at least one source.');
    return;
  }
  const urls = Array.from(selectedUrlsForReport);
  isGeneratingReport = true;
  window.jarvisApp.render();

  try {
    const report = await jarvisApi.createResearchReport(
      searchQuery || 'Web Investigation',
      searchQuery,
      urls.length > 0 ? urls : searchResults.slice(0, 3).map(r => r.url),
      ['Key Developments', 'Authoritative Claims', 'Implications']
    );
    activeReport = report;
    loadSavedReports();
  } catch (err) {
    alert(`Report generation failed: ${err.message}`);
  } finally {
    isGeneratingReport = false;
    window.jarvisApp.render();
  }
}

export async function openReportDetail(reportId) {
  try {
    const report = await jarvisApi.getResearchReport(reportId);
    activeReport = report;
    window.jarvisApp.render();
  } catch (err) {
    alert(`Could not load report: ${err.message}`);
  }
}

export function closeReportModal() {
  activeReport = null;
  window.jarvisApp.render();
}

export async function deleteReportAction(reportId) {
  if (confirm('Delete this cited research report from database?')) {
    try {
      await jarvisApi.deleteResearchReport(reportId);
      if (activeReport && activeReport.id === reportId) {
        activeReport = null;
      }
      loadSavedReports();
    } catch (err) {
      alert(`Deletion failed: ${err.message}`);
    }
  }
}

export async function summarizeSingleSource(url, title) {
  window.jarvisApp.playHudBeep(850, 0.04);
  activeSummary = { loading: true, title, url };
  window.jarvisApp.render();

  try {
    const doc = await jarvisApi.fetchSource(url);
    const summary = await jarvisApi.summarizeSource(doc.id);
    activeSummary = {
      loading: false,
      title: doc.title || title,
      publisher: doc.publisher,
      author: doc.author,
      published_at: doc.published_at || 'Date unavailable',
      status: doc.extraction_status,
      summary: summary.summary,
      key_facts: summary.key_facts || [],
      url: doc.url
    };
  } catch (err) {
    activeSummary = {
      loading: false,
      title,
      url,
      error: err.message
    };
  }
  window.jarvisApp.render();
}

export function closeSummaryModal() {
  activeSummary = null;
  window.jarvisApp.render();
}

export function openExternalUrl(url) {
  if (!url) return;
  window.open(url, '_blank', 'noopener,noreferrer');
}

// ----------------- Formatting Helpers -----------------
function renderInlineCitations(text) {
  if (!text) return '';
  // Convert [1], [2], etc. into interactive tappable badges
  return text.replace(/\[(\d+)\]/g, (match, id) => {
    const isLit = highlightedCitationId === id;
    return `
      <span 
        onclick="window.jarvisApp.highlightCitation('${id}'); event.stopPropagation();" 
        style="
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: ${isLit ? 'var(--warning-amber)' : 'rgba(0, 240, 255, 0.18)'};
          color: ${isLit ? 'var(--bg-void)' : 'var(--cyan-core)'};
          border: 1px solid ${isLit ? 'var(--warning-amber)' : 'var(--cyan-core)'};
          font-family: var(--font-telemetry);
          font-size: 9px;
          font-weight: 700;
          padding: 1px 5px;
          margin: 0 2px;
          border-radius: 3px;
          cursor: pointer;
          vertical-align: middle;
          box-shadow: ${isLit ? '0 0 8px var(--warning-amber)' : 'none'};
          transition: all 0.2s ease;
        "
        title="Tap to highlight verified source [${id}]"
      >[${id}]</span>
    `;
  });
}

// ----------------- Screen Renderers -----------------
export function renderResearchScreen() {
  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar with Navigation -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <span class="label-caps" style="color: var(--cyan-core); letter-spacing: 0.15em;">REAL WEB INTELLIGENCE</span>
          <h2 class="hud-title" style="font-size: 18px; margin-top: 2px;">Research Briefs & Citations</h2>
        </div>

        <div style="display: flex; gap: 6px; align-items: center;">
          <span class="badge ${providerStatus.includes('FULL') ? 'badge-cyan' : providerStatus.includes('NOT CONFIGURED') ? 'badge-red' : 'badge-amber'}" style="font-size: 8px;">
            ${providerStatus}
          </span>
          <button onclick="window.jarvisApp.navigate('news')" class="hud-btn" style="padding: 6px 10px; font-size: 10px;">
            <span class="material-symbols-outlined" style="font-size: 14px;">newspaper</span>
            News Wire
          </button>
        </div>
      </div>

      <!-- Navigation Tabs (Search / Saved Briefs / History) -->
      <div style="display: flex; gap: 6px; border-bottom: 1px solid rgba(0, 240, 255, 0.15); padding-bottom: 6px;">
        <button onclick="window.jarvisApp.setResearchTab('search')" style="
          background: ${activeTab === 'search' ? 'var(--cyan-core)' : 'transparent'};
          color: ${activeTab === 'search' ? 'var(--bg-void)' : 'var(--text-secondary)'};
          border: 1px solid ${activeTab === 'search' ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
          font-family: var(--font-telemetry);
          font-size: 10px;
          font-weight: 700;
          padding: 6px 12px;
          cursor: pointer;
          clip-path: var(--chamfer-clip-sm);
        ">
          RESEARCH BRIEF
        </button>

        <button onclick="window.jarvisApp.setResearchTab('reports')" style="
          background: ${activeTab === 'reports' ? 'var(--cyan-core)' : 'transparent'};
          color: ${activeTab === 'reports' ? 'var(--bg-void)' : 'var(--text-secondary)'};
          border: 1px solid ${activeTab === 'reports' ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
          font-family: var(--font-telemetry);
          font-size: 10px;
          font-weight: 700;
          padding: 6px 12px;
          cursor: pointer;
          clip-path: var(--chamfer-clip-sm);
        ">
          SAVED BRIEFS (${savedBriefs.length + savedReports.length})
        </button>

        <button onclick="window.jarvisApp.setResearchTab('history')" style="
          background: ${activeTab === 'history' ? 'var(--cyan-core)' : 'transparent'};
          color: ${activeTab === 'history' ? 'var(--bg-void)' : 'var(--text-secondary)'};
          border: 1px solid ${activeTab === 'history' ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
          font-family: var(--font-telemetry);
          font-size: 10px;
          font-weight: 700;
          padding: 6px 12px;
          cursor: pointer;
          clip-path: var(--chamfer-clip-sm);
        ">
          HISTORY
        </button>
      </div>

      ${activeTab === 'search' ? renderSearchTab() : ''}
      ${activeTab === 'reports' ? renderReportsTab() : ''}
      ${activeTab === 'history' ? renderHistoryTab() : ''}

      <!-- Modals -->
      ${activeReport ? renderReportModal(activeReport) : ''}
      ${activeSummary ? renderSummaryModal(activeSummary) : ''}

    </div>
  `;
}

function renderSearchTab() {
  return `
    <!-- Search Input Panel -->
    <div class="hud-panel" style="padding: 12px; display: flex; flex-direction: column; gap: 10px;">
      <div style="display: flex; gap: 8px;">
        <input 
          type="text" 
          id="research-search-input" 
          class="hud-input" 
          placeholder="Ask a factual, research, technology, or company question..." 
          value="${searchQuery}"
          onkeydown="if(event.key === 'Enter') window.jarvisApp.handleSearchSubmit()"
        >
        <button onclick="window.jarvisApp.handleSearchSubmit()" class="hud-btn" style="padding: 10px 14px;" ${isSearching ? 'disabled' : ''}>
          <span class="material-symbols-outlined" style="font-size: 18px;">${isSearching ? 'sync' : 'auto_awesome'}</span>
        </button>
      </div>

      <!-- Quick Topic Chips -->
      <div style="display: flex; align-items: center; gap: 6px; overflow-x: auto; scrollbar-width: none;">
        <span class="label-caps" style="font-size: 8px; white-space: nowrap; color: var(--text-muted);">TOPICS:</span>
        ${[
          'What is quantum computing and why is it important?',
          'High-NA EUV lithography mechanics',
          'NVIDIA Blackwell architecture comparison',
          'AI Agent Orchestration state of the art',
          'Commercial fusion energy breakthroughs'
        ].map(t => `
          <button onclick="window.jarvisApp.runQuickSearch('${t.replace(/'/g, "\\'")}')" class="hud-btn-ghost" style="font-size: 9px; padding: 3px 8px; white-space: nowrap;">
            ${t.length > 32 ? t.substring(0, 30) + '...' : t}
          </button>
        `).join('')}
      </div>
    </div>

    <!-- Dynamic Status Stepper Bar -->
    ${isSearching ? `
      <div class="hud-panel" style="padding: 14px 16px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="material-symbols-outlined spin" style="color: var(--cyan-core); font-size: 18px;">autorenew</span>
            <span class="font-telemetry" style="font-size: 11px; font-weight: 700; color: var(--cyan-core); letter-spacing: 0.1em;">
              STAGE: ${researchStage}
            </span>
          </div>
          <span class="font-telemetry" style="font-size: 9px; color: var(--text-muted);">PARALLEL SSRF EXTRACTION ACTIVE</span>
        </div>

        <div style="display: flex; gap: 4px; align-items: center;">
          <div style="flex: 1; height: 3px; background: ${['SEARCHING', 'SELECTING SOURCES', 'READING SOURCES', 'EXTRACTING EVIDENCE', 'SYNTHESIZING', 'VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
          <div style="flex: 1; height: 3px; background: ${['SELECTING SOURCES', 'READING SOURCES', 'EXTRACTING EVIDENCE', 'SYNTHESIZING', 'VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
          <div style="flex: 1; height: 3px; background: ${['READING SOURCES', 'EXTRACTING EVIDENCE', 'SYNTHESIZING', 'VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
          <div style="flex: 1; height: 3px; background: ${['EXTRACTING EVIDENCE', 'SYNTHESIZING', 'VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
          <div style="flex: 1; height: 3px; background: ${['SYNTHESIZING', 'VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
          <div style="flex: 1; height: 3px; background: ${['VALIDATING CITATIONS', 'READY'].includes(researchStage) ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.15)'};"></div>
        </div>
      </div>
    ` : ''}

    <!-- Error / Provider Status State with Retry -->
    ${!isSearching && ['FAILED', 'OFFLINE', 'PROVIDER NOT CONFIGURED', 'ERROR'].includes(researchStage) ? `
      <div class="hud-panel" style="padding: 16px; border-color: var(--warning-amber); display: flex; flex-direction: column; gap: 8px; background: rgba(255, 170, 0, 0.05);">
        <div style="display: flex; align-items: center; justify-content: space-between;">
          <div style="display: flex; align-items: center; gap: 8px;">
            <span class="material-symbols-outlined" style="color: var(--warning-amber); font-size: 20px;">warning</span>
            <span class="font-telemetry" style="font-size: 11px; font-weight: 700; color: var(--warning-amber); letter-spacing: 0.08em;">
              STATUS: ${researchStage === 'OFFLINE' ? 'OFFLINE — NO INTERNET' : researchStage === 'PROVIDER NOT CONFIGURED' ? 'LLM PROVIDER NOT CONFIGURED' : 'SYNTHESIS FAILURE'}
            </span>
          </div>
          <span class="badge badge-amber" style="font-size: 8px;">ACTION REQUIRED</span>
        </div>
        <p style="font-size: 11px; color: var(--text-secondary); margin: 0; line-height: 1.45;">
          ${searchMetadata && searchMetadata.error ? searchMetadata.error : 'JARVIS was unable to complete multi-source research synthesis under current conditions.'}
        </p>
        <div style="display: flex; gap: 8px; margin-top: 4px;">
          <button onclick="window.jarvisApp.handleSearchSubmit()" class="hud-btn" style="font-size: 10px; padding: 5px 14px;">
            <span class="material-symbols-outlined" style="font-size: 14px;">refresh</span>
            Retry
          </button>
          ${researchStage === 'PROVIDER NOT CONFIGURED' ? `
            <button onclick="window.jarvisApp.navigate('integrations')" class="hud-btn-ghost" style="font-size: 10px; padding: 5px 12px;">
              <span class="material-symbols-outlined" style="font-size: 14px;">settings</span>
              Configure Provider
            </button>
          ` : ''}
        </div>
      </div>
    ` : ''}

    <!-- Research Brief Content -->
    ${activeBrief ? renderBriefContainer(activeBrief) : ''}

    <!-- Collapsible Related Sources Section -->
    ${searchResults.length > 0 ? renderRelatedSourcesAccordion() : ''}

    <!-- Empty Directive Prompt State -->
    ${!activeBrief && !isSearching && !['FAILED', 'OFFLINE', 'PROVIDER NOT CONFIGURED', 'ERROR'].includes(researchStage) ? `
      <div class="hud-panel" style="padding: 24px; text-align: center; border-style: dashed;">
        <span class="material-symbols-outlined" style="color: var(--cyan-core); font-size: 36px; opacity: 0.7;">description</span>
        <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 8px;">Autonomous Research Brief Generator</h3>
        <p style="font-size: 11px; color: var(--text-secondary); max-width: 360px; margin: 6px auto 0 auto; line-height: 1.45;">
          JARVIS conducts multi-source retrieval, page extraction, and grounded evidence synthesis to return a concise 10–15 line research brief with direct answers and verifiable inline citations.
        </p>
      </div>
    ` : ''}
  `;
}

function renderBriefContainer(brief) {
  return `
    <div class="hud-panel" style="padding: 16px; border-left: 3px solid var(--cyan-core); display: flex; flex-direction: column; gap: 12px; background: rgba(5, 15, 28, 0.65);">
      
      <!-- Header with Mode & Metadata -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(0, 240, 255, 0.12); padding-bottom: 8px;">
        <div>
          <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 3px;">
            <span class="badge badge-cyan" style="font-size: 8px; text-transform: uppercase;">
              ${brief.answer_mode || 'BRIEF'} MODE (~${brief.answer_mode === 'quick' ? '3-6' : brief.answer_mode === 'detailed' ? '20-35' : '10-15'} LINES)
            </span>
            <span class="label-caps" style="font-size: 8px; color: var(--text-muted);">
              TOPIC: ${brief.topic_type || 'GENERAL'}
            </span>
            <span class="badge ${brief.coverage_status.includes('PARTIAL') ? 'badge-amber' : 'badge-cyan'}" style="font-size: 8px;">
              ${brief.coverage_status}
            </span>
          </div>
          <h3 style="font-size: 15px; font-weight: 700; color: var(--text-primary); margin: 0; line-height: 1.35;">
            ${brief.title}
          </h3>
        </div>

        <div style="display: flex; gap: 4px;">
          <button onclick="window.jarvisApp.saveCurrentBrief()" class="hud-btn-ghost" style="padding: 4px 8px; font-size: 9px;" title="Save to Vault">
            <span class="material-symbols-outlined" style="font-size: 14px; color: ${brief.saved ? 'var(--cyan-core)' : 'inherit'};">
              ${brief.saved ? 'bookmark' : 'bookmark_add'}
            </span>
            ${brief.saved ? 'Saved' : 'Save'}
          </button>
          <button onclick="window.jarvisApp.shareCurrentBrief()" class="hud-btn-ghost" style="padding: 4px 8px; font-size: 9px;" title="Share Brief">
            <span class="material-symbols-outlined" style="font-size: 14px;">share</span>
            Share
          </button>
        </div>
      </div>

      <!-- 1. Direct Answer Section -->
      <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.25); border-radius: 4px; padding: 10px 12px;">
        <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); display: block; margin-bottom: 4px; font-weight: 700; letter-spacing: 0.1em;">
          DIRECT ANSWER
        </span>
        <p style="font-size: 12px; font-weight: 600; color: var(--text-primary); line-height: 1.5; margin: 0;">
          ${renderInlineCitations(brief.direct_answer)}
        </p>
      </div>

      <!-- 2. Research Brief Body (10-15 lines) -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <span class="label-caps" style="font-size: 8px; color: var(--plasma-cobalt); letter-spacing: 0.1em;">
          RESEARCH SYNTHESIS (~10–15 READABLE LINES)
        </span>
        ${(brief.brief_paragraphs || []).map(p => `
          <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.6; margin: 0;">
            ${renderInlineCitations(p)}
          </p>
        `).join('')}
      </div>

      <!-- Key Points (Optional) -->
      ${brief.key_points && brief.key_points.length > 0 ? `
        <div style="background: rgba(0, 240, 255, 0.02); border-left: 2px solid rgba(0, 240, 255, 0.4); padding: 6px 10px;">
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); margin-bottom: 4px; display: block;">KEY EMPIRICAL POINTS</span>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${brief.key_points.map(kp => `
              <div style="font-size: 10px; color: var(--text-secondary); display: flex; gap: 6px; align-items: flex-start;">
                <span style="color: var(--cyan-core);">•</span>
                <span>${renderInlineCitations(kp.text)}</span>
              </div>
            `).join('')}
          </div>
        </div>
      ` : ''}

      <!-- 3. Concluding Takeaway -->
      <div style="border-top: 1px dashed rgba(0, 240, 255, 0.15); padding-top: 8px; display: flex; gap: 8px; align-items: flex-start;">
        <span class="material-symbols-outlined" style="font-size: 16px; color: var(--cyan-core); margin-top: 1px;">verified_user</span>
        <div>
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); display: block;">KEY TAKEAWAY</span>
          <p style="font-size: 11px; color: var(--text-primary); font-weight: 600; line-height: 1.4; margin: 2px 0 0 0;">
            ${renderInlineCitations(brief.takeaway)}
          </p>
        </div>
      </div>

      <!-- Limitations & Uncertainty -->
      ${brief.limitations && brief.limitations.length > 0 ? `
        <div style="padding: 6px 8px; background: rgba(255, 170, 0, 0.04); border: 1px solid rgba(255, 170, 0, 0.2); border-radius: 3px; font-size: 9px; color: var(--text-muted);">
          <span style="color: var(--warning-amber); font-weight: 700;">LIMITATIONS: </span>
          ${brief.limitations.join(' ')}
        </div>
      ` : ''}

      <!-- 4. Interactive Follow-Up Controls -->
      <div style="border-top: 1px solid rgba(0, 240, 255, 0.12); padding-top: 8px; display: flex; flex-direction: column; gap: 6px;">
        <span class="label-caps" style="font-size: 8px; color: var(--text-muted);">FOLLOW-UP DIRECTIVES:</span>
        
        <div style="display: flex; gap: 6px; flex-wrap: wrap;">
          <button onclick="window.jarvisApp.triggerBriefAction('more_detail')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">expand_content</span>
            More detail (20-35 lines)
          </button>

          <button onclick="window.jarvisApp.triggerBriefAction('simplify')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">compress</span>
            Simplify (3-6 lines)
          </button>

          <button onclick="window.jarvisApp.triggerBriefAction('give_examples')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">lightbulb</span>
            Give examples
          </button>

          <button onclick="window.jarvisApp.triggerBriefAction('compare_alternatives')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">compare_arrows</span>
            Compare alternatives
          </button>

          <button onclick="window.jarvisApp.toggleRelatedSources()" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">list</span>
            ${showRelatedSources ? 'Hide sources' : 'Show sources'}
          </button>

          <button onclick="window.jarvisApp.askFollowUpPrompt()" class="hud-btn" style="font-size: 9px; padding: 4px 10px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">chat</span>
            Ask follow-up
          </button>
        </div>
      </div>

      <!-- 5. Compact Verified Sources Section (2-5 primary sources) -->
      <div style="border-top: 1px solid rgba(0, 240, 255, 0.12); padding-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">
            VERIFIED SOURCES (${brief.citations ? brief.citations.length : 0} PRIMARY)
          </span>
          <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">ZERO HALLUCINATIONS</span>
        </div>

        <div style="display: flex; flex-direction: column; gap: 6px;">
          ${(brief.citations || []).map(cit => {
            const isHighlighted = highlightedCitationId === cit.id;
            return `
              <div 
                class="hud-panel" 
                style="
                  padding: 8px 10px; 
                  display: flex; 
                  justify-content: space-between; 
                  align-items: center;
                  border-color: ${isHighlighted ? 'var(--warning-amber)' : 'rgba(0, 240, 255, 0.15)'};
                  background: ${isHighlighted ? 'rgba(255, 170, 0, 0.08)' : 'transparent'};
                  transition: all 0.2s ease;
                "
              >
                <div style="overflow: hidden; max-width: 78%;">
                  <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 2px;">
                    <span class="badge ${isHighlighted ? 'badge-amber' : 'badge-cyan'}" style="font-size: 8px;">[${cit.id}]</span>
                    <span style="font-size: 11px; font-weight: 700; color: var(--text-primary); text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">
                      ${cit.title || 'Verified Document'}
                    </span>
                  </div>
                  <div style="font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry);">
                    ${cit.publisher || 'Web'} • ${cit.publication_date || 'Date unavailable'} • ${cit.source_type || 'web'}
                  </div>
                </div>

                <button onclick="window.jarvisApp.openExternalUrl('${cit.url}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
                  <span class="material-symbols-outlined" style="font-size: 12px;">open_in_new</span>
                  Source
                </button>
              </div>
            `;
          }).join('')}
        </div>
      </div>

    </div>
  `;
}

function renderRelatedSourcesAccordion() {
  return `
    <div class="hud-panel" style="padding: 10px 12px;">
      <div 
        onclick="window.jarvisApp.toggleRelatedSources()" 
        style="display: flex; justify-content: space-between; align-items: center; cursor: pointer;"
      >
        <div style="display: flex; align-items: center; gap: 6px;">
          <span class="material-symbols-outlined" style="font-size: 16px; color: var(--cyan-core);">
            ${showRelatedSources ? 'expand_less' : 'expand_more'}
          </span>
          <span class="label-caps" style="color: var(--text-secondary); font-size: 9px;">
            ALL RETRIEVED SEARCH RESULTS (${searchResults.length})
          </span>
        </div>
        <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">COLLAPSIBLE DRAWER</span>
      </div>

      ${showRelatedSources ? `
        <div style="margin-top: 10px; display: flex; flex-direction: column; gap: 8px;">
          ${searchResults.map((res, idx) => `
            <div class="hud-panel" style="padding: 8px 10px; border-left: 2px solid rgba(0, 240, 255, 0.2);">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                <span class="label-caps" style="font-size: 8px; color: var(--plasma-cobalt); font-weight: 700;">${res.publisher || res.domain}</span>
                <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">${res.published_at || ''}</span>
              </div>
              <h4 style="font-size: 11px; font-weight: 700; color: var(--text-primary); margin: 2px 0 4px 0;">${res.title}</h4>
              <p style="font-size: 10px; color: var(--text-secondary); margin: 0 0 6px 0; line-height: 1.35;">${res.snippet || ''}</p>
              <div style="display: flex; justify-content: flex-end; gap: 6px;">
                <button onclick="window.jarvisApp.summarizeSingleSource('${res.url}', '${encodeURIComponent(res.title)}')" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px;">
                  Summarize
                </button>
                <button onclick="window.jarvisApp.openExternalUrl('${res.url}')" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px;">
                  Open
                </button>
              </div>
            </div>
          `).join('')}
        </div>
      ` : ''}
    </div>
  `;
}

export async function openBriefDetail(briefId) {
  try {
    const brief = await jarvisApi.getResearchBrief(briefId);
    activeBrief = brief;
    activeTab = 'search';
    window.jarvisApp.render();
  } catch (err) {
    alert(`Could not load brief: ${err.message}`);
  }
}

function renderReportsTab() {
  const allSaved = [...savedBriefs, ...savedReports];

  return `
    <div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 0 2px;">
        <span class="label-caps" style="color: var(--cyan-core);">PERSISTED RESEARCH BRIEFS & REPORTS</span>
        <button onclick="window.jarvisApp.loadSavedReports(); window.jarvisApp.loadSavedBriefs();" class="hud-btn-ghost" style="font-size: 9px; padding: 3px 8px;">
          <span class="material-symbols-outlined" style="font-size: 12px;">refresh</span>
          Refresh
        </button>
      </div>

      <!-- Search Filter for Saved Briefs -->
      <div style="margin-bottom: 12px;">
        <input 
          type="text" 
          class="hud-input" 
          placeholder="Filter saved research briefs by title, query, or facts..." 
          oninput="window.jarvisApp.searchSavedBriefs(this.value)"
          style="font-size: 11px; padding: 7px 10px;"
        >
      </div>

      ${allSaved.length === 0 ? `
        <div class="hud-panel" style="padding: 24px; text-align: center;">
          <span class="material-symbols-outlined" style="font-size: 32px; color: var(--text-muted);">description</span>
          <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">No research briefs or reports archived yet.</p>
          <button onclick="window.jarvisApp.setResearchTab('search')" class="hud-btn" style="margin-top: 10px; font-size: 10px; padding: 6px 12px;">
            Create Brief
          </button>
        </div>
      ` : `
        <div style="display: flex; flex-direction: column; gap: 10px;">
          ${allSaved.map(item => {
            const isBrief = !!item.brief_paragraphs;
            return `
              <div class="hud-panel" style="padding: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
                  <div style="display: flex; gap: 6px; align-items: center;">
                    <span class="badge ${isBrief ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">
                      ${isBrief ? 'VERIFIED RESEARCH BRIEF' : 'FULL REPORT'}
                    </span>
                    ${item.source_coverage ? `
                      <span class="badge ${item.source_coverage === 'complete' ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">
                        ${item.source_coverage.toUpperCase()}
                      </span>
                    ` : ''}
                  </div>
                  <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">
                    ${item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}
                  </span>
                </div>

                <h3 style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin: 4px 0 6px 0;">
                  ${item.title}
                </h3>

                <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.4; margin-bottom: 8px;">
                  ${item.direct_answer || item.executive_summary || 'Archived research intelligence.'}
                </p>

                <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px;">
                  <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">
                    ${item.citations ? item.citations.length : 0} VERIFIED SOURCES
                  </span>

                  <div style="display: flex; gap: 4px;">
                    ${isBrief ? `
                      <button onclick="window.jarvisApp.openBriefDetail('${item.id}')" class="hud-btn" style="font-size: 9px; padding: 4px 8px;">
                        Open
                      </button>
                      <button onclick="window.jarvisApp.renameBriefAction('${item.id}', '${item.title.replace(/'/g, "\\'")}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 6px;" title="Rename Brief">
                        <span class="material-symbols-outlined" style="font-size: 12px;">edit</span>
                      </button>
                      <button onclick="window.jarvisApp.exportBriefAction('${item.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 6px;" title="Export Markdown">
                        <span class="material-symbols-outlined" style="font-size: 12px;">download</span>
                      </button>
                      <button onclick="window.jarvisApp.deleteBriefAction('${item.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 6px; color: var(--warning-amber);" title="Delete Brief">
                        <span class="material-symbols-outlined" style="font-size: 12px;">delete</span>
                      </button>
                    ` : `
                      <button onclick="window.jarvisApp.openReportDetail('${item.id}')" class="hud-btn" style="font-size: 9px; padding: 4px 10px;">
                        Read
                      </button>
                      <button onclick="window.jarvisApp.deleteReportAction('${item.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 6px; color: var(--warning-amber);">
                        <span class="material-symbols-outlined" style="font-size: 12px;">delete</span>
                      </button>
                    `}
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `}
    </div>
  `;
}

function renderHistoryTab() {
  return `
    <div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding: 0 2px;">
        <span class="label-caps" style="color: var(--cyan-core);">RECENT SEARCH DIRECTIVES</span>
        <button onclick="window.jarvisApp.loadSearchHistory()" class="hud-btn-ghost" style="font-size: 9px; padding: 3px 8px;">
          <span class="material-symbols-outlined" style="font-size: 12px;">refresh</span>
          Refresh
        </button>
      </div>

      ${searchHistory.length === 0 ? `
        <div class="hud-panel" style="padding: 24px; text-align: center;">
          <span class="material-symbols-outlined" style="font-size: 32px; color: var(--text-muted);">history</span>
          <p style="font-size: 12px; color: var(--text-secondary); margin-top: 6px;">No search history on record.</p>
        </div>
      ` : `
        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${searchHistory.map(h => `
            <div class="hud-panel" style="padding: 10px 12px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-size: 12px; font-weight: 700; color: var(--text-primary);">${h.query_text || h.query}</div>
                <div style="font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry); margin-top: 2px;">
                  Provider: ${h.provider} | Results: ${h.result_count} | ${new Date(h.created_at).toLocaleTimeString()}
                </div>
              </div>

              <button onclick="window.jarvisApp.runQuickSearch('${(h.query_text || h.query).replace(/'/g, "\\'")}')" class="hud-btn" style="font-size: 9px; padding: 4px 10px;">
                Re-Run
              </button>
            </div>
          `).join('')}
        </div>
      `}
    </div>
  `;
}

function renderReportModal(report) {
  return `
    <div style="position: fixed; inset: 0; background: rgba(5, 11, 20, 0.88); backdrop-filter: blur(8px); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 16px;">
      <div class="hud-panel hud-scroll" style="width: 100%; max-width: 680px; max-height: 85vh; overflow-y: auto; padding: 20px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 14px; position: relative;">
        
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 10px;">
          <div>
            <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 4px;">
              <span class="badge badge-cyan" style="font-size: 8px;">CITED RESEARCH REPORT</span>
              <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">${new Date(report.created_at).toLocaleString()}</span>
            </div>
            <h2 style="font-size: 16px; font-weight: 700; color: var(--text-primary);">${report.title}</h2>
          </div>

          <button onclick="window.jarvisApp.closeReportModal()" class="hud-btn-ghost" style="padding: 4px; border-radius: 50%;">
            <span class="material-symbols-outlined" style="font-size: 20px;">close</span>
          </button>
        </div>

        <div class="hud-panel" style="padding: 12px; background: rgba(0, 240, 255, 0.03);">
          <span class="label-caps" style="font-size: 9px; color: var(--cyan-core); display: block; margin-bottom: 4px;">EXECUTIVE SUMMARY</span>
          <p style="font-size: 12px; color: var(--text-primary); line-height: 1.5;">${report.executive_summary || report.direct_answer}</p>
        </div>

        <div>
          <span class="label-caps" style="font-size: 9px; color: var(--cyan-core); display: block; margin-bottom: 6px;">STRUCTURED CITATIONS (${report.citations ? report.citations.length : 0})</span>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${(report.citations || []).map(cit => `
              <div class="hud-panel" style="padding: 8px 10px; display: flex; justify-content: space-between; align-items: center;">
                <div style="overflow: hidden; max-width: 80%;">
                  <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 2px;">
                    <span class="badge badge-cyan" style="font-size: 8px;">${cit.id || cit.citation_label}</span>
                    <span style="font-size: 11px; font-weight: 700; color: var(--text-primary); text-overflow: ellipsis; white-space: nowrap; overflow: hidden;">${cit.title || cit.source_title || 'Web Document'}</span>
                  </div>
                  <div style="font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry);">
                    ${cit.publisher || cit.domain} • ${cit.source_type}
                  </div>
                </div>

                <button onclick="window.jarvisApp.openExternalUrl('${cit.url}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
                  <span class="material-symbols-outlined" style="font-size: 12px;">link</span>
                  Source
                </button>
              </div>
            `).join('')}
          </div>
        </div>

        <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid rgba(0, 240, 255, 0.15); padding-top: 10px;">
          <button onclick="window.jarvisApp.closeReportModal()" class="hud-btn" style="font-size: 10px; padding: 6px 14px;">
            Close
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderSummaryModal(sum) {
  return `
    <div style="position: fixed; inset: 0; background: rgba(5, 11, 20, 0.88); backdrop-filter: blur(8px); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 16px;">
      <div class="hud-panel" style="width: 100%; max-width: 540px; padding: 18px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 8px;">
          <div>
            <span class="badge badge-cyan" style="font-size: 8px;">SOURCE INTELLIGENCE</span>
            <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              ${sum.title ? decodeURIComponent(sum.title) : 'Web Document'}
            </h3>
          </div>

          <button onclick="window.jarvisApp.closeSummaryModal()" class="hud-btn-ghost" style="padding: 4px;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        ${sum.loading ? `
          <div style="padding: 24px; text-align: center;">
            <div style="font-family: var(--font-telemetry); font-size: 12px; color: var(--cyan-core); margin-bottom: 8px;">
              PARSING HTML & EXTRACTING ARTICLE CONTENT...
            </div>
            <div style="height: 2px; width: 80%; margin: 0 auto; background: var(--cyan-core); animation: hud-scan 1s infinite alternate;"></div>
          </div>
        ` : sum.error ? `
          <div class="hud-panel" style="padding: 12px; border-color: var(--warning-amber);">
            <span class="label-caps" style="color: var(--warning-amber); font-size: 9px;">EXTRACTION ERROR</span>
            <p style="font-size: 11px; color: var(--text-secondary); margin-top: 4px;">${sum.error}</p>
          </div>
        ` : `
          <div style="display: flex; flex-direction: column; gap: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry);">
              <span>PUBLISHER: ${sum.publisher || 'Web Site'}</span>
              <span>DATE: ${sum.published_at}</span>
            </div>

            <div class="hud-panel" style="padding: 10px; background: rgba(0, 240, 255, 0.03);">
              <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); display: block; margin-bottom: 4px;">EXTRACTED SUMMARY</span>
              <p style="font-size: 11px; color: var(--text-primary); line-height: 1.45;">${sum.summary}</p>
            </div>
          </div>
        `}

        <div style="display: flex; justify-content: flex-end; gap: 8px; border-top: 1px solid rgba(0, 240, 255, 0.1); padding-top: 8px;">
          ${sum.url ? `
            <button onclick="window.jarvisApp.openExternalUrl('${sum.url}')" class="hud-btn-ghost" style="font-size: 9px; padding: 5px 10px;">
              <span class="material-symbols-outlined" style="font-size: 12px;">open_in_new</span>
              Visit Page
            </button>
          ` : ''}
          <button onclick="window.jarvisApp.closeSummaryModal()" class="hud-btn" style="font-size: 9px; padding: 5px 12px;">
            Done
          </button>
        </div>

      </div>
    </div>
  `;
}
