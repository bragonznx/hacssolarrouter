"""Services for Solar Router integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv

from .const import (
    DOMAIN,
    SERVICE_APPLY_USAGE,
    SERVICE_DISABLE_RULE,
    SERVICE_ENABLE_RULE,
    SERVICE_FORCE_HEATING,
    SERVICE_REMOVE_RULE,
    SERVICE_RESET_DAILY_STATS,
    SERVICE_SET_RULE,
    SERVICE_SET_TANK_TEMP,
    SERVICE_STOP_HEATING,
)
from .coordinator import SolarRouterCoordinator
from .rule_engine import Rule, RuleAction, RuleActionType, RuleCondition, RuleConditionType

_LOGGER = logging.getLogger(__name__)

# Service names
SERVICE_APPLY_USAGE = "apply_usage_event"

# Service schemas
SERVICE_FORCE_HEATING_SCHEMA = vol.Schema(
    {
        vol.Optional("duration", default=60): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=480)
        ),
    }
)

SERVICE_SET_TANK_TEMP_SCHEMA = vol.Schema(
    {
        vol.Required("temperature"): vol.All(
            vol.Coerce(float), vol.Range(min=10, max=80)
        ),
    }
)

SERVICE_APPLY_USAGE_SCHEMA = vol.Schema(
    {
        vol.Required("event"): vol.In(["shower", "dishes"]),
    }
)

SERVICE_RULE_NAME_SCHEMA = vol.Schema(
    {
        vol.Required("rule_name"): cv.string,
    }
)

SERVICE_SET_RULE_SCHEMA = vol.Schema(
    {
        vol.Required("name"): cv.string,
        vol.Optional("description", default=""): cv.string,
        vol.Optional("enabled", default=True): cv.boolean,
        vol.Optional("priority", default=50): vol.All(
            vol.Coerce(int), vol.Range(min=0, max=100)
        ),
        vol.Required("conditions"): vol.All(
            cv.ensure_list,
            [
                vol.Schema(
                    {
                        vol.Required("type"): vol.In([e.value for e in RuleConditionType]),
                        vol.Required("value"): vol.Any(int, float, str),
                        vol.Optional("value2"): vol.Any(int, float, str, None),
                    }
                )
            ],
        ),
        vol.Required("action"): vol.In(["turn_on", "turn_off"]),
    }
)


def _get_coordinator(hass: HomeAssistant) -> SolarRouterCoordinator | None:
    """Get the first available coordinator."""
    if DOMAIN not in hass.data:
        return None
    for entry_id, coordinator in hass.data[DOMAIN].items():
        if isinstance(coordinator, SolarRouterCoordinator):
            return coordinator
    return None


async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up services for Solar Router integration."""

    async def async_handle_force_heating(call: ServiceCall) -> None:
        """Handle force heating service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        duration = call.data.get("duration", 60)
        await coordinator.async_force_heating(duration)
        _LOGGER.info("Forced heating for %d minutes", duration)

    async def async_handle_stop_heating(call: ServiceCall) -> None:
        """Handle stop heating service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        await coordinator.async_stop_heating()
        _LOGGER.info("Stopped heating")

    async def async_handle_set_tank_temp(call: ServiceCall) -> None:
        """Handle set tank temperature service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        temperature = call.data["temperature"]
        await coordinator.async_set_tank_temperature(temperature)
        _LOGGER.info("Set tank temperature to %.1f°C", temperature)

    async def async_handle_apply_usage(call: ServiceCall) -> None:
        """Handle apply usage event service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        event = call.data["event"]
        await coordinator.async_apply_usage_event(event)
        _LOGGER.info("Applied usage event: %s", event)

    async def async_handle_reset_daily_stats(call: ServiceCall) -> None:
        """Handle reset daily stats service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        coordinator.water_tank.reset_daily_stats()
        await coordinator.async_refresh()
        _LOGGER.info("Reset daily statistics")

    async def async_handle_enable_rule(call: ServiceCall) -> None:
        """Handle enable rule service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        rule_name = call.data["rule_name"]
        if coordinator.rule_engine.enable_rule(rule_name):
            _LOGGER.info("Enabled rule: %s", rule_name)
        else:
            _LOGGER.warning("Rule not found: %s", rule_name)

    async def async_handle_disable_rule(call: ServiceCall) -> None:
        """Handle disable rule service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        rule_name = call.data["rule_name"]
        if coordinator.rule_engine.disable_rule(rule_name):
            _LOGGER.info("Disabled rule: %s", rule_name)
        else:
            _LOGGER.warning("Rule not found: %s", rule_name)

    async def async_handle_remove_rule(call: ServiceCall) -> None:
        """Handle remove rule service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        rule_name = call.data["rule_name"]
        if coordinator.rule_engine.remove_rule(rule_name):
            _LOGGER.info("Removed rule: %s", rule_name)
        else:
            _LOGGER.warning("Rule not found: %s", rule_name)

    async def async_handle_set_rule(call: ServiceCall) -> None:
        """Handle set rule service call."""
        coordinator = _get_coordinator(hass)
        if coordinator is None:
            _LOGGER.error("No Solar Router coordinator found")
            return

        # Build conditions
        conditions = []
        for cond_data in call.data["conditions"]:
            conditions.append(
                RuleCondition(
                    condition_type=RuleConditionType(cond_data["type"]),
                    value=cond_data["value"],
                    value2=cond_data.get("value2"),
                )
            )

        # Build action
        action_type = (
            RuleActionType.TURN_ON_HEATER
            if call.data["action"] == "turn_on"
            else RuleActionType.TURN_OFF_HEATER
        )
        actions = [RuleAction(action_type=action_type)]

        # Create and add rule
        rule = Rule(
            name=call.data["name"],
            description=call.data.get("description", ""),
            conditions=conditions,
            actions=actions,
            enabled=call.data.get("enabled", True),
            priority=call.data.get("priority", 50),
        )

        coordinator.rule_engine.add_rule(rule)
        _LOGGER.info("Added/updated rule: %s", rule.name)

    # Register services
    hass.services.async_register(
        DOMAIN,
        SERVICE_FORCE_HEATING,
        async_handle_force_heating,
        schema=SERVICE_FORCE_HEATING_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_HEATING,
        async_handle_stop_heating,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_TANK_TEMP,
        async_handle_set_tank_temp,
        schema=SERVICE_SET_TANK_TEMP_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_USAGE,
        async_handle_apply_usage,
        schema=SERVICE_APPLY_USAGE_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RESET_DAILY_STATS,
        async_handle_reset_daily_stats,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_ENABLE_RULE,
        async_handle_enable_rule,
        schema=SERVICE_RULE_NAME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DISABLE_RULE,
        async_handle_disable_rule,
        schema=SERVICE_RULE_NAME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE_RULE,
        async_handle_remove_rule,
        schema=SERVICE_RULE_NAME_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_RULE,
        async_handle_set_rule,
        schema=SERVICE_SET_RULE_SCHEMA,
    )


async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload Solar Router services."""
    services = [
        SERVICE_FORCE_HEATING,
        SERVICE_STOP_HEATING,
        SERVICE_SET_TANK_TEMP,
        SERVICE_APPLY_USAGE,
        SERVICE_RESET_DAILY_STATS,
        SERVICE_ENABLE_RULE,
        SERVICE_DISABLE_RULE,
        SERVICE_REMOVE_RULE,
        SERVICE_SET_RULE,
    ]

    for service in services:
        hass.services.async_remove(DOMAIN, service)
