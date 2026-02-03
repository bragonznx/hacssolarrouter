/**
 * Solar Router Flow Card
 * A custom Lovelace card for visualizing solar energy flow to water heater
 */

class SolarRouterFlowCard extends HTMLElement {
  set hass(hass) {
    this._hass = hass;
    if (!this.content) {
      this.innerHTML = `
        <ha-card>
          <div class="card-content">
            <div class="flow-container">
              <svg viewBox="0 0 400 300" class="flow-svg">
                <!-- Background -->
                <defs>
                  <!-- Gradient for solar -->
                  <linearGradient id="solarGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#fdd835;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ff9800;stop-opacity:1" />
                  </linearGradient>
                  <!-- Gradient for battery -->
                  <linearGradient id="batteryGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#4caf50;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#8bc34a;stop-opacity:1" />
                  </linearGradient>
                  <!-- Gradient for heater -->
                  <linearGradient id="heaterGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#f44336;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#ff5722;stop-opacity:1" />
                  </linearGradient>
                  <!-- Animated dash -->
                  <pattern id="flowPattern" patternUnits="userSpaceOnUse" width="20" height="1">
                    <rect width="10" height="1" fill="currentColor"/>
                  </pattern>
                </defs>

                <!-- Solar Panel Icon -->
                <g class="solar-node" transform="translate(50, 30)">
                  <circle cx="40" cy="40" r="45" fill="#fff3e0" stroke="#ff9800" stroke-width="2"/>
                  <text x="40" y="35" text-anchor="middle" class="icon-text">☀️</text>
                  <text x="40" y="55" text-anchor="middle" class="value-text solar-power">0 W</text>
                  <text x="40" y="70" text-anchor="middle" class="label-text">Solar</text>
                </g>

                <!-- Battery Icon -->
                <g class="battery-node" transform="translate(50, 160)">
                  <circle cx="40" cy="40" r="45" fill="#e8f5e9" stroke="#4caf50" stroke-width="2"/>
                  <text x="40" y="35" text-anchor="middle" class="icon-text">🔋</text>
                  <text x="40" y="55" text-anchor="middle" class="value-text battery-soc">0%</text>
                  <text x="40" y="70" text-anchor="middle" class="label-text">Battery</text>
                </g>

                <!-- Water Heater Icon -->
                <g class="heater-node" transform="translate(260, 95)">
                  <circle cx="40" cy="40" r="45" fill="#ffebee" stroke="#f44336" stroke-width="2" class="heater-circle"/>
                  <text x="40" y="35" text-anchor="middle" class="icon-text">🚿</text>
                  <text x="40" y="55" text-anchor="middle" class="value-text tank-temp">0°C</text>
                  <text x="40" y="70" text-anchor="middle" class="label-text">Heater</text>
                </g>

                <!-- Flow Lines -->
                <!-- Solar to Heater -->
                <path class="flow-line solar-to-heater" d="M 130 70 Q 200 70 260 135"
                      fill="none" stroke="#ff9800" stroke-width="4" stroke-dasharray="10,5">
                  <animate attributeName="stroke-dashoffset" from="0" to="-15" dur="1s" repeatCount="indefinite"/>
                </path>

                <!-- Battery to Heater (when needed) -->
                <path class="flow-line battery-to-heater" d="M 130 200 Q 200 200 260 155"
                      fill="none" stroke="#4caf50" stroke-width="4" stroke-dasharray="10,5" opacity="0.3">
                  <animate attributeName="stroke-dashoffset" from="0" to="-15" dur="1s" repeatCount="indefinite"/>
                </path>

                <!-- Solar to Battery -->
                <path class="flow-line solar-to-battery" d="M 90 120 L 90 160"
                      fill="none" stroke="#ff9800" stroke-width="4" stroke-dasharray="10,5">
                  <animate attributeName="stroke-dashoffset" from="0" to="-15" dur="1s" repeatCount="indefinite"/>
                </path>

                <!-- Status Text -->
                <text x="200" y="280" text-anchor="middle" class="status-text">Auto Mode Active</text>
              </svg>
            </div>

            <!-- Stats Bar -->
            <div class="stats-bar">
              <div class="stat">
                <span class="stat-value showers-available">0</span>
                <span class="stat-label">Showers</span>
              </div>
              <div class="stat">
                <span class="stat-value heating-time">0 min</span>
                <span class="stat-label">Today</span>
              </div>
              <div class="stat">
                <span class="stat-value energy-used">0 kWh</span>
                <span class="stat-label">Energy</span>
              </div>
            </div>
          </div>
        </ha-card>
      `;

      const style = document.createElement('style');
      style.textContent = `
        .flow-container {
          padding: 16px;
        }
        .flow-svg {
          width: 100%;
          max-width: 400px;
          margin: 0 auto;
          display: block;
        }
        .icon-text {
          font-size: 24px;
        }
        .value-text {
          font-size: 14px;
          font-weight: bold;
          fill: var(--primary-text-color);
        }
        .label-text {
          font-size: 11px;
          fill: var(--secondary-text-color);
        }
        .status-text {
          font-size: 12px;
          fill: var(--secondary-text-color);
        }
        .flow-line {
          transition: opacity 0.3s, stroke-width 0.3s;
        }
        .flow-line.active {
          stroke-width: 6;
          opacity: 1;
        }
        .flow-line.inactive {
          stroke-width: 2;
          opacity: 0.2;
        }
        .heater-circle.heating {
          fill: #ffcdd2;
          animation: pulse 1s infinite;
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        .stats-bar {
          display: flex;
          justify-content: space-around;
          padding: 16px;
          border-top: 1px solid var(--divider-color);
          margin-top: 8px;
        }
        .stat {
          text-align: center;
        }
        .stat-value {
          font-size: 18px;
          font-weight: bold;
          display: block;
          color: var(--primary-text-color);
        }
        .stat-label {
          font-size: 12px;
          color: var(--secondary-text-color);
        }
      `;
      this.appendChild(style);
      this.content = this.querySelector('.card-content');
    }
    this._updateCard();
  }

