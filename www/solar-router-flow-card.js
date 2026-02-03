/**
 * Solar Router Flow Card - Built-in Energy Flow Visualization
 * No external dependencies required
 */

const CARD_VERSION = '1.0.0';

class SolarRouterFlowCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this._hass = null;
    this._config = null;
    this._animationFrameId = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._updateCard();
  }

  setConfig(config) {
    this._config = {
      title: config.title || 'Solar Router',
      show_header: config.show_header !== false,
      animation_speed: config.animation_speed || 1,
      ...config
    };
    this._render();
  }

  _render() {
    const style = `
      <style>
        :host {
          display: block;
        }
        .card {
          background: var(--ha-card-background, var(--card-background-color, white));
          border-radius: var(--ha-card-border-radius, 12px);
          box-shadow: var(--ha-card-box-shadow, 0 2px 6px rgba(0,0,0,0.1));
          padding: 16px;
          color: var(--primary-text-color);
        }
        .header {
          font-size: 16px;
          font-weight: 500;
          margin-bottom: 16px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .status-badge {
          font-size: 12px;
          padding: 4px 8px;
          border-radius: 12px;
          background: var(--primary-color);
          color: white;
        }
        .status-badge.heating {
          background: #f44336;
          animation: pulse 1.5s infinite;
        }
        .status-badge.solar {
          background: #4caf50;
        }
        .status-badge.offpeak {
          background: #2196f3;
        }
        .status-badge.idle {
          background: #9e9e9e;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        .flow-diagram {
          position: relative;
          width: 100%;
          padding-bottom: 75%;
        }
        .flow-svg {
          position: absolute;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
        }
        .node {
          cursor: pointer;
          transition: transform 0.2s;
        }
        .node:hover {
          transform: scale(1.05);
        }
        .node-circle {
          stroke-width: 3;
          transition: all 0.3s;
        }
        .node-icon {
          font-size: 28px;
          text-anchor: middle;
          dominant-baseline: middle;
        }
        .node-value {
          font-size: 14px;
          font-weight: bold;
          text-anchor: middle;
          fill: var(--primary-text-color);
        }
        .node-label {
          font-size: 11px;
          text-anchor: middle;
          fill: var(--secondary-text-color);
        }
        .flow-path {
          fill: none;
          stroke-width: 4;
          stroke-linecap: round;
          transition: opacity 0.3s;
        }
        .flow-path.active {
          stroke-width: 6;
        }
        .flow-path.inactive {
          opacity: 0.15;
          stroke-width: 2;
        }
        .flow-dots {
          fill: currentColor;
        }
        .stats-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 8px;
          margin-top: 16px;
          padding-top: 16px;
          border-top: 1px solid var(--divider-color);
        }
        .stat-item {
          text-align: center;
          padding: 8px 4px;
          background: var(--secondary-background-color);
          border-radius: 8px;
        }
        .stat-value {
          font-size: 18px;
          font-weight: bold;
          color: var(--primary-text-color);
        }
        .stat-label {
          font-size: 10px;
          color: var(--secondary-text-color);
          margin-top: 2px;
        }
        .time-info {
          display: flex;
          justify-content: space-around;
          margin-top: 12px;
          padding: 8px;
          background: var(--secondary-background-color);
          border-radius: 8px;
          font-size: 11px;
        }
        .time-item {
          text-align: center;
        }
        .time-label {
          color: var(--secondary-text-color);
        }
        .time-value {
          font-weight: bold;
          margin-top: 2px;
        }
      </style>
    `;

    const html = `
      <div class="card">
        ${this._config.show_header ? `
          <div class="header">
            <span>${this._config.title}</span>
            <span class="status-badge idle" id="status-badge">Idle</span>
          </div>
        ` : ''}

        <div class="flow-diagram">
          <svg class="flow-svg" viewBox="0 0 400 300" preserveAspectRatio="xMidYMid meet">
            <defs>
              <!-- Gradients -->
              <linearGradient id="solarGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#FFD54F"/>
                <stop offset="100%" style="stop-color:#FF9800"/>
              </linearGradient>
              <linearGradient id="batteryGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#81C784"/>
                <stop offset="100%" style="stop-color:#4CAF50"/>
              </linearGradient>
              <linearGradient id="heaterGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#EF5350"/>
                <stop offset="100%" style="stop-color:#F44336"/>
              </linearGradient>
              <linearGradient id="gridGrad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" style="stop-color:#64B5F6"/>
                <stop offset="100%" style="stop-color:#2196F3"/>
              </linearGradient>
            </defs>

            <!-- Flow Paths -->
            <g id="flow-paths">
              <!-- Solar to Battery -->
              <path id="path-solar-battery" class="flow-path inactive"
                    d="M 80 95 Q 80 150 80 180" stroke="#FF9800"/>

              <!-- Solar to Heater -->
              <path id="path-solar-heater" class="flow-path inactive"
                    d="M 105 70 Q 200 50 280 95" stroke="#FF9800"/>

              <!-- Battery to Heater -->
              <path id="path-battery-heater" class="flow-path inactive"
                    d="M 105 220 Q 200 240 280 195" stroke="#4CAF50"/>

              <!-- Grid to Heater -->
              <path id="path-grid-heater" class="flow-path inactive"
                    d="M 80 265 Q 150 280 200 260 Q 260 240 280 195" stroke="#2196F3"/>
            </g>

            <!-- Animated dots will be added here -->
            <g id="flow-animations"></g>

            <!-- Solar Node -->
            <g class="node" id="node-solar" transform="translate(80, 55)">
              <circle class="node-circle" cx="0" cy="0" r="40" fill="#FFF8E1" stroke="#FF9800"/>
              <text class="node-icon" x="0" y="-5">☀️</text>
              <text class="node-value" id="solar-value" x="0" y="55">0 W</text>
              <text class="node-label" x="0" y="70">Solar</text>
            </g>

            <!-- Battery Node -->
            <g class="node" id="node-battery" transform="translate(80, 220)">
              <circle class="node-circle" cx="0" cy="0" r="40" fill="#E8F5E9" stroke="#4CAF50"/>
              <text class="node-icon" x="0" y="-5">🔋</text>
              <text class="node-value" id="battery-value" x="0" y="55">0%</text>
              <text class="node-label" x="0" y="70">Battery</text>
            </g>

            <!-- Water Heater Node -->
            <g class="node" id="node-heater" transform="translate(320, 150)">
              <circle class="node-circle" id="heater-circle" cx="0" cy="0" r="45" fill="#FFEBEE" stroke="#F44336"/>
              <text class="node-icon" x="0" y="-8">🚿</text>
              <text class="node-value" id="heater-temp" x="0" y="12">--°C</text>
              <text class="node-value" id="heater-showers" x="0" y="60" style="font-size:12px">-- showers</text>
              <text class="node-label" x="0" y="75">Water Tank</text>
            </g>

            <!-- Grid Node (small) -->
            <g class="node" id="node-grid" transform="translate(80, 265)" style="opacity: 0.7">
              <circle class="node-circle" cx="0" cy="0" r="25" fill="#E3F2FD" stroke="#2196F3"/>
              <text style="font-size:16px" text-anchor="middle" dominant-baseline="middle" x="0" y="0">⚡</text>
              <text class="node-label" x="0" y="40">Grid</text>
            </g>

            <!-- Center Status -->
            <g transform="translate(200, 150)">
              <text id="center-status" text-anchor="middle" style="font-size:12px; fill: var(--secondary-text-color)"></text>
            </g>
          </svg>
        </div>

        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-value" id="stat-heating-time">0</div>
            <div class="stat-label">min today</div>
          </div>
          <div class="stat-item">
            <div class="stat-value" id="stat-energy">0</div>
            <div class="stat-label">kWh today</div>
          </div>
          <div class="stat-item">
            <div class="stat-value" id="stat-sessions">0</div>
            <div class="stat-label">sessions</div>
          </div>
          <div class="stat-item">
            <div class="stat-value" id="stat-tank-energy">0</div>
            <div class="stat-label">kWh stored</div>
          </div>
        </div>

        <div class="time-info">
          <div class="time-item">
            <div class="time-label">Solar Hours</div>
            <div class="time-value" id="solar-hours">10:00 - 17:00</div>
          </div>
          <div class="time-item">
            <div class="time-label">Fallback Check</div>
            <div class="time-value" id="fallback-time">20:00</div>
          </div>
          <div class="time-item">
            <div class="time-label">Off-Peak</div>
            <div class="time-value" id="offpeak-hours">02:00 - 06:00</div>
          </div>
        </div>
      </div>
    `;

    this.shadowRoot.innerHTML = style + html;
    this._startAnimation();
  }

  _updateCard() {
    if (!this._hass || !this.shadowRoot.querySelector('.card')) return;

    const getState = (entityId, defaultVal = 0) => {
      if (!entityId) return defaultVal;
      const state = this._hass.states[entityId];
      if (!state || state.state === 'unavailable' || state.state === 'unknown') return defaultVal;
      const val = parseFloat(state.state);
      return isNaN(val) ? state.state : val;
    };

    const getBoolState = (entityId) => {
      if (!entityId) return false;
      const state = this._hass.states[entityId];
      return state && state.state === 'on';
    };

    // Get values - use config entities or auto-detect solar_router entities
    const prefix = 'sensor.solar_router_';
    const bprefix = 'binary_sensor.solar_router_';
    const swprefix = 'switch.solar_router_';

    const solarPower = getState(this._config.solar_power_entity || prefix + 'solar_power_mirror', 0);
    const batterySoc = getState(this._config.battery_soc_entity || prefix + 'battery_soc_mirror', 0);
    const tankTemp = getState(prefix + 'tank_temp_estimate', 0);
    const showers = getState(prefix + 'estimated_showers', 0);
    const heatingTime = getState(prefix + 'daily_heating_time', 0);
    const heatingEnergy = getState(prefix + 'daily_heating_energy', 0);
    const tankEnergy = getState(prefix + 'energy_content', 0);
    const sessions = getState(prefix + 'heating_sessions_today', 0);
    const isHeating = getBoolState(bprefix + 'is_heating');
    const solarSufficient = getBoolState(bprefix + 'solar_sufficient');
    const batterySufficient = getBoolState(bprefix + 'battery_sufficient');
    const activeRule = getState(prefix + 'current_rule', 'none');

    // Update values in DOM
    this._setText('solar-value', `${Math.round(solarPower)} W`);
    this._setText('battery-value', `${Math.round(batterySoc)}%`);
    this._setText('heater-temp', `${Math.round(tankTemp)}°C`);
    this._setText('heater-showers', `${showers} showers`);
    this._setText('stat-heating-time', Math.round(heatingTime));
    this._setText('stat-energy', heatingEnergy.toFixed(1));
    this._setText('stat-sessions', sessions);
    this._setText('stat-tank-energy', tankEnergy.toFixed(1));

    // Update status badge
    const badge = this.shadowRoot.getElementById('status-badge');
    if (badge) {
      badge.className = 'status-badge';
      if (isHeating) {
        if (activeRule === 'offpeak_fallback') {
          badge.textContent = '⚡ Off-Peak Heating';
          badge.classList.add('offpeak');
        } else if (activeRule === 'solar_excess' || activeRule === 'grid_export_divert') {
          badge.textContent = '☀️ Solar Heating';
          badge.classList.add('solar');
        } else {
          badge.textContent = '🔥 Heating';
          badge.classList.add('heating');
        }
      } else {
        badge.textContent = 'Idle';
        badge.classList.add('idle');
      }
    }

    // Update center status
    this._setText('center-status', activeRule !== 'none' ? activeRule.replace(/_/g, ' ') : '');

    // Update flow paths
    this._updateFlowPath('path-solar-battery', solarPower > 100 && batterySoc < 100);
    this._updateFlowPath('path-solar-heater', isHeating && solarSufficient && batterySufficient);
    this._updateFlowPath('path-battery-heater', isHeating && !solarSufficient && batterySufficient);
    this._updateFlowPath('path-grid-heater', isHeating && activeRule === 'offpeak_fallback');

    // Update heater circle for heating animation
    const heaterCircle = this.shadowRoot.getElementById('heater-circle');
    if (heaterCircle) {
      if (isHeating) {
        heaterCircle.style.fill = '#FFCDD2';
        heaterCircle.style.strokeWidth = '4';
      } else {
        heaterCircle.style.fill = '#FFEBEE';
        heaterCircle.style.strokeWidth = '3';
      }
    }

    // Store states for animation
    this._flowStates = {
      solarToBattery: solarPower > 100 && batterySoc < 100,
      solarToHeater: isHeating && solarSufficient && batterySufficient,
      batteryToHeater: isHeating && !solarSufficient && batterySufficient,
      gridToHeater: isHeating && activeRule === 'offpeak_fallback'
    };
  }

  _setText(id, text) {
    const el = this.shadowRoot.getElementById(id);
    if (el) el.textContent = text;
  }

  _updateFlowPath(id, active) {
    const path = this.shadowRoot.getElementById(id);
    if (path) {
      path.classList.toggle('active', active);
      path.classList.toggle('inactive', !active);
    }
  }

  _startAnimation() {
    this._flowStates = {
      solarToBattery: false,
      solarToHeater: false,
      batteryToHeater: false,
      gridToHeater: false
    };

    const animateFlows = () => {
      this._animationFrameId = requestAnimationFrame(animateFlows);

      const animContainer = this.shadowRoot.getElementById('flow-animations');
      if (!animContainer) return;

      // Clear old animations
      animContainer.innerHTML = '';

      const time = Date.now() / 1000 * this._config.animation_speed;

      // Draw animated dots for active flows
      if (this._flowStates.solarToHeater) {
        this._drawFlowDots(animContainer, 'path-solar-heater', time, '#FF9800');
      }
      if (this._flowStates.solarToBattery) {
        this._drawFlowDots(animContainer, 'path-solar-battery', time, '#FF9800');
      }
      if (this._flowStates.batteryToHeater) {
        this._drawFlowDots(animContainer, 'path-battery-heater', time, '#4CAF50');
      }
      if (this._flowStates.gridToHeater) {
        this._drawFlowDots(animContainer, 'path-grid-heater', time, '#2196F3');
      }
    };

    animateFlows();
  }

  _drawFlowDots(container, pathId, time, color) {
    const path = this.shadowRoot.getElementById(pathId);
    if (!path) return;

    const pathLength = path.getTotalLength();
    const numDots = 5;
    const spacing = pathLength / numDots;

    for (let i = 0; i < numDots; i++) {
      const offset = ((time * 50 + i * spacing) % pathLength);
      const point = path.getPointAtLength(offset);

      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', point.x);
      dot.setAttribute('cy', point.y);
      dot.setAttribute('r', '4');
      dot.setAttribute('fill', color);
      dot.setAttribute('opacity', '0.8');
      container.appendChild(dot);
    }
  }

  disconnectedCallback() {
    if (this._animationFrameId) {
      cancelAnimationFrame(this._animationFrameId);
    }
  }

  getCardSize() {
    return 5;
  }

  static getConfigElement() {
    return document.createElement('solar-router-flow-card-editor');
  }

  static getStubConfig() {
    return {
      title: 'Solar Router',
      show_header: true,
      animation_speed: 1
    };
  }
}

