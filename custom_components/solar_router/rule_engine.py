"""Rule engine for solar router decisions."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time
from typing import TYPE_CHECKING, Any

from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_MIN_DAILY_HEATING_TIME,
    DEFAULT_MIN_SOC,
    DEFAULT_MIN_SOLAR_POWER,
    DEFAULT_OFFPEAK_END,
    DEFAULT_OFFPEAK_START,
    DEFAULT_SOLAR_END,
    DEFAULT_SOLAR_START,
    RuleActionType,
    RuleConditionType,
)

if TYPE_CHECKING:
    from .coordinator import SolarRouterCoordinator
    from .water_tank import WaterTankModel

_LOGGER = logging.getLogger(__name__)


@dataclass
class RuleCondition:
    """A condition that must be met for a rule to trigger."""

    condition_type: RuleConditionType
    value: Any
    value2: Any | None = None  # For range conditions like TIME_BETWEEN

    def evaluate(self, context: dict) -> bool:
        """Evaluate if this condition is met."""
        try:
            if self.condition_type == RuleConditionType.BATTERY_SOC_ABOVE:
                return context.get("battery_soc", 0) >= self.value

            elif self.condition_type == RuleConditionType.BATTERY_SOC_BELOW:
                return context.get("battery_soc", 100) <= self.value

            elif self.condition_type == RuleConditionType.SOLAR_POWER_ABOVE:
                return context.get("solar_power", 0) >= self.value

            elif self.condition_type == RuleConditionType.SOLAR_POWER_BELOW:
                return context.get("solar_power", float("inf")) <= self.value

            elif self.condition_type == RuleConditionType.GRID_EXPORT_ABOVE:
                grid_power = context.get("grid_power", 0)
                # Negative grid power = export
                return grid_power < 0 and abs(grid_power) >= self.value

            elif self.condition_type == RuleConditionType.GRID_IMPORT_ABOVE:
                grid_power = context.get("grid_power", 0)
                # Positive grid power = import
                return grid_power > 0 and grid_power >= self.value

            elif self.condition_type == RuleConditionType.TANK_TEMP_ABOVE:
                return context.get("tank_temp", 0) >= self.value

            elif self.condition_type == RuleConditionType.TANK_TEMP_BELOW:
                return context.get("tank_temp", 100) <= self.value

            elif self.condition_type == RuleConditionType.TIME_BETWEEN:
                now = dt_util.now().time()
                start = self._parse_time(self.value)
                end = self._parse_time(self.value2)
                return self._time_in_range(now, start, end)

            elif self.condition_type == RuleConditionType.DAILY_HEATING_BELOW:
                heating_minutes = context.get("daily_heating_minutes", 0)
                return heating_minutes < self.value

            elif self.condition_type == RuleConditionType.DAILY_HEATING_ABOVE:
                heating_minutes = context.get("daily_heating_minutes", 0)
                return heating_minutes >= self.value

            elif self.condition_type == RuleConditionType.OFFPEAK_HOURS:
                now = dt_util.now().time()
                start = self._parse_time(context.get("offpeak_start", DEFAULT_OFFPEAK_START))
                end = self._parse_time(context.get("offpeak_end", DEFAULT_OFFPEAK_END))
                return self._time_in_range(now, start, end)

            else:
                _LOGGER.warning("Unknown condition type: %s", self.condition_type)
                return False

        except (ValueError, TypeError) as e:
            _LOGGER.error("Error evaluating condition %s: %s", self.condition_type, e)
            return False

    @staticmethod
    def _parse_time(time_str: str | time) -> time:
        """Parse time string to time object."""
        if isinstance(time_str, time):
            return time_str
        parts = time_str.split(":")
        return time(int(parts[0]), int(parts[1]))

    @staticmethod
    def _time_in_range(check_time: time, start: time, end: time) -> bool:
        """Check if time is in range, handling overnight ranges."""
        if start <= end:
            return start <= check_time <= end
        else:
            # Overnight range (e.g., 22:00 to 06:00)
            return check_time >= start or check_time <= end


@dataclass
class RuleAction:
    """An action to take when a rule triggers."""

    action_type: RuleActionType
    value: Any | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "action_type": self.action_type.value,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RuleAction":
        """Create from dictionary."""
        return cls(
            action_type=RuleActionType(data["action_type"]),
            value=data.get("value"),
        )


@dataclass
class Rule:
    """A routing rule with conditions and actions."""

    name: str
    conditions: list[RuleCondition]
    actions: list[RuleAction]
    enabled: bool = True
    priority: int = 50  # 0-100, higher = more important
    description: str = ""

    def evaluate(self, context: dict) -> bool:
        """Check if all conditions are met."""
        if not self.enabled:
            return False
        return all(condition.evaluate(context) for condition in self.conditions)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "conditions": [
                {
                    "condition_type": c.condition_type.value,
                    "value": c.value,
                    "value2": c.value2,
                }
                for c in self.conditions
            ],
            "actions": [a.to_dict() for a in self.actions],
            "enabled": self.enabled,
            "priority": self.priority,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Rule":
        """Create rule from dictionary."""
        return cls(
            name=data["name"],
            conditions=[
                RuleCondition(
                    condition_type=RuleConditionType(c["condition_type"]),
                    value=c["value"],
                    value2=c.get("value2"),
                )
                for c in data.get("conditions", [])
            ],
            actions=[RuleAction.from_dict(a) for a in data.get("actions", [])],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 50),
            description=data.get("description", ""),
        )


class RuleEngine:
    """Engine for evaluating and executing routing rules."""

    def __init__(self) -> None:
        """Initialize the rule engine."""
        self.rules: list[Rule] = []
        self._last_triggered_rule: str | None = None
        self._create_default_rules()

    def _create_default_rules(self) -> None:
        """Create default routing rules."""
        # Rule 1: Solar excess routing
        self.rules.append(
            Rule(
                name="solar_excess",
                description="Route solar excess to water heater when battery is charged",
                conditions=[
                    RuleCondition(RuleConditionType.BATTERY_SOC_ABOVE, DEFAULT_MIN_SOC),
                    RuleCondition(RuleConditionType.SOLAR_POWER_ABOVE, DEFAULT_MIN_SOLAR_POWER),
                    RuleCondition(RuleConditionType.TIME_BETWEEN, DEFAULT_SOLAR_START, DEFAULT_SOLAR_END),
                    RuleCondition(RuleConditionType.TANK_TEMP_BELOW, 55),
                ],
                actions=[RuleAction(RuleActionType.TURN_ON_HEATER)],
                priority=80,
            )
        )

        # Rule 2: Grid export routing (feed excess to heater instead of grid)
        self.rules.append(
            Rule(
                name="grid_export_divert",
                description="Divert grid export to water heater",
                conditions=[
                    RuleCondition(RuleConditionType.GRID_EXPORT_ABOVE, 1000),
                    RuleCondition(RuleConditionType.BATTERY_SOC_ABOVE, 50),
                    RuleCondition(RuleConditionType.TANK_TEMP_BELOW, 55),
                ],
                actions=[RuleAction(RuleActionType.TURN_ON_HEATER)],
                priority=70,
            )
        )

        # Rule 3: Off-peak fallback
        self.rules.append(
            Rule(
                name="offpeak_fallback",
                description="Heat during off-peak if daily minimum not met",
                conditions=[
                    RuleCondition(RuleConditionType.OFFPEAK_HOURS, True),
                    RuleCondition(RuleConditionType.DAILY_HEATING_BELOW, DEFAULT_MIN_DAILY_HEATING_TIME),
                    RuleCondition(RuleConditionType.TANK_TEMP_BELOW, 50),
                ],
                actions=[RuleAction(RuleActionType.TURN_ON_HEATER)],
                priority=60,
            )
        )

        # Rule 4: Emergency heating (tank too cold)
        self.rules.append(
            Rule(
                name="emergency_heating",
                description="Emergency heating when tank is too cold",
                conditions=[
                    RuleCondition(RuleConditionType.TANK_TEMP_BELOW, 35),
                ],
                actions=[RuleAction(RuleActionType.TURN_ON_HEATER)],
                priority=100,
            )
        )

        # Rule 5: Stop when tank is hot enough
        self.rules.append(
            Rule(
                name="tank_full",
                description="Stop heating when tank reaches target",
                conditions=[
                    RuleCondition(RuleConditionType.TANK_TEMP_ABOVE, 55),
                ],
                actions=[RuleAction(RuleActionType.TURN_OFF_HEATER)],
                priority=90,
            )
        )

        # Rule 6: Battery protection
        self.rules.append(
            Rule(
                name="battery_protection",
                description="Stop heating when battery is low",
                conditions=[
                    RuleCondition(RuleConditionType.BATTERY_SOC_BELOW, 40),
                    RuleCondition(RuleConditionType.SOLAR_POWER_BELOW, 500),
                ],
                actions=[RuleAction(RuleActionType.TURN_OFF_HEATER)],
                priority=95,
            )
        )

    def add_rule(self, rule: Rule) -> None:
        """Add a rule to the engine."""
        # Remove existing rule with same name
        self.rules = [r for r in self.rules if r.name != rule.name]
        self.rules.append(rule)
        self._sort_rules()

    def remove_rule(self, name: str) -> bool:
        """Remove a rule by name."""
        initial_count = len(self.rules)
        self.rules = [r for r in self.rules if r.name != name]
        return len(self.rules) < initial_count

    def enable_rule(self, name: str) -> bool:
        """Enable a rule by name."""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = True
                return True
        return False

    def disable_rule(self, name: str) -> bool:
        """Disable a rule by name."""
        for rule in self.rules:
            if rule.name == name:
                rule.enabled = False
                return True
        return False

    def get_rule(self, name: str) -> Rule | None:
        """Get a rule by name."""
        for rule in self.rules:
            if rule.name == name:
                return rule
        return None

    def _sort_rules(self) -> None:
        """Sort rules by priority (highest first)."""
        self.rules.sort(key=lambda r: r.priority, reverse=True)

    def evaluate(self, context: dict) -> tuple[list[RuleAction], list[str]]:
        """
        Evaluate all rules and return actions to take.

        Returns:
            Tuple of (actions to execute, list of triggered rule names)
        """
        triggered_rules: list[str] = []
        actions: list[RuleAction] = []

        self._sort_rules()

        for rule in self.rules:
            if rule.evaluate(context):
                _LOGGER.debug("Rule '%s' triggered", rule.name)
                triggered_rules.append(rule.name)
                actions.extend(rule.actions)

                # For conflicting actions, higher priority wins
                # We process in priority order, so first match wins
                break

        if triggered_rules:
            self._last_triggered_rule = triggered_rules[0]
        else:
            self._last_triggered_rule = None

        return actions, triggered_rules

    def should_heat(self, context: dict) -> tuple[bool, str | None]:
        """
        Determine if heater should be on based on rules.

        Returns:
            Tuple of (should_heat, triggered_rule_name)
        """
        actions, triggered_rules = self.evaluate(context)

        for action in actions:
            if action.action_type == RuleActionType.TURN_ON_HEATER:
                return True, triggered_rules[0] if triggered_rules else None
            elif action.action_type == RuleActionType.TURN_OFF_HEATER:
                return False, triggered_rules[0] if triggered_rules else None

        # No explicit action, maintain current state (default off for safety)
        return False, None

    @property
    def last_triggered_rule(self) -> str | None:
        """Get the name of the last triggered rule."""
        return self._last_triggered_rule

    def to_dict(self) -> list[dict]:
        """Convert all rules to dictionary for storage."""
        return [rule.to_dict() for rule in self.rules]

    def from_dict(self, data: list[dict]) -> None:
        """Load rules from dictionary."""
        self.rules = [Rule.from_dict(r) for r in data]
        self._sort_rules()
