"""Constants for the MyTankApp integration."""

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "mytankapp"
PLATFORMS: Final = [Platform.SENSOR, Platform.BINARY_SENSOR]

CONF_SCAN_INTERVAL: Final = "scan_interval"
CONF_LOW_LEVEL: Final = "low_level"

DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_LOW_LEVEL: Final = 20
MIN_SCAN_INTERVAL: Final = 5
MAX_SCAN_INTERVAL: Final = 180

BASE_URL: Final = "https://www.mytankapp.com"
