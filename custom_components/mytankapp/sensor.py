"""Sensor entities for MyTankApp."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    EntityCategory,
    UnitOfEnergy,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolume,
    UnitOfVolumeFlowRate,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MyTankAppConfigEntry
from .entity import MyTankAppEntity
from .models import LITERS_PER_GALLON, MyTankAppAccount, MyTankAppTank


@dataclass(frozen=True, kw_only=True)
class MyTankAppSensorDescription(SensorEntityDescription):
    """Describe a MyTankApp sensor."""

    value_fn: Callable[[MyTankAppTank, MyTankAppAccount], Any]


SENSORS: tuple[MyTankAppSensorDescription, ...] = (
    MyTankAppSensorDescription(
        key="level",
        translation_key="level",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda tank, account: tank.level,
    ),
    MyTankAppSensorDescription(
        key="inventory",
        translation_key="inventory",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda tank, account: tank.inventory,
    ),
    MyTankAppSensorDescription(
        key="ullage",
        translation_key="ullage",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda tank, account: tank.ullage,
    ),
    MyTankAppSensorDescription(
        key="capacity",
        translation_key="capacity",
        device_class=SensorDeviceClass.VOLUME_STORAGE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=0,
        value_fn=lambda tank, account: tank.tank_size,
    ),
    MyTankAppSensorDescription(
        key="average_daily_usage",
        translation_key="average_daily_usage",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        suggested_display_precision=1,
        value_fn=lambda tank, account: (
            None
            if tank.average_daily_usage is None
            else tank.average_daily_usage * (tank.tank_size or 0) / 100
            if account.average_usage_is_volume
            else tank.average_daily_usage
        ),
    ),
    MyTankAppSensorDescription(
        key="last_reported",
        translation_key="last_reported",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.last_reported,
    ),
    MyTankAppSensorDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.temperature,
    ),
    MyTankAppSensorDescription(
        key="base_temperature",
        translation_key="base_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.base_temperature,
    ),
    MyTankAppSensorDescription(
        key="days_to_30",
        translation_key="days_to_30",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.days_until(30),
    ),
    MyTankAppSensorDescription(
        key="days_to_15",
        translation_key="days_to_15",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.days_until(15),
    ),
    MyTankAppSensorDescription(
        key="days_to_empty",
        translation_key="days_to_empty",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.DAYS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda tank, account: tank.days_until(0),
    ),
)

CONSUMPTION_DESCRIPTION = SensorEntityDescription(
    key="propane_energy_consumed",
    translation_key="propane_energy_consumed",
    device_class=SensorDeviceClass.ENERGY,
    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    state_class=SensorStateClass.TOTAL_INCREASING,
    suggested_display_precision=2,
)

GAS_CONSUMPTION_DESCRIPTION = SensorEntityDescription(
    key="propane_consumed",
    translation_key="propane_consumed",
    device_class=SensorDeviceClass.VOLUME,
    state_class=SensorStateClass.TOTAL_INCREASING,
    suggested_display_precision=2,
)

ESTIMATED_GAS_CONSUMPTION_DESCRIPTION = SensorEntityDescription(
    key="estimated_propane_consumed",
    translation_key="estimated_propane_consumed",
    device_class=SensorDeviceClass.VOLUME,
    state_class=SensorStateClass.TOTAL_INCREASING,
    suggested_display_precision=2,
)

ESTIMATED_ENERGY_DESCRIPTION = SensorEntityDescription(
    key="estimated_propane_energy_consumed",
    translation_key="estimated_propane_energy_consumed",
    device_class=SensorDeviceClass.ENERGY,
    native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
    state_class=SensorStateClass.TOTAL_INCREASING,
    suggested_display_precision=2,
)

FLOW_RATE_DESCRIPTION = SensorEntityDescription(
    key="propane_flow_rate",
    translation_key="propane_flow_rate",
    device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
)

ESTIMATED_FLOW_RATE_DESCRIPTION = SensorEntityDescription(
    key="estimated_propane_flow_rate",
    translation_key="estimated_propane_flow_rate",
    device_class=SensorDeviceClass.VOLUME_FLOW_RATE,
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=3,
)

DAILY_USAGE_DESCRIPTION = SensorEntityDescription(
    key="propane_daily_usage",
    translation_key="propane_daily_usage",
    state_class=SensorStateClass.MEASUREMENT,
    suggested_display_precision=2,
)

LAST_SUCCESSFUL_SYNC_DESCRIPTION = SensorEntityDescription(
    key="last_successful_sync",
    translation_key="last_successful_sync",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)

LAST_HISTORY_REFRESH_DESCRIPTION = SensorEntityDescription(
    key="last_history_refresh",
    translation_key="last_history_refresh",
    device_class=SensorDeviceClass.TIMESTAMP,
    entity_category=EntityCategory.DIAGNOSTIC,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MyTankAppConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Add sensors for every tank returned during initial setup."""
    coordinator = entry.runtime_data.coordinator
    known_device_ids: set[str] = set()

    @callback
    def add_new_entities() -> None:
        new_device_ids = coordinator.data.keys() - known_device_ids
        if not new_device_ids:
            return
        entities: list[SensorEntity] = [
            MyTankAppSensor(entry, device_id, description)
            for device_id in new_device_ids
            for description in SENSORS
        ]
        entities.extend(
            MyTankAppEnergyConsumedSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppGasConsumedSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppEstimatedGasConsumedSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppEstimatedEnergyConsumedSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppPropaneFlowRateSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppEstimatedPropaneFlowRateSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppCalculatedDailyUsageSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        entities.extend(
            MyTankAppLastSuccessfulSyncSensor(entry, device_id)
            for device_id in new_device_ids
        )
        entities.extend(
            MyTankAppLastHistoryRefreshSensor(entry, device_id)
            for device_id in new_device_ids
            if coordinator.data[device_id].is_propane
        )
        async_add_entities(entities)
        known_device_ids.update(new_device_ids)

    add_new_entities()
    entry.async_on_unload(coordinator.async_add_listener(add_new_entities))


class MyTankAppSensor(MyTankAppEntity, SensorEntity):
    """A sensor backed by the shared tank coordinator."""

    entity_description: MyTankAppSensorDescription

    def __init__(
        self,
        entry: MyTankAppConfigEntry,
        device_id: str,
        description: MyTankAppSensorDescription,
    ) -> None:
        super().__init__(entry, device_id, description.key)
        self.entity_description = description
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        tank = self.tank
        if tank is None:
            return None
        threshold = {
            "days_to_30": 30.0,
            "days_to_15": 15.0,
            "days_to_empty": 0.0,
        }.get(self.entity_description.key)
        if threshold is not None:
            if tank.level is None or tank.level < threshold:
                return None

            consumption = self.coordinator.consumption.get(self._device_id)
            if (
                consumption is not None
                and consumption.rolling_usage_per_day is not None
                and tank.tank_size is not None
                and tank.tank_size > 0
            ):
                current_inventory = tank.tank_size * tank.level / 100
                target_inventory = tank.tank_size * threshold / 100
                return int(
                    (
                        (current_inventory - target_inventory)
                        / consumption.rolling_usage_per_day
                    )
                    + 0.5
                )

            if (
                tank.average_daily_usage is not None
                and tank.average_daily_usage > 0
            ):
                return int(
                    ((tank.level - threshold) / tank.average_daily_usage)
                    + 0.5
                )
            return None

        if (
            self.entity_description.key == "average_daily_usage"
            and self._account.average_usage_is_volume
            and tank.tank_size is None
        ):
            return None
        return self.entity_description.value_fn(tank, self._account)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the account-aware native unit."""
        if self.entity_description.key in {"inventory", "ullage", "capacity"}:
            return (
                UnitOfVolume.LITERS
                if self._account.uses_liters
                else UnitOfVolume.GALLONS
            )
        if self.entity_description.key == "average_daily_usage":
            if not self._account.average_usage_is_volume:
                return f"{PERCENTAGE}/d"
            volume = "L" if self._account.uses_liters else "gal"
            return f"{volume}/d"
        return self.entity_description.native_unit_of_measurement


class MyTankAppEnergyConsumedSensor(MyTankAppEntity, SensorEntity):
    """Cumulative propane energy consumed since this sensor was created."""

    entity_description = CONSUMPTION_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)

    @property
    def native_value(self) -> float | None:
        """Return cumulative consumed propane energy in kWh."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None:
            return None
        return round(consumption.total_kwh, 3)


class MyTankAppGasConsumedSensor(MyTankAppEntity, SensorEntity):
    """Cumulative liquid propane volume consumed."""

    entity_description = GAS_CONSUMPTION_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> float | None:
        """Return cumulative liquid propane volume consumed."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None:
            return None
        value = (
            consumption.total_liters
            if self._account.uses_liters
            else consumption.total_liters / LITERS_PER_GALLON
        )
        return round(value, 3)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the account-aware liquid volume unit."""
        return (
            UnitOfVolume.LITERS
            if self._account.uses_liters
            else UnitOfVolume.GALLONS
        )

    @property
    def suggested_unit_of_measurement(self) -> str:
        """Prefer the account's liquid volume display unit."""
        return self.native_unit_of_measurement


class MyTankAppEstimatedGasConsumedSensor(MyTankAppEntity, SensorEntity):
    """Estimated cumulative liquid propane volume."""

    entity_description = ESTIMATED_GAS_CONSUMPTION_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> float | None:
        """Return estimated cumulative liquid propane volume."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None or not consumption.estimated_initialized:
            return None
        value = (
            consumption.estimated_total_liters
            if self._account.uses_liters
            else consumption.estimated_total_liters / LITERS_PER_GALLON
        )
        return round(value, 3)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the account-aware liquid volume unit."""
        return (
            UnitOfVolume.LITERS
            if self._account.uses_liters
            else UnitOfVolume.GALLONS
        )

    @property
    def suggested_unit_of_measurement(self) -> str:
        """Prefer the account's liquid volume display unit."""
        return self.native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Describe the estimation method and source resolution."""
        tank = self.tank
        if tank is None:
            return {}
        return {
            "method": "linear_interpolation_between_confirmed_level_changes",
            "source_resolution": (
                tank.tank_size / 100
                if tank.tank_size is not None and tank.tank_size > 0
                else None
            ),
            "source_resolution_unit": (
                "L" if self.coordinator.account.uses_liters else "gal"
            ),
        }


class MyTankAppEstimatedEnergyConsumedSensor(MyTankAppEntity, SensorEntity):
    """Estimated cumulative propane energy equivalent."""

    entity_description = ESTIMATED_ENERGY_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)

    @property
    def native_value(self) -> float | None:
        """Return estimated cumulative propane energy in kWh."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None or not consumption.estimated_energy_initialized:
            return None
        return round(consumption.estimated_energy_total_kwh, 3)


class MyTankAppLastSuccessfulSyncSensor(MyTankAppEntity, SensorEntity):
    """Timestamp of the latest successful tank-data refresh."""

    entity_description = LAST_SUCCESSFUL_SYNC_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)

    @property
    def native_value(self) -> Any:
        """Return the latest successful coordinator refresh time."""
        return self.coordinator.last_successful_sync


