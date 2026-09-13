// ==========================================================================
// News Screen: Real-Time World Headline Intelligence, Clustering & Briefings
// ==========================================================================

import { store } from '../services/store.js';
import { jarvisApi } from '../services/api.js';

let activeCategory = 'all';
let activeTopicId = null;
let newsItems = [];
let eventClusters = [];
let subscribedTopics = [];
let activeBriefing = null;
let clusterSummaries = {}; // clusterId -> summary
let expandedClusters = {}; // clusterId -> boolean
let isFetchingNews = false;
let isGeneratingBriefing = false;
let showTopicsModal = false;
let showNotificationsModal = false;
let notificationRules = [];
let dispatchedNotifications = [];
let providerStatus = 'LIVE RSS WIRE';

export function setNewsCategory(cat) {
  activeCategory = cat;
  activeTopicId = null;
  loadNewsData();
}

export function setNewsTopic(topicId) {
  activeTopicId = topicId;
  activeCategory = 'topic';
  loadNewsData();
}

export async function loadNewsData() {
  isFetchingNews = true;
  window.jarvisApp.render();

  try {
    const data = await jarvisApi.getNews(
      activeCategory === 'all' || activeCategory === 'topic' ? null : activeCategory,
      null,
      30,
      activeTopicId
    );
    newsItems = Array.isArray(data) ? data : (data.items || []);
    
    // Group into clusters if not returned
    const clustersData = await jarvisApi.getNewsClusters(activeCategory === 'all' || activeCategory === 'topic' ? null : activeCategory);
    eventClusters = Array.isArray(clustersData) ? clustersData : [];
    providerStatus = 'LIVE VERIFIED WIRE';
  } catch (err) {
    console.warn('Failed to fetch real news:', err);
    providerStatus = err.message && err.message.includes('PROVIDER_NOT_CONFIGURED') ? 'PROVIDER NOT CONFIGURED' : 'OFFLINE';
  } finally {
    isFetchingNews = false;
    window.jarvisApp.render();
  }
}

export async function loadTopics() {
  try {
    const data = await jarvisApi.getNewsTopics();
    subscribedTopics = Array.isArray(data) ? data : [];
  } catch (err) {
    console.warn('Failed to load news topics:', err);
  }
  window.jarvisApp.render();
}

export async function loadNotificationRules() {
  try {
    notificationRules = await jarvisApi.getNotificationRules();
    dispatchedNotifications = await jarvisApi.getDispatchedNotifications(20);
  } catch (err) {
    console.warn('Failed to load notifications:', err);
  }
  window.jarvisApp.render();
}

export async function subscribeTopicAction(topicName, topicType = 'keyword', ticker = null, notifEnabled = false, importanceThresh = 'high') {
  if (!topicName || !topicName.trim()) return;
  
  if (notifEnabled) {
    const confirmed = confirm(
      `CONFIRM RECURRING NOTIFICATIONS:\n\n` +
      `Topic: ${topicName.trim()}\n` +
      `Threshold: ${importanceThresh.toUpperCase()} priority and above\n` +
      `Source: Verified global wire telemetry\n\n` +
      `You can pause or disable notifications at any time in Topic Settings. Proceed?`
    );
    if (!confirmed) notifEnabled = false;
  }

  try {
    await jarvisApi.createNewsTopic({
      topic_name: topicName.trim(),
      query: topicName.trim(),
      topic_type: topicType,
      ticker: ticker,
      category: activeCategory !== 'all' && activeCategory !== 'topic' ? activeCategory : 'General',
      notifications_enabled: notifEnabled,
      importance_threshold: importanceThresh
    });
    await loadTopics();
    alert(`Radar online: Following "${topicName}".`);
  } catch (err) {
    alert(`Failed to follow topic: ${err.message}`);
  }
}

export async function unsubscribeTopicAction(topicId) {
  try {
    await jarvisApi.deleteNewsTopic(topicId);
    await loadTopics();
  } catch (err) {
    alert(`Failed to unfollow topic: ${err.message}`);
  }
}

