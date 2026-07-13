import logging

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
    RestoreEntity,
    callback,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfEnergy, UnitOfMass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IntegrationNumberEntityDescription
from .const import DOMAIN, MANUFACTURER, MODEL

_LOGGER = logging.getLogger(__name__)
_MISSING_KEYS_LOGGED: set[str] = set()


async def async_setup_entry(
    hass: HomeAssistant, config: ConfigEntry, async_add_entities
):
    """Set up the sensor platform."""
    stoker = hass.data[DOMAIN][config.entry_id]

    # Fetch initial data so we have data when entities subscribe
    # await CustomIntegration._coordinator.async_config_entry_first_refresh()

    entities: list[IntegrationNumber] = [
        IntegrationNumber(stoker, number) for number in NUMBER_SENSORS
    ]

    async_add_entities(entities)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    # Code for setting up your platform inside of the event loop
    _LOGGER.debug("async_setup_platform")

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        self._attr_native_value = value
        # send value to device / API here
        self.async_write_ha_state()


class IntegrationNumber(CoordinatorEntity, NumberEntity, RestoreEntity):
    def __init__(
        self,
        client,
        number: IntegrationNumberEntityDescription,
    ):
        """Initialize the number."""
        super().__init__(client._coordinator)
        self._data = client
        self.coordinator = client._coordinator
        self.entity_description: IntegrationNumberEntityDescription = number
        self._attr_unique_id = f"{self.coordinator._alias}_{number.key}"
        self._attr_name = f"{self.coordinator._alias} {number.name}"

        # self._attr_native_value = None
        # self._attr_min_value = None
        # self._attr_max_value = None
        # self._attr_step = number.step

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        last_state = await self.async_get_last_state()
        if last_state and last_state.state not in ("unknown", "unavailable"):
            self._attr_native_value = float(last_state.state)
        else:
            # FIRST TIME ONLY
            value = self.coordinator.data.get(self.entity_description.key)
            if value is None:
                value = self.entity_description.default_value

            if value is not None:
                self._attr_native_value = value

            if (
                self.entity_description.key.startswith("internal")
                and self._attr_native_value is not None
            ):
                self.coordinator.data[self.entity_description.key] = self._attr_native_value
                await self.coordinator.async_save()

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("StokerCloudNumber: device_info")

        return {
            "identifiers": {(DOMAIN, self.coordinator._alias)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": self.coordinator._alias,
        }

    @property
    def should_poll(self):
        return False

    @property
    def friendly_name(self):
        return self.entity_description.name

    @property
    def native_value(self):
        return self._attr_native_value

    async def async_set_native_value(self, value: float):
        # send value to device / API here

        if not self.entity_description.key.startswith("internal"):
            updated_value = await self.coordinator._api.update_controller_value(
                self.entity_description.updateParams[0],
                self.entity_description.updateParams[1],
                value,
            )
            self._attr_native_value = float(updated_value)
        else:
            self._attr_native_value = value
            self.coordinator.data[self.entity_description.key] = value
            await self.coordinator.async_save()  # persist to disk

        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data_available = False

        # if self.entity_description.key:
        if not self.coordinator.data:
            _LOGGER.warning("StokerCloudNumber: No data received from coordinator")
            return
        if self.entity_description.key in self.coordinator.data:
            val = self.coordinator.data[self.entity_description.key]

            _MISSING_KEYS_LOGGED.discard(self.entity_description.key)

            self._attr_native_value = val

            data_available = True
            self._attr_available = data_available
        else:
            if self.entity_description.key not in _MISSING_KEYS_LOGGED:
                _LOGGER.debug(
                    "The item %s is not returned from the 'cloud'",
                    self.entity_description.key,
                )
                _MISSING_KEYS_LOGGED.add(self.entity_description.key)

        # Only call async_write_ha_state if the state has changed
        if data_available:
            self.async_write_ha_state()


NUMBER_SENSORS: tuple[IntegrationNumberEntityDescription, ...] = (
    IntegrationNumberEntityDescription(
        key="frontdata_hoppercontent_value",
        name="Hopper content",
        icon="mdi:information",
        native_min_value=0,
        native_max_value=250,
        native_step=1,
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value=lambda data, key: data[key],
        updateParams=["hopper.content", "hopper.content"],
    ),
    IntegrationNumberEntityDescription(
        key="internaldata_pellet_energy_per_kg",
        name="Pellet energy (kWh/kg)",
        icon="mdi:fire",
        default_value=5.0,
        native_min_value=0,
        native_max_value=10,
        native_step=0.1,
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.ENERGY,
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        value=lambda data, key: data[key],
        updateParams=["internal", "pellet.energy_per_kg"],
    ),
    IntegrationNumberEntityDescription(
        key="frontdata_wantedboilertemp_value",
        name="Boiler Temperature Setpoint",
        icon="mdi:thermometer-chevron-up",
        native_min_value=40,
        native_max_value=95,
        native_step=1,
        mode=NumberMode.BOX,
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement="°C",
        value=lambda data, key: data[key],
        updateParams=["boiler.temp", "boiler.temp"],
    ),
)
