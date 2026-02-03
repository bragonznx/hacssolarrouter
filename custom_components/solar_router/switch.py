"""Switch platform for Solar Router integration."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SolarRouterCoordinator


SWITCH_DESCRIPTIONS: tuple[SwitchEntityDescription, ...] = (
    SwitchEntityDescription(
        key="auto_mode",
        translation_key="auto_mode",
        name="Auto Mode",
        icon="mdi:robot",
    ),
    SwitchEntityDescription(
        key="offpeak_fallback",
        translation_key="offpeak_fallback",
        name="Off-Peak Fallback",
        icon="mdi:clock-alert",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Solar Router switches based on a config entry."""
    coordinator: SolarRouterCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SwitchEntity] = [
        SolarRouterAutoModeSwitch(coordinator, SWITCH_DESCRIPTIONS[0], entry),
        SolarRouterOffpeakFallbackSwitch(coordinator, SWITCH_DESCRIPTIONS[1], entry),
        SolarRouterForceHeatingSwitch(coordinator, entry),
    ]

    async_add_entities(entities)


class SolarRouterAutoModeSwitch(
    CoordinatorEntity[SolarRouterCoordinator], SwitchEntity
):
    """Switch to enable/disable auto mode."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        description: SwitchEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
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
    def is_on(self) -> bool:
        """Return true if auto mode is enabled."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("auto_mode_enabled", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on auto mode."""
        await self.coordinator.async_set_auto_mode(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off auto mode."""
        await self.coordinator.async_set_auto_mode(False)


class SolarRouterOffpeakFallbackSwitch(
    CoordinatorEntity[SolarRouterCoordinator], SwitchEntity
):
    """Switch to enable/disable off-peak fallback."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        description: SwitchEntityDescription,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
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
    def is_on(self) -> bool:
        """Return true if off-peak fallback is enabled."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("offpeak_fallback_enabled", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on off-peak fallback."""
        await self.coordinator.async_set_offpeak_fallback(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off off-peak fallback."""
        await self.coordinator.async_set_offpeak_fallback(False)


class SolarRouterForceHeatingSwitch(
    CoordinatorEntity[SolarRouterCoordinator], SwitchEntity
):
    """Switch to force heating on/off manually."""

    _attr_has_entity_name = True
    _attr_name = "Force Heating"
    _attr_icon = "mdi:fire"

    def __init__(
        self,
        coordinator: SolarRouterCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_force_heating"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Solar Router",
            "model": "Water Heater Router",
            "sw_version": "1.0.0",
        }

    @property
    def is_on(self) -> bool:
        """Return true if currently in forced heating mode."""
        if self.coordinator.data is None:
            return False
        return self.coordinator.data.get("heating_mode") == "forced"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Force heating on."""
        await self.coordinator.async_force_heating()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Stop forced heating."""
        await self.coordinator.async_stop_heating()