  _updateCard() {
    if (!this._hass || !this._config) return;

    const config = this._config;

    // Get entity states
    const solarPower = this._getEntityState(config.solar_power_entity, 0);
    const batterySoc = this._getEntityState(config.battery_soc_entity, 0);
    const tankTemp = this._getEntityState(config.tank_temp_entity || 'sensor.solar_router_tank_temp_estimate', 0);
    const isHeating = this._getEntityState(config.heating_entity || 'binary_sensor.solar_router_is_heating', 'off') === 'on';
    const autoMode = this._getEntityState(config.auto_mode_entity || 'switch.solar_router_auto_mode', 'off') === 'on';
    const showers = this._getEntityState(config.showers_entity || 'sensor.solar_router_estimated_showers', 0);
    const heatingTime = this._getEntityState(config.heating_time_entity || 'sensor.solar_router_daily_heating_time', 0);
    const energyUsed = this._getEntityState(config.energy_entity || 'sensor.solar_router_daily_heating_energy', 0);

    // Update values
    this.content.querySelector('.solar-power').textContent = `${Math.round(solarPower)} W`;
    this.content.querySelector('.battery-soc').textContent = `${Math.round(batterySoc)}%`;
    this.content.querySelector('.tank-temp').textContent = `${Math.round(tankTemp)}°C`;
    this.content.querySelector('.showers-available').textContent = showers;
    this.content.querySelector('.heating-time').textContent = `${Math.round(heatingTime)} min`;
    this.content.querySelector('.energy-used').textContent = `${parseFloat(energyUsed).toFixed(1)} kWh`;

    // Update status
    let status = 'Idle';
    if (isHeating) {
      status = '🔥 Heating Active';
    } else if (autoMode) {
      status = '🤖 Auto Mode Active';
    } else {
      status = 'Manual Mode';
    }
    this.content.querySelector('.status-text').textContent = status;

    // Update flow lines
    const solarToHeater = this.content.querySelector('.solar-to-heater');
    const batteryToHeater = this.content.querySelector('.battery-to-heater');
    const solarToBattery = this.content.querySelector('.solar-to-battery');
    const heaterCircle = this.content.querySelector('.heater-circle');

    // Animate based on state
    if (isHeating && solarPower > 1000) {
      solarToHeater.classList.add('active');
      solarToHeater.classList.remove('inactive');
    } else {
      solarToHeater.classList.remove('active');
      solarToHeater.classList.add('inactive');
    }

    if (isHeating && solarPower < 500) {
      batteryToHeater.classList.add('active');
      batteryToHeater.classList.remove('inactive');
    } else {
      batteryToHeater.classList.remove('active');
      batteryToHeater.classList.add('inactive');
    }

    if (solarPower > 100 && batterySoc < 100) {
      solarToBattery.classList.add('active');
      solarToBattery.classList.remove('inactive');
    } else {
      solarToBattery.classList.remove('active');
      solarToBattery.classList.add('inactive');
    }

    if (isHeating) {
      heaterCircle.classList.add('heating');
    } else {
      heaterCircle.classList.remove('heating');
    }
  }

