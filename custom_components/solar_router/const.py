"""Constants for the Solar Router integration."""
from enum import Enum
from typing import Final

DOMAIN: Final = "solar_router"
PLATFORMS: Final = ["sensor", "switch", "binary_sensor", "number"]

# Configuration keys
CONF_BATTERY_SOC_ENTITY: Final = "battery_soc_entity"
CONF_SOLAR_POWER_ENTITY: Final = "solar_power_entity"
CONF_GRID_POWER_ENTITY: Final = "grid_power_entity"
CONF_BATTERY_POWER_ENTITY: Final = "battery_power_entity"
CONF_HEATER_SWITCH_ENTITY: Final = "heater_switch_entity"
CONF_HEATER_POWER_ENTITY: Final = "heater_power_entity"

# Water tank configuration
CONF_TANK_VOLUME: Final = "tank_volume"
CONF_HEATER_WATTAGE: Final = "heater_wattage"
CONF_TANK_HEAT_LOSS_RATE: Final = "tank_heat_loss_rate"
CONF_SHOWER_DURATION: Final = "shower_duration"
CONF_SHOWER_FLOW_RATE: Final = "shower_flow_rate"
CONF_DISH_DURATION: Final = "dish_duration"
CONF_DISH_FLOW_RATE: Final = "dish_flow_rate"
CONF_COLD_WATER_TEMP: Final = "cold_water_temp"
CONF_TARGET_TEMP: Final = "target_temp"
CONF_MIN_TEMP: Final = "min_temp"
CONF_AMBIENT_TEMP: Final = "ambient_temp"

# Rule configuration
CONF_RULES: Final = "rules"
CONF_RULE_NAME: Final = "name"
CONF_RULE_ENABLED: Final = "enabled"
CONF_RULE_PRIORITY: Final = "priority"
CONF_RULE_CONDITIONS: Final = "conditions"
CONF_RULE_ACTIONS: Final = "actions"

# Threshold defaults
DEFAULT_MIN_SOC: Final = 70
DEFAULT_STOP_SOC: Final = 50
DEFAULT_MIN_SOLAR_POWER: Final = 2500
DEFAULT_CHECK_INTERVAL: Final = 60  # seconds
DEFAULT_MIN_DAILY_HEATING_TIME: Final = 60  # minutes
DEFAULT_MAX_DAILY_HEATING_TIME: Final = 180  # minutes

# Water tank defaults
DEFAULT_TANK_VOLUME: Final = 200  # liters
DEFAULT_HEATER_WATTAGE: Final = 2400  # watts
DEFAULT_TANK_HEAT_LOSS_RATE: Final = 0.5  # °C per hour
DEFAULT_SHOWER_DURATION: Final = 10  # minutes
DEFAULT_SHOWER_FLOW_RATE: Final = 10  # liters per minute
DEFAULT_DISH_DURATION: Final = 10  # minutes
DEFAULT_DISH_FLOW_RATE: Final = 6  # liters per minute
DEFAULT_COLD_WATER_TEMP: Final = 15  # °C
DEFAULT_TARGET_TEMP: Final = 55  # °C
DEFAULT_MIN_TEMP: Final = 40  # °C
DEFAULT_AMBIENT_TEMP: Final = 20  # °C

# Off-peak hours (for fallback heating)
CONF_OFFPEAK_START: Final = "offpeak_start"
CONF_OFFPEAK_END: Final = "offpeak_end"
DEFAULT_OFFPEAK_START: Final = "22:00"
DEFAULT_OFFPEAK_END: Final = "06:00"

# Time windows
CONF_SOLAR_START: Final = "solar_start"
CONF_SOLAR_END: Final = "solar_end"
DEFAULT_SOLAR_START: Final = "10:00"
DEFAULT_SOLAR_END: Final = "17:00"


class HeatingMode(Enum):
    """Heating modes."""

    OFF = "off"
    AUTO = "auto"
    SOLAR_ONLY = "solar_only"
    FORCED = "forced"
    OFFPEAK = "offpeak"


