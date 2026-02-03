"""Sensor platform for Solar Router integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarRouterCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarRouterSensorEntityDescription(SensorEntityDescription):
    """Describes Solar Router sensor entity."""

    value_fn: Callable[[dict[str, Any]], Any] | None = None
    attr_fn: Callable[[SolarRouterCoordinator], dict[str, Any]] | None = None


SENSOR_DESCRIPTIONS: tuple[SolarRouterSensorEntityDescription, ...] = (
    SolarRouterSensorEntityDescription(
        key="tank_temp_estimate",
        translation_key="tank_temp_estimate",
        name="Tank Temperature (Estimated)",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-thermometer",
        value_fn=lambda data: data.get("tank_temp_estimate"),
    ),
    SolarRouterSensorEntityDescription(
        key="daily_heating_time",
        translation_key="daily_heating_time",
        name="Daily Heating Time",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:clock-outline",
        value_fn=lambda data: data.get("daily_heating_minutes"),
    ),
    SolarRouterSensorEntityDescription(
        key="daily_heating_energy",
        translation_key="daily_heating_energy",
        name="Daily Heating Energy",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
        value_fn=lambda data: data.get("daily_heating_energy_kwh"),
    ),
    SolarRouterSensorEntityDescription(
        key="energy_content",
        translation_key="energy_content",
        name="Tank Energy Content",
        device_class=SensorDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:water-boiler",
        value_fn=lambda data: data.get("energy_content_kwh"),
    ),
    SolarRouterSensorEntityDescription(
        key="estimated_showers",
        translation_key="estimated_showers",
        name="Estimated Showers Available",
        native_unit_of_measurement="showers",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:shower-head",
        value_fn=lambda data: data.get("estimated_showers"),
    ),
    SolarRouterSensorEntityDescription(
        key="time_to_target",
        translation_key="time_to_target",
        name="Time to Target Temperature",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        icon="mdi:timer-outline",
        value_fn=lambda data: data.get("time_to_target_minutes"),
    ),
    SolarRouterSensorEntityDescription(
        key="time_to_cold",
        translation_key="time_to_cold",
        name="Time Until Cold",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        icon="mdi:timer-sand",
        value_fn=lambda data: data.get("time_to_cold_hours"),
    ),
    SolarRouterSensorEntityDescription(
        key="current_rule",
        translation_key="current_rule",
        name="Active Rule",
        icon="mdi:state-machine",
        value_fn=lambda data: data.get("current_rule") or "none",
    ),
    SolarRouterSensorEntityDescription(
        key="heating_mode",
        translation_key="heating_mode",
        name="Heating Mode",
        icon="mdi:water-boiler",
        value_fn=lambda data: data.get("heating_mode"),
    ),
    SolarRouterSensorEntityDescription(
        key="heating_sessions_today",
        translation_key="heating_sessions_today",
        name="Heating Sessions Today",
        native_unit_of_measurement="sessions",
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:counter",
        value_fn=lambda data: data.get("heating_sessions_today"),
    ),
    SolarRouterSensorEntityDescription(
        key="solar_excess",
        translation_key="solar_excess",
        name="Solar Excess Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
        value_fn=lambda data: max(0, data.get("solar_power", 0) - data.get("heater_power", 0)),
    ),
    SolarRouterSensorEntityDescription(
        key="battery_soc_mirror",
        translation_key="battery_soc",
        name="Battery SoC",
        device_class=SensorDeviceClass.BATTERY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
        value_fn=lambda data: data.get("battery_soc"),
    ),
    SolarRouterSensorEntityDescription(
        key="solar_power_mirror",
        translation_key="solar_power",
        name="Solar Power",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.WATT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-panel",
        value_fn=lambda data: data.get("solar_power"),
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Router sensors based on a config entry."""
    coordinator: SolarRouterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        SolarRouterSensor(coordinator, description, entry)
        for description in SENSOR_DESCRIPTIONS
    ]

    # Add forecast sensor
    entities.append(SolarRouterForecastSensor(coordinator, entry))

    async_add_entities(entities)


class SolarRouterSensor(CoordinatorEntity[SolarRouterCoordinator], SensorEntity):
    """Representation of a Solar Router sensor."""

    entity_description: SolarRouterSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        description: SolarRouterSensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Solar Router",
            "model": "Water Heater Router",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        if self.entity_description.value_fn:
            return self.entity_description.value_fn(self.coordinator.data)
        return self.coordinator.data.get(self.entity_description.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return extra state attributes."""
        if self.entity_description.attr_fn:
            return self.entity_description.attr_fn(self.coordinator)
        return None


class SolarRouterForecastSensor(CoordinatorEntity[SolarRouterCoordinator], SensorEntity):
    """Sensor that provides temperature forecast data."""

    _attr_has_entity_name = True
    _attr_name = "Temperature Forecast"
    _attr_icon = "mdi:chart-line"

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the forecast sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_temperature_forecast"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Solar Router",
            "model": "Water Heater Router",
            "sw_version": "1.0.0",
        }

    @property
    def native_value(self) -> str:
        """Return the current state."""
        if self.coordinator.data:
            return f"{self.coordinator.data.get('tank_temp_estimate', 0):.1f}°C"
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return forecast data as attributes."""
        forecast = self.coordinator.get_temperature_forecast(24)
        return {
            "forecast": forecast,
            "forecast_hours": 24,
            "unit_of_measurement": "°C",
        }
