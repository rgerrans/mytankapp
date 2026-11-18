"""Polling coordinator for MyTankApp."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import logging
from typing import Any

from homeassistant.components.recorder.models import StatisticMeanType, StatisticMetaData
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfVolume
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store
from homeassistant.util import slugify
from homeassistant.util.unit_conversion import VolumeConverter

from .api import MyTankAppAuthError, MyTankAppClient, MyTankAppError
from .const import (
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    HISTORY_REFRESH_INTERVAL_HOURS,
)
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
        self.last_successful_sync: datetime | None = None
        self.consumption: dict[str, MyTankAppConsumption] = {}
        self._store: Store[dict[str, dict[str, Any]]] = Store(
            hass, 1, f"{DOMAIN}.{entry.entry_id}.consumption"
        )
        self._normal_update_interval = timedelta(
            minutes=entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=self._normal_update_interval,
            # A successful sync timestamp must be published even when the tank
            # payload is identical to the previous poll.
            always_update=True,
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
            # DNS, timeout, rate-limit, and 5xx errors are transient. Do not
            # shorten the interval or trigger another login attempt.
            raise UpdateFailed(str(err)) from err

        changed = False
        now = datetime.now(timezone.utc)
        refresh_history_for: list[str] = []
        for device_id, tank in tanks.items():
            if not tank.is_propane:
                continue
            consumption = self.consumption.setdefault(
                device_id, MyTankAppConsumption()
            )
            history_refresh_due = (
                consumption.history_refreshed_at is None
                or now - consumption.history_refreshed_at
                >= timedelta(hours=HISTORY_REFRESH_INTERVAL_HOURS)
            )
            if (
                history_refresh_due
                or not consumption.statistics_initialized
                or not consumption.estimated_initialized
                or consumption.flow_rate_per_hour is None
                or consumption.usage_calculated_at is None
                or (
                    tank.last_reported is not None
                    and (
                        consumption.usage_calculated_at is None
                        or tank.last_reported > consumption.usage_calculated_at
                    )
                )
            ):
                refresh_history_for.append(device_id)

        for device_id in refresh_history_for:
            tank = tanks[device_id]
            consumption = self.consumption[device_id]
            try:
                readings = await self.client.async_get_recent_readings(device_id)
            except MyTankAppAuthError as err:
                raise ConfigEntryAuthFailed from err
            except MyTankAppError as err:
                _LOGGER.warning(
                    "Unable to update usage history for tank ending in %s: %s",
                    device_id[-4:],
                    err,
                )
            else:
                filtered_readings = consumption.filter_history_outliers(
                    readings, tank_size=tank.tank_size
                )
                changed |= consumption.update_from_readings(
                    filtered_readings,
                    tank_size=tank.tank_size,
                    uses_liters=self.account.uses_liters,
                )
                changed |= consumption.update_flow_rate(
                    filtered_readings, tank_size=tank.tank_size
                )
                changed |= consumption.update_rolling_usage(
                    filtered_readings, tank_size=tank.tank_size
                )

                statistics = consumption.build_external_statistics(
                    filtered_readings,
                    tank_size=tank.tank_size,
                    uses_liters=self.account.uses_liters,
                )
                estimated_statistics = (
                    consumption.build_estimated_external_statistics(
                        readings,
                        tank_size=tank.tank_size,
                        uses_liters=self.account.uses_liters,
                    )
                )
                consumption.history_refreshed_at = now
                changed = True

                if statistics:
                    metadata: StatisticMetaData = {
                        "source": DOMAIN,
                        "name": f"{tank.display_name} propane consumption",
                        "statistic_id": (
                            f"{DOMAIN}:{slugify(device_id)}_propane_consumption"
                        ),
                        "unit_class": VolumeConverter.UNIT_CLASS,
                        "unit_of_measurement": UnitOfVolume.LITERS,
                        "mean_type": StatisticMeanType.NONE,
                        "has_sum": True,
                    }
                    async_add_external_statistics(
                        self.hass, metadata, statistics
                    )
                    changed = True

                if estimated_statistics:
                    estimated_metadata: StatisticMetaData = {
                        "source": DOMAIN,
                        "name": (
                            f"{tank.display_name} estimated propane consumption"
                        ),
                        "statistic_id": (
                            f"{DOMAIN}:{slugify(device_id)}"
                            "_estimated_propane_consumption"
                        ),
                        "unit_class": VolumeConverter.UNIT_CLASS,
                        "unit_of_measurement": UnitOfVolume.LITERS,
                        "mean_type": StatisticMeanType.NONE,
                        "has_sum": True,
                    }
                    async_add_external_statistics(
                        self.hass,
                        estimated_metadata,
                        estimated_statistics,
                    )
                    changed = True

        # Apply the current device-list inventory after history as a fallback
        # when the transaction endpoint is unavailable or lags behind.
        for device_id, tank in tanks.items():
            if not tank.is_propane:
                continue
            changed |= self.consumption[device_id].update(
                tank, uses_liters=self.account.uses_liters
            )

        if changed:
            await self._store.async_save(
                {
                    device_id: consumption.as_dict()
                    for device_id, consumption in self.consumption.items()
                }
            )
        self.last_successful_sync = now
        return tanks
