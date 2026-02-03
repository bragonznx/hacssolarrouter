# Solar Router - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/bragonznx/hacssolarrouter.svg)](https://github.com/bragonznx/hacssolarrouter/releases)
[![License](https://img.shields.io/github/license/bragonznx/hacssolarrouter.svg)](LICENSE)

A Home Assistant integration for intelligent solar power routing to your water heater. Maximize self-consumption of your solar energy by heating water when you have excess solar power.

![Solar Router Dashboard](https://raw.githubusercontent.com/bragonznx/hacssolarrouter/main/images/dashboard.png)

## Features

### Intelligent Solar Routing
- **Battery-Aware Routing**: Only routes power to water heater when battery is sufficiently charged
- **Solar Power Threshold**: Configurable minimum solar power required before routing
- **Grid Export Diversion**: Automatically diverts power that would be exported to the grid
- **Time Window Control**: Solar routing only during configurable daylight hours

### Water Tank Management
- **Temperature Estimation**: Estimates water tank temperature based on heating time and usage
- **Shower Availability**: Shows estimated number of showers available
- **Energy Content Tracking**: Monitors energy stored in the water tank
- **Usage Event Tracking**: Record shower/dish usage to update temperature estimate
- **24h Temperature Forecast**: Predicts tank temperature over the next 24 hours

### Fallback Heating
- **Off-Peak Fallback**: If minimum daily heating isn't met, uses off-peak grid hours
- **Emergency Heating**: Automatically heats if tank temperature drops too low
- **Minimum Daily Heating**: Configurable minimum heating time per day

### Customizable Rules
- **Rule Engine**: Create custom rules with conditions and actions
- **Priority System**: Higher priority rules override lower ones
- **Multiple Conditions**: Combine battery, solar, time, and temperature conditions
- **Default Rules**: Comes with sensible default rules that can be customized

### Custom Dashboard
- **Energy Flow Visualization**: Custom Lovelace card showing real-time energy flow
- **Ready-to-use Dashboard**: Import the included dashboard YAML
- **Compatible with power-flow-card-plus**: Works with popular HACS frontend cards

---

## Installation

### Prerequisites

- Home Assistant 2024.1 or newer
- HACS (Home Assistant Community Store) installed
- A solar system with accessible sensors (e.g., Victron with HACS integration)
- A controllable water heater switch

### Method 1: HACS Installation (Recommended)

1. **Open HACS** in your Home Assistant instance

2. **Add Custom Repository**:
   - Click on the three dots menu (⋮) in the top right
   - Select **"Custom repositories"**
   - Enter the repository URL:
     ```
     https://github.com/bragonznx/hacssolarrouter
     ```
   - Select **"Integration"** as the category
   - Click **"Add"**

3. **Install the Integration**:
   - Search for **"Solar Router"** in HACS
   - Click on it and then click **"Download"**
   - Select the latest version

4. **Restart Home Assistant**:
   - Go to **Settings → System → Restart**
   - Click **"Restart"**

5. **Add the Integration**:
   - Go to **Settings → Devices & Services**
   - Click **"+ Add Integration"**
   - Search for **"Solar Router"**
   - Follow the configuration wizard

### Method 2: Manual Installation

1. **Download the Integration**:
   ```bash
   cd /tmp
   git clone https://github.com/bragonznx/hacssolarrouter.git
   ```

2. **Copy to Custom Components**:
   ```bash
   cp -r hacssolarrouter/custom_components/solar_router /config/custom_components/
   ```

3. **Copy Frontend Resources** (optional, for custom card):
   ```bash
   mkdir -p /config/www
   cp hacssolarrouter/www/solar-router-flow-card.js /config/www/
   ```

4. **Restart Home Assistant**

5. **Add the Integration** via Settings → Devices & Services

### Method 3: Using Docker/SSH

```bash
# SSH into your Home Assistant
ssh root@homeassistant.local

# Navigate to config directory
cd /config

# Clone the repository
git clone https://github.com/bragonznx/hacssolarrouter.git /tmp/solar-router

# Copy the integration
cp -r /tmp/solar-router/custom_components/solar_router custom_components/

# Copy frontend resources
mkdir -p www
cp /tmp/solar-router/www/solar-router-flow-card.js www/

# Clean up
rm -rf /tmp/solar-router

# Restart Home Assistant
ha core restart
```

---

## Configuration

### Initial Setup Wizard

After installation, add the integration via Settings → Devices & Services → Add Integration → Solar Router.

The setup wizard has 6 steps:

#### Step 1: Basic Setup
- **Name**: Give your solar router a name (e.g., "Solar Router")

#### Step 2: Entity Configuration
Select entities from your solar system (Victron, SolarEdge, etc.):

| Setting | Description | Example |
|---------|-------------|---------|
| Battery SoC | Battery state of charge sensor | `sensor.victron_battery_soc` |
| Solar Power | Solar panel power production | `sensor.victron_pv_power` |
| Grid Power | Grid import/export (optional) | `sensor.victron_grid_power` |
| Battery Power | Battery charge/discharge (optional) | `sensor.victron_battery_power` |
| Heater Switch | Switch controlling water heater | `switch.water_heater` |
| Heater Power | Power consumption (optional) | `sensor.water_heater_power` |

#### Step 3: Water Tank Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| Tank Volume | 200 L | Your water tank capacity |
| Heater Power | 2400 W | Heating element wattage |
| Target Temperature | 55°C | Desired water temperature |
| Minimum Temperature | 40°C | Lowest usable temperature |
| Heat Loss Rate | 0.5°C/h | How fast tank loses heat |
| Cold Water Temperature | 15°C | Incoming water temperature |
| Ambient Temperature | 20°C | Room temperature around tank |

#### Step 4: Routing Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| Minimum Battery SoC | 70% | Battery level before routing starts |
| Minimum Solar Power | 2500 W | Solar power to trigger routing |
| Minimum Daily Heating | 60 min | Ensure this much heating per day |

#### Step 5: Time Windows

| Setting | Default | Description |
|---------|---------|-------------|
| Solar Window Start | 10:00 | When solar routing begins |
| Solar Window End | 17:00 | When solar routing ends |
| Off-Peak Start | 22:00 | Off-peak electricity starts |
| Off-Peak End | 06:00 | Off-peak electricity ends |

#### Step 6: Usage Patterns

| Setting | Default | Description |
|---------|---------|-------------|
| Shower Duration | 10 min | Average shower length |
| Shower Flow Rate | 10 L/min | Hot water flow during shower |
| Dish Duration | 10 min | Average dishwashing time |
| Dish Flow Rate | 6 L/min | Hot water flow for dishes |

---

## Dashboard Setup

### Option 1: Import Ready-Made Dashboard

1. Go to **Settings → Dashboards**
2. Click **"+ Add Dashboard"**
3. Select **"New dashboard from scratch"**
4. Name it "Solar Router"
5. Click on the new dashboard, then **Edit Dashboard**
6. Click the three dots (⋮) → **"Raw configuration editor"**
7. Paste the contents of [dashboards/solar_router.yaml](dashboards/solar_router.yaml)
8. Save

### Option 2: Use the Custom Flow Card

The integration includes a custom Lovelace card for energy flow visualization.

**Add to your dashboard:**
```yaml
type: custom:solar-router-flow-card
solar_power_entity: sensor.victron_pv_power
battery_soc_entity: sensor.victron_battery_soc
```

### Option 3: Use with power-flow-card-plus

For the best energy flow visualization, install **power-flow-card-plus** from HACS:

1. In HACS, go to **Frontend**
2. Search for **"power-flow-card-plus"**
3. Install and restart

See [dashboard.md](dashboard.md) for complete dashboard configurations.

---

## Entities

### Sensors

| Entity | Description |
|--------|-------------|
| `sensor.solar_router_tank_temp_estimate` | Estimated water tank temperature |
| `sensor.solar_router_daily_heating_time` | Total heating time today |
| `sensor.solar_router_daily_heating_energy` | Total energy used for heating today |
| `sensor.solar_router_energy_content` | Energy stored in the water tank (kWh) |
| `sensor.solar_router_estimated_showers` | Number of showers available |
| `sensor.solar_router_time_to_target` | Time until tank reaches target temp |
| `sensor.solar_router_time_to_cold` | Time until tank is too cold |
| `sensor.solar_router_active_rule` | Currently active routing rule |
| `sensor.solar_router_heating_mode` | Current heating mode |
| `sensor.solar_router_heating_sessions_today` | Number of heating sessions today |
| `sensor.solar_router_temperature_forecast` | 24h temperature forecast (attribute) |

### Binary Sensors

| Entity | Description |
|--------|-------------|
| `binary_sensor.solar_router_is_heating` | Currently heating |
| `binary_sensor.solar_router_solar_sufficient` | Solar power above threshold |
| `binary_sensor.solar_router_battery_sufficient` | Battery above threshold |
| `binary_sensor.solar_router_fallback_needed` | Daily minimum not met |
| `binary_sensor.solar_router_tank_cold` | Tank temperature too low |
| `binary_sensor.solar_router_tank_hot` | Tank temperature OK |
| `binary_sensor.solar_router_auto_mode_active` | Auto mode is active |

### Switches

| Entity | Description |
|--------|-------------|
| `switch.solar_router_auto_mode` | Enable/disable automatic routing |
| `switch.solar_router_offpeak_fallback` | Enable/disable off-peak fallback |
| `switch.solar_router_force_heating` | Manually force heating on/off |

### Numbers (Adjustable Thresholds)

| Entity | Description |
|--------|-------------|
| `number.solar_router_min_soc_threshold` | Adjust minimum battery SoC (20-95%) |
| `number.solar_router_min_solar_power_threshold` | Adjust minimum solar power (100-5000W) |
| `number.solar_router_min_daily_heating_threshold` | Adjust minimum daily heating (0-240 min) |
| `number.solar_router_tank_temperature_calibration` | Calibrate tank temperature (10-70°C) |

---

## Services

### `solar_router.force_heating`
Force the heater to turn on for a specified duration.
```yaml
service: solar_router.force_heating
data:
  duration: 60  # minutes (1-480)
```

### `solar_router.stop_heating`
Stop heating immediately.
```yaml
service: solar_router.stop_heating
```

### `solar_router.set_tank_temp`
Manually set the estimated tank temperature (for calibration).
```yaml
service: solar_router.set_tank_temp
data:
  temperature: 50  # °C
```

### `solar_router.apply_usage_event`
Record a water usage event to update the temperature estimate.
```yaml
service: solar_router.apply_usage_event
data:
  event: shower  # or "dishes"
```

### `solar_router.reset_daily_stats`
Reset daily heating time and energy counters.
```yaml
service: solar_router.reset_daily_stats
```

### `solar_router.enable_rule` / `solar_router.disable_rule`
Enable or disable a specific routing rule.
```yaml
service: solar_router.enable_rule
data:
  rule_name: offpeak_fallback
```

### `solar_router.set_rule`
Create or update a custom routing rule.
```yaml
service: solar_router.set_rule
data:
  name: my_custom_rule
  description: "Heat when battery is full and solar is high"
  priority: 75
  enabled: true
  conditions:
    - type: battery_soc_above
      value: 90
    - type: solar_power_above
      value: 3000
    - type: tank_temp_below
      value: 50
  action: turn_on  # or "turn_off"
```

### Condition Types

| Type | Description | Value |
|------|-------------|-------|
| `battery_soc_above` | Battery SoC >= value | % |
| `battery_soc_below` | Battery SoC <= value | % |
| `solar_power_above` | Solar power >= value | W |
| `solar_power_below` | Solar power <= value | W |
| `grid_export_above` | Exporting >= value to grid | W |
| `grid_import_above` | Importing >= value from grid | W |
| `tank_temp_above` | Tank temp >= value | °C |
| `tank_temp_below` | Tank temp <= value | °C |
| `time_between` | Time is between value and value2 | HH:MM |
| `daily_heating_below` | Daily heating < value | minutes |
| `daily_heating_above` | Daily heating >= value | minutes |
| `offpeak_hours` | Currently in off-peak window | true |

---

## Default Rules

The integration comes with these pre-configured rules:

| Rule | Priority | Description |
|------|----------|-------------|
| `emergency_heating` | 100 | Heat if tank < 35°C |
| `battery_protection` | 95 | Stop if battery < 40% and solar < 500W |
| `tank_full` | 90 | Stop heating when tank > 55°C |
| `solar_excess` | 80 | Route when battery > 70% and solar > 2500W |
| `grid_export_divert` | 70 | Divert grid export > 1000W to heater |
| `offpeak_fallback` | 60 | Heat during off-peak if daily min not met |

---

## Example Automations

### Notify when solar heating starts
```yaml
automation:
  - alias: "Solar Router - Notify Solar Heating"
    trigger:
      - platform: event
        event_type: solar_router_heating_started
    condition:
      - condition: template
        value_template: "{{ trigger.event.data.rule == 'solar_excess' }}"
    action:
      - service: notify.mobile_app
        data:
          message: "☀️ Solar routing started! Tank at {{ trigger.event.data.tank_temp }}°C"
```

### Track hot water usage with a button
```yaml
input_button:
  record_shower:
    name: Record Shower
    icon: mdi:shower

automation:
  - alias: "Solar Router - Record Shower"
    trigger:
      - platform: state
        entity_id: input_button.record_shower
    action:
      - service: solar_router.apply_usage_event
        data:
          event: shower
```

### Daily summary notification
```yaml
automation:
  - alias: "Solar Router - Daily Summary"
    trigger:
      - platform: time
        at: "21:00:00"
    action:
      - service: notify.mobile_app
        data:
          message: >
            🚿 Solar Router Summary:
            - Heating time: {{ states('sensor.solar_router_daily_heating_time') }} min
            - Energy used: {{ states('sensor.solar_router_daily_heating_energy') }} kWh
            - Tank temp: {{ states('sensor.solar_router_tank_temp_estimate') }}°C
            - Showers available: {{ states('sensor.solar_router_estimated_showers') }}
```

---

## Troubleshooting

### Temperature estimate seems wrong
Use the calibration entity or service:
```yaml
service: solar_router.set_tank_temp
data:
  temperature: 55
```

### Heater doesn't turn on
1. Check that **Auto Mode** switch is enabled
2. Verify battery SoC is above threshold (check `binary_sensor.solar_router_battery_sufficient`)
3. Verify solar power is above threshold (check `binary_sensor.solar_router_solar_sufficient`)
4. Check the **Active Rule** sensor to see which rule is in control
5. Verify the heater switch entity is correctly configured

### Fallback heating not working
1. Ensure **Off-Peak Fallback** switch is enabled
2. Verify current time is within off-peak hours
3. Check that daily heating time is below minimum threshold

### Integration not loading
1. Check Home Assistant logs: **Settings → System → Logs**
2. Ensure all required entities exist and are available
3. Try removing and re-adding the integration

---

## Events

The integration fires these events that you can use in automations:

| Event | Data | Description |
|-------|------|-------------|
| `solar_router_heating_started` | `rule`, `tank_temp` | Heating began |
| `solar_router_heating_stopped` | `rule`, `tank_temp` | Heating stopped |
| `solar_router_rule_triggered` | `rule`, `action` | A rule was triggered |
| `solar_router_fallback_activated` | - | Off-peak fallback started |

---

## Compatibility

### Tested Solar Systems
- Victron (via victron HACS integration)
- Any system that exposes power sensors to Home Assistant

### Tested Heater Controls
- Shelly relays
- Sonoff switches
- Any Home Assistant switch entity

---

## Support

- **Issues**: [GitHub Issues](https://github.com/bragonznx/hacssolarrouter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/bragonznx/hacssolarrouter/discussions)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue or pull request on GitHub.

---

## Credits

- Inspired by the [shelly_warmup](https://github.com/bragonznx/shelly_warmup) project
- Built for the Home Assistant community
