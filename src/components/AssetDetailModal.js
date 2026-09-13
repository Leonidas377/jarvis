// ==========================================================================
// Asset Detail Modal Component
// Deep-dive financial telemetry with sparkline/chart, scenario analysis, and watchlist toggle
// ==========================================================================

import { store } from '../services/store.js';

export function renderAssetDetailModal(symbol) {
  const asset = store.state.markets.find(m => m.symbol === symbol) || store.state.markets[0];
  const isPos = asset.isPositive;
  const color = isPos ? 'var(--success-green)' : 'var(--alert-red)';

  // Build SVG path for chart
  const points = asset.sparkline || [40, 50, 45, 60, 70, 65, 80, 85, 90];
  const max = Math.max(...points);
  const min = Math.min(...points);
  const width = 340;
  const height = 120;
  
  const coords = points.map((p, idx) => {
    const x = (idx / (points.length - 1)) * width;
    const y = height - ((p - min) / (max - min || 1)) * (height - 20) - 10;
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  }).join(' ');

  return `
    <div id="asset-detail-modal" class="hud-modal-overlay active">
      <div class="hud-modal-content" style="padding: 24px 16px 32px 16px; max-height: 90vh; overflow-y: auto;">
        
        <!-- Header -->
        <div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px;">
              <h2 style="font-size: 22px; font-weight: 700; color: var(--text-primary); font-family: var(--font-telemetry);">
                ${asset.symbol}
              </h2>
              <span class="badge badge-amber" style="font-size: 8px;">SIMULATED DATA</span>
            </div>
            <span style="font-size: 13px; color: var(--text-secondary);">${asset.name}</span>
          </div>
          <button onclick="window.jarvisApp.closeAssetDetailModal()" class="hud-btn-ghost" style="width: 32px; height: 32px; padding: 0; display: flex; align-items: center; justify-content: center;">
            <span class="material-symbols-outlined" style="font-size: 18px;">close</span>
          </button>
        </div>

        <!-- Price & Delta -->
        <div style="display: flex; align-items: baseline; gap: 10px; margin-bottom: 14px;">
          <span class="font-telemetry" style="font-size: 28px; font-weight: 700; color: var(--text-primary);">
            $${asset.price}
          </span>
          <span class="font-telemetry" style="font-size: 15px; font-weight: 600; color: ${color};">
            ${asset.change} (${asset.changePct})
          </span>
        </div>

        <!-- Telemetry Chart -->
        <div style="background: var(--surface-input); border: var(--border-cyan); padding: 12px; clip-path: var(--chamfer-clip-sm); margin-bottom: 16px;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
            <span class="label-caps" style="font-size: 8px;">INTRADAY ORBITAL TELEMETRY</span>
            <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">DELAYED: 15 MIN</span>
          </div>
          
          <svg viewBox="0 0 ${width} ${height}" style="width: 100%; height: 120px; overflow: visible;">
            <!-- Grid Lines -->
            <line x1="0" y1="30" x2="${width}" y2="30" stroke="rgba(0,240,255,0.08)" stroke-dasharray="3 3"/>
            <line x1="0" y1="60" x2="${width}" y2="60" stroke="rgba(0,240,255,0.08)" stroke-dasharray="3 3"/>
            <line x1="0" y1="90" x2="${width}" y2="90" stroke="rgba(0,240,255,0.08)" stroke-dasharray="3 3"/>

            <!-- Area Fill -->
            <polygon points="0,${height} ${coords} ${width},${height}" fill="url(#chart-grad)" opacity="0.25"/>
            <defs>
              <linearGradient id="chart-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="${color}"/>
                <stop offset="100%" stop-color="transparent"/>
              </linearGradient>
            </defs>

            <!-- Line Path -->
            <polyline fill="none" stroke="${color}" stroke-width="2.5" points="${coords}" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 0 6px ${color});"/>
          </svg>
        </div>

        <!-- Metrics Grid (4 tiles) -->
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px;">
          <div class="hud-panel" style="padding: 10px;">
            <span class="label-caps" style="font-size: 8px;">24H VOLUME</span>
            <div class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              ${asset.volume || '42.1M'}
            </div>
          </div>

          <div class="hud-panel" style="padding: 10px;">
            <span class="label-caps" style="font-size: 8px;">MARKET STATUS</span>
            <div class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--cyan-core); margin-top: 2px;">
              NYSE OPEN
            </div>
          </div>

          <div class="hud-panel" style="padding: 10px;">
            <span class="label-caps" style="font-size: 8px;">VOLATILITY (BETA)</span>
            <div class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--text-primary); margin-top: 2px;">
              1.24 // MODERATE
            </div>
          </div>

          <div class="hud-panel" style="padding: 10px;">
            <span class="label-caps" style="font-size: 8px;">BROKER ACTION</span>
            <div class="font-telemetry" style="font-size: 14px; font-weight: 700; color: var(--warning-amber); margin-top: 2px;">
              READ-ONLY
            </div>
          </div>
        </div>

        <!-- Scenario Analysis -->
        <div style="background: var(--surface-card); border: 1px solid rgba(0, 240, 255, 0.2); padding: 12px; clip-path: var(--chamfer-clip-sm); margin-bottom: 20px;">
          <span class="label-caps" style="color: var(--cyan-core); display: block; margin-bottom: 4px;">J.A.R.V.I.S. SCENARIO SYNTHESIS</span>
          <p style="font-size: 12px; color: var(--text-secondary); line-height: 1.4;">
            Bullish momentum supported by recent earnings revisions and sector demand. Key resistance at +3.5%. Stop-loss parameters recommended at 2.0% trailing threshold.
          </p>
        </div>

        <!-- Action Controls -->
        <div style="display: flex; gap: 10px;">
          <button onclick="window.jarvisApp.toggleWatchlistAction('${asset.symbol}')" class="${asset.isWatchlist ? 'hud-btn-ghost' : 'hud-btn'}" style="flex: 1;">
            <span class="material-symbols-outlined" style="font-size: 18px;">
              ${asset.isWatchlist ? 'bookmark_remove' : 'bookmark_add'}
            </span>
            ${asset.isWatchlist ? 'In Watchlist' : 'Add Watchlist'}
          </button>

          <button onclick="window.jarvisApp.deepDiveResearch('${asset.name} earnings and market outlook')" class="hud-btn" style="flex: 1.2;">
            <span class="material-symbols-outlined" style="font-size: 18px;">travel_explore</span>
            Research Asset
          </button>
        </div>

      </div>
    </div>
  `;
}
