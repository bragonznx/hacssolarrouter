"""Water tank temperature estimation model."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from homeassistant.util import dt as dt_util

from .const import (
    DEFAULT_AMBIENT_TEMP,
    DEFAULT_COLD_WATER_TEMP,
    DEFAULT_DISH_DURATION,
    DEFAULT_DISH_FLOW_RATE,
    DEFAULT_HEATER_WATTAGE,
    DEFAULT_MIN_TEMP,
    DEFAULT_SHOWER_DURATION,
    DEFAULT_SHOWER_FLOW_RATE,
    DEFAULT_TANK_HEAT_LOSS_RATE,
    DEFAULT_TANK_VOLUME,
    DEFAULT_TARGET_TEMP,
)

if TYPE_CHECKING:
    from .coordinator import SolarRouterCoordinator

_LOGGER = logging.getLogger(__name__)

# Physical constants
WATER_SPECIFIC_HEAT = 4186  # J/(kg·°C)
WATER_DENSITY = 1  # kg/L


@dataclass
class WaterUsageEvent:
    """Represents a water usage event."""

    name: str
    duration_minutes: float
    flow_rate_lpm: float
    hot_water_fraction: float = 0.7  # 70% hot water typically

    @property
    def volume_liters(self) -> float:
        """Calculate total volume used."""
        return self.duration_minutes * self.flow_rate_lpm * self.hot_water_fraction


@dataclass
class TankState:
    """Current state of the water tank."""

    estimated_temp: float = DEFAULT_TARGET_TEMP
    last_update: datetime = field(default_factory=dt_util.utcnow)
    last_heating_start: datetime | None = None
    last_heating_end: datetime | None = None
    total_heating_today: timedelta = field(default_factory=lambda: timedelta(0))
    total_energy_today: float = 0.0  # kWh
    heating_sessions_today: int = 0
    is_heating: bool = False


class WaterTankModel:
    """Model for water tank temperature estimation."""

    def __init__(
        self,
        volume_liters: float = DEFAULT_TANK_VOLUME,
        heater_wattage: float = DEFAULT_HEATER_WATTAGE,
        heat_loss_rate: float = DEFAULT_TANK_HEAT_LOSS_RATE,
        cold_water_temp: float = DEFAULT_COLD_WATER_TEMP,
        target_temp: float = DEFAULT_TARGET_TEMP,
        min_temp: float = DEFAULT_MIN_TEMP,
        ambient_temp: float = DEFAULT_AMBIENT_TEMP,
    ) -> None:
        """Initialize the water tank model."""
        self.volume_liters = volume_liters
        self.heater_wattage = heater_wattage
        self.heat_loss_rate = heat_loss_rate  # °C/hour
        self.cold_water_temp = cold_water_temp
        self.target_temp = target_temp
        self.min_temp = min_temp
        self.ambient_temp = ambient_temp
        self.state = TankState()

        # Define standard usage events
        self.usage_events = {
            "shower": WaterUsageEvent(
                name="Shower",
                duration_minutes=DEFAULT_SHOWER_DURATION,
                flow_rate_lpm=DEFAULT_SHOWER_FLOW_RATE,
            ),
            "dishes": WaterUsageEvent(
                name="Dishes",
                duration_minutes=DEFAULT_DISH_DURATION,
                flow_rate_lpm=DEFAULT_DISH_FLOW_RATE,
            ),
        }

    @property
    def tank_thermal_mass(self) -> float:
        """Calculate thermal mass of water in tank (J/°C)."""
        return self.volume_liters * WATER_DENSITY * WATER_SPECIFIC_HEAT

    @property
    def heating_rate(self) -> float:
        """Calculate temperature increase rate when heating (°C/second)."""
        return self.heater_wattage / self.tank_thermal_mass

    @property
    def heating_rate_per_minute(self) -> float:
        """Calculate temperature increase rate when heating (°C/minute)."""
        return self.heating_rate * 60

    @property
    def heating_rate_per_hour(self) -> float:
        """Calculate temperature increase rate when heating (°C/hour)."""
        return self.heating_rate * 3600

    def calculate_heat_loss(self, hours: float) -> float:
        """Calculate temperature drop due to heat loss over time."""
        # Simple linear model - could be enhanced with exponential decay
        temp_diff = self.state.estimated_temp - self.ambient_temp
        if temp_diff <= 0:
            return 0
        # Heat loss is proportional to temperature difference
        return self.heat_loss_rate * hours * (temp_diff / (DEFAULT_TARGET_TEMP - DEFAULT_AMBIENT_TEMP))

    def calculate_usage_temp_drop(self, event: WaterUsageEvent) -> float:
        """Calculate temperature drop from water usage event."""
        hot_water_used = event.volume_liters
        if hot_water_used >= self.volume_liters:
            # Tank completely replaced
            return self.state.estimated_temp - self.cold_water_temp

        # Mix calculation
        remaining_volume = self.volume_liters - hot_water_used
        new_temp = (
            (remaining_volume * self.state.estimated_temp)
            + (hot_water_used * self.cold_water_temp)
        ) / self.volume_liters

        return self.state.estimated_temp - new_temp

    def update_temperature(
        self,
        is_heating: bool,
        elapsed_seconds: float,
    ) -> float:
        """Update estimated temperature based on heating state and time."""
        now = dt_util.utcnow()
        hours_elapsed = elapsed_seconds / 3600

        if is_heating:
            # Temperature increases from heating
            temp_increase = self.heating_rate * elapsed_seconds

            # Account for heat loss even while heating
            temp_loss = self.calculate_heat_loss(hours_elapsed)

            new_temp = self.state.estimated_temp + temp_increase - temp_loss

            # Cap at target temperature (thermostat effect)
            new_temp = min(new_temp, self.target_temp)

            # Track heating time
            if not self.state.is_heating:
                self.state.last_heating_start = now
                self.state.heating_sessions_today += 1

            self.state.total_heating_today += timedelta(seconds=elapsed_seconds)
            self.state.total_energy_today += (self.heater_wattage * elapsed_seconds) / 3600000  # kWh

        else:
            # Only heat loss when not heating
            temp_loss = self.calculate_heat_loss(hours_elapsed)
            new_temp = self.state.estimated_temp - temp_loss

            # Can't go below cold water temp
            new_temp = max(new_temp, self.cold_water_temp)

            if self.state.is_heating:
                self.state.last_heating_end = now

        self.state.estimated_temp = new_temp
        self.state.is_heating = is_heating
        self.state.last_update = now

        return new_temp

    def apply_usage_event(self, event_name: str) -> float:
        """Apply a water usage event and return new temperature."""
        if event_name not in self.usage_events:
            _LOGGER.warning("Unknown usage event: %s", event_name)
            return self.state.estimated_temp

        event = self.usage_events[event_name]
        temp_drop = self.calculate_usage_temp_drop(event)
        self.state.estimated_temp -= temp_drop

        _LOGGER.debug(
            "Applied %s event: temperature dropped by %.1f°C to %.1f°C",
            event_name,
            temp_drop,
            self.state.estimated_temp,
        )

        return self.state.estimated_temp

    def time_to_target(self) -> timedelta | None:
        """Calculate time needed to reach target temperature."""
        if self.state.estimated_temp >= self.target_temp:
            return timedelta(0)

        temp_needed = self.target_temp - self.state.estimated_temp

        # Account for heat loss during heating
        # This is a simplified calculation
        net_heating_rate = self.heating_rate_per_hour - (self.heat_loss_rate / 2)
        if net_heating_rate <= 0:
            return None  # Can't reach target

        hours_needed = temp_needed / net_heating_rate
        return timedelta(hours=hours_needed)

    def time_to_cold(self) -> timedelta:
        """Calculate time until tank reaches minimum usable temperature (no heating)."""
        if self.state.estimated_temp <= self.min_temp:
            return timedelta(0)

        temp_to_lose = self.state.estimated_temp - self.min_temp
        hours = temp_to_lose / self.heat_loss_rate

        return timedelta(hours=hours)

    def estimated_showers_available(self) -> float:
        """Estimate number of showers available at current temperature."""
        if self.state.estimated_temp <= self.min_temp:
            return 0

        shower = self.usage_events["shower"]

        # Calculate how many showers until we hit min temp
        current_temp = self.state.estimated_temp
        showers = 0

        while current_temp > self.min_temp:
            # Simulate a shower
            hot_water_used = shower.volume_liters
            remaining_volume = self.volume_liters - hot_water_used

            new_temp = (
                (remaining_volume * current_temp)
                + (hot_water_used * self.cold_water_temp)
            ) / self.volume_liters

            if new_temp < self.min_temp:
                # Partial shower possible
                showers += (current_temp - self.min_temp) / (current_temp - new_temp)
                break

            current_temp = new_temp
            showers += 1

        return round(showers, 1)

    def energy_content(self) -> float:
        """Calculate energy content of tank above cold water temp (kWh)."""
        temp_diff = self.state.estimated_temp - self.cold_water_temp
        if temp_diff <= 0:
            return 0

        energy_joules = self.tank_thermal_mass * temp_diff
        return energy_joules / 3600000  # Convert to kWh

    def reset_daily_stats(self) -> None:
        """Reset daily statistics (should be called at midnight)."""
        self.state.total_heating_today = timedelta(0)
        self.state.total_energy_today = 0.0
        self.state.heating_sessions_today = 0

    def set_temperature(self, temp: float) -> None:
        """Manually set the estimated temperature (for calibration)."""
        self.state.estimated_temp = max(
            self.cold_water_temp,
            min(temp, self.target_temp + 10),  # Allow some overshoot
        )
        self.state.last_update = dt_util.utcnow()

    def get_forecast(self, hours_ahead: int = 24) -> list[dict]:
        """Generate temperature forecast for the next N hours."""
        forecast = []
        current_temp = self.state.estimated_temp
        current_time = dt_util.now()

        for hour in range(hours_ahead + 1):
            # Simple forecast assuming no heating and daily usage pattern
            temp = current_temp

            # Apply heat loss
            temp -= self.heat_loss_rate * hour

            # Simulate typical daily usage (morning and evening)
            forecast_time = current_time + timedelta(hours=hour)
            hour_of_day = forecast_time.hour

            # Morning shower around 7-8 AM
            if hour_of_day == 7:
                temp -= self.calculate_usage_temp_drop(self.usage_events["shower"])

            # Evening dishes around 7-8 PM
            if hour_of_day == 19:
                temp -= self.calculate_usage_temp_drop(self.usage_events["dishes"])

            temp = max(temp, self.cold_water_temp)

            forecast.append({
                "time": forecast_time.isoformat(),
                "temperature": round(temp, 1),
                "hour": hour,
            })

        return forecast

    def to_dict(self) -> dict:
        """Serialize state to dictionary."""
        return {
            "estimated_temp": self.state.estimated_temp,
            "last_update": self.state.last_update.isoformat() if self.state.last_update else None,
            "last_heating_start": self.state.last_heating_start.isoformat() if self.state.last_heating_start else None,
            "last_heating_end": self.state.last_heating_end.isoformat() if self.state.last_heating_end else None,
            "total_heating_today_seconds": self.state.total_heating_today.total_seconds(),
            "total_energy_today": self.state.total_energy_today,
            "heating_sessions_today": self.state.heating_sessions_today,
            "is_heating": self.state.is_heating,
        }

    def from_dict(self, data: dict) -> None:
        """Restore state from dictionary."""
        if not data:
            return

        self.state.estimated_temp = data.get("estimated_temp", DEFAULT_TARGET_TEMP)

        if data.get("last_update"):
            self.state.last_update = datetime.fromisoformat(data["last_update"])

        if data.get("last_heating_start"):
            self.state.last_heating_start = datetime.fromisoformat(data["last_heating_start"])

        if data.get("last_heating_end"):
            self.state.last_heating_end = datetime.fromisoformat(data["last_heating_end"])

        self.state.total_heating_today = timedelta(
            seconds=data.get("total_heating_today_seconds", 0)
        )
        self.state.total_energy_today = data.get("total_energy_today", 0.0)
        self.state.heating_sessions_today = data.get("heating_sessions_today", 0)
        self.state.is_heating = data.get("is_heating", False)
