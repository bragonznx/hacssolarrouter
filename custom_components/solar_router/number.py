"""Number platform for Solar Router integration."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfPower, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DEFAULT_MIN_DAILY_HEATING_TIME,
    DEFAULT_MIN_SOC,
    DEFAULT_MIN_SOLAR_POWER,
    DEFAULT_TARGET_TEMP,
    DOMAIN,
    NUMBER_MIN_DAILY_HEATING,
    NUMBER_MIN_SOC,
    NUMBER_MIN_SOLAR_POWER,
)
from .coordinator import SolarRouterCoordinator


@dataclass(frozen=True, kw_only=True)
class SolarRouterNumberEntityDescription(NumberEntityDescription):
    """Describes Solar Router number entity."""

    config_key: str
    default_value: float


NUMBER_DESCRIPTIONS: tuple[SolarRouterNumberEntityDescription, ...] = (
    SolarRouterNumberEntityDescription(
        key="min_soc_threshold",
        translation_key="min_soc_threshold",
        name="Minimum Battery SoC",
        icon="mdi:battery-charging-60",
        native_min_value=20,
        native_max_value=95,
        native_step=5,
        native_unit_of_measurement=PERCENTAGE,
        mode=NumberMode.SLIDER,
        config_key=NUMBER_MIN_SOC,
        default_value=DEFAULT_MIN_SOC,
    ),
    SolarRouterNumberEntityDescription(
        key="min_solar_power_threshold",
        translation_key="min_solar_power_threshold",
        name="Minimum Solar Power",
        icon="mdi:solar-power",
        device_class=NumberDeviceClass.POWER,
        native_min_value=100,
        native_max_value=5000,
        native_step=100,
        native_unit_of_measurement=UnitOfPower.WATT,
        mode=NumberMode.SLIDER,
        config_key=NUMBER_MIN_SOLAR_POWER,
        default_value=DEFAULT_MIN_SOLAR_POWER,
    ),
    SolarRouterNumberEntityDescription(
        key="min_daily_heating_threshold",
        translation_key="min_daily_heating_threshold",
        name="Minimum Daily Heating",
        icon="mdi:timer-outline",
        native_min_value=0,
        native_max_value=240,
        native_step=15,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        mode=NumberMode.SLIDER,
        config_key=NUMBER_MIN_DAILY_HEATING,
        default_value=DEFAULT_MIN_DAILY_HEATING_TIME,
    ),
    SolarRouterNumberEntityDescription(
        key="tank_temperature_calibration",
        translation_key="tank_temperature_calibration",
        name="Tank Temperature Calibration",
        icon="mdi:thermometer-water",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_min_value=10,
        native_max_value=70,
        native_step=1,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        mode=NumberMode.BOX,
        config_key="tank_temp_calibration",
        default_value=DEFAULT_TARGET_TEMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Router numbers based on a config entry."""
    coordinator: SolarRouterCoordinator = hass.data[DOMAIN][entry.entry_id]

    async_add_entities(
        SolarRouterNumber(coordinator, description, entry)
        for description in NUMBER_DESCRIPTIONS
    )


class SolarRouterNumber(CoordinatorEntity[SolarRouterCoordinator], NumberEntity):
    """Representation of a Solar Router number entity."""

    entity_description: SolarRouterNumberEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        description: SolarRouterNumberEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
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
    def native_value(self) -> float | None:
        """Return the current value."""
        # Special case for temperature calibration - read from water tank model
        if self.entity_description.key == "tank_temperature_calibration":
            if self.coordinator.data:
                return self.coordinator.data.get("tank_temp_estimate")
            return None

        # For other numbers, read from config
        return self._entry.options.get(
            self.entity_description.config_key,
            self._entry.data.get(
                self.entity_description.config_key,
                self.entity_description.default_value,
            ),
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        # Special case for temperature calibration
        if self.entity_description.key == "tank_temperature_calibration":
            await self.coordinator.async_set_tank_temperature(value)
            return

        # For other numbers, update options
        new_options = dict(self._entry.options)
        new_options[self.entity_description.config_key] = value

        self.hass.config_entries.async_update_entry(
            self._entry,
            options=new_options,
        )
