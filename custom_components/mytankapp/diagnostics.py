"""Diagnostics support for MyTankApp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MyTankAppConfigEntry

TO_REDACT = {
    "password",
    "username",
    "device_id",
    "user_device_id",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: MyTankAppConfigEntry
) -> dict[str, Any]:
    """Return privacy-safe diagnostics."""
    runtime = entry.runtime_data
    tanks = [
        {
            "device_id": tank.device_id,
            "user_device_id": tank.user_device_id,
            "fuel_type": tank.fuel_type,
            "tank_size": tank.tank_size,
            "inventory": tank.inventory,
            "ullage": tank.ullage,
            "level": tank.level,
            "average_daily_usage": tank.average_daily_usage,
            "last_reported": (
                tank.last_reported.isoformat() if tank.last_reported else None
            ),
            "temperature": tank.temperature,
            "base_temperature": tank.base_temperature,
        }
        for tank in runtime.coordinator.data.values()
    ]
    return async_redact_data(
        {
            "entry": {"data": dict(entry.data), "options": dict(entry.options)},
            "account": {
                "username": runtime.account.username,
                "default_units": runtime.account.default_units,
                "data_source": runtime.account.data_source,
            },
            "tanks": tanks,
        },
        TO_REDACT,
    )