export async function toggleArticleRead(newsId, currentRead) {
  try {
    if (currentRead) {
      await jarvisApi.markNewsUnread(newsId);
    } else {
      await jarvisApi.markNewsRead(newsId);
    }
    const item = newsItems.find(n => n.id === newsId);
    if (item) item.is_read = !currentRead;
    window.jarvisApp.render();
  } catch (err) {
    console.warn('Failed to toggle read state:', err);
  }
}

export async function toggleArticleSaved(newsId, currentSaved) {
  try {
    await jarvisApi.toggleNewsSaved(newsId, !currentSaved);
    const item = newsItems.find(n => n.id === newsId);
    if (item) item.is_saved = !currentSaved;
    window.jarvisApp.render();
  } catch (err) {
    console.warn('Failed to toggle saved state:', err);
  }
}

export function toggleClusterExpanded(clusterId) {
  expandedClusters[clusterId] = !expandedClusters[clusterId];
  window.jarvisApp.render();
}

export async function summarizeClusterAction(clusterId) {
  try {
    clusterSummaries[clusterId] = { loading: true };
    window.jarvisApp.render();

    const summary = await jarvisApi.summarizeCluster(clusterId);
    clusterSummaries[clusterId] = summary;
    window.jarvisApp.render();
  } catch (err) {
    alert(`Failed to summarize cluster: ${err.message}`);
    delete clusterSummaries[clusterId];
    window.jarvisApp.render();
  }
}

export async function generateNewsBriefing(briefingType = 'on_demand', timeWindow = '24h') {
  isGeneratingBriefing = true;
  window.jarvisApp.render();

  try {
    const briefing = await jarvisApi.createNewsBriefing(
      activeCategory === 'all' || activeCategory === 'topic' ? null : activeCategory,
      timeWindow,
      briefingType,
      activeTopicId,
      true
    );
    activeBriefing = briefing;
  } catch (err) {
    alert(`Failed to synthesize intelligence briefing: ${err.message}`);
  } finally {
    isGeneratingBriefing = false;
    window.jarvisApp.render();
  }
}

export async function saveActiveBriefingAction() {
  if (!activeBriefing || !activeBriefing.briefing_id) return;
  try {
    await jarvisApi.saveNewsBriefing(activeBriefing.briefing_id);
    activeBriefing.saved = true;
    alert('Briefing permanently secured in intelligence vault.');
    window.jarvisApp.render();
  } catch (err) {
    alert(`Failed to save briefing: ${err.message}`);
  }
}

export function closeBriefingModal() {
  activeBriefing = null;
  window.jarvisApp.render();
}

export function toggleTopicsModal(show) {
  showTopicsModal = show;
  if (show) loadTopics();
  window.jarvisApp.render();
}

export function toggleNotificationsModal(show) {
  showNotificationsModal = show;
  if (show) loadNotificationRules();
  window.jarvisApp.render();
}

export function openArticleLink(url) {
  if (!url) return;
  window.open(url, '_blank', 'noopener,noreferrer');
}

