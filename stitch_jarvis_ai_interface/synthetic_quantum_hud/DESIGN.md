---
name: Synthetic Quantum HUD
colors:
  surface: '#0e141b'
  surface-dim: '#0e141b'
  surface-bright: '#343942'
  surface-container-lowest: '#090e16'
  surface-container-low: '#171c24'
  surface-container: '#1b2028'
  surface-container-high: '#252a32'
  surface-container-highest: '#30353d'
  on-surface: '#dee2ed'
  on-surface-variant: '#b9cacb'
  inverse-surface: '#dee2ed'
  inverse-on-surface: '#2b3139'
  outline: '#849495'
  outline-variant: '#3b494b'
  surface-tint: '#00dbe9'
  primary: '#dbfcff'
  on-primary: '#00363a'
  primary-container: '#00f0ff'
  on-primary-container: '#006970'
  inverse-primary: '#006970'
  secondary: '#afc6ff'
  on-secondary: '#002d6d'
  secondary-container: '#548dff'
  on-secondary-container: '#002760'
  tertiary: '#fff4e8'
  on-tertiary: '#412d00'
  tertiary-container: '#ffd386'
  on-tertiary-container: '#7d5800'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#7df4ff'
  primary-fixed-dim: '#00dbe9'
  on-primary-fixed: '#002022'
  on-primary-fixed-variant: '#004f54'
  secondary-fixed: '#d9e2ff'
  secondary-fixed-dim: '#afc6ff'
  on-secondary-fixed: '#001944'
  on-secondary-fixed-variant: '#00429a'
  tertiary-fixed: '#ffdea8'
  tertiary-fixed-dim: '#ffba20'
  on-tertiary-fixed: '#271900'
  on-tertiary-fixed-variant: '#5e4200'
  background: '#0e141b'
  on-background: '#dee2ed'
  surface-variant: '#30353d'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 52px
    letterSpacing: -0.03em
  display-lg-mobile:
    fontFamily: Space Grotesk
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Space Grotesk
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 34px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: 0em
  headline-sm:
    fontFamily: Space Grotesk
    fontSize: 18px
    fontWeight: '500'
    lineHeight: 24px
    letterSpacing: 0.01em
  body-lg:
    fontFamily: Space Grotesk
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: 0em
  body-md:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.01em
  body-sm:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
    letterSpacing: 0.02em
  telemetry-lg:
    fontFamily: JetBrains Mono
    fontSize: 20px
    fontWeight: '700'
    lineHeight: 24px
    letterSpacing: 0.05em
  telemetry-md:
    fontFamily: JetBrains Mono
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 18px
    letterSpacing: 0.08em
  telemetry-sm:
    fontFamily: JetBrains Mono
    fontSize: 11px
    fontWeight: '500'
    lineHeight: 14px
    letterSpacing: 0.12em
  label-caps:
    fontFamily: JetBrains Mono
    fontSize: 10px
    fontWeight: '600'
    lineHeight: 12px
    letterSpacing: 0.2em
spacing:
  space-xxs: 0.125rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-base: 1rem
  space-lg: 1.25rem
  space-xl: 1.5rem
  space-2xl: 2rem
  space-3xl: 3rem
  margin-mobile: 1rem
  gutter-mobile: 0.75rem
  panel-padding: 1rem
---

## Brand & Style

The design system embodies an advanced tactical intelligence operating environment: precise, omniscient, hyper-responsive, and relentlessly computational. Designed for an ultra-high-end mobile HUD experience, it merges aerospace avionics, laboratory telemetry, and military-grade holographic projections into an everyday operational interface.

The design movement synthesizes **Cybernetic Glassmorphism** with **Technical Futurism**. Rather than ornamental sci-fi tropes, it uses functional optical physics: deep-space optical density, chromatic dispersion, polarized photon borders, and micro-grid scaffolding. Interfaces feel projected in 2.5D space rather than painted on glass. Precision tick-marks, dynamic circular gauges, and synthetic scanlines contextualize live computational intelligence, delivering the sensation of wielding an Arc Reactor-level quantum processor in the palm of one's hand.

## Colors

The palette is constructed around infinite void absorption and high-energy photonic emissions. Light does not merely sit on the surface; it radiates through volumetric atmosphere.

