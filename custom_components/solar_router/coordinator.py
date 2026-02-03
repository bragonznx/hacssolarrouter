"""Data coordinator for Solar Router integration."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_time_interval, async_track_time_change
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_GRID_POWER_ENTITY,
    CONF_HEATER_POWER_ENTITY,
    CONF_HEATER_SWITCH_ENTITY,
    CONF_HEATER_WATTAGE,
    CONF_OFFPEAK_END,
    CONF_OFFPEAK_START,
    CONF_SOLAR_POWER_ENTITY,
    CONF_TANK_HEAT_LOSS_RATE,
    CONF_TANK_VOLUME,
    DEFAULT_CHECK_INTERVAL,
    DEFAULT_HEATER_WATTAGE,
    DEFAULT_OFFPEAK_END,
    DEFAULT_OFFPEAK_START,
    DEFAULT_TANK_HEAT_LOSS_RATE,
    DEFAULT_TANK_VOLUME,
    DOMAIN,
    EVENT_FALLBACK_ACTIVATED,
    EVENT_HEATING_STARTED,
    EVENT_HEATING_STOPPED,
    EVENT_RULE_TRIGGERED,
    HeatingMode,
    RuleActionType,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from .rule_engine import RuleEngine
from .water_tank import WaterTankModel

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=DEFAULT_CHECK_INTERVAL)


class SolarRouterCoordinator(DataUpdateCoordinator):
    """Coordinator for solar router data and logic."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )

        self.config_entry = entry
        self._entry_data = entry.data
        self._entry_options = entry.options

        # Initialize components
        self.rule_engine = RuleEngine()
        self.water_tank = WaterTankModel(
            volume_liters=self._get_option(CONF_TANK_VOLUME, DEFAULT_TANK_VOLUME),
            heater_wattage=self._get_option(CONF_HEATER_WATTAGE, DEFAULT_HEATER_WATTAGE),
            heat_loss_rate=self._get_option(CONF_TANK_HEAT_LOSS_RATE, DEFAULT_TANK_HEAT_LOSS_RATE),
        )

        # State
        self._heating_mode = HeatingMode.AUTO
        self._auto_mode_enabled = True
        self._offpeak_fallback_enabled = True
        self._last_update_time: datetime | None = None
        self._heater_was_on = False

        # Storage for persistence
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry.entry_id}")

        # Unsub handlers
        self._unsub_midnight: callable | None = None

    def _get_option(self, key: str, default: Any) -> Any:
        """Get option from options or data."""
        return self._entry_options.get(key, self._entry_data.get(key, default))

    async def async_setup(self) -> None:
        """Set up the coordinator."""
        # Load stored data
        stored = await self._store.async_load()
        if stored:
            self._load_stored_data(stored)

        # Set up midnight reset
        self._unsub_midnight = async_track_time_change(
            self.hass,
            self._async_midnight_reset,
            hour=0,
            minute=0,
            second=0,
        )

    async def async_shutdown(self) -> None:
        """Shutdown the coordinator."""
        if self._unsub_midnight:
            self._unsub_midnight()
            self._unsub_midnight = None

        # Save state
        await self._async_save_state()

    async def _async_save_state(self) -> None:
        """Save current state to storage."""
        data = {
            "water_tank": self.water_tank.to_dict(),
            "rules": self.rule_engine.to_dict(),
            "heating_mode": self._heating_mode.value,
            "auto_mode_enabled": self._auto_mode_enabled,
            "offpeak_fallback_enabled": self._offpeak_fallback_enabled,
        }
        await self._store.async_save(data)

    def _load_stored_data(self, data: dict) -> None:
        """Load state from storage."""
        if "water_tank" in data:
            self.water_tank.from_dict(data["water_tank"])
        if "rules" in data:
            self.rule_engine.from_dict(data["rules"])
        if "heating_mode" in data:
            self._heating_mode = HeatingMode(data["heating_mode"])
        self._auto_mode_enabled = data.get("auto_mode_enabled", True)
        self._offpeak_fallback_enabled = data.get("offpeak_fallback_enabled", True)

    @callback
    async def _async_midnight_reset(self, now: datetime) -> None:
        """Reset daily stats at midnight."""
        _LOGGER.info("Resetting daily statistics")
        self.water_tank.reset_daily_stats()
        await self._async_save_state()
        await self.async_refresh()

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data and run routing logic."""
        now = dt_util.utcnow()

        try:
            # Get current sensor values
            data = await self._async_get_sensor_data()

            # Calculate elapsed time since last update
            elapsed_seconds = 0.0
            if self._last_update_time:
                elapsed_seconds = (now - self._last_update_time).total_seconds()

            # Update water tank model
            heater_on = data.get("heater_on", False)
            self.water_tank.update_temperature(heater_on, elapsed_seconds)

            # Build context for rule evaluation
            context = self._build_rule_context(data)

            # Evaluate rules if in auto mode
            if self._auto_mode_enabled:
                should_heat, triggered_rule = self.rule_engine.should_heat(context)
                data["should_heat"] = should_heat
                data["triggered_rule"] = triggered_rule

                # Control the heater
                if should_heat != heater_on:
                    await self._async_set_heater(should_heat)

                    if should_heat:
                        self.hass.bus.async_fire(EVENT_HEATING_STARTED, {
                            "rule": triggered_rule,
                            "tank_temp": self.water_tank.state.estimated_temp,
                        })
                    else:
                        self.hass.bus.async_fire(EVENT_HEATING_STOPPED, {
                            "rule": triggered_rule,
                            "tank_temp": self.water_tank.state.estimated_temp,
                        })

                    if triggered_rule:
                        self.hass.bus.async_fire(EVENT_RULE_TRIGGERED, {
                            "rule": triggered_rule,
                            "action": "turn_on" if should_heat else "turn_off",
                        })
            else:
                data["should_heat"] = None
                data["triggered_rule"] = None

            # Add computed values
            data.update(self._get_computed_values())

            self._last_update_time = now
            self._heater_was_on = data.get("heater_on", False)

            # Periodically save state
            if elapsed_seconds > 300:  # Every 5 minutes
                await self._async_save_state()

            return data

        except Exception as err:
            _LOGGER.error("Error updating solar router: %s", err)
            raise UpdateFailed(f"Error updating solar router: {err}") from err

    async def _async_get_sensor_data(self) -> dict[str, Any]:
        """Get current values from configured sensors."""
        data = {}

        # Battery SoC
        soc_entity = self._get_option(CONF_BATTERY_SOC_ENTITY, None)
        if soc_entity:
            data["battery_soc"] = self._get_entity_value(soc_entity, 0)

        # Solar power
        solar_entity = self._get_option(CONF_SOLAR_POWER_ENTITY, None)
        if solar_entity:
            data["solar_power"] = self._get_entity_value(solar_entity, 0)

        # Grid power
        grid_entity = self._get_option(CONF_GRID_POWER_ENTITY, None)
        if grid_entity:
            data["grid_power"] = self._get_entity_value(grid_entity, 0)

        # Battery power
        battery_power_entity = self._get_option(CONF_BATTERY_POWER_ENTITY, None)
        if battery_power_entity:
            data["battery_power"] = self._get_entity_value(battery_power_entity, 0)

        # Heater power consumption
        heater_power_entity = self._get_option(CONF_HEATER_POWER_ENTITY, None)
        if heater_power_entity:
            data["heater_power"] = self._get_entity_value(heater_power_entity, 0)

        # Heater switch state
        heater_switch_entity = self._get_option(CONF_HEATER_SWITCH_ENTITY, None)
        if heater_switch_entity:
            state = self.hass.states.get(heater_switch_entity)
            data["heater_on"] = state.state == "on" if state else False

        return data

    def _get_entity_value(self, entity_id: str, default: float) -> float:
        """Get numeric value from entity state."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in (STATE_UNAVAILABLE, STATE_UNKNOWN):
            return default
        try:
            return float(state.state)
        except (ValueError, TypeError):
            return default

    def _build_rule_context(self, data: dict) -> dict:
        """Build context dictionary for rule evaluation."""
        return {
            "battery_soc": data.get("battery_soc", 0),
            "solar_power": data.get("solar_power", 0),
            "grid_power": data.get("grid_power", 0),
            "battery_power": data.get("battery_power", 0),
            "heater_power": data.get("heater_power", 0),
            "tank_temp": self.water_tank.state.estimated_temp,
            "daily_heating_minutes": self.water_tank.state.total_heating_today.total_seconds() / 60,
            "offpeak_start": self._get_option(CONF_OFFPEAK_START, DEFAULT_OFFPEAK_START),
            "offpeak_end": self._get_option(CONF_OFFPEAK_END, DEFAULT_OFFPEAK_END),
        }

    def _get_computed_values(self) -> dict:
        """Get computed values from water tank model."""
        time_to_target = self.water_tank.time_to_target()
        time_to_cold = self.water_tank.time_to_cold()

        return {
            "tank_temp_estimate": round(self.water_tank.state.estimated_temp, 1),
            "daily_heating_minutes": round(self.water_tank.state.total_heating_today.total_seconds() / 60, 1),
            "daily_heating_energy_kwh": round(self.water_tank.state.total_energy_today, 2),
            "heating_sessions_today": self.water_tank.state.heating_sessions_today,
            "energy_content_kwh": round(self.water_tank.energy_content(), 2),
            "estimated_showers": self.water_tank.estimated_showers_available(),
            "time_to_target_minutes": round(time_to_target.total_seconds() / 60, 0) if time_to_target else None,
            "time_to_cold_hours": round(time_to_cold.total_seconds() / 3600, 1),
            "heating_mode": self._heating_mode.value,
            "auto_mode_enabled": self._auto_mode_enabled,
            "offpeak_fallback_enabled": self._offpeak_fallback_enabled,
            "current_rule": self.rule_engine.last_triggered_rule,
            "is_heating": self.water_tank.state.is_heating,
        }

    async def _async_set_heater(self, turn_on: bool) -> None:
        """Control the heater switch."""
        heater_entity = self._get_option(CONF_HEATER_SWITCH_ENTITY, None)
        if not heater_entity:
            _LOGGER.warning("No heater switch entity configured")
            return

        service = "turn_on" if turn_on else "turn_off"
        domain = heater_entity.split(".")[0]

        try:
            await self.hass.services.async_call(
                domain,
                service,
                {"entity_id": heater_entity},
                blocking=True,
            )
            _LOGGER.info("Heater %s via rule engine", "turned on" if turn_on else "turned off")
        except Exception as err:
            _LOGGER.error("Failed to control heater: %s", err)

    # Public methods for external control

    async def async_set_auto_mode(self, enabled: bool) -> None:
        """Enable or disable auto mode."""
        self._auto_mode_enabled = enabled
        await self._async_save_state()
        await self.async_refresh()

    async def async_set_offpeak_fallback(self, enabled: bool) -> None:
        """Enable or disable off-peak fallback."""
        self._offpeak_fallback_enabled = enabled
        self.rule_engine.enable_rule("offpeak_fallback") if enabled else self.rule_engine.disable_rule("offpeak_fallback")
        await self._async_save_state()
        await self.async_refresh()

    async def async_force_heating(self, duration_minutes: int = 60) -> None:
        """Force heating for specified duration."""
        self._heating_mode = HeatingMode.FORCED
        await self._async_set_heater(True)
        await self._async_save_state()
        await self.async_refresh()

    async def async_stop_heating(self) -> None:
        """Stop heating immediately."""
        await self._async_set_heater(False)
        self._heating_mode = HeatingMode.AUTO if self._auto_mode_enabled else HeatingMode.OFF
        await self.async_refresh()

    async def async_set_tank_temperature(self, temperature: float) -> None:
        """Manually set tank temperature estimate (for calibration)."""
        self.water_tank.set_temperature(temperature)
        await self._async_save_state()
        await self.async_refresh()

    async def async_apply_usage_event(self, event_name: str) -> None:
        """Apply a water usage event (shower, dishes, etc.)."""
        self.water_tank.apply_usage_event(event_name)
        await self._async_save_state()
        await self.async_refresh()

    def get_temperature_forecast(self, hours: int = 24) -> list[dict]:
        """Get temperature forecast for the next N hours."""
        return self.water_tank.get_forecast(hours)
