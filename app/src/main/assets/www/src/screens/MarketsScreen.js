// ==========================================================================
// Markets Screen: Real Market Data & Financial Telemetry Radar
// Phase 6: Read-Only Market Intelligence, Charts, Watchlists & News Correlation
// Strictly Read-Only: No live order placement or broker write execution
// ==========================================================================

import { store } from '../services/store.js';
import { jarvisApi } from '../services/api.js';

let activeSubTab = 'overview'; // 'overview' | 'watchlist' | 'portfolio' | 'insights'
let overviewData = null;
let marketStatusData = null;
let userWatchlists = [];
let activeWatchlistId = null;
let activeAssetDetail = null;
let activeAssetQuote = null;
let activeAssetHistory = [];
let activeAssetNews = [];
let activeChartRange = '1mo'; // 1d | 1w | 1mo | 3mo | 1y | 5y
let activeInsight = null;
let searchResults = [];
let isSearching = false;
let isFetchingData = false;
let showSearchModal = false;
let showAlertModal = false;
let showInsightModal = false;
let candidateToAdd = null;

export function setMarketSubTab(tab) {
  activeSubTab = tab;
  if (tab === 'overview' && !overviewData) {
    loadMarketOverview();
  } else if (tab === 'watchlist') {
    loadWatchlists();
  }
  window.jarvisApp.render();
}

export function setChartRange(range) {
  activeChartRange = range;
  if (activeAssetDetail) {
    loadAssetHistory(activeAssetDetail.id, range);
  }
}

export async function loadMarketOverview(forceRefresh = false) {
  isFetchingData = true;
  window.jarvisApp.render();
  try {
    const [ov, st] = await Promise.all([
      forceRefresh ? jarvisApi.refreshMarketOverview() : jarvisApi.getMarketOverview(),
      jarvisApi.getMarketStatus()
    ]);
    overviewData = ov;
    marketStatusData = st;
  } catch (err) {
    console.error('Failed to load market overview:', err);
  } finally {
    isFetchingData = false;
    window.jarvisApp.render();
  }
}

export async function loadWatchlists() {
  isFetchingData = true;
  window.jarvisApp.render();
  try {
    const wls = await jarvisApi.getWatchlists();
    userWatchlists = wls || [];
    if (userWatchlists.length > 0 && !activeWatchlistId) {
      activeWatchlistId = userWatchlists[0].id;
    }
  } catch (err) {
    console.error('Failed to load watchlists:', err);
  } finally {
    isFetchingData = false;
    window.jarvisApp.render();
  }
}

export async function openAssetDetail(assetId) {
  isFetchingData = true;
  window.jarvisApp.render();
  try {
    const [detail, quote, hist, news] = await Promise.all([
      jarvisApi.getAssetDetail(assetId),
      jarvisApi.getAssetQuote(assetId),
      jarvisApi.getAssetHistory(assetId, '1d', activeChartRange),
      jarvisApi.getAssetNews(assetId)
    ]);
    activeAssetDetail = detail;
    activeAssetQuote = quote;
    activeAssetHistory = hist.bars || [];
    activeAssetNews = news || [];
  } catch (err) {
    console.error('Failed to open asset detail:', err);
  } finally {
    isFetchingData = false;
    window.jarvisApp.render();
  }
}

export async function loadAssetHistory(assetId, range) {
  try {
    const hist = await jarvisApi.getAssetHistory(assetId, '1d', range);
    activeAssetHistory = hist.bars || [];
    window.jarvisApp.render();
  } catch (err) {
    console.error('Failed to update chart range:', err);
  }
}

export function closeAssetDetail() {
  activeAssetDetail = null;
  activeAssetQuote = null;
  activeAssetHistory = [];
  activeAssetNews = [];
  window.jarvisApp.render();
}

export async function handleSearchInput(query) {
  if (!query || query.trim().length < 1) {
    searchResults = [];
    window.jarvisApp.render();
    return;
  }
  isSearching = true;
  window.jarvisApp.render();
  try {
    const res = await jarvisApi.searchMarketAssets(query.trim(), 8);
    searchResults = res || [];
  } catch (err) {
    console.error('Search failed:', err);
  } finally {
    isSearching = false;
    window.jarvisApp.render();
  }
}

export function promptAddAsset(candidate) {
  candidateToAdd = candidate;
  window.jarvisApp.render();
}

