"""Binary sensor platform for Solar Router integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_MIN_DAILY_HEATING_TIME,
    DEFAULT_MIN_SOC,
    DEFAULT_MIN_SOLAR_POWER,
    DOMAIN,
    NUMBER_MIN_DAILY_HEATING,
    NUMBER_MIN_SOC,
    NUMBER_MIN_SOLAR_POWER,
)
from .coordinator import SolarRouterCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarRouterBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Describes Solar Router binary sensor entity."""

    value_fn: Callable[[dict[str, Any], dict[str, Any]], bool]


def _get_option(entry: ConfigEntry, key: str, default: Any) -> Any:
    """Get option from entry."""
    return entry.options.get(key, entry.data.get(key, default))


BINARY_SENSOR_DESCRIPTIONS: tuple[SolarRouterBinarySensorEntityDescription, ...] = (
    SolarRouterBinarySensorEntityDescription(
        key="heater_should_run",
        translation_key="heater_should_run",
        name="Heater Should Run",
        device_class=BinarySensorDeviceClass.RUNNING,
        icon="mdi:water-boiler",
        value_fn=lambda data, opts: data.get("should_heat", False),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="is_heating",
        translation_key="is_heating",
        name="Currently Heating",
        device_class=BinarySensorDeviceClass.HEAT,
        icon="mdi:fire",
        value_fn=lambda data, opts: data.get("is_heating", False),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="solar_sufficient",
        translation_key="solar_sufficient",
        name="Solar Power Sufficient",
        device_class=BinarySensorDeviceClass.POWER,
        icon="mdi:solar-power",
        value_fn=lambda data, opts: data.get("solar_power", 0) >= opts.get(NUMBER_MIN_SOLAR_POWER, DEFAULT_MIN_SOLAR_POWER),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="battery_sufficient",
        translation_key="battery_sufficient",
        name="Battery Level Sufficient",
        device_class=BinarySensorDeviceClass.BATTERY,
        icon="mdi:battery-check",
        value_fn=lambda data, opts: data.get("battery_soc", 0) >= opts.get(NUMBER_MIN_SOC, DEFAULT_MIN_SOC),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="fallback_needed",
        translation_key="fallback_needed",
        name="Fallback Heating Needed",
        device_class=BinarySensorDeviceClass.PROBLEM,
        icon="mdi:alert-circle",
        value_fn=lambda data, opts: data.get("daily_heating_minutes", 0) < opts.get(NUMBER_MIN_DAILY_HEATING, DEFAULT_MIN_DAILY_HEATING_TIME),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="auto_mode_active",
        translation_key="auto_mode_active",
        name="Auto Mode Active",
        icon="mdi:robot",
        value_fn=lambda data, opts: data.get("auto_mode_enabled", False),
    ),
    SolarRouterBinarySensorEntityDescription(
        key="tank_cold",
        translation_key="tank_cold",
        name="Tank Temperature Low",
        device_class=BinarySensorDeviceClass.COLD,
        icon="mdi:snowflake-thermometer",
        value_fn=lambda data, opts: data.get("tank_temp_estimate", 50) < 40,
    ),
    SolarRouterBinarySensorEntityDescription(
        key="tank_hot",
        translation_key="tank_hot",
        name="Tank Temperature OK",
        device_class=BinarySensorDeviceClass.HEAT,
        icon="mdi:thermometer-check",
        value_fn=lambda data, opts: data.get("tank_temp_estimate", 0) >= 50,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Router binary sensors based on a config entry."""
    coordinator: SolarRouterCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        SolarRouterBinarySensor(coordinator, description, entry)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SolarRouterBinarySensor(
    CoordinatorEntity[SolarRouterCoordinator], BinarySensorEntity
):
    """Representation of a Solar Router binary sensor."""

    entity_description: SolarRouterBinarySensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        description: SolarRouterBinarySensorEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Solar Router",
            "model": "Water Heater Router",
            "sw_version": "1.0.0",
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return None

        options = {**self._entry.data, **self._entry.options}
        return self.entity_description.value_fn(self.coordinator.data, options)
