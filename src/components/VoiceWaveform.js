// ==========================================================================
// Voice Waveform Equalizer Component
// ==========================================================================

export function renderVoiceWaveform() {
  return `
    <div class="hud-waveform-pod" style="
      width: 100%;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
      padding: 10px 0;
    ">
      <!-- 13 Real-time Dynamic Equalizer Bars -->
      <div id="equalizer-strip" style="
        display: flex;
        align-items: flex-end;
        justify-content: center;
        gap: 5px;
        height: 36px;
        width: 100%;
        max-width: 280px;
      ">
        <div class="eq-bar" style="width: 4px; height: 12px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 22px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 16px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 28px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 20px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 32px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 24px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 30px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 18px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 26px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 14px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 20px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
        <div class="eq-bar" style="width: 4px; height: 12px; background: var(--cyan-core); border-radius: 2px; transition: height 0.15s ease;"></div>
      </div>

      <!-- Frequency Diagnostics Line -->
      <div style="
        display: flex;
        justify-content: space-between;
        width: 100%;
        max-width: 280px;
        padding: 0 4px;
      ">
        <span class="label-caps" style="font-size: 8px;">12.4 KHZ · MOD</span>
        <span class="label-caps" style="font-size: 8px; color: var(--cyan-core);">VOICE MATRIX LOCK</span>
        <span class="label-caps" style="font-size: 8px;">SNR +48 dB</span>
      </div>
    </div>
  `;
}

// Micro-animation for equalizer
export function initWaveformAnimation() {
  const strip = document.getElementById('equalizer-strip');
  if (!strip) return;
  const bars = strip.children;
  setInterval(() => {
    for (let i = 0; i < bars.length; i++) {
      const h = Math.floor(Math.random() * 26) + 6;
      bars[i].style.height = `${h}px`;
    }
  }, 160);
}
