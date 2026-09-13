// ==========================================================================
// Markets Screen: Financial Telemetry & Portfolio Radar
// Adapts global_telemetry_radar concepts into financial market intelligence
// ==========================================================================

import { store } from '../services/store.js';

let activeSubTab = 'overview'; // 'overview' | 'watchlist' | 'portfolio' | 'insights'

export function setMarketSubTab(tab) {
  activeSubTab = tab;
  window.jarvisApp.render();
}

export function renderMarketsScreen() {
  const state = store.state;
  const items = activeSubTab === 'watchlist' 
    ? state.markets.filter(m => m.isWatchlist) 
    : state.markets;

  return `
    <div class="screen-container hud-scroll" style="flex: 1; padding: 14px 14px 84px 14px; display: flex; flex-direction: column; gap: 14px;">
      
      <!-- Top Title Bar -->
      <div style="display: flex; align-items: center; justify-content: space-between;">
        <div>
          <span class="label-caps" style="color: var(--cyan-core);">FINANCIAL TELEMETRY RADAR</span>
          <h2 class="hud-title" style="font-size: 18px; margin-top: 2px;">Market Intelligence</h2>
        </div>

        <span class="badge badge-amber" style="font-size: 8px;">SIMULATED DATA</span>
      </div>

      <!-- Market Status Banner -->
      <div class="hud-panel" style="padding: 10px 12px; display: flex; align-items: center; justify-content: space-between;">
        <div style="display: flex; align-items: center; gap: 8px;">
          <span style="width: 6px; height: 6px; border-radius: 50%; background: var(--success-green); box-shadow: 0 0 6px var(--success-green);"></span>
          <div>
            <span class="label-caps" style="font-size: 8px; color: var(--success-green);">US MARKETS: OPEN</span>
            <span style="font-size: 10px; color: var(--text-muted); font-family: var(--font-telemetry); display: block;">NYSE // NASDAQ LIVE SESSIONS</span>
          </div>
        </div>

        <div style="text-align: right;">
          <span class="label-caps" style="font-size: 8px; color: var(--warning-amber);">BROKER: READ-ONLY</span>
          <span style="font-size: 10px; color: var(--text-muted); font-family: var(--font-telemetry); display: block;">NO LIVE ORDERS</span>
        </div>
      </div>

      <!-- Segmented Market Tabs -->
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

      <!-- Portfolio Summary Card (Shown on Portfolio tab) -->
      ${activeSubTab === 'portfolio' ? `
        <div class="hud-panel" style="padding: 14px;">
          <span class="label-caps" style="color: var(--cyan-core);">SIMULATED PAPER PORTFOLIO</span>
          <div style="display: flex; align-items: baseline; gap: 8px; margin-top: 4px; margin-bottom: 8px;">
            <span class="font-telemetry" style="font-size: 24px; font-weight: 700; color: var(--text-primary);">$148,290.45</span>
            <span class="font-telemetry" style="font-size: 13px; font-weight: 600; color: var(--success-green);">+$2,410.20 (+1.65%)</span>
          </div>

          <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0, 240, 255, 0.1);">
            <div>
              <span class="label-caps" style="font-size: 8px;">BUYING POWER</span>
              <div class="font-telemetry" style="font-size: 13px; color: var(--text-primary);">$42,500.00</div>
            </div>
            <div>
              <span class="label-caps" style="font-size: 8px;">ACTIVE POSITIONS</span>
              <div class="font-telemetry" style="font-size: 13px; color: var(--cyan-core);">6 ASSETS</div>
            </div>
          </div>
        </div>
      ` : ''}

      <!-- Insights Card (Shown on Insights tab) -->
      ${activeSubTab === 'insights' ? `
        <div class="hud-panel" style="padding: 14px; border-color: rgba(255, 184, 0, 0.4);">
          <div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;">
            <span class="material-symbols-outlined" style="font-size: 18px; color: var(--warning-amber);">insights</span>
            <span class="label-caps" style="color: var(--warning-amber);">CORRELATION SYNTHESIS</span>
          </div>
          <h4 style="font-size: 13px; font-weight: 700; color: var(--text-primary); margin-bottom: 4px;">
            Semiconductor Sector Momentum Outperforming Broad Index
          </h4>
          <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">
            Photonic interconnect announcements and steady datacenter capex continue to decouple enterprise hardware from macroeconomic rate fluctuations.
          </p>
        </div>
      ` : ''}

      <!-- Market Asset Cards Grid -->
      <div style="display: flex; flex-direction: column; gap: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 2px;">
          <span class="label-caps" style="color: var(--text-secondary);">${activeSubTab.toUpperCase()} INSTRUMENTS</span>
          <span class="label-caps" style="color: var(--cyan-core);">${items.length} TRACKED</span>
        </div>

        ${items.map(asset => {
          const isPos = asset.isPositive;
          const color = isPos ? 'var(--success-green)' : 'var(--alert-red)';

          // Mini sparkline SVG
          const points = asset.sparkline || [50, 52, 48, 60, 58, 65, 70];
          const max = Math.max(...points);
          const min = Math.min(...points);
          const w = 70;
          const h = 24;
          const coords = points.map((p, idx) => {
            const x = (idx / (points.length - 1)) * w;
            const y = h - ((p - min) / (max - min || 1)) * (h - 6) - 3;
            return `${x.toFixed(1)},${y.toFixed(1)}`;
          }).join(' ');

          return `
            <div onclick="window.jarvisApp.openAssetDetail('${asset.symbol}')" class="hud-panel" style="
              padding: 12px;
              cursor: pointer;
              display: flex;
              align-items: center;
              justify-content: space-between;
              gap: 8px;
            ">
              <!-- Left: Symbol & Name -->
              <div style="min-width: 100px;">
                <div style="display: flex; align-items: center; gap: 6px;">
                  <span class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--text-primary);">
                    ${asset.symbol}
                  </span>
                  ${asset.isWatchlist ? `
                    <span class="material-symbols-outlined" style="font-size: 12px; color: var(--cyan-core);">bookmark</span>
                  ` : ''}
                </div>
                <span style="font-size: 10px; color: var(--text-muted); display: block; max-width: 110px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                  ${asset.name}
                </span>
              </div>

              <!-- Center: Mini Sparkline -->
              <div style="width: 70px; height: 24px;">
                <svg viewBox="0 0 ${w} ${h}" style="width: 100%; height: 100%; overflow: visible;">
                  <polyline fill="none" stroke="${color}" stroke-width="1.8" points="${coords}" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </div>

              <!-- Right: Price & Percent Delta -->
              <div style="text-align: right; min-width: 80px;">
                <div class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--text-primary);">
                  $${asset.price}
                </div>
                <div class="font-telemetry" style="font-size: 11px; font-weight: 600; color: ${color};">
                  ${asset.changePct}
                </div>
              </div>
            </div>
          `;
        }).join('')}
      </div>

    </div>
  `;
}