// Simple editor
class SolarRouterFlowCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
    this._render();
  }

  _render() {
    this.innerHTML = `
      <div style="padding: 16px;">
        <p style="margin-bottom: 16px; color: var(--secondary-text-color);">
          This card automatically uses Solar Router entities. Optional overrides:
        </p>
        <div style="margin-bottom: 8px;">
          <label>Title:</label><br>
          <input type="text" id="title" value="${this._config.title || 'Solar Router'}"
                 style="width: 100%; padding: 8px; margin-top: 4px;">
        </div>
        <div style="margin-bottom: 8px;">
          <label>
            <input type="checkbox" id="show_header" ${this._config.show_header !== false ? 'checked' : ''}>
            Show header
          </label>
        </div>
        <div style="margin-bottom: 8px;">
          <label>Animation speed:</label><br>
          <input type="range" id="animation_speed" min="0.5" max="3" step="0.5"
                 value="${this._config.animation_speed || 1}" style="width: 100%;">
        </div>
      </div>
    `;

    this.querySelector('#title').addEventListener('change', (e) => this._valueChanged('title', e.target.value));
    this.querySelector('#show_header').addEventListener('change', (e) => this._valueChanged('show_header', e.target.checked));
    this.querySelector('#animation_speed').addEventListener('change', (e) => this._valueChanged('animation_speed', parseFloat(e.target.value)));
  }

  _valueChanged(key, value) {
    const event = new CustomEvent('config-changed', {
      detail: { config: { ...this._config, [key]: value } },
      bubbles: true,
      composed: true
    });
    this.dispatchEvent(event);
  }
}

customElements.define('solar-router-flow-card', SolarRouterFlowCard);
customElements.define('solar-router-flow-card-editor', SolarRouterFlowCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'solar-router-flow-card',
  name: 'Solar Router Flow',
  description: 'Built-in energy flow visualization for Solar Router',
  preview: true,
  documentationURL: 'https://github.com/bragonznx/hacssolarrouter'
});

console.info(`%c SOLAR-ROUTER-FLOW %c v${CARD_VERSION} `,
  'color: white; background: #FF9800; font-weight: bold;',
  'color: #FF9800; background: white; font-weight: bold;');