class MyTankAppLastHistoryRefreshSensor(MyTankAppEntity, SensorEntity):
    """Timestamp of the latest successful history-endpoint refresh."""

    entity_description = LAST_HISTORY_REFRESH_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)

    @property
    def native_value(self) -> Any:
        """Return the latest successful history refresh time."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None:
            return None
        return consumption.history_refreshed_at


class MyTankAppPropaneFlowRateSensor(MyTankAppEntity, SensorEntity):
    """Propane flow rate calculated from consecutive history readings."""

    entity_description = FLOW_RATE_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> float | None:
        """Return average volume used per hour in the latest report interval."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None or consumption.flow_rate_per_hour is None:
            return None
        return round(consumption.flow_rate_per_hour, 3)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the account-aware volume flow-rate unit."""
        return (
            UnitOfVolumeFlowRate.LITERS_PER_HOUR
            if self._account.uses_liters
            else UnitOfVolumeFlowRate.GALLONS_PER_HOUR
        )

    @property
    def suggested_unit_of_measurement(self) -> str:
        """Prefer the account's liquid flow-rate unit."""
        return self.native_unit_of_measurement


class MyTankAppEstimatedPropaneFlowRateSensor(MyTankAppEntity, SensorEntity):
    """Average estimated propane flow over the latest confirmed interval."""

    entity_description = ESTIMATED_FLOW_RATE_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> float | None:
        """Return the estimated average volume used per hour."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None or consumption.estimated_flow_rate_per_hour is None:
            return None
        return round(consumption.estimated_flow_rate_per_hour, 4)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the account-aware flow-rate unit."""
        return (
            UnitOfVolumeFlowRate.LITERS_PER_HOUR
            if self._account.uses_liters
            else UnitOfVolumeFlowRate.GALLONS_PER_HOUR
        )

    @property
    @property
    def suggested_unit_of_measurement(self) -> str:
        """Prefer the account's liquid flow-rate unit."""
        return self.native_unit_of_measurement

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the confirmed interval used for the estimate."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None:
            return {}
        return {
            "method": "average_between_confirmed_level_changes",
            "interval_start": (
                consumption.estimated_flow_interval_start.isoformat()
                if consumption.estimated_flow_interval_start
                else None
            ),
            "interval_end": (
                consumption.estimated_flow_calculated_at.isoformat()
                if consumption.estimated_flow_calculated_at
                else None
            ),
            "interval_hours": (
                round(consumption.estimated_flow_interval_hours, 2)
                if consumption.estimated_flow_interval_hours is not None
                else None
            ),
        }


class MyTankAppCalculatedDailyUsageSensor(MyTankAppEntity, SensorEntity):
    """Rolling propane usage calculated from timestamped tank history."""

    entity_description = DAILY_USAGE_DESCRIPTION

    def __init__(self, entry: MyTankAppConfigEntry, device_id: str) -> None:
        super().__init__(entry, device_id, self.entity_description.key)
        self._account = entry.runtime_data.account

    @property
    def native_value(self) -> float | None:
        """Return rolling average daily propane use."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None or consumption.rolling_usage_per_day is None:
            return None
        return round(consumption.rolling_usage_per_day, 3)

    @property
    def native_unit_of_measurement(self) -> str:
        """Return the account-aware daily volume unit."""
        volume = "L" if self._account.uses_liters else "gal"
        return f"{volume}/d"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose the effective history window used for the calculation."""
        consumption = self.coordinator.consumption.get(self._device_id)
        if consumption is None:
            return {}
        return {
            "window_days": (
                round(consumption.usage_window_days, 2)
                if consumption.usage_window_days is not None
                else None
            ),
            "calculated_at": (
                consumption.usage_calculated_at.isoformat()
                if consumption.usage_calculated_at is not None
                else None
            ),
        }
