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
