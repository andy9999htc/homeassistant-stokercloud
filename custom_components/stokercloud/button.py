from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry, async_add_entities):
    """Set up button entities."""
    stoker = hass.data[DOMAIN][config.entry_id]
    async_add_entities(
        [
            StokerCloudActionButton(stoker, "start", "Boiler Start", "misc.start", "misc.start", 1),
            StokerCloudActionButton(stoker, "stop", "Boiler Stop", "misc.stop", "misc.stop", 1),
        ]
    )


class StokerCloudActionButton(CoordinatorEntity, ButtonEntity):
    """Button entity that triggers cloud write actions."""

    def __init__(self, client, key: str, name: str, menu: str, param_name: str, value: int):
        super().__init__(client._coordinator)
        self._data = client
        self.coordinator = client._coordinator
        self._menu = menu
        self._param_name = param_name
        self._value = value
        self._attr_unique_id = f"{self.coordinator._alias}_button_{key}"
        self._attr_name = f"{self.coordinator._alias} {name}"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self.coordinator._alias)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self.coordinator._alias,
        }

    async def async_press(self) -> None:
        await self.coordinator._api.update_controller_value(
            self._menu,
            self._param_name,
            self._value,
        )
        await self.coordinator.async_request_refresh()
