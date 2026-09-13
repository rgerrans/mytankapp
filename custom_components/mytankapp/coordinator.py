"""Polling coordinator for MyTankApp."""

from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MyTankAppAuthError, MyTankAppClient, MyTankAppError
from .const import CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL, DOMAIN
from .models import MyTankAppTank

_LOGGER = logging.getLogger(__name__)


class MyTankAppCoordinator(DataUpdateCoordinator[dict[str, MyTankAppTank]]):
    """Fetch all tank data in one request."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        client: MyTankAppClient,
    ) -> None:
        self.client = client
        interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval),
            always_update=False,
        )

    async def _async_update_data(self) -> dict[str, MyTankAppTank]:
        try:
            return await self.client.async_get_tanks()
        except MyTankAppAuthError as err:
            raise ConfigEntryAuthFailed from err
        except MyTankAppError as err:
            raise UpdateFailed(str(err)) from err
