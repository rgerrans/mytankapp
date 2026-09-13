"""Base entity for MyTankApp."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MyTankAppConfigEntry
from .const import DOMAIN
from .coordinator import MyTankAppCoordinator
from .models import MyTankAppTank


class MyTankAppEntity(CoordinatorEntity[MyTankAppCoordinator]):
    """Base class for entities belonging to one tank."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: MyTankAppConfigEntry,
        device_id: str,
        key: str,
    ) -> None:
        super().__init__(entry.runtime_data.coordinator)
        self._device_id = device_id
        self._attr_unique_id = f"{device_id}_{key}"

    @property
    def tank(self) -> MyTankAppTank | None:
        """Return the current tank model."""
        return self.coordinator.data.get(self._device_id)

    @property
    def available(self) -> bool:
        """Return whether the coordinator and tank are available."""
        return super().available and self.tank is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Describe the physical tank as a Home Assistant device."""
        tank = self.tank
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Anova",
            model=(tank.fuel_type if tank and tank.fuel_type else "Tank monitor"),
            name=(tank.display_name if tank else f"Tank {self._device_id[-4:]}"),
            configuration_url="https://www.mytankapp.com/main",
        )

