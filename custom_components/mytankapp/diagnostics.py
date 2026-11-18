"""Diagnostics support for MyTankApp."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MyTankAppConfigEntry
from .api import MyTankAppError

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
    history: list[dict[str, Any]] = []
    for index, tank in enumerate(runtime.coordinator.data.values(), start=1):
        if not tank.is_propane:
            continue
        item: dict[str, Any] = {"tank": f"tank_{index}"}
        try:
            readings = await runtime.client.async_get_recent_readings(tank.device_id)
        except MyTankAppError as err:
            item["error"] = type(err).__name__
        else:
            filtered = runtime.coordinator.consumption.get(tank.device_id)
            filtered_readings = (
                filtered.filter_history_outliers(
                    readings, tank_size=tank.tank_size
                )
                if filtered is not None
                else readings
            )
            item["raw_reading_count"] = len(readings)
            item["filtered_reading_count"] = len(filtered_readings)
            item["readings"] = [
                {
                    "reported_at": reading.reported_at.isoformat(),
                    "units": reading.units,
                    "percent": reading.percent,
                }
                for reading in readings[:30]
            ]
        history.append(item)

    return async_redact_data(
        {
            "entry": {"data": dict(entry.data), "options": dict(entry.options)},
            "account": {
                "username": runtime.account.username,
                "default_units": runtime.account.default_units,
                "data_source": runtime.account.data_source,
            },
            "tanks": tanks,
            "recent_history": history,
        },
        TO_REDACT,
    )
