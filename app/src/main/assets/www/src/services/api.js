// ==========================================================================
// JARVIS API Client: Connects Frontend HUD to Python FastAPI Backend
// With offline fallback, token management, and approval handling
// ==========================================================================

const BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
  ? window.location.origin
  : 'http://127.0.0.1:8000';

class JarvisApiClient {
  constructor() {
    this.token = localStorage.getItem('JARVIS_JWT_TOKEN') || null;
    this.activeConversationId = localStorage.getItem('JARVIS_ACTIVE_CONV_ID') || null;
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('JARVIS_JWT_TOKEN', token);
    } else {
      localStorage.removeItem('JARVIS_JWT_TOKEN');
    }
  }

  setActiveConversation(convId) {
    this.activeConversationId = convId;
    if (convId) {
      localStorage.setItem('JARVIS_ACTIVE_CONV_ID', convId);
    } else {
      localStorage.removeItem('JARVIS_ACTIVE_CONV_ID');
    }
  }

  async request(endpoint, options = {}) {
    const headers = {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const config = {
      ...options,
      headers
    };

    try {
      const response = await fetch(`${BASE_URL}${endpoint}`, config);
      if (!response.ok) {
        let errDetail = `HTTP ${response.status}: ${response.statusText}`;
        try {
          const errJson = await response.json();
          if (errJson.detail) errDetail = errJson.detail;
        } catch (_) {}
        throw new Error(errDetail);
      }
      return await response.json();
    } catch (error) {
      console.warn(`[JARVIS API] Request to ${endpoint} failed:`, error.message);
      throw error;
    }
  }

  // Auth
  async login(username, password) {
    const data = await this.request('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    if (data && data.access_token) {
      this.setToken(data.access_token);
    }
    return data;
  }

  async getMe() {
    return await this.request('/api/auth/me');
  }

  // System Telemetry & Status
  async getSystemStatus() {
    return await this.request('/api/system/status');
  }

  async getTools() {
    return await this.request('/api/tools');
  }

  // AI Chat & Orchestration
  async sendChat(content, conversationId = null, approvalId = null) {
    const convId = conversationId || this.activeConversationId;
    const data = await this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify({
        content,
        conversation_id: convId,
        approval_id: approvalId
      })
    });

    if (data.conversation_id) {
      this.setActiveConversation(data.conversation_id);
    }
    return data;
  }

  // Directives / Tasks
  async getTasks(status = null) {
    const query = status ? `?status=${encodeURIComponent(status)}` : '';
    return await this.request(`/api/tasks${query}`);
  }

  async createTask(title, description = '', priority = 'medium', category = 'general', dueDate = 'Tomorrow') {
    return await this.request('/api/tasks', {
      method: 'POST',
      body: JSON.stringify({
        title,
        description,
        priority,
        category,
        due_date: dueDate
      })
    });
  }

  async updateTask(taskId, updates) {
    return await this.request(`/api/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(updates)
    });
  }

  async deleteTask(taskId) {
    return await this.request(`/api/tasks/${taskId}`, {
      method: 'DELETE'
    });
  }

  // Human-in-the-Loop Approvals
  async getPendingApprovals() {
    return await this.request('/api/approvals');
  }

  async decideApproval(approvalId, action, reason = null) {
    return await this.request(`/api/approvals/${approvalId}/decide`, {
      method: 'POST',
      body: JSON.stringify({ action, reason })
    });
  }

  async executeApproval(approvalId) {
    return await this.request(`/api/approvals/${approvalId}/execute`, {
      method: 'POST'
    });
  }

  // Episodic Memory
  async getMemories(query = null) {
    const q = query ? `?q=${encodeURIComponent(query)}` : '';
    return await this.request(`/api/memories${q}`);
  }

  async createMemory(category, key, value) {
    return await this.request('/api/memories', {
      method: 'POST',
      body: JSON.stringify({ category, key, value })
    });
  }

  async deleteMemory(memoryId) {
    return await this.request(`/api/memories/${memoryId}`, {
      method: 'DELETE'
    });
  }

  // Research & Search (Phase 3)
  async searchWeb(query, topic = null, region = 'us-en', limit = 8) {
    return await this.request('/api/research/search', {
      method: 'POST',
      body: JSON.stringify({ query, topic, region, limit })
    });
  }

  async getSearchHistory() {
    return await this.request('/api/research/search-history');
  }

  async saveSearchResult(resultId) {
    return await this.request(`/api/research/results/${resultId}/save`, {
      method: 'POST'
    });
  }

  async unsaveSearchResult(resultId) {
    return await this.request(`/api/research/results/${resultId}/save`, {
      method: 'DELETE'
    });
  }

  async fetchSource(url) {
    return await this.request('/api/research/source/fetch', {
      method: 'POST',
      body: JSON.stringify({ url })
    });
  }

  async summarizeSource(sourceId) {
    return await this.request(`/api/research/source/${sourceId}/summarize`, {
      method: 'POST'
    });
  }

  async createResearchReport(topic, query, sourceUrls = [], focusAreas = []) {
    return await this.request('/api/research/reports', {
      method: 'POST',
      body: JSON.stringify({
        topic,
        query,
        source_urls: sourceUrls,
        focus_areas: focusAreas
      })
    });
  }

  async getResearchReports() {
    return await this.request('/api/research/reports');
  }

  async getResearchReport(reportId) {
    return await this.request(`/api/research/reports/${reportId}`);
  }

  async deleteResearchReport(reportId) {
    return await this.request(`/api/research/reports/${reportId}`, {
      method: 'DELETE'
    });
  }

  // Research Briefs (10-15 line synthesized briefs with citations)
  async generateResearchBrief(query, answerMode = 'brief', topicType = null, parentBriefId = null, followUpAction = null, saveResult = false) {
    return await this.request('/api/research/brief', {
      method: 'POST',
      body: JSON.stringify({
        query,
        answer_mode: answerMode,
        topic_type: topicType,
        parent_brief_id: parentBriefId,
        follow_up_action: followUpAction,
        save_result: saveResult
      })
    });
  }

  async getSavedBriefs(query = null, limit = 20) {
    const qParam = query ? `?query=${encodeURIComponent(query)}&limit=${limit}` : `?limit=${limit}`;
    return await this.request(`/api/research/briefs${qParam}`);
  }

  async getResearchBrief(briefId) {
    return await this.request(`/api/research/briefs/${briefId}`);
  }

  async saveResearchBrief(briefId) {
    return await this.request(`/api/research/briefs/${briefId}/save`, {
      method: 'POST'
    });
  }

  async unsaveResearchBrief(briefId) {
    return await this.request(`/api/research/briefs/${briefId}/save`, {
      method: 'DELETE'
    });
  }

  async renameResearchBrief(briefId, title) {
    return await this.request(`/api/research/briefs/${briefId}`, {
      method: 'PATCH',
      body: JSON.stringify({ title })
    });
  }

  async deleteResearchBrief(briefId) {
    return await this.request(`/api/research/briefs/${briefId}`, {
      method: 'DELETE'
    });
  }

  async exportResearchBrief(briefId) {
    return await this.request(`/api/research/briefs/${briefId}/export`);
  }

  async executeBriefAction(briefId, action, followUpQuery = null) {
    return await this.request(`/api/research/briefs/${briefId}/action`, {
      method: 'POST',
      body: JSON.stringify({
        action,
        follow_up_query: followUpQuery
      })
    });
  }


  // News Intelligence (Phase 5)
  async getNews(category = null, region = null, limit = 25, topicId = null) {
    const params = new URLSearchParams();
    if (category && category !== 'all') params.append('category', category);
    if (region && region !== 'all') params.append('region', region);
    if (topicId) params.append('topic_id', topicId);
    if (limit) params.append('limit', limit);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return await this.request(`/api/news${qs}`);
  }

  async getNewsArticle(newsId) {
    return await this.request(`/api/news/${newsId}`);
  }

  async refreshNewsFeed() {
    return await this.request('/api/news/refresh', { method: 'POST' });
  }

  async getNewsTopics() {
    return await this.request('/api/news/topics');
  }

  async createNewsTopic(topicData) {
    return await this.request('/api/news/topics', {
      method: 'POST',
      body: JSON.stringify(topicData)
    });
  }

  async updateNewsTopic(topicId, updateData) {
    return await this.request(`/api/news/topics/${topicId}`, {
      method: 'PATCH',
      body: JSON.stringify(updateData)
    });
  }

  async deleteNewsTopic(topicId) {
    return await this.request(`/api/news/topics/${topicId}`, {
      method: 'DELETE'
    });
  }

  async refreshTopicNews(topicId) {
    return await this.request(`/api/news/topics/${topicId}/refresh`, {
      method: 'POST'
    });
  }

  async markNewsRead(newsId) {
    return await this.request(`/api/news/${newsId}/read`, {
      method: 'POST'
    });
  }

  async markNewsUnread(newsId) {
    return await this.request(`/api/news/${newsId}/unread`, {
      method: 'POST'
    });
  }

  async toggleNewsSaved(newsId, save = true) {
    return await this.request(`/api/news/${newsId}/save`, {
      method: save ? 'POST' : 'DELETE'
    });
  }

  async getNewsClusters(category = null) {
    const qs = category && category !== 'all' ? `?category=${encodeURIComponent(category)}` : '';
    return await this.request(`/api/news/clusters${qs}`);
  }

  async getClusterDetails(clusterId) {
    return await this.request(`/api/news/clusters/${clusterId}`);
  }

  async summarizeCluster(clusterId) {
    return await this.request(`/api/news/clusters/${clusterId}/summarize`, {
      method: 'POST'
    });
  }

  async createNewsBriefing(category = null, timeWindow = '24h', type = 'on_demand', topicId = null, saveResult = false) {
    return await this.request('/api/news/briefings', {
      method: 'POST',
      body: JSON.stringify({
        category,
        time_window: timeWindow,
        type,
        topic_id: topicId,
        save_result: saveResult
      })
    });
  }

  async getNewsBriefings(limit = 20) {
    return await this.request(`/api/news/briefings?limit=${limit}`);
  }

  async getNewsBriefing(briefingId) {
    return await this.request(`/api/news/briefings/${briefingId}`);
  }

  async saveNewsBriefing(briefingId) {
    return await this.request(`/api/news/briefings/${briefingId}/save`, {
      method: 'POST'
    });
  }

  async unsaveNewsBriefing(briefingId) {
    return await this.request(`/api/news/briefings/${briefingId}/save`, {
      method: 'DELETE'
    });
  }

  async getNotificationRules() {
    return await this.request('/api/news/notification-rules');
  }

  async createNotificationRule(rule) {
    return await this.request('/api/news/notification-rules', {
      method: 'POST',
      body: JSON.stringify(rule)
    });
  }

  async updateNotificationRule(ruleId, update) {
    return await this.request(`/api/news/notification-rules/${ruleId}`, {
      method: 'PATCH',
      body: JSON.stringify(update)
    });
  }

  async deleteNotificationRule(ruleId) {
    return await this.request(`/api/news/notification-rules/${ruleId}`, {
      method: 'DELETE'
    });
  }

  async getDispatchedNotifications(limit = 30) {
    return await this.request(`/api/news/notifications?limit=${limit}`);
  }


  // LLM Provider Configuration (Bring Your Own Key)
  async getLLMConfig() {
    return await this.request('/api/settings/llm');
  }

  async saveLLMConfig(config) {
    return await this.request('/api/settings/llm', {
      method: 'POST',
      body: JSON.stringify(config)
    });
  }

  async testLLMConfig(testPayload) {
    return await this.request('/api/settings/llm/test', {
      method: 'POST',
      body: JSON.stringify(testPayload)
    });
  }

  async updateLLMStatus(isEnabled) {
    return await this.request('/api/settings/llm/status', {
      method: 'PATCH',
      body: JSON.stringify({ is_enabled: isEnabled })
    });
  }

  async deleteLLMConfig() {
    return await this.request('/api/settings/llm', {
      method: 'DELETE'
    });
  }

  // Phase 6 Market Intelligence & Telemetry API Methods
  async getMarketOverview() {
    return await this.request('/api/markets/overview');
  }

  async refreshMarketOverview() {
    return await this.request('/api/markets/refresh', { method: 'POST' });
  }

  async getMarketStatus() {
    return await this.request('/api/markets/status');
  }

  async searchMarketAssets(query, limit = 10) {
    return await this.request(`/api/markets/assets/search?query=${encodeURIComponent(query)}&limit=${limit}`);
  }

  async getAssetDetail(assetId) {
    return await this.request(`/api/markets/assets/${encodeURIComponent(assetId)}`);
  }

  async getAssetQuote(assetId) {
    return await this.request(`/api/markets/assets/${encodeURIComponent(assetId)}/quote`);
  }

  async getAssetHistory(assetId, interval = '1d', range = '1mo') {
    return await this.request(`/api/markets/assets/${encodeURIComponent(assetId)}/history?interval=${interval}&range=${range}`);
  }

  async getAssetNews(assetId) {
    return await this.request(`/api/markets/assets/${encodeURIComponent(assetId)}/news`);
  }

  async getAssetInsights(assetId) {
    return await this.request(`/api/markets/assets/${encodeURIComponent(assetId)}/insights`);
  }

  async getWatchlists() {
    return await this.request('/api/markets/watchlists');
  }

  async createWatchlist(name) {
    return await this.request('/api/markets/watchlists', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
  }

  async deleteWatchlist(watchlistId) {
    return await this.request(`/api/markets/watchlists/${watchlistId}`, {
      method: 'DELETE'
    });
  }

  async addWatchlistItem(watchlistId, assetId) {
    return await this.request(`/api/markets/watchlists/${watchlistId}/items`, {
      method: 'POST',
      body: JSON.stringify({ asset_id: assetId })
    });
  }

  async removeWatchlistItem(watchlistId, itemId) {
    return await this.request(`/api/markets/watchlists/${watchlistId}/items/${itemId}`, {
      method: 'DELETE'
    });
  }

  async refreshWatchlist(watchlistId) {
    return await this.request(`/api/markets/watchlists/${watchlistId}/refresh`, { method: 'POST' });
  }

  async getMarketAlerts() {
    return await this.request('/api/markets/alerts');
  }

  async createMarketAlert(alertPayload) {
    return await this.request('/api/markets/alerts', {
      method: 'POST',
      body: JSON.stringify(alertPayload)
    });
  }

  async deleteMarketAlert(alertId) {
    return await this.request(`/api/markets/alerts/${alertId}`, {
      method: 'DELETE'
    });
  }

  async generateMarketInsight(question, assetId = null, timeWindow = '24h') {
    return await this.request('/api/markets/insights', {
      method: 'POST',
      body: JSON.stringify({ question, asset_id: assetId, time_window: timeWindow })
    });
  }

  async getReadOnlyPortfolio() {
    return await this.request('/api/markets/portfolio');
  }
}

export const jarvisApi = new JarvisApiClient();

