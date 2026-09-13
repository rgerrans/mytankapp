"""Data models for MyTankApp."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _text(value: Any) -> str | None:
    if value is None:
        return None
    result = str(value).strip()
    return result or None


def _float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _datetime(value: Any) -> datetime | None:
    text = _text(value)
    if text is None or text.startswith("0001-01-01"):
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class MyTankAppAccount:
    """Metadata needed to normalize account data."""

    username: str
    display_name: str | None
    default_units: str
    data_source: str | None

    @property
    def uses_liters(self) -> bool:
        """Return whether the account displays metric volume."""
        return self.default_units.casefold() == "liters"

    @property
    def average_usage_is_volume(self) -> bool:
        """Return whether the web client converts average usage to volume."""
        return (self.data_source or "").strip().casefold() == "itank"


@dataclass(frozen=True)
class MyTankAppTank:
    """Normalized tank status."""

    device_id: str
    user_device_id: str | None
    name: str | None
    description: str | None
    fuel_type: str | None
    tank_size: float | None
    inventory: float | None
    ullage: float | None
    level: float | None
    average_daily_usage: float | None
    last_reported: datetime | None
    temperature: float | None
    base_temperature: float | None

    @classmethod
    def from_api(cls, data: dict[str, Any]) -> MyTankAppTank | None:
        """Create a tank from an API response object."""
        device_id = _text(data.get("DeviceID"))
        if device_id is None:
            return None

        temperature = _float(data.get("Temp"))
        if temperature is not None and temperature < -40:
            temperature = None
        base_temperature = _float(data.get("BaseTemp"))
        if base_temperature is not None and base_temperature < -40:
            base_temperature = None

        return cls(
            device_id=device_id,
            user_device_id=_text(data.get("UserDeviceID")),
            name=_text(data.get("Name")),
            description=_text(data.get("Description")),
            fuel_type=_text(data.get("FuelType")),
            tank_size=_float(data.get("TankSize")),
            inventory=_float(data.get("Inventory")),
            ullage=_float(data.get("Ullage")),
            level=_float(data.get("LastReportedPercent")),
            average_daily_usage=_float(data.get("AverageDailyUsage")),
            last_reported=_datetime(data.get("LastReported")),
            temperature=temperature,
            base_temperature=base_temperature,
        )

    def days_until(self, level: float) -> int | None:
        """Estimate whole days until a percentage threshold."""
        if (
            self.level is None
            or self.average_daily_usage is None
            or self.average_daily_usage <= 0
            or self.level < level
        ):
            return None
        return int(((self.level - level) / self.average_daily_usage) + 0.5)

    @property
    def display_name(self) -> str:
        """Return the best non-empty name for the tank."""
        return self.description or self.name or f"Tank {self.device_id[-4:]}"

    @property
    def is_propane(self) -> bool:
        """Return whether the tank contains propane/LPG."""
        fuel_type = (self.fuel_type or "").casefold()
        return "propane" in fuel_type or fuel_type in {"lp", "lpg", "lp gas"}


PROPANE_KWH_PER_GALLON = 91_452 / 3_412
LITERS_PER_GALLON = 3.785411784


@dataclass
class MyTankAppConsumption:
    """Persisted cumulative propane consumption for one tank."""

    total_kwh: float = 0.0
    last_inventory: float | None = None
    last_reported: datetime | None = None

    def update(self, tank: MyTankAppTank, *, uses_liters: bool) -> bool:
        """Apply a new tank reading and return whether stored data changed."""
        current = tank.inventory
        if current is None:
            return False
        if (
            tank.last_reported is not None
            and tank.last_reported == self.last_reported
        ):
            return False

        if self.last_inventory is None:
            self.last_inventory = current
            self.last_reported = tank.last_reported
            return True

        previous = self.last_inventory
        refill_threshold = max(2.0, (tank.tank_size or 0) * 0.02)
        increase = current - previous

        if increase >= refill_threshold:
            # A delivery starts a new consumption baseline; it is not usage.
            self.last_inventory = current
        elif current < previous:
            consumed = previous - current
            gallons = consumed / LITERS_PER_GALLON if uses_liters else consumed
            self.total_kwh += gallons * PROPANE_KWH_PER_GALLON
            self.last_inventory = current
        # Ignore small increases as gauge/temperature noise. Keeping the lower
        # baseline prevents that noise from being counted again on the next dip.
        self.last_reported = tank.last_reported
        return True

    def as_dict(self) -> dict[str, Any]:
        """Serialize state for Home Assistant storage."""
        return {
            "total_kwh": self.total_kwh,
            "last_inventory": self.last_inventory,
            "last_reported": (
                self.last_reported.isoformat() if self.last_reported else None
            ),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MyTankAppConsumption:
        """Restore state from Home Assistant storage."""
        return cls(
            total_kwh=_float(data.get("total_kwh")) or 0.0,
            last_inventory=_float(data.get("last_inventory")),
            last_reported=_datetime(data.get("last_reported")),
        )