class RuleConditionType(Enum):
    """Types of conditions for rules."""

    BATTERY_SOC_ABOVE = "battery_soc_above"
    BATTERY_SOC_BELOW = "battery_soc_below"
    SOLAR_POWER_ABOVE = "solar_power_above"
    SOLAR_POWER_BELOW = "solar_power_below"
    GRID_EXPORT_ABOVE = "grid_export_above"
    GRID_IMPORT_ABOVE = "grid_import_above"
    TANK_TEMP_ABOVE = "tank_temp_above"
    TANK_TEMP_BELOW = "tank_temp_below"
    TIME_BETWEEN = "time_between"
    DAILY_HEATING_BELOW = "daily_heating_below"
    DAILY_HEATING_ABOVE = "daily_heating_above"
    OFFPEAK_HOURS = "offpeak_hours"


class RuleActionType(Enum):
    """Types of actions for rules."""

    TURN_ON_HEATER = "turn_on_heater"
    TURN_OFF_HEATER = "turn_off_heater"
    SET_HEATING_MODE = "set_heating_mode"


# Sensor types
SENSOR_TANK_TEMP_ESTIMATE = "tank_temp_estimate"
SENSOR_DAILY_HEATING_TIME = "daily_heating_time"
SENSOR_DAILY_HEATING_ENERGY = "daily_heating_energy"
SENSOR_CURRENT_RULE = "current_rule"
SENSOR_SOLAR_EXCESS = "solar_excess"
SENSOR_TANK_ENERGY_CONTENT = "tank_energy_content"
SENSOR_ESTIMATED_SHOWERS = "estimated_showers"
SENSOR_TIME_TO_TARGET = "time_to_target"
SENSOR_TIME_TO_COLD = "time_to_cold"

# Binary sensors
BINARY_SENSOR_HEATER_SHOULD_RUN = "heater_should_run"
BINARY_SENSOR_SOLAR_SUFFICIENT = "solar_sufficient"
BINARY_SENSOR_BATTERY_SUFFICIENT = "battery_sufficient"
BINARY_SENSOR_FALLBACK_NEEDED = "fallback_needed"

# Switches
SWITCH_AUTO_MODE = "auto_mode"
SWITCH_OFFPEAK_FALLBACK = "offpeak_fallback"

# Numbers (configurable thresholds)
NUMBER_MIN_SOC = "min_soc"
NUMBER_MIN_SOLAR_POWER = "min_solar_power"
NUMBER_MIN_DAILY_HEATING = "min_daily_heating"

# Attributes
ATTR_LAST_HEATING_START = "last_heating_start"
ATTR_LAST_HEATING_END = "last_heating_end"
ATTR_HEATING_SESSIONS_TODAY = "heating_sessions_today"
ATTR_TRIGGERED_RULES = "triggered_rules"
ATTR_NEXT_SCHEDULED_CHECK = "next_scheduled_check"

# Services
SERVICE_SET_RULE = "set_rule"
SERVICE_REMOVE_RULE = "remove_rule"
SERVICE_ENABLE_RULE = "enable_rule"
SERVICE_DISABLE_RULE = "disable_rule"
SERVICE_FORCE_HEATING = "force_heating"
SERVICE_STOP_HEATING = "stop_heating"
SERVICE_RESET_DAILY_STATS = "reset_daily_stats"
SERVICE_SET_TANK_TEMP = "set_tank_temp"

# Events
EVENT_HEATING_STARTED = f"{DOMAIN}_heating_started"
EVENT_HEATING_STOPPED = f"{DOMAIN}_heating_stopped"
EVENT_RULE_TRIGGERED = f"{DOMAIN}_rule_triggered"
EVENT_FALLBACK_ACTIVATED = f"{DOMAIN}_fallback_activated"
EVENT_DAILY_MINIMUM_REACHED = f"{DOMAIN}_daily_minimum_reached"

# Storage
STORAGE_KEY = DOMAIN
STORAGE_VERSION = 1