export function renderNewsScreen() {
  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <button onclick="window.jarvisApp.goBack()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">arrow_back</span>
          </button>
          <div>
            <span class="label-caps" style="color: var(--cyan-core); letter-spacing: 0.15em;">GLOBAL TELEMETRY STREAM</span>
            <h2 class="hud-title" style="font-size: 18px; margin-top: 1px;">News Intelligence</h2>
          </div>
        </div>

        <div style="display: flex; gap: 6px; align-items: center;">
          <span class="badge ${providerStatus.includes('LIVE') ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">${providerStatus}</span>
          <button onclick="window.jarvisApp.toggleNotificationsModal(true)" class="hud-btn-ghost" style="padding: 6px 8px; font-size: 10px;" title="Notification Rules">
            <span class="material-symbols-outlined" style="font-size: 14px;">notifications</span>
          </button>
          <button onclick="window.jarvisApp.toggleTopicsModal(true)" class="hud-btn-ghost" style="padding: 6px 8px; font-size: 10px;" title="Follow Topics">
            <span class="material-symbols-outlined" style="font-size: 14px;">subscriptions</span>
          </button>
        </div>
      </div>

      <!-- Control Strip: Category Filter Pills & Actions -->
      <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px;">
        <div style="display: flex; gap: 6px; overflow-x: auto; scrollbar-width: none; flex: 1;">
          ${['all', 'technology', 'economy', 'science', 'energy'].map(cat => {
            const isActive = activeCategory === cat && !activeTopicId;
            return `
              <button onclick="window.jarvisApp.filterNews('${cat}')" style="
                background: ${isActive ? 'var(--cyan-core)' : 'var(--surface-input)'};
                color: ${isActive ? 'var(--bg-void)' : 'var(--text-secondary)'};
                border: 1px solid ${isActive ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
                font-family: var(--font-telemetry);
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                padding: 4px 10px;
                cursor: pointer;
                clip-path: var(--chamfer-clip-sm);
                white-space: nowrap;
              ">
                ${cat}
              </button>
            `;
          }).join('')}

          ${subscribedTopics.map(top => {
            const isActive = activeTopicId === top.id;
            return `
              <button onclick="window.jarvisApp.filterNewsTopic('${top.id}')" style="
                background: ${isActive ? 'var(--cyan-glow)' : 'rgba(0, 240, 255, 0.08)'};
                color: ${isActive ? '#ffffff' : 'var(--cyan-core)'};
                border: 1px solid var(--cyan-core);
                font-family: var(--font-telemetry);
                font-size: 10px;
                font-weight: 700;
                text-transform: uppercase;
                padding: 4px 10px;
                cursor: pointer;
                clip-path: var(--chamfer-clip-sm);
                white-space: nowrap;
              ">
                ★ ${top.topic_name}
              </button>
            `;
          }).join('')}
        </div>

        <div style="display: flex; gap: 4px;">
          <button onclick="window.jarvisApp.generateNewsBriefing()" class="hud-btn" style="padding: 6px 10px; font-size: 9px; white-space: nowrap;" ${isGeneratingBriefing ? 'disabled' : ''}>
            <span class="material-symbols-outlined" style="font-size: 12px;">summarize</span>
            ${isGeneratingBriefing ? 'Synthesizing...' : 'Briefing'}
          </button>
          <button onclick="window.jarvisApp.refreshNewsFeed()" class="hud-btn-ghost" style="padding: 6px 8px; font-size: 10px;" title="Refresh Wires">
            <span class="material-symbols-outlined" style="font-size: 14px;">refresh</span>
          </button>
        </div>
      </div>

      <!-- Telemetry Bar -->
      ${isFetchingNews ? `
        <div style="display: flex; align-items: center; gap: 8px; padding: 6px 10px; background: rgba(0, 240, 255, 0.05); border-left: 2px solid var(--cyan-core);">
          <div class="pulse-dot"></div>
          <span class="font-telemetry" style="font-size: 9px; color: var(--cyan-core);">
            INTERCEPTING AUTHORITATIVE WIRES • NORMALIZING TELEMETRY...
          </span>
        </div>
      ` : ''}

      <!-- Event Clusters Section -->
      ${eventClusters.length > 0 ? `
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <div style="display: flex; justify-content: space-between; align-items: center;">
            <span class="label-caps" style="color: var(--cyan-core);">CLUSTERED INTELLIGENCE EVENTS (${eventClusters.length})</span>
            <span style="font-size: 8px; color: var(--text-muted);">Multi-source deduplicated streams</span>
          </div>

          <div style="display: flex; flex-direction: column; gap: 10px;">
            ${eventClusters.map(cl => renderEventClusterCard(cl)).join('')}
          </div>
        </div>
      ` : ''}

      <!-- Individual Stories Feed -->
      <div style="display: flex; flex-direction: column; gap: 8px; margin-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="label-caps" style="color: var(--text-secondary);">INDIVIDUAL WIRE DISPATCHES (${newsItems.length})</span>
          <span style="font-size: 8px; color: var(--text-muted);">Timestamped source records</span>
        </div>

        ${newsItems.length === 0 && !isFetchingNews ? `
          <div class="hud-panel" style="padding: 24px; text-align: center;">
            <span class="material-symbols-outlined" style="font-size: 32px; color: var(--text-muted);">newspaper</span>
            <p style="font-size: 12px; color: var(--text-muted); margin-top: 8px;">No news items available under active filters.</p>
          </div>
        ` : ''}

        <div style="display: flex; flex-direction: column; gap: 8px;">
          ${newsItems.map(item => renderArticleCard(item)).join('')}
        </div>
      </div>

      <!-- Modals -->
      ${activeBriefing ? renderBriefingModal(activeBriefing) : ''}
      ${showTopicsModal ? renderTopicsModal(subscribedTopics) : ''}
      ${showNotificationsModal ? renderNotificationsModal(notificationRules, dispatchedNotifications) : ''}

    </div>
  `;
}

function renderEventClusterCard(cl) {
  const isExpanded = !!expandedClusters[cl.id];
  const summaryState = clusterSummaries[cl.id];
  const memberArticles = newsItems.filter(n => (cl.member_item_ids || cl.item_ids || []).includes(n.id));

  const impColor = cl.importance_level === 'critical' ? 'var(--stark-red)' :
                   cl.importance_level === 'high' ? 'var(--warning-amber)' : 'var(--cyan-core)';

  return `
    <div class="hud-panel" style="padding: 12px; border-left: 3px solid ${impColor}; display: flex; flex-direction: column; gap: 8px;">
      
      <!-- Cluster Header -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
        <div style="display: flex; flex-wrap: wrap; gap: 4px; align-items: center;">
          <span class="badge" style="background: rgba(0,0,0,0.4); border-color: ${impColor}; color: ${impColor}; font-size: 8px;">
            ${(cl.importance_level || 'NORMAL').toUpperCase()}
          </span>
          <span class="badge badge-cyan" style="font-size: 8px;">
            ${cl.publisher_count || (cl.sources && cl.sources.length) || 1} PUBLISHERS
          </span>
          <span class="badge badge-cyan" style="font-size: 8px;">
            ${cl.source_count || (cl.item_ids && cl.item_ids.length) || 1} SOURCES
          </span>
          ${cl.conflicting_coverage ? `
            <span class="badge badge-amber" style="font-size: 8px;">CONFLICTING COVERAGE</span>
          ` : ''}
        </div>

        <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted); white-space: nowrap;">
          ${new Date(cl.first_observed_at || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      <!-- Representative Headline -->
      <h3 style="font-size: 13px; font-weight: 700; color: var(--text-primary); line-height: 1.35; margin: 0;">
        ${cl.representative_headline}
      </h3>

      <!-- Summary -->
      <p style="font-size: 11px; color: var(--text-secondary); line-height: 1.45; margin: 0;">
        ${cl.summary}
      </p>

      <!-- Inline AI Summary if generated -->
      ${summaryState && summaryState.summary ? `
        <div style="background: rgba(0, 240, 255, 0.05); border: 1px solid rgba(0, 240, 255, 0.2); padding: 8px 10px; margin-top: 4px;">
          <div style="display: flex; align-items: center; gap: 4px; margin-bottom: 4px;">
            <span class="material-symbols-outlined" style="font-size: 12px; color: var(--cyan-core);">smart_toy</span>
            <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">J.A.R.V.I.S. CLUSTER SYNTHESIS</span>
          </div>
          <p style="font-size: 10px; color: var(--text-primary); margin: 0; line-height: 1.4;">
            ${summaryState.summary}
          </p>
        </div>
      ` : ''}

      <!-- Cluster Action Bar -->
      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.08); padding-top: 8px; margin-top: 4px;">
        <div style="display: flex; gap: 4px;">
          <button onclick="window.jarvisApp.toggleClusterExpanded('${cl.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">${isExpanded ? 'expand_less' : 'expand_more'}</span>
            ${isExpanded ? 'Hide Sources' : 'View Sources (' + (memberArticles.length || cl.source_count || 1) + ')'}
          </button>

          <button onclick="window.jarvisApp.summarizeClusterAction('${cl.id}')" class="hud-btn-ghost" style="font-size: 9px; padding: 4px 8px;" ${summaryState && summaryState.loading ? 'disabled' : ''}>
            <span class="material-symbols-outlined" style="font-size: 12px;">auto_awesome</span>
            ${summaryState && summaryState.loading ? 'Summarizing...' : 'Summarize'}
          </button>
        </div>

        <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted);">
          ${(cl.sources || []).slice(0, 3).join(', ')}
        </span>
      </div>

      <!-- Expandable Member Articles -->
      ${isExpanded ? `
        <div style="display: flex; flex-direction: column; gap: 6px; padding-top: 8px; border-top: 1px dashed rgba(0, 240, 255, 0.15);">
          ${memberArticles.map(m => `
            <div style="padding: 6px 8px; background: var(--surface-subtle); display: flex; justify-content: space-between; align-items: center;">
              <div style="flex: 1; padding-right: 8px;">
                <span style="font-size: 11px; font-weight: 600; color: var(--text-primary); cursor: pointer;" onclick="window.jarvisApp.openArticleLink('${m.url}')">
                  ${m.headline}
                </span>
                <div style="font-size: 8px; color: var(--text-muted); margin-top: 2px;">
                  ${m.publisher} • ${new Date(m.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
              <button onclick="window.jarvisApp.openArticleLink('${m.url}')" class="hud-btn-ghost" style="padding: 4px; font-size: 9px;" title="Open Source URL">
                <span class="material-symbols-outlined" style="font-size: 12px;">open_in_new</span>
              </button>
            </div>
          `).join('')}
        </div>
      ` : ''}

    </div>
  `;
}

function renderArticleCard(item) {
  const isRead = !!item.is_read;
  const isSaved = !!item.is_saved;

  return `
    <div class="hud-panel" style="padding: 10px; opacity: ${isRead ? '0.75' : '1.0'}; display: flex; flex-direction: column; gap: 6px;">
      
      <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px;">
        <div style="display: flex; gap: 4px; align-items: center; flex-wrap: wrap;">
          <span class="badge badge-cyan" style="font-size: 8px;">${item.publisher}</span>
          <span class="badge" style="font-size: 8px; background: rgba(0,0,0,0.4);">${item.category}</span>
          ${item.ticker ? `<span class="badge badge-cyan" style="font-size: 8px;">$${item.ticker}</span>` : ''}
          ${item.importance_label === 'critical' ? `<span class="badge badge-red" style="font-size: 8px;">CRITICAL</span>` : ''}
        </div>

        <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted); white-space: nowrap;">
          ${new Date(item.published_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>

      <h4 style="font-size: 12px; font-weight: 700; color: var(--text-primary); line-height: 1.35; margin: 0; cursor: pointer;" onclick="window.jarvisApp.openArticleLink('${item.url}')">
        ${item.headline}
      </h4>

      <p style="font-size: 10px; color: var(--text-secondary); line-height: 1.4; margin: 0;">
        ${item.summary}
      </p>

      <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.05); padding-top: 6px; margin-top: 2px;">
        <div style="display: flex; gap: 4px;">
          <button onclick="window.jarvisApp.toggleArticleRead('${item.id}', ${isRead})" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px;">
            <span class="material-symbols-outlined" style="font-size: 10px;">${isRead ? 'mark_email_read' : 'mark_email_unread'}</span>
            ${isRead ? 'Read' : 'Mark Read'}
          </button>

          <button onclick="window.jarvisApp.toggleArticleSaved('${item.id}', ${isSaved})" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px; color: ${isSaved ? 'var(--cyan-core)' : 'inherit'};">
            <span class="material-symbols-outlined" style="font-size: 10px;">${isSaved ? 'bookmark' : 'bookmark_border'}</span>
            ${isSaved ? 'Saved' : 'Save'}
          </button>
        </div>

        <button onclick="window.jarvisApp.openArticleLink('${item.url}')" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px;">
          <span class="material-symbols-outlined" style="font-size: 10px;">open_in_new</span>
          Source Link
        </button>
      </div>

    </div>
  `;
}

function renderBriefingModal(briefing) {
  return `
    <div style="position: fixed; inset: 0; background: rgba(5, 11, 20, 0.9); backdrop-filter: blur(8px); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 14px;">
      <div class="hud-panel hud-scroll" style="width: 100%; max-width: 580px; max-height: 85vh; overflow-y: auto; padding: 18px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 14px;">
        
        <!-- Header -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 10px;">
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">EXECUTIVE INTELLIGENCE SYNTHESIS</span>
            <h2 class="hud-title" style="font-size: 16px; margin-top: 2px;">
              ${briefing.title}
            </h2>
            <div style="font-size: 8px; color: var(--text-muted); margin-top: 2px;">
              Window: ${briefing.time_window || '24h'} • Provider: ${briefing.provider_name || 'LLM Engine'} • ${briefing.timestamp}
            </div>
          </div>

          <button onclick="window.jarvisApp.closeBriefingModal()" class="hud-btn-ghost" style="padding: 4px;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Executive Summary -->
        <div>
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">EXECUTIVE OVERVIEW</span>
          <p style="font-size: 11px; color: var(--text-primary); line-height: 1.5; margin-top: 4px;">
            ${briefing.summary}
          </p>
        </div>

        <!-- Key Events -->
        <div style="display: flex; flex-direction: column; gap: 8px;">
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">SYNTHESIZED CLUSTER EVENTS (${(briefing.key_events || []).length})</span>
          
          ${(briefing.key_events || []).map((ev, idx) => `
            <div style="padding: 8px 10px; background: rgba(0, 240, 255, 0.04); border-left: 2px solid var(--cyan-core);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 11px; font-weight: 700; color: var(--text-primary);">${ev.headline}</span>
                <span class="badge badge-cyan" style="font-size: 7px;">${ev.coverage_depth || 'Covered'}</span>
              </div>
              <p style="font-size: 10px; color: var(--text-secondary); line-height: 1.4; margin-top: 4px; margin-bottom: 0;">
                ${ev.summary}
              </p>
            </div>
          `).join('')}
        </div>

        <!-- Market Implications (Observational Only) -->
        ${briefing.market_implications ? `
          <div style="background: rgba(255, 170, 0, 0.05); border: 1px solid rgba(255, 170, 0, 0.2); padding: 8px 10px;">
            <span class="label-caps" style="color: var(--warning-amber); font-size: 8px;">MARKET & SECTOR SCENARIO OBSERVATION</span>
            <p style="font-size: 10px; color: var(--text-primary); line-height: 1.4; margin-top: 4px; margin-bottom: 2px;">
              ${briefing.market_implications}
            </p>
            <div style="font-size: 8px; color: var(--text-muted);">
              Notice: Information is informational scenario telemetry only. Zero trading or broker execution permitted.
            </div>
          </div>
        ` : ''}

        <!-- Verified Citations -->
        <div>
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">VERIFIED WIRE SOURCES (${(briefing.citations || []).length})</span>
          <div style="display: flex; flex-direction: column; gap: 4px; margin-top: 4px;">
            ${(briefing.citations || []).map(c => `
              <div style="font-size: 9px; color: var(--text-secondary); display: flex; justify-content: space-between; align-items: center;">
                <span>[${c.id}] ${c.title} <strong>(${c.publisher})</strong></span>
                <button onclick="window.jarvisApp.openArticleLink('${c.url}')" class="hud-btn-ghost" style="padding: 1px 4px; font-size: 8px;">
                  Open
                </button>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Action Footer -->
        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid rgba(0, 240, 255, 0.1); padding-top: 10px;">
          <button onclick="window.jarvisApp.saveActiveBriefingAction()" class="hud-btn-ghost" style="font-size: 10px; padding: 6px 12px;">
            <span class="material-symbols-outlined" style="font-size: 12px;">bookmark</span>
            ${briefing.saved ? 'Saved in Vault' : 'Save to Vault'}
          </button>

          <div style="display: flex; gap: 6px;">
            <button onclick="window.jarvisApp.closeBriefingModal()" class="hud-btn" style="font-size: 10px; padding: 6px 14px;">
              Done
            </button>
          </div>
        </div>

      </div>
    </div>
  `;
}

function renderTopicsModal(topics) {
  return `
    <div style="position: fixed; inset: 0; background: rgba(5, 11, 20, 0.88); backdrop-filter: blur(8px); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 16px;">
      <div class="hud-panel" style="width: 100%; max-width: 480px; padding: 18px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 8px;">
          <div>
            <span class="badge badge-cyan" style="font-size: 8px;">TOPIC RADAR</span>
            <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              Topic Subscriptions & Entity Radar
            </h3>
          </div>

          <button onclick="window.jarvisApp.toggleTopicsModal(false)" class="hud-btn-ghost" style="padding: 4px;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Add Topic Form with Type & Ticker Selector -->
        <div style="display: flex; flex-direction: column; gap: 8px; background: rgba(0, 240, 255, 0.03); padding: 10px;">
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">FOLLOW NEW ENTITY OR KEYWORD</span>
          
          <div style="display: flex; gap: 6px;">
            <input 
              type="text" 
              id="new-topic-name" 
              class="hud-input" 
              placeholder="Topic or Company (e.g. ASML, NVIDIA, Superconductors)..."
              style="flex: 1;"
            >
            <select id="new-topic-type" class="hud-input" style="width: 100px; font-size: 9px;">
              <option value="company">Company</option>
              <option value="ticker">Ticker</option>
              <option value="industry">Industry</option>
              <option value="keyword" selected>Keyword</option>
              <option value="country">Country</option>
            </select>
          </div>

          <div style="display: flex; gap: 6px; align-items: center;">
            <input 
              type="text" 
              id="new-topic-ticker" 
              class="hud-input" 
              placeholder="Ticker symbol (e.g. NVDA, TSM)"
              style="width: 120px;"
            >

            <label style="display: flex; align-items: center; gap: 4px; font-size: 10px; color: var(--text-secondary); cursor: pointer;">
              <input type="checkbox" id="new-topic-notif" checked>
              Alerts
            </label>

            <select id="new-topic-thresh" class="hud-input" style="flex: 1; font-size: 9px;">
              <option value="high" selected>High & Critical</option>
              <option value="critical">Critical Only</option>
              <option value="moderate">Moderate & Up</option>
              <option value="all">All Updates</option>
            </select>

            <button onclick="
              const name = document.getElementById('new-topic-name').value;
              const type = document.getElementById('new-topic-type').value;
              const ticker = document.getElementById('new-topic-ticker').value;
              const notif = document.getElementById('new-topic-notif').checked;
              const thresh = document.getElementById('new-topic-thresh').value;
              document.getElementById('new-topic-name').value = '';
              document.getElementById('new-topic-ticker').value = '';
              window.jarvisApp.subscribeTopicAction(name, type, ticker, notif, thresh);
            " class="hud-btn" style="padding: 6px 12px; font-size: 9px;">
              Follow
            </button>
          </div>
        </div>

        <!-- Current Subscriptions -->
        <div style="display: flex; flex-direction: column; gap: 6px; max-height: 220px; overflow-y: auto;">
          ${topics.length === 0 ? `
            <div style="padding: 16px; text-align: center; color: var(--text-muted); font-size: 11px;">
              No custom topic subscriptions active.
            </div>
          ` : topics.map(t => `
            <div class="hud-panel" style="padding: 8px 10px; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <span style="font-size: 11px; font-weight: 700; color: var(--text-primary);">${t.topic_name}</span>
                ${t.ticker ? `<span class="badge badge-cyan" style="font-size: 7px; margin-left: 4px;">$${t.ticker}</span>` : ''}
                <span class="font-telemetry" style="font-size: 8px; color: var(--text-muted); margin-left: 4px;">[${t.topic_type || 'keyword'}]</span>
              </div>

              <div style="display: flex; gap: 6px; align-items: center;">
                <button onclick="window.jarvisApp.filterNewsTopic('${t.id}')" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px;">
                  View Feed
                </button>
                <button onclick="window.jarvisApp.unsubscribeTopicAction('${t.id}')" class="hud-btn-ghost" style="font-size: 8px; padding: 2px 6px; color: var(--warning-amber);">
                  Unfollow
                </button>
              </div>
            </div>
          `).join('')}
        </div>

        <div style="display: flex; justify-content: flex-end; border-top: 1px solid rgba(0, 240, 255, 0.1); padding-top: 8px;">
          <button onclick="window.jarvisApp.toggleTopicsModal(false)" class="hud-btn" style="font-size: 9px; padding: 5px 12px;">
            Done
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderNotificationsModal(rules, dispatches) {
  return `
    <div style="position: fixed; inset: 0; background: rgba(5, 11, 20, 0.88); backdrop-filter: blur(8px); z-index: 999; display: flex; align-items: center; justify-content: center; padding: 16px;">
      <div class="hud-panel hud-scroll" style="width: 100%; max-width: 500px; max-height: 80vh; overflow-y: auto; padding: 18px; border-color: var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(0, 240, 255, 0.2); padding-bottom: 8px;">
          <div>
            <span class="badge badge-cyan" style="font-size: 8px;">ALERT RULES</span>
            <h3 style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              Notification Rules & Quiet Hours
            </h3>
          </div>

          <button onclick="window.jarvisApp.toggleNotificationsModal(false)" class="hud-btn-ghost" style="padding: 4px;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Quiet Hours Info -->
        <div style="background: rgba(0, 240, 255, 0.04); border: 1px solid rgba(0, 240, 255, 0.15); padding: 8px 10px;">
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">QUIET HOURS & DEDUPLICATION</span>
          <p style="font-size: 10px; color: var(--text-secondary); margin: 4px 0 0 0; line-height: 1.4;">
            Default quiet hours: <strong>22:00 to 07:00</strong>. Alerts are strictly suppressed unless updated with critical material facts.
          </p>
        </div>

        <!-- Dispatched Notifications History -->
        <div style="display: flex; flex-direction: column; gap: 6px;">
          <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">RECENT DISPATCHED NOTIFICATIONS (${dispatches.length})</span>
          
          ${dispatches.length === 0 ? `
            <div style="padding: 12px; text-align: center; color: var(--text-muted); font-size: 10px;">
              No notification events logged in the last 24 hours.
            </div>
          ` : dispatches.slice(0, 6).map(d => `
            <div style="padding: 6px 8px; background: var(--surface-subtle); border-left: 2px solid var(--cyan-core);">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 10px; font-weight: 700; color: var(--text-primary);">${d.title}</span>
                <span class="badge badge-cyan" style="font-size: 7px;">${d.importance.toUpperCase()}</span>
              </div>
              <div style="font-size: 8px; color: var(--text-muted); margin-top: 2px;">
                ${d.message} • ${d.sent_at}
              </div>
            </div>
          `).join('')}
        </div>

        <div style="display: flex; justify-content: flex-end; border-top: 1px solid rgba(0, 240, 255, 0.1); padding-top: 8px;">
          <button onclick="window.jarvisApp.toggleNotificationsModal(false)" class="hud-btn" style="font-size: 9px; padding: 5px 12px;">
            Close
          </button>
        </div>

      </div>
    </div>
  `;
}
