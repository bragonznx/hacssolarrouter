"""Config flow for Solar Router integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_AMBIENT_TEMP,
    CONF_BATTERY_POWER_ENTITY,
    CONF_BATTERY_SOC_ENTITY,
    CONF_COLD_WATER_TEMP,
    CONF_DISH_DURATION,
    CONF_DISH_FLOW_RATE,
    CONF_FALLBACK_CHECK_TIME,
    CONF_GRID_POWER_ENTITY,
    CONF_HEATER_POWER_ENTITY,
    CONF_HEATER_SWITCH_ENTITY,
    CONF_HEATER_WATTAGE,
    CONF_MIN_TEMP,
    CONF_OFFPEAK_END,
    CONF_OFFPEAK_START,
    CONF_SHOWER_DURATION,
    CONF_SHOWER_FLOW_RATE,
    CONF_SOLAR_END,
    CONF_SOLAR_POWER_ENTITY,
    CONF_SOLAR_START,
    CONF_TANK_HEAT_LOSS_RATE,
    CONF_TANK_VOLUME,
    CONF_TARGET_TEMP,
    DEFAULT_AMBIENT_TEMP,
    DEFAULT_COLD_WATER_TEMP,
    DEFAULT_DISH_DURATION,
    DEFAULT_DISH_FLOW_RATE,
    DEFAULT_FALLBACK_CHECK_TIME,
    DEFAULT_HEATER_WATTAGE,
    DEFAULT_MIN_DAILY_HEATING_TIME,
    DEFAULT_MIN_SOC,
    DEFAULT_MIN_SOLAR_POWER,
    DEFAULT_MIN_TEMP,
    DEFAULT_OFFPEAK_END,
    DEFAULT_OFFPEAK_START,
    DEFAULT_SHOWER_DURATION,
    DEFAULT_SHOWER_FLOW_RATE,
    DEFAULT_SOLAR_END,
    DEFAULT_SOLAR_START,
    DEFAULT_TANK_HEAT_LOSS_RATE,
    DEFAULT_TANK_VOLUME,
    DEFAULT_TARGET_TEMP,
    DOMAIN,
    NUMBER_MIN_DAILY_HEATING,
    NUMBER_MIN_SOC,
    NUMBER_MIN_SOLAR_POWER,
)

_LOGGER = logging.getLogger(__name__)


def get_entity_selector(domain: str | list[str]) -> selector.EntitySelector:
    """Get an entity selector for the given domain(s)."""
    if isinstance(domain, str):
        domain = [domain]
    return selector.EntitySelector(
        selector.EntitySelectorConfig(domain=domain)
    )


def get_number_selector(
    min_val: float,
    max_val: float,
    step: float = 1,
    unit: str | None = None,
    mode: str = "box",
) -> selector.NumberSelector:
    """Get a number selector."""
    return selector.NumberSelector(
        selector.NumberSelectorConfig(
            min=min_val,
            max=max_val,
            step=step,
            unit_of_measurement=unit,
            mode=selector.NumberSelectorMode(mode),
        )
    )


def get_time_selector() -> selector.TimeSelector:
    """Get a time selector."""
    return selector.TimeSelector()


class SolarRouterConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Solar Router."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._data: dict[str, Any] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step - basic setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_entities()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default="Solar Router"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle entity configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_water_tank()

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_BATTERY_SOC_ENTITY): get_entity_selector("sensor"),
                    vol.Required(CONF_SOLAR_POWER_ENTITY): get_entity_selector("sensor"),
                    vol.Optional(CONF_GRID_POWER_ENTITY): get_entity_selector("sensor"),
                    vol.Optional(CONF_BATTERY_POWER_ENTITY): get_entity_selector("sensor"),
                    vol.Required(CONF_HEATER_SWITCH_ENTITY): get_entity_selector(["switch", "input_boolean"]),
                    vol.Optional(CONF_HEATER_POWER_ENTITY): get_entity_selector("sensor"),
                }
            ),
            errors=errors,
            description_placeholders={
                "victron_hint": "Select entities from your Victron integration",
            },
        )

    async def async_step_water_tank(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle water tank configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_thresholds()

        return self.async_show_form(
            step_id="water_tank",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TANK_VOLUME, default=DEFAULT_TANK_VOLUME
                    ): get_number_selector(50, 500, 10, "L"),
                    vol.Required(
                        CONF_HEATER_WATTAGE, default=DEFAULT_HEATER_WATTAGE
                    ): get_number_selector(500, 5000, 100, "W"),
                    vol.Required(
                        CONF_TARGET_TEMP, default=DEFAULT_TARGET_TEMP
                    ): get_number_selector(40, 70, 1, "°C"),
                    vol.Required(
                        CONF_MIN_TEMP, default=DEFAULT_MIN_TEMP
                    ): get_number_selector(30, 50, 1, "°C"),
                    vol.Optional(
                        CONF_TANK_HEAT_LOSS_RATE, default=DEFAULT_TANK_HEAT_LOSS_RATE
                    ): get_number_selector(0.1, 2.0, 0.1, "°C/h"),
                    vol.Optional(
                        CONF_COLD_WATER_TEMP, default=DEFAULT_COLD_WATER_TEMP
                    ): get_number_selector(5, 25, 1, "°C"),
                    vol.Optional(
                        CONF_AMBIENT_TEMP, default=DEFAULT_AMBIENT_TEMP
                    ): get_number_selector(10, 30, 1, "°C"),
                }
            ),
            errors=errors,
        )

    async def async_step_thresholds(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle threshold configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_time_windows()

        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        NUMBER_MIN_SOC, default=DEFAULT_MIN_SOC
                    ): get_number_selector(30, 95, 5, "%"),
                    vol.Required(
                        NUMBER_MIN_SOLAR_POWER, default=DEFAULT_MIN_SOLAR_POWER
                    ): get_number_selector(500, 5000, 100, "W"),
                    vol.Required(
                        NUMBER_MIN_DAILY_HEATING, default=DEFAULT_MIN_DAILY_HEATING_TIME
                    ): get_number_selector(0, 240, 15, "min"),
                }
            ),
            errors=errors,
        )

    async def async_step_time_windows(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle time window configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_usage_patterns()

        return self.async_show_form(
            step_id="time_windows",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SOLAR_START, default=DEFAULT_SOLAR_START
                    ): get_time_selector(),
                    vol.Required(
                        CONF_SOLAR_END, default=DEFAULT_SOLAR_END
                    ): get_time_selector(),
                    vol.Required(
                        CONF_FALLBACK_CHECK_TIME, default=DEFAULT_FALLBACK_CHECK_TIME
                    ): get_time_selector(),
                    vol.Required(
                        CONF_OFFPEAK_START, default=DEFAULT_OFFPEAK_START
                    ): get_time_selector(),
                    vol.Required(
                        CONF_OFFPEAK_END, default=DEFAULT_OFFPEAK_END
                    ): get_time_selector(),
                }
            ),
            errors=errors,
        )

    async def async_step_usage_patterns(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle usage patterns configuration step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            # Create the config entry
            return self.async_create_entry(
                title=self._data.get(CONF_NAME, "Solar Router"),
                data=self._data,
            )

        return self.async_show_form(
            step_id="usage_patterns",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SHOWER_DURATION, default=DEFAULT_SHOWER_DURATION
                    ): get_number_selector(5, 30, 1, "min"),
                    vol.Optional(
                        CONF_SHOWER_FLOW_RATE, default=DEFAULT_SHOWER_FLOW_RATE
                    ): get_number_selector(5, 15, 1, "L/min"),
                    vol.Optional(
                        CONF_DISH_DURATION, default=DEFAULT_DISH_DURATION
                    ): get_number_selector(5, 30, 1, "min"),
                    vol.Optional(
                        CONF_DISH_FLOW_RATE, default=DEFAULT_DISH_FLOW_RATE
                    ): get_number_selector(3, 10, 1, "L/min"),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> SolarRouterOptionsFlow:
        """Get the options flow for this handler."""
        return SolarRouterOptionsFlow(config_entry)


class SolarRouterOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Solar Router."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry
        self._data: dict[str, Any] = dict(config_entry.options)

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options - show menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["entities", "water_tank", "thresholds", "time_windows", "usage_patterns"],
        )

    async def async_step_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle entity options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="entities",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BATTERY_SOC_ENTITY,
                        default=current.get(CONF_BATTERY_SOC_ENTITY),
                    ): get_entity_selector("sensor"),
                    vol.Required(
                        CONF_SOLAR_POWER_ENTITY,
                        default=current.get(CONF_SOLAR_POWER_ENTITY),
                    ): get_entity_selector("sensor"),
                    vol.Optional(
                        CONF_GRID_POWER_ENTITY,
                        default=current.get(CONF_GRID_POWER_ENTITY),
                    ): get_entity_selector("sensor"),
                    vol.Optional(
                        CONF_BATTERY_POWER_ENTITY,
                        default=current.get(CONF_BATTERY_POWER_ENTITY),
                    ): get_entity_selector("sensor"),
                    vol.Required(
                        CONF_HEATER_SWITCH_ENTITY,
                        default=current.get(CONF_HEATER_SWITCH_ENTITY),
                    ): get_entity_selector(["switch", "input_boolean"]),
                    vol.Optional(
                        CONF_HEATER_POWER_ENTITY,
                        default=current.get(CONF_HEATER_POWER_ENTITY),
                    ): get_entity_selector("sensor"),
                }
            ),
        )

    async def async_step_water_tank(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle water tank options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="water_tank",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_TANK_VOLUME,
                        default=current.get(CONF_TANK_VOLUME, DEFAULT_TANK_VOLUME),
                    ): get_number_selector(50, 500, 10, "L"),
                    vol.Required(
                        CONF_HEATER_WATTAGE,
                        default=current.get(CONF_HEATER_WATTAGE, DEFAULT_HEATER_WATTAGE),
                    ): get_number_selector(500, 5000, 100, "W"),
                    vol.Required(
                        CONF_TARGET_TEMP,
                        default=current.get(CONF_TARGET_TEMP, DEFAULT_TARGET_TEMP),
                    ): get_number_selector(40, 70, 1, "°C"),
                    vol.Required(
                        CONF_MIN_TEMP,
                        default=current.get(CONF_MIN_TEMP, DEFAULT_MIN_TEMP),
                    ): get_number_selector(30, 50, 1, "°C"),
                    vol.Optional(
                        CONF_TANK_HEAT_LOSS_RATE,
                        default=current.get(CONF_TANK_HEAT_LOSS_RATE, DEFAULT_TANK_HEAT_LOSS_RATE),
                    ): get_number_selector(0.1, 2.0, 0.1, "°C/h"),
                    vol.Optional(
                        CONF_COLD_WATER_TEMP,
                        default=current.get(CONF_COLD_WATER_TEMP, DEFAULT_COLD_WATER_TEMP),
                    ): get_number_selector(5, 25, 1, "°C"),
                    vol.Optional(
                        CONF_AMBIENT_TEMP,
                        default=current.get(CONF_AMBIENT_TEMP, DEFAULT_AMBIENT_TEMP),
                    ): get_number_selector(10, 30, 1, "°C"),
                }
            ),
        )

    async def async_step_thresholds(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle threshold options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="thresholds",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        NUMBER_MIN_SOC,
                        default=current.get(NUMBER_MIN_SOC, DEFAULT_MIN_SOC),
                    ): get_number_selector(30, 95, 5, "%"),
                    vol.Required(
                        NUMBER_MIN_SOLAR_POWER,
                        default=current.get(NUMBER_MIN_SOLAR_POWER, DEFAULT_MIN_SOLAR_POWER),
                    ): get_number_selector(500, 5000, 100, "W"),
                    vol.Required(
                        NUMBER_MIN_DAILY_HEATING,
                        default=current.get(NUMBER_MIN_DAILY_HEATING, DEFAULT_MIN_DAILY_HEATING_TIME),
                    ): get_number_selector(0, 240, 15, "min"),
                }
            ),
        )

    async def async_step_time_windows(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle time window options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="time_windows",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SOLAR_START,
                        default=current.get(CONF_SOLAR_START, DEFAULT_SOLAR_START),
                    ): get_time_selector(),
                    vol.Required(
                        CONF_SOLAR_END,
                        default=current.get(CONF_SOLAR_END, DEFAULT_SOLAR_END),
                    ): get_time_selector(),
                    vol.Required(
                        CONF_FALLBACK_CHECK_TIME,
                        default=current.get(CONF_FALLBACK_CHECK_TIME, DEFAULT_FALLBACK_CHECK_TIME),
                    ): get_time_selector(),
                    vol.Required(
                        CONF_OFFPEAK_START,
                        default=current.get(CONF_OFFPEAK_START, DEFAULT_OFFPEAK_START),
                    ): get_time_selector(),
                    vol.Required(
                        CONF_OFFPEAK_END,
                        default=current.get(CONF_OFFPEAK_END, DEFAULT_OFFPEAK_END),
                    ): get_time_selector(),
                }
            ),
        )

    async def async_step_usage_patterns(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle usage pattern options."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)

        current = {**self.config_entry.data, **self.config_entry.options}

        return self.async_show_form(
            step_id="usage_patterns",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SHOWER_DURATION,
                        default=current.get(CONF_SHOWER_DURATION, DEFAULT_SHOWER_DURATION),
                    ): get_number_selector(5, 30, 1, "min"),
                    vol.Optional(
                        CONF_SHOWER_FLOW_RATE,
                        default=current.get(CONF_SHOWER_FLOW_RATE, DEFAULT_SHOWER_FLOW_RATE),
                    ): get_number_selector(5, 15, 1, "L/min"),
                    vol.Optional(
                        CONF_DISH_DURATION,
                        default=current.get(CONF_DISH_DURATION, DEFAULT_DISH_DURATION),
                    ): get_number_selector(5, 30, 1, "min"),
                    vol.Optional(
                        CONF_DISH_FLOW_RATE,
                        default=current.get(CONF_DISH_FLOW_RATE, DEFAULT_DISH_FLOW_RATE),
                    ): get_number_selector(3, 10, 1, "L/min"),
                }
            ),
        )