* **Void Ground (Base Obsidian):** `#04080F` anchors the base canvas, minimizing OLED battery consumption and emulating deep unlit space.
* **Sub-Surface Horizon:** `#08121E` provides the foundational layer for panels, HUD containers, and card housings.
* **Primary Arc Core (Luminous Cyan):** `#00F0FF` represents operational baseline stability, active data links, focused states, and core telemetry.
* **Secondary Plasma (Electric Cobalt):** `#0072FF` handles secondary depth, unselected telemetry rings, gradients, and atmospheric shadows.
* **Holographic Flare (Ice Blue):** `#A6EFFF` is reserved for ultra-high-priority data readouts, scalar maximums, and photon focus points.
* **Core Warning / Alert (Arc Amber):** `#FFB800` signals thermal limits, critical overrides, low power reserves, and diagnostic exceptions.
* **Terminal Red (Emergency Defcon):** `#FF2A55` handles direct failure states, security compromises, and terminal abort sequences.

Surfaces should never use pure flat color fills. Layer `rgba(0, 240, 255, 0.04)` to `rgba(8, 18, 30, 0.75)` over the void ground to simulate glassmorphic optic plates.

## Typography

Typography functions as visual instrumentation. The pairing leverages **Space Grotesk** for clean, forward-leaning architectural clarity in headlines and structural copy, balanced by **JetBrains Mono** for absolute precision in analytical readings, data arrays, status labels, and spatial coordinates.

All analytical micro-labels (`label-caps` and `telemetry-sm`) must be rendered in uppercase to reinforce operational rigor. Numeric readings rely strictly on monospaced figures to prevent layout jitter during real-time scalar streaming and sensor recalculation. Text glow should be reserved strictly for `display-lg` numbers and primary status indicators using a constrained drop-shadow filter: `drop-shadow(0 0 8px rgba(0, 240, 255, 0.45))`.

## Layout & Spacing

The layout is built on a high-density 4px baseline sub-grid configured for an 8-column mobile viewport (scaling to 12 columns on foldable or tablet devices). Because HUD interfaces balance high informational density with instantaneous legibility, layout rhythm prioritizes modular telemetry pods.

* **Screen Margins:** Fixed 16px (`space-base`) horizontal margins create a calibrated edge-to-edge frame that accommodates peripheral status ticks and scalar meters.
* **Component Padding:** Standard pods and HUD containers maintain 16px internal clearance, reducing to 12px on secondary sub-modules.
* **Scaffolding Dividers:** Space is bounded by 1px technical separator rules (`rgba(0, 240, 255, 0.15)`) rather than vast white-space, anchoring dynamic visual elements in rigorous analytical slots.
* **Dynamic Safe Zones:** The upper 48px is reserved exclusively for system vitals (Arc Core status, connectivity vectors, quantum latency), while the bottom 72px houses navigational command triggers.

## Elevation & Depth

Spatial hierarchy is defined through **Photonic Luminescence and Multi-Planar Layering** rather than traditional physical drop shadows. Dark layers sit farther back in optical space, while higher-elevation elements brighten in both border intensity and inner atmospheric bloom.

1. **Layer 0 (Sub-Void Canvas):** Pure obsidian `#04080F`. Host to subtle background vector coordinate grids (`rgba(0, 114, 255, 0.04)`) and animated radial radar sweeps.
2. **Layer 1 (Telemetry Pods / Backplanes):** Surface color `rgba(8, 18, 30, 0.65)` layered with backdrop blur (12px to 16px). Outlined with an ultra-fine 1px ghost border `rgba(0, 240, 255, 0.18)`.
3. **Layer 2 (Interactive Instruments / Floating Cards):** Surface color `rgba(10, 26, 44, 0.75)` with backdrop blur (20px). Border increases to `rgba(0, 240, 255, 0.4)` accompanied by an ambient photonic glow: `box-shadow: 0 0 16px rgba(0, 240, 255, 0.12), inset 0 0 12px rgba(0, 240, 255, 0.06)`.
4. **Layer 3 (Modal Scrims & Critical Tactical Overrides):** Ambient lighting shifts to saturated dark cobalt `rgba(4, 8, 15, 0.92)` with active scanlines. Alert states dynamically cast `rgba(255, 184, 0, 0.2)` or `rgba(255, 42, 85, 0.25)` outward blooms.