export async function confirmAddAssetToWatchlist() {
  if (!candidateToAdd || !activeWatchlistId) return;
  try {
    await jarvisApi.addWatchlistItem(activeWatchlistId, candidateToAdd.id);
    candidateToAdd = null;
    showSearchModal = false;
    await loadWatchlists();
  } catch (err) {
    alert('Failed to add asset to watchlist: ' + err.message);
  }
}

export async function removeWatchlistItem(itemId) {
  if (!activeWatchlistId) return;
  try {
    await jarvisApi.removeWatchlistItem(activeWatchlistId, itemId);
    await loadWatchlists();
  } catch (err) {
    console.error('Failed to remove item:', err);
  }
}

export async function triggerInsightForAsset(assetId, symbol) {
  closeAssetDetail();
  isFetchingData = true;
  window.jarvisApp.render();
  try {
    const question = `Why is ${symbol} moving today? Explain key market telemetry and correlated news wire factors.`;
    const insight = await jarvisApi.generateMarketInsight(question, assetId, '24h');
    activeInsight = insight;
    showInsightModal = true;
  } catch (err) {
    alert('Failed to generate insight: ' + err.message);
  } finally {
    isFetchingData = false;
    window.jarvisApp.render();
  }
}

// Render SVG Chart for Asset History
function renderHistoryChart(bars) {
  if (!bars || bars.length < 2) {
    return `
      <div style="height: 140px; display: flex; align-items: center; justify-content: center; color: var(--text-muted); font-size: 11px; font-family: var(--font-telemetry);">
        NO CHART TELEMETRY AVAILABLE
      </div>
    `;
  }

  const closes = bars.map(b => b.close);
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = (max - min) || 1;
  const width = 320;
  const height = 110;
  const padding = 10;

  const points = closes.map((val, idx) => {
    const x = padding + (idx / (closes.length - 1)) * (width - 2 * padding);
    const y = height - padding - ((val - min) / range) * (height - 2 * padding);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  const isUp = closes[closes.length - 1] >= closes[0];
  const strokeColor = isUp ? 'var(--success-green)' : 'var(--error-red)';

  return `
    <div style="width: 100%; overflow: hidden; background: rgba(0, 0, 0, 0.4); border-radius: 4px; padding: 6px 0;">
      <div style="display: flex; justify-content: space-between; padding: 0 10px; font-family: var(--font-telemetry); font-size: 9px; color: var(--text-muted);">
        <span>LOW: $${min.toFixed(2)}</span>
        <span>HIGH: $${max.toFixed(2)}</span>
      </div>
      <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 120px; display: block;">
        <!-- Grid lines -->
        <line x1="10" y1="20" x2="310" y2="20" stroke="rgba(255,255,255,0.05)" stroke-width="1" stroke-dasharray="2,2"/>
        <line x1="10" y1="55" x2="310" y2="55" stroke="rgba(255,255,255,0.05)" stroke-width="1" stroke-dasharray="2,2"/>
        <line x1="10" y1="90" x2="310" y2="90" stroke="rgba(255,255,255,0.05)" stroke-width="1" stroke-dasharray="2,2"/>
        <!-- Price Polyline -->
        <polyline fill="none" stroke="${strokeColor}" stroke-width="2" points="${points}" />
      </svg>
    </div>
  `;
}

export function renderMarketsScreen() {
  if (!overviewData && !isFetchingData && activeSubTab === 'overview') {
    loadMarketOverview();
  }

  const statusLabel = marketStatusData ? marketStatusData.status : 'OPEN';
  const providerLabel = overviewData ? overviewData.provider_status : 'LIVE WIRE';
  const lastUpdated = overviewData ? overviewData.timestamp : 'SYNCHRONIZED';

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <span class="label-caps" style="color: var(--cyan-core);">FINANCIAL TELEMETRY & ASSET RADAR</span>
          <h2 class="hud-title" style="font-size: 18px; margin-top: 2px;">Market Intelligence</h2>
        </div>

        <div style="display: flex; align-items: center; gap: 8px;">
          <span class="badge ${providerLabel.includes('LIVE') ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">
            ${providerLabel}
          </span>
          <button onclick="window.jarvisApp.refreshMarketOverview(true)" class="hud-btn hud-btn-outline" style="padding: 4px 8px; font-size: 9px;">
            REFRESH
          </button>
        </div>
      </div>

      <!-- Market Status & Strictly Read-Only Trading Boundary Banner -->
      <div class="hud-panel" style="padding: 10px 12px; display: flex; align-items: center; justify-content: space-between; border-left: 3px solid var(--cyan-core);">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 8px; height: 8px; border-radius: 50%; background: ${statusLabel === 'OPEN' ? 'var(--success-green)' : 'var(--warning-amber)'}; box-shadow: 0 0 6px ${statusLabel === 'OPEN' ? 'var(--success-green)' : 'var(--warning-amber)'};"></span>
          <div>
            <span class="label-caps" style="font-size: 9px; color: ${statusLabel === 'OPEN' ? 'var(--success-green)' : 'var(--warning-amber)'};">
              US MARKETS: ${statusLabel}
            </span>
            <span style="font-size: 10px; color: var(--text-muted); font-family: var(--font-telemetry); display: block;">
              UPDATED: ${lastUpdated}
            </span>
          </div>
        </div>

        <div style="text-align: right;">
          <span class="badge badge-amber" style="font-size: 8px;">STRICTLY READ-ONLY</span>
          <span style="font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry); display: block; margin-top: 2px;">
            NO BROKER WRITE ACCESS
          </span>
        </div>
      </div>

      <!-- Segmented Market Sub-Tabs -->
      <div style="display: flex; gap: 4px; overflow-x: auto; scrollbar-width: none;">
        ${['overview', 'watchlist', 'portfolio', 'insights'].map(tab => {
          const isActive = activeSubTab === tab;
          return `
            <button onclick="window.jarvisApp.setMarketTab('${tab}')" style="
              flex: 1;
              background: ${isActive ? 'var(--cyan-core)' : 'var(--surface-input)'};
              color: ${isActive ? 'var(--bg-void)' : 'var(--text-secondary)'};
              border: 1px solid ${isActive ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
              font-family: var(--font-telemetry);
              font-size: 10px;
              font-weight: 700;
              text-transform: uppercase;
              padding: 6px 10px;
              cursor: pointer;
              clip-path: var(--chamfer-clip-sm);
              text-align: center;
            ">
              ${tab}
            </button>
          `;
        }).join('')}
      </div>

      ${isFetchingData ? `
        <div class="hud-panel" style="padding: 16px; text-align: center;">
          <span style="font-family: var(--font-telemetry); font-size: 11px; color: var(--cyan-core);">
            [SYNCHRONIZING FINANCIAL TELEMETRY FEED...]
          </span>
        </div>
      ` : ''}

      <!-- SUB-TAB 1: OVERVIEW -->
      ${activeSubTab === 'overview' ? renderOverviewSubTab() : ''}

      <!-- SUB-TAB 2: WATCHLIST -->
      ${activeSubTab === 'watchlist' ? renderWatchlistSubTab() : ''}

      <!-- SUB-TAB 3: READ-ONLY PORTFOLIO -->
      ${activeSubTab === 'portfolio' ? renderPortfolioSubTab() : ''}

      <!-- SUB-TAB 4: INSIGHTS -->
      ${activeSubTab === 'insights' ? renderInsightsSubTab() : ''}

      <!-- ASSET DETAIL MODAL -->
      ${activeAssetDetail ? renderAssetDetailModal() : ''}

      <!-- SEARCH ASSET MODAL -->
      ${showSearchModal ? renderSearchModal() : ''}

      <!-- INSIGHT MODAL -->
      ${showInsightModal && activeInsight ? renderInsightModal() : ''}

    </div>
  `;
}

function renderOverviewSubTab() {
  const indices = overviewData?.indices || [];
  const gainers = overviewData?.gainers || [];
  const losers = overviewData?.losers || [];
  const sectors = overviewData?.sectors || [];

  return `
    <!-- Major Indices Telemetry Grid -->
    <div>
      <span class="label-caps" style="color: var(--text-muted); font-size: 9px; margin-bottom: 6px; display: block;">
        MAJOR INDEX BENCHMARKS
      </span>
      <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 8px;">
        ${indices.map(idx => `
          <div onclick="window.jarvisApp.openAssetDetail('${idx.asset_id}')" class="hud-card" style="padding: 10px; cursor: pointer;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: 700; font-size: 13px; color: var(--text-primary); font-family: var(--font-telemetry);">${idx.symbol}</span>
              <span style="font-size: 8px; color: var(--text-muted);">${idx.exchange}</span>
            </div>
            <div style="font-size: 16px; font-weight: 700; font-family: var(--font-telemetry); margin-top: 4px;">
              $${idx.price.toFixed(2)}
            </div>
            <div style="font-size: 11px; font-family: var(--font-telemetry); color: ${idx.change >= 0 ? 'var(--success-green)' : 'var(--error-red)'};">
              ${idx.change >= 0 ? '+' : ''}${idx.change.toFixed(2)} (${idx.change_percent >= 0 ? '+' : ''}${idx.change_percent.toFixed(2)}%)
            </div>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Active Gainers & Losers -->
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
      <div class="hud-panel" style="padding: 10px;">
        <span class="label-caps" style="color: var(--success-green); font-size: 8px; display: block; margin-bottom: 6px;">TOP ADVANCING</span>
        ${gainers.map(g => `
          <div onclick="window.jarvisApp.openAssetDetail('${g.asset_id}')" style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer;">
            <span style="font-size: 11px; font-family: var(--font-telemetry); font-weight: 700;">${g.symbol}</span>
            <span style="font-size: 11px; font-family: var(--font-telemetry); color: var(--success-green);">+${g.change_percent.toFixed(2)}%</span>
          </div>
        `).join('')}
      </div>

      <div class="hud-panel" style="padding: 10px;">
        <span class="label-caps" style="color: var(--error-red); font-size: 8px; display: block; margin-bottom: 6px;">DECLINING</span>
        ${losers.map(l => `
          <div onclick="window.jarvisApp.openAssetDetail('${l.asset_id}')" style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid rgba(255,255,255,0.05); cursor: pointer;">
            <span style="font-size: 11px; font-family: var(--font-telemetry); font-weight: 700;">${l.symbol}</span>
            <span style="font-size: 11px; font-family: var(--font-telemetry); color: var(--error-red);">${l.change_percent.toFixed(2)}%</span>
          </div>
        `).join('')}
      </div>
    </div>

    <!-- Sector Performance Radar -->
    <div class="hud-panel" style="padding: 10px;">
      <span class="label-caps" style="color: var(--cyan-core); font-size: 8px; display: block; margin-bottom: 8px;">
        GLOBAL SECTOR PERFORMANCE
      </span>
      <div style="display: flex; flex-direction: column; gap: 6px;">
        ${sectors.map(s => `
          <div style="display: flex; justify-content: space-between; align-items: center; font-family: var(--font-telemetry); font-size: 11px;">
            <span>${s.sector}</span>
            <div style="display: flex; gap: 8px;">
              <span style="color: ${s.performance.startsWith('+') ? 'var(--success-green)' : 'var(--error-red)'}; font-weight: 700;">
                ${s.performance}
              </span>
              <span style="color: var(--text-muted); font-size: 9px;">${s.sentiment}</span>
            </div>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

function renderWatchlistSubTab() {
  const activeWl = userWatchlists.find(w => w.id === activeWatchlistId) || userWatchlists[0];
  const items = activeWl?.items || [];

  return `
    <div style="display: flex; justify-content: space-between; align-items: center;">
      <div style="display: flex; align-items: center; gap: 8px;">
        <span class="label-caps" style="font-size: 9px; color: var(--cyan-core);">ACTIVE RADAR:</span>
        <select onchange="window.jarvisApp.switchWatchlist(this.value)" class="hud-input" style="padding: 4px 8px; font-size: 11px; font-family: var(--font-telemetry);">
          ${userWatchlists.map(w => `
            <option value="${w.id}" ${w.id === activeWatchlistId ? 'selected' : ''}>${w.name} (${w.items.length})</option>
          `).join('')}
        </select>
      </div>

      <button onclick="window.jarvisApp.openSearchModal()" class="hud-btn hud-btn-cyan" style="padding: 4px 10px; font-size: 9px;">
        + ADD ASSET
      </button>
    </div>

    ${items.length === 0 ? `
      <div class="hud-panel" style="padding: 24px; text-align: center;">
        <span style="font-size: 12px; color: var(--text-muted); font-family: var(--font-telemetry); display: block;">
          NO ASSETS TRACKED IN THIS RADAR
        </span>
        <button onclick="window.jarvisApp.openSearchModal()" class="hud-btn hud-btn-outline" style="margin-top: 10px; font-size: 10px;">
          SEARCH & ADD INSTRUMENT
        </button>
      </div>
    ` : `
      <div style="display: flex; flex-direction: column; gap: 8px;">
        ${items.map(it => {
          const q = it.quote;
          const isUp = q ? q.change >= 0 : true;
          return `
            <div class="hud-card" style="padding: 12px; display: flex; justify-content: space-between; align-items: center;">
              <div onclick="window.jarvisApp.openAssetDetail('${it.asset_id}')" style="cursor: pointer; flex: 1;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span style="font-weight: 700; font-size: 14px; color: var(--text-primary); font-family: var(--font-telemetry);">
                    ${it.asset?.symbol || 'UNKNOWN'}
                  </span>
                  <span style="font-size: 9px; color: var(--text-muted);">${it.asset?.exchange || ''}</span>
                  <span class="badge ${q?.data_status?.includes('LIVE') ? 'badge-cyan' : 'badge-amber'}" style="font-size: 7px; padding: 1px 4px;">
                    ${q?.data_status || 'SIMULATED'}
                  </span>
                </div>
                <div style="font-size: 11px; color: var(--text-secondary); margin-top: 2px;">
                  ${it.asset?.name || ''}
                </div>
              </div>

              <div style="text-align: right; display: flex; align-items: center; gap: 12px;">
                <div onclick="window.jarvisApp.openAssetDetail('${it.asset_id}')" style="cursor: pointer;">
                  <div style="font-size: 15px; font-weight: 700; font-family: var(--font-telemetry);">
                    $${q ? q.price.toFixed(2) : '0.00'}
                  </div>
                  <div style="font-size: 10px; font-family: var(--font-telemetry); color: ${isUp ? 'var(--success-green)' : 'var(--error-red)'};">
                    ${q && q.change >= 0 ? '+' : ''}${q ? q.change.toFixed(2) : '0.00'} (${q && q.change_percent >= 0 ? '+' : ''}${q ? q.change_percent.toFixed(2) : '0.00'}%)
                  </div>
                </div>

                <button onclick="window.jarvisApp.removeWatchlistItem('${it.id}')" style="background: none; border: none; color: var(--text-muted); cursor: pointer; font-size: 14px; padding: 4px;">
                  &times;
                </button>
              </div>
            </div>
          `;
        }).join('')}
      </div>
    `}
  `;
}

function renderPortfolioSubTab() {
  return `
    <div class="hud-panel" style="padding: 20px; text-align: center; border-top: 2px solid var(--warning-amber);">
      <div style="font-size: 28px; margin-bottom: 8px;">🛡️</div>
      <span class="label-caps" style="color: var(--warning-amber); font-size: 10px;">READ-ONLY BOUNDARY</span>
      <h3 class="hud-title" style="font-size: 15px; margin-top: 4px; color: var(--text-primary);">
        BROKER READ-ONLY NOT CONFIGURED
      </h3>
      <p style="font-size: 11px; color: var(--text-muted); font-family: var(--font-telemetry); max-width: 320px; margin: 8px auto;">
        Broker read-only telemetry is not linked. Live broker order placement, balance transfers, and automated trading write operations are strictly disabled.
      </p>

      <div style="display: inline-block; margin-top: 12px; padding: 6px 12px; background: rgba(255, 170, 0, 0.1); border: 1px dashed var(--warning-amber); border-radius: 4px;">
        <span class="badge badge-amber" style="font-size: 8px;">
          LIVE TRADING WILL BE IMPLEMENTED IN A LATER PHASE
        </span>
      </div>
    </div>
  `;
}

function renderInsightsSubTab() {
  return `
    <div class="hud-panel" style="padding: 14px;">
      <span class="label-caps" style="color: var(--cyan-core); font-size: 9px; display: block; margin-bottom: 6px;">
        AI FINANCIAL SYNTHESIS RADAR
      </span>
      <p style="font-size: 11px; color: var(--text-muted); font-family: var(--font-telemetry); margin-bottom: 12px;">
        Generate source-grounded explanations of market movements using configured LLM intelligence with verified citations and observational scenario disclaimers.
      </p>

      <div style="display: flex; flex-direction: column; gap: 8px;">
        <button onclick="window.jarvisApp.quickInsight('Why are technology and semiconductor stocks leading today?')" class="hud-btn hud-btn-outline" style="text-align: left; padding: 8px 12px; font-size: 11px;">
          💡 "Why are technology and semiconductor stocks leading today?"
        </button>
        <button onclick="window.jarvisApp.quickInsight('What are the key market-wide drivers behind today\\'s S&P 500 movement?')" class="hud-btn hud-btn-outline" style="text-align: left; padding: 8px 12px; font-size: 11px;">
          💡 "What are the key market-wide drivers behind today's movement?"
        </button>
      </div>
    </div>
  `;
}

function renderAssetDetailModal() {
  const a = activeAssetDetail;
  const q = activeAssetQuote;
  const bars = activeAssetHistory;
  const news = activeAssetNews;
  const isUp = q ? q.change >= 0 : true;

  return `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 14px;">
      <div class="hud-panel hud-scroll" style="width: 100%; max-width: 440px; max-height: 90vh; overflow-y: auto; padding: 16px; border: 1px solid var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <!-- Modal Header -->
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <div style="display: flex; align-items: center; gap: 6px;">
              <h3 style="font-size: 18px; font-family: var(--font-telemetry); color: var(--cyan-core); margin: 0;">
                ${a.symbol}
              </h3>
              <span style="font-size: 10px; color: var(--text-muted);">${a.exchange}</span>
              <span class="badge ${q?.data_status?.includes('LIVE') ? 'badge-cyan' : 'badge-amber'}" style="font-size: 8px;">
                ${q?.data_status || 'SIMULATED'}
              </span>
            </div>
            <div style="font-size: 12px; color: var(--text-secondary); margin-top: 2px;">
              ${a.name}
            </div>
          </div>

          <button onclick="window.jarvisApp.closeAssetDetail()" style="background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer;">
            &times;
          </button>
        </div>

        <!-- Quote Metric Bar -->
        <div style="display: flex; justify-content: space-between; align-items: baseline; background: rgba(0, 240, 255, 0.05); padding: 8px 12px; border-radius: 4px;">
          <div>
            <span style="font-size: 22px; font-weight: 700; font-family: var(--font-telemetry);">
              $${q ? q.price.toFixed(2) : '0.00'}
            </span>
            <span style="font-size: 12px; font-family: var(--font-telemetry); margin-left: 6px; color: ${isUp ? 'var(--success-green)' : 'var(--error-red)'};">
              ${q && q.change >= 0 ? '+' : ''}${q ? q.change.toFixed(2) : '0.00'} (${q && q.change_percent >= 0 ? '+' : ''}${q ? q.change_percent.toFixed(2) : '0.00'}%)
            </span>
          </div>

          <span style="font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry);">
            VOL: ${q?.volume ? (q.volume / 1e6).toFixed(1) + 'M' : 'N/A'}
          </span>
        </div>

        <!-- Chart Time Range Selector -->
        <div style="display: flex; gap: 4px;">
          ${['1d', '1w', '1mo', '3mo', '1y', '5y'].map(r => `
            <button onclick="window.jarvisApp.setChartRange('${r}')" style="
              flex: 1;
              padding: 4px;
              font-size: 9px;
              font-family: var(--font-telemetry);
              font-weight: 700;
              text-transform: uppercase;
              cursor: pointer;
              background: ${activeChartRange === r ? 'var(--cyan-core)' : 'var(--surface-input)'};
              color: ${activeChartRange === r ? 'var(--bg-void)' : 'var(--text-secondary)'};
              border: 1px solid ${activeChartRange === r ? 'var(--cyan-core)' : 'rgba(0, 240, 255, 0.2)'};
            ">
              ${r}
            </button>
          `).join('')}
        </div>

        <!-- Interactive SVG Chart -->
        ${renderHistoryChart(bars)}

        <!-- Correlated News Events Drawer -->
        <div>
          <span class="label-caps" style="font-size: 9px; color: var(--cyan-core); margin-bottom: 6px; display: block;">
            CORRELATED WIRE EVENTS (PHASE 5 INTEGRATION)
          </span>
          <div style="display: flex; flex-direction: column; gap: 6px;">
            ${news.length === 0 ? `
              <span style="font-size: 10px; color: var(--text-muted); font-family: var(--font-telemetry);">
                NO DIRECT CO-OCCURRING PRESS WIRE EVENTS
              </span>
            ` : news.map(n => `
              <div style="background: rgba(255,255,255,0.03); padding: 8px; border-radius: 4px; border-left: 2px solid var(--cyan-core);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                  <span class="badge badge-cyan" style="font-size: 7px;">${n.relationship_label || 'REPORTED EVENT'}</span>
                  <span style="font-size: 8px; color: var(--text-muted);">${n.publisher}</span>
                </div>
                <div style="font-size: 11px; font-weight: 600; color: var(--text-primary); margin-top: 3px;">
                  ${n.headline}
                </div>
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Modal Actions -->
        <div style="display: flex; gap: 8px; margin-top: 6px;">
          <button onclick="window.jarvisApp.triggerInsightForAsset('${a.id}', '${a.symbol}')" class="hud-btn hud-btn-cyan" style="flex: 1; font-size: 10px; padding: 8px;">
            💡 WHY DID THIS MOVE? (AI INSIGHT)
          </button>
        </div>

      </div>
    </div>
  `;
}

function renderSearchModal() {
  return `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 14px;">
      <div class="hud-panel" style="width: 100%; max-width: 420px; max-height: 85vh; overflow-y: auto; padding: 16px; border: 1px solid var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span class="label-caps" style="color: var(--cyan-core);">SEARCH & RESOLVE EXACT ASSET</span>
          <button onclick="window.jarvisApp.closeSearchModal()" style="background: none; border: none; color: var(--text-muted); font-size: 18px; cursor: pointer;">
            &times;
          </button>
        </div>

        <input type="text" placeholder="Enter company name or ticker (e.g. NVDA, Apple, TSM)..." 
               oninput="window.jarvisApp.handleSearchInput(this.value)"
               class="hud-input" style="padding: 8px 12px; font-size: 12px;" />

        <!-- Confirmation prompt if candidate selected -->
        ${candidateToAdd ? `
          <div style="background: rgba(0, 240, 255, 0.1); border: 1px solid var(--cyan-core); padding: 10px; border-radius: 4px;">
            <span class="label-caps" style="color: var(--cyan-core); font-size: 8px;">CONFIRM EXACT INSTRUMENT</span>
            <div style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              ${candidateToAdd.name} (${candidateToAdd.symbol})
            </div>
            <div style="font-size: 10px; color: var(--text-secondary); font-family: var(--font-telemetry);">
              Exchange: ${candidateToAdd.exchange} // Type: ${candidateToAdd.asset_type} // Currency: ${candidateToAdd.currency}
            </div>

            <div style="display: flex; gap: 8px; margin-top: 8px;">
              <button onclick="window.jarvisApp.confirmAddAssetToWatchlist()" class="hud-btn hud-btn-cyan" style="flex: 1; font-size: 10px; padding: 6px;">
                CONFIRM & ADD TO WATCHLIST
              </button>
              <button onclick="window.jarvisApp.cancelAddAsset()" class="hud-btn hud-btn-outline" style="padding: 6px; font-size: 10px;">
                CANCEL
              </button>
            </div>
          </div>
        ` : ''}

        <!-- Candidate Results List -->
        <div style="display: flex; flex-direction: column; gap: 6px; max-height: 280px; overflow-y: auto;">
          ${isSearching ? `
            <span style="font-size: 10px; color: var(--cyan-core); font-family: var(--font-telemetry); text-align: center;">
              RESOLVING INSTRUMENT IDENTITIES...
            </span>
          ` : searchResults.map(cand => `
            <div onclick="window.jarvisApp.promptAddAsset(${JSON.stringify(cand).replace(/"/g, '&quot;')})" 
                 class="hud-card" style="padding: 8px 10px; cursor: pointer; display: flex; justify-content: space-between; align-items: center;">
              <div>
                <div style="font-weight: 700; font-size: 12px; font-family: var(--font-telemetry); color: var(--cyan-core);">
                  ${cand.symbol}
                </div>
                <div style="font-size: 10px; color: var(--text-secondary);">
                  ${cand.name}
                </div>
              </div>
              <div style="text-align: right;">
                <span class="badge badge-cyan" style="font-size: 7px;">${cand.exchange}</span>
                <span style="font-size: 8px; color: var(--text-muted); display: block;">${cand.asset_type}</span>
              </div>
            </div>
          `).join('')}
        </div>

      </div>
    </div>
  `;
}

function renderInsightModal() {
  const ins = activeInsight;
  return `
    <div style="position: fixed; inset: 0; background: rgba(0,0,0,0.85); z-index: 1000; display: flex; align-items: center; justify-content: center; padding: 14px;">
      <div class="hud-panel hud-scroll" style="width: 100%; max-width: 460px; max-height: 88vh; overflow-y: auto; padding: 16px; border: 1px solid var(--cyan-core); display: flex; flex-direction: column; gap: 12px;">
        
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
          <div>
            <span class="label-caps" style="color: var(--cyan-core);">J.A.R.V.I.S. MARKET EXPLANATION RADAR</span>
            <div style="font-size: 12px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              ${ins.question}
            </div>
          </div>
          <button onclick="window.jarvisApp.closeInsightModal()" style="background: none; border: none; color: var(--text-muted); font-size: 20px; cursor: pointer;">
            &times;
          </button>
        </div>

        <!-- Direct Answer -->
        <div style="background: rgba(0, 240, 255, 0.05); padding: 10px; border-radius: 4px; font-size: 12px; line-height: 1.5; color: var(--text-primary);">
          ${ins.direct_answer}
        </div>

        <!-- Possible Explanations -->
        <div>
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); display: block; margin-bottom: 4px;">OBSERVED FACTORS:</span>
          <ul style="margin: 0; padding-left: 18px; font-size: 11px; color: var(--text-secondary); line-height: 1.4;">
            ${(ins.possible_explanations || []).map(exp => `<li>${exp}</li>`).join('')}
          </ul>
        </div>

        <!-- Uncertainty Notes -->
        ${ins.uncertainty_notes ? `
          <div style="background: rgba(255, 170, 0, 0.05); border-left: 2px solid var(--warning-amber); padding: 6px 10px; font-size: 10px; color: var(--text-muted); font-family: var(--font-telemetry);">
            ⚠️ UNCERTAINTY: ${ins.uncertainty_notes}
          </div>
        ` : ''}

        <!-- Verified Citations Drawer -->
        <div>
          <span class="label-caps" style="font-size: 8px; color: var(--cyan-core); display: block; margin-bottom: 4px;">VERIFIED CITATIONS:</span>
          <div style="display: flex; flex-direction: column; gap: 4px;">
            ${(ins.citations || []).map(c => `
              <div style="font-size: 9px; font-family: var(--font-telemetry); color: var(--text-muted);">
                [${c.id}] ${c.title} (${c.publisher || 'Market Data'})
              </div>
            `).join('')}
          </div>
        </div>

        <!-- Mandatory Observational Disclaimer -->
        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; font-size: 9px; color: var(--text-muted); font-family: var(--font-telemetry); line-height: 1.3;">
          ${ins.market_disclaimer}
        </div>

      </div>
    </div>
  `;
}

// Window app bindings
if (typeof window !== 'undefined') {
  window.jarvisApp = window.jarvisApp || {};
  window.jarvisApp.setMarketTab = setMarketSubTab;
  window.jarvisApp.setChartRange = setChartRange;
  window.jarvisApp.refreshMarketOverview = loadMarketOverview;
  window.jarvisApp.openAssetDetail = openAssetDetail;
  window.jarvisApp.closeAssetDetail = closeAssetDetail;
  window.jarvisApp.openSearchModal = () => { showSearchModal = true; searchResults = []; candidateToAdd = null; window.jarvisApp.render(); };
  window.jarvisApp.closeSearchModal = () => { showSearchModal = false; window.jarvisApp.render(); };
  window.jarvisApp.handleSearchInput = handleSearchInput;
  window.jarvisApp.promptAddAsset = promptAddAsset;
  window.jarvisApp.cancelAddAsset = () => { candidateToAdd = null; window.jarvisApp.render(); };
  window.jarvisApp.confirmAddAssetToWatchlist = confirmAddAssetToWatchlist;
  window.jarvisApp.removeWatchlistItem = removeWatchlistItem;
  window.jarvisApp.triggerInsightForAsset = triggerInsightForAsset;
  window.jarvisApp.closeInsightModal = () => { showInsightModal = false; activeInsight = null; window.jarvisApp.render(); };
  window.jarvisApp.switchWatchlist = (id) => { activeWatchlistId = id; window.jarvisApp.render(); };
  window.jarvisApp.quickInsight = async (q) => {
    isFetchingData = true;
    window.jarvisApp.render();
    try {
      const ins = await jarvisApi.generateMarketInsight(q);
      activeInsight = ins;
      showInsightModal = true;
    } catch (e) {
      alert('Insight failed: ' + e.message);
    } finally {
      isFetchingData = false;
      window.jarvisApp.render();
    }
  };
}
