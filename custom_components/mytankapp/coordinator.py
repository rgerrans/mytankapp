"""Polling coordinator for MyTankApp."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .api import MyTankAppAuthError, MyTankAppClient, MyTankAppError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import MyTankAppAccount, MyTankAppConsumption, MyTankAppTank

_LOGGER = logging.getLogger(__name__)


class MyTankAppCoordinator(DataUpdateCoordinator[dict[str, MyTankAppTank]]):
    """Fetch all tank data in one request."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MyTankAppClient,
        account: MyTankAppAccount,
    ) -> None:
        self.client = client
        self.account = account
        self.consumption: dict[str, MyTankAppConsumption] = {}
        self._store: Store[dict[str, dict[str, Any]]] = Store(
            hass, 1, f"{DOMAIN}.{entry.entry_id}.consumption"
        )
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    async def async_load_consumption(self) -> None:
        """Load cumulative consumption before the first API refresh."""
        stored = await self._store.async_load()
        if not isinstance(stored, dict):
            return
        self.consumption = {
            device_id: MyTankAppConsumption.from_dict(value)
            for device_id, value in stored.items()
            if isinstance(device_id, str) and isinstance(value, dict)
        }

    async def _async_update_data(self) -> dict[str, MyTankAppTank]:
        try:
            tanks = await self.client.async_get_tanks()
        except MyTankAppAuthError as err:
            raise ConfigEntryAuthFailed from err
        except MyTankAppError as err:
            raise UpdateFailed(str(err)) from err

        changed = False
        for device_id, tank in tanks.items():
            if not tank.is_propane:
                continue
            consumption = self.consumption.setdefault(
                device_id, MyTankAppConsumption()
            )
            changed |= consumption.update(
                tank, uses_liters=self.account.uses_liters
            )
        if changed:
            await self._store.async_save(
                {
                    device_id: consumption.as_dict()
                    for device_id, consumption in self.consumption.items()
                }
            )
        return tanks