Corner accents (L-shaped bracket notches, calibration tick-marks) are physically pinned to Layer 2 and Layer 3 containers, reinforcing optical projection aesthetics.

## Shapes

The shape architecture is strictly **Zero-Radius (`0`) Technical Sharp** accented with **Chamfered 45-Degree Clipped Geometry**. Rounded, organic corners dilute military-industrial avionics; therefore, standard containers, buttons, and telemetry slots enforce sharp geometric edges (`border-radius: 0px`).

For featured HUD cards, interactive primary nodes, and Arc Reactor diagnostics, use clipped polygonal corners:
* **Chamfer Standard:** 45-degree corner clips sized at 8px (`clip-path: polygon(0 0, calc(100% - 8px) 0, 100% 8px, 100% 100%, 8px 100%, 0 calc(100% - 8px))`).
* **Micro Corner Brackets:** 1px width, 4px length tick marks sitting outside container perimeters at the four cardinal vertices.
* **Concentric Telemetry Rings:** Pure circles (`border-radius: 50%`) are used exclusively for circular telemetry instruments, core arc monitors, compass headings, and audio spectrogram nodes.

## Components

### Buttons & Tactical Triggers
* **Primary Trigger:** Chamfered corners, background `rgba(0, 240, 255, 0.12)`, 1px solid `#00F0FF`, text `#00F0FF` (`Space Grotesk`, medium, uppercase). Active state fills to solid `#00F0FF` with `#04080F` text and an outer glow `0 0 20px rgba(0, 240, 255, 0.6)`.
* **Secondary Action:** Ghost frame, 1px border `rgba(0, 114, 255, 0.4)`, text `#A6EFFF`. Hover/Tap initiates a scanline flash across the button surface.
* **Alert Trigger:** Border and typography shift to `#FFB800` or `#FF2A55` with matching hazard corner ticks.

### HUD Cards & Telemetry Pods
* Constructed with semi-transparent tinted glass (`rgba(8, 18, 30, 0.7)`), 1px cyan outline, and 8px 45-degree upper-right chamfer.
* **Corner Brackets:** Absolute-positioned L-brackets on top-left and bottom-right edges in `#00F0FF`.
* **Metadata Header:** Pinned top row featuring monospaced serial indexing (`SYS.COR // 04.99`), status beacon (blinking pulse dot), and diagnostic classification.
* **Scanline Texture:** Subtle horizontal CSS gradient repeating every 4px at `rgba(0, 240, 255, 0.02)`.

### Form Inputs & Terminal Fields
* Darkened field wells (`rgba(4, 8, 15, 0.8)`) with bottom-only structural active rules (`1px solid rgba(0, 240, 255, 0.3)`).
* Focused state activates full enclosing cyan frame with a blinking monospaced cursor block (`width: 8px`, `height: 14px`, background `#00F0FF`).
* Value entry uses `JetBrains Mono`, tracking wide, with dynamic inline units (`[MHZ]`, `[KPA]`, `[%]`).

### Switches, Checkboxes & Selectors
* **Checkboxes:** Square sharp-edged brackets (`16x16px`). Checked state renders an inner illuminated diamond or crosshair node with `box-shadow: 0 0 8px #00F0FF`.
* **Telemetry Toggles:** Replaced by binary segmented switches (`[01 // ACTIVE]` vs `[00 // STANDBY]`) with back-lit blue LED indicators.

### Data Rings & Gauge Arrays
* Circular SVG-based Arc Reactor core dials utilizing nested segmented strokes, displaying operational efficiency (0–100%).
* Segmented tick meters with dynamic gradient color-stops: transitioning from Electric Cobalt (low) to Luminous Cyan (nominal) to Amber Gold (overdrive).

### Audio Waveform & Neural Visualizers
* Real-time dynamic vertical equalizer bars (2px width, 2px spacing) fluctuating in heights, anchored to the bottom console or voice-command synthesis pods.
* Core state uses `#00F0FF` with `#A6EFFF` peak indicator pips.