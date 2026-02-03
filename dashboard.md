# Solar Router Dashboard

This document provides a sample Lovelace dashboard configuration for the Solar Router integration.

## Prerequisites

For the best experience, install these HACS frontend components:
- **power-flow-card-plus**: For energy flow visualization
- **apexcharts-card**: For advanced graphs
- **mushroom-cards**: For modern entity cards
- **mini-graph-card**: For simple graphs

## Dashboard YAML

Copy this YAML to create a new dashboard or view.

```yaml
title: Solar Router
path: solar-router
icon: mdi:water-boiler
badges: []
cards:
  # Row 1: Power Flow Visualization
  - type: custom:power-flow-card-plus
    entities:
      battery:
        entity: sensor.victron_battery_soc
        state_of_charge: sensor.victron_battery_soc
      grid:
        entity: sensor.victron_grid_power
        invert_state: true
      solar:
        entity: sensor.victron_solar_power
      home:
        entity: sensor.victron_consumption
      individual:
        - entity: sensor.solar_router_heater_power
          name: Water Heater
          icon: mdi:water-boiler
          color: '#ff6b6b'
          display_zero: true
    watt_threshold: 0
    kw_decimals: 2
    min_flow_rate: 0.75
    max_flow_rate: 6
    w_decimals: 0
    clickable_entities: true
    display_zero_lines:
      mode: show
      transparency: 50
      grey_color:
        - 189
        - 189
        - 189

  # Row 2: Tank Status and Controls
  - type: horizontal-stack
    cards:
      # Tank Temperature Gauge
      - type: gauge
        entity: sensor.solar_router_tank_temp_estimate
        name: Tank Temperature
        min: 10
        max: 70
        severity:
          green: 45
          yellow: 35
          red: 0
        needle: true
        segments:
          - from: 0
            color: '#4fc3f7'
          - from: 35
            color: '#ffb74d'
          - from: 45
            color: '#81c784'
          - from: 55
            color: '#e57373'

      # Showers Available
      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_estimated_showers') }} Showers"
        secondary: Available
        icon: mdi:shower-head
        icon_color: >
          {% set showers = states('sensor.solar_router_estimated_showers') | float %}
          {% if showers >= 2 %}green
          {% elif showers >= 1 %}orange
          {% else %}red{% endif %}
        layout: vertical

      # Heating Status
      - type: custom:mushroom-template-card
        primary: >
          {% if is_state('binary_sensor.solar_router_is_heating', 'on') %}
          Heating
          {% else %}
          Idle
          {% endif %}
        secondary: "{{ states('sensor.solar_router_active_rule') | replace('_', ' ') | title }}"
        icon: >
          {% if is_state('binary_sensor.solar_router_is_heating', 'on') %}
          mdi:fire
          {% else %}
          mdi:water-boiler-off
          {% endif %}
        icon_color: >
          {% if is_state('binary_sensor.solar_router_is_heating', 'on') %}
          red
          {% else %}
          grey
          {% endif %}
        layout: vertical

  # Row 3: Control Switches
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: switch.solar_router_auto_mode
        name: Auto Mode
        icon: mdi:robot
        tap_action:
          action: toggle
        fill_container: true

      - type: custom:mushroom-entity-card
        entity: switch.solar_router_offpeak_fallback
        name: Off-Peak Fallback
        icon: mdi:clock-alert
        tap_action:
          action: toggle
        fill_container: true

      - type: custom:mushroom-entity-card
        entity: switch.solar_router_force_heating
        name: Force Heating
        icon: mdi:fire
        tap_action:
          action: toggle
        fill_container: true

  # Row 4: Daily Statistics
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_daily_heating_time') | round(0) }} min"
        secondary: Heating Today
        icon: mdi:clock-outline
        layout: vertical

      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_daily_heating_energy') }} kWh"
        secondary: Energy Today
        icon: mdi:lightning-bolt
        layout: vertical

      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_heating_sessions_today') }}"
        secondary: Sessions Today
        icon: mdi:counter
        layout: vertical

      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_energy_content') }} kWh"
        secondary: Tank Energy
        icon: mdi:water-thermometer
        layout: vertical

  # Row 5: Temperature Graph (24h)
  - type: custom:apexcharts-card
    header:
      show: true
      title: Tank Temperature (24h)
      show_states: true
      colorize_states: true
    graph_span: 24h
    span:
      end: now
    yaxis:
      - min: 10
        max: 70
        decimals: 0
    series:
      - entity: sensor.solar_router_tank_temp_estimate
        name: Temperature
        type: area
        color: '#ff6b6b'
        stroke_width: 2
        fill_raw: last
        group_by:
          func: avg
          duration: 10min
    apex_config:
      chart:
        height: 200
      annotations:
        yaxis:
          - y: 55
            borderColor: '#81c784'
            label:
              text: Target
          - y: 40
            borderColor: '#ffb74d'
            label:
              text: Minimum

  # Row 6: Power Graph (Real-time)
  - type: custom:apexcharts-card
    header:
      show: true
      title: Power Flow (6h)
      show_states: true
    graph_span: 6h
    span:
      end: now
    yaxis:
      - decimals: 0
        apex_config:
          tickAmount: 5
    series:
      - entity: sensor.victron_solar_power
        name: Solar
        type: area
        color: '#fdd835'
        stroke_width: 1
        opacity: 0.3
        group_by:
          func: avg
          duration: 5min
      - entity: sensor.solar_router_heater_power
        name: Heater
        type: area
        color: '#ff6b6b'
        stroke_width: 1
        opacity: 0.3
        group_by:
          func: avg
          duration: 5min
    apex_config:
      chart:
        height: 200

  # Row 7: Solar Routing Conditions
  - type: entities
    title: Routing Conditions
    entities:
      - entity: binary_sensor.solar_router_battery_sufficient
        name: Battery OK
        secondary_info: last-changed
      - entity: binary_sensor.solar_router_solar_sufficient
        name: Solar OK
        secondary_info: last-changed
      - entity: binary_sensor.solar_router_tank_hot
        name: Tank Warm
        secondary_info: last-changed
      - entity: binary_sensor.solar_router_fallback_needed
        name: Fallback Needed
        secondary_info: last-changed

  # Row 8: Threshold Adjustments
  - type: entities
    title: Thresholds
    entities:
      - entity: number.solar_router_min_soc_threshold
        name: Min Battery SoC
      - entity: number.solar_router_min_solar_power_threshold
        name: Min Solar Power
      - entity: number.solar_router_min_daily_heating_threshold
        name: Min Daily Heating
      - type: divider
      - entity: number.solar_router_tank_temperature_calibration
        name: Calibrate Tank Temp

  # Row 9: Quick Actions
  - type: horizontal-stack
    cards:
      - type: button
        name: Record Shower
        icon: mdi:shower
        tap_action:
          action: call-service
          service: solar_router.apply_usage_event
          service_data:
            event: shower

      - type: button
        name: Record Dishes
        icon: mdi:silverware-clean
        tap_action:
          action: call-service
          service: solar_router.apply_usage_event
          service_data:
            event: dishes

      - type: button
        name: Force 1 Hour
        icon: mdi:fire
        tap_action:
          action: call-service
          service: solar_router.force_heating
          service_data:
            duration: 60

      - type: button
        name: Stop Heating
        icon: mdi:stop
        tap_action:
          action: call-service
          service: solar_router.stop_heating

  # Row 10: Time Estimates
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-template-card
        primary: >
          {% set mins = states('sensor.solar_router_time_to_target') | float(0) %}
          {% if mins == 0 %}At Target
          {% elif mins < 60 %}{{ mins | round(0) }} min
          {% else %}{{ (mins / 60) | round(1) }} hrs{% endif %}
        secondary: Time to Target
        icon: mdi:timer-outline
        layout: vertical

      - type: custom:mushroom-template-card
        primary: "{{ states('sensor.solar_router_time_to_cold') }} hrs"
        secondary: Time Until Cold
        icon: mdi:timer-sand
        layout: vertical

  # Row 11: History Graph
  - type: history-graph
    title: Heating History (24h)
    hours_to_show: 24
    entities:
      - entity: binary_sensor.solar_router_is_heating
        name: Heating
      - entity: binary_sensor.solar_router_solar_sufficient
        name: Solar OK
      - entity: binary_sensor.solar_router_battery_sufficient
        name: Battery OK
```

