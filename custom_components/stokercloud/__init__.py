"""The Stokercloud integration."""

import asyncio
from dataclasses import field
from datetime import timedelta
import logging
from typing import Any

import voluptuous as vol

from homeassistant.components.number import NumberEntityDescription
from homeassistant.components.sensor import SensorEntityDescription, dataclass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONF_API_VARIANT,
    CONF_SCREEN,
    DEFAULT_API_VARIANT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SCREEN,
    DOMAIN,
)
from .stokercloud_api import Client as StokerCloudClient

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.NUMBER, Platform.SENSOR]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Stokercloud component."""

    hass.data[DOMAIN] = {}
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Stokercloud from a config entry."""
    nbe_user = entry.data[CONF_USERNAME]
    nbe_pass = entry.data[CONF_PASSWORD]
    api_variant = entry.data.get(CONF_API_VARIANT, DEFAULT_API_VARIANT)
    screen = entry.data.get(CONF_SCREEN, DEFAULT_SCREEN)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    stokerCloud = StokerCloudClient(
        nbe_user,
        nbe_pass,
        api_variant=api_variant,
        screen=screen,
    )

    # Fetch initial data so we have data when entities subscribe
    coordinator = IntegrationCoordinator(hass, stokerCloud, nbe_user, scan_interval)

    # 🔑 Load persisted data from disk
    await coordinator.async_load()

    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = HassIntegration(coordinator, nbe_user)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class HassIntegration:
    def __init__(self, coordinator: DataUpdateCoordinator, nbe_user: str):
        self._nbe_user = nbe_user
        _LOGGER.debug("StokerCloud __init__" + self._nbe_user)

        # create an instance of StokerCloud
        self._coordinator = coordinator

    def get_name(self):
        return f"stoker_cloud_{self._nbe_user}"

    def get_unique_id(self):
        return f"stoker_cloud_{self._nbe_user}"


class IntegrationCoordinator(DataUpdateCoordinator):
    """StokerCloud coordinator."""

    def __init__(
        self, hass, stokerClient: StokerCloudClient, alias: str, pollinterval: int
    ):
        """Initialize my coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=f"StokerCloud coordinator for '{alias}'",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=pollinterval),
        )

        self.store = Store(hass, 1, "stokercloud_data.json")
        self.data = {}

        self._api = stokerClient
        self._alias = alias

    async def async_load(self):
        stored = await self.store.async_load()
        if stored is not None:
            self.data.update(stored)

    async def async_save(self):
        await self.store.async_save(self.data)

    async def _async_update_data(self):
        # Fetch data from API endpoint. This is the place to pre-process the data to lookup tables so entities can quickly look up their data.

        try:
            # controller_data = await self._api.controller_data()
            controller_data = await self._api.controller_data_json()

            # 🔑 Preserve internal values across refreshes
            for key, value in self.data.items():
                if key.startswith("internal"):
                    controller_data[key] = value

            return controller_data

        except Exception as err:
            _LOGGER.error("Stokercloud _async_update_data failed: %s", err)
            raise


@dataclass(frozen=True, kw_only=True)
class IntegrationSensorEntityDescription(SensorEntityDescription):
    """Custom SensorEntityDescription with extra attributes."""

    value: Any  # extra field
    format: str | None = None  # optional extra field


@dataclass(frozen=True, kw_only=True)
class IntegrationNumberEntityDescription(NumberEntityDescription):
    """Custom SensorEntityDescription with extra attributes."""

    value: Any  # extra field
    format: str | None = None  # optional extra field
    default_value: float | None = None  # optional extra field
    updateParams: list[str] = field(default_factory=list)  # optional extra field