  _getEntityState(entityId, defaultValue) {
    if (!entityId || !this._hass.states[entityId]) {
      return defaultValue;
    }
    const state = this._hass.states[entityId].state;
    if (state === 'unavailable' || state === 'unknown') {
      return defaultValue;
    }
    return isNaN(state) ? state : parseFloat(state);
  }

  setConfig(config) {
    if (!config.solar_power_entity || !config.battery_soc_entity) {
      throw new Error('Please define solar_power_entity and battery_soc_entity');
    }
    this._config = config;
  }

  getCardSize() {
    return 4;
  }

  static getConfigElement() {
    return document.createElement('solar-router-flow-card-editor');
  }

  static getStubConfig() {
    return {
      solar_power_entity: 'sensor.victron_solar_power',
      battery_soc_entity: 'sensor.victron_battery_soc',
    };
  }
}

// Editor for the card
class SolarRouterFlowCardEditor extends HTMLElement {
  setConfig(config) {
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    this._render();
  }

  _render() {
    if (!this._rendered) {
      this.innerHTML = `
        <div class="card-config">
          <ha-entity-picker
            label="Solar Power Entity"
            .hass="${this._hass}"
            .value="${this._config?.solar_power_entity || ''}"
            .configValue="${'solar_power_entity'}"
            @value-changed="${this._valueChanged.bind(this)}"
            allow-custom-entity
          ></ha-entity-picker>
          <ha-entity-picker
            label="Battery SoC Entity"
            .hass="${this._hass}"
            .value="${this._config?.battery_soc_entity || ''}"
            .configValue="${'battery_soc_entity'}"
            @value-changed="${this._valueChanged.bind(this)}"
            allow-custom-entity
          ></ha-entity-picker>
        </div>
      `;
      this._rendered = true;
    }
  }

  _valueChanged(ev) {
    if (!this._config || !this._hass) return;
    const target = ev.target;
    const value = ev.detail?.value;
    const configValue = target.configValue;

    if (configValue && value !== this._config[configValue]) {
      const newConfig = { ...this._config, [configValue]: value };
      const event = new CustomEvent('config-changed', {
        detail: { config: newConfig },
        bubbles: true,
        composed: true,
      });
      this.dispatchEvent(event);
    }
  }
}

customElements.define('solar-router-flow-card', SolarRouterFlowCard);
customElements.define('solar-router-flow-card-editor', SolarRouterFlowCardEditor);

window.customCards = window.customCards || [];
window.customCards.push({
  type: 'solar-router-flow-card',
  name: 'Solar Router Flow Card',
  description: 'Visualize energy flow to your water heater',
  preview: true,
  documentationURL: 'https://github.com/bragonznx/hacssolarrouter',
});

console.info('%c SOLAR-ROUTER-FLOW-CARD %c v1.0.0 ',
  'color: white; background: #f44336; font-weight: bold;',
  'color: #f44336; background: white; font-weight: bold;'
);