## Alternative: Simple Dashboard (No HACS Cards Required)

If you don't want to install additional frontend cards, here's a simpler version using only built-in cards:

```yaml
title: Solar Router
path: solar-router
icon: mdi:water-boiler
cards:
  # Status Overview
  - type: entities
    title: Solar Router Status
    show_header_toggle: false
    entities:
      - entity: sensor.solar_router_tank_temp_estimate
        name: Tank Temperature
      - entity: sensor.solar_router_estimated_showers
        name: Showers Available
      - entity: sensor.solar_router_active_rule
        name: Active Rule
      - entity: sensor.solar_router_heating_mode
        name: Mode

  # Controls
  - type: entities
    title: Controls
    entities:
      - entity: switch.solar_router_auto_mode
      - entity: switch.solar_router_offpeak_fallback
      - entity: switch.solar_router_force_heating

  # Conditions
  - type: glance
    title: Conditions
    entities:
      - entity: binary_sensor.solar_router_is_heating
        name: Heating
      - entity: binary_sensor.solar_router_battery_sufficient
        name: Battery OK
      - entity: binary_sensor.solar_router_solar_sufficient
        name: Solar OK
      - entity: binary_sensor.solar_router_tank_hot
        name: Tank OK

  # Temperature Gauge
  - type: gauge
    entity: sensor.solar_router_tank_temp_estimate
    name: Tank Temperature
    min: 10
    max: 70
    severity:
      green: 45
      yellow: 35
      red: 0

  # Daily Stats
  - type: glance
    title: Today
    entities:
      - entity: sensor.solar_router_daily_heating_time
        name: Heating Time
      - entity: sensor.solar_router_daily_heating_energy
        name: Energy Used
      - entity: sensor.solar_router_heating_sessions_today
        name: Sessions

  # Thresholds
  - type: entities
    title: Thresholds
    entities:
      - entity: number.solar_router_min_soc_threshold
      - entity: number.solar_router_min_solar_power_threshold
      - entity: number.solar_router_min_daily_heating_threshold
      - entity: number.solar_router_tank_temperature_calibration

  # History
  - type: history-graph
    title: Temperature History
    hours_to_show: 24
    entities:
      - entity: sensor.solar_router_tank_temp_estimate

  - type: history-graph
    title: Heating History
    hours_to_show: 24
    entities:
      - entity: binary_sensor.solar_router_is_heating
```

## Custom Energy Flow Card

For a visual energy flow diagram similar to the Home Assistant Energy Dashboard, install the `power-flow-card-plus` from HACS:

1. In HACS, go to Frontend
2. Search for "power-flow-card-plus"
3. Install and restart Home Assistant

The card shows energy flowing from solar to battery, grid, home consumption, and your water heater in real-time.
