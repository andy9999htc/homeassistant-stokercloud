"""Platform for sensor integration."""

from __future__ import annotations

import datetime
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfMass,
    UnitOfPower,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import IntegrationCoordinator, IntegrationSensorEntityDescription
from .const import DOMAIN, LNG_STATE_MAP, MANUFACTURER, MODEL, STATE_STATE

_LOGGER = logging.getLogger(__name__)
_MISSING_KEYS_LOGGED: set[str] = set()

MIN_TIME_BETWEEN_UPDATES = datetime.timedelta(minutes=1)


async def async_setup_entry(hass, config, async_add_entities):
    """Set up the sensor platform."""
    stoker = hass.data[DOMAIN][config.entry_id]

    entities: list[StokerCloudSensor] = [
        StokerCloudSensor(stoker._coordinator, sensor, stoker)
        for sensor in SENSORS_BOILER
    ]

    async_add_entities(entities)


class StokerCloudSensor(CoordinatorEntity, SensorEntity):
    """Representation of a meter reading sensor."""

    def __init__(
        self,
        coordinator: IntegrationCoordinator,
        sensor: IntegrationSensorEntityDescription,
        client,
    ):
        """Initialize the sensor."""
        self._data = client
        self.coordinator = coordinator
        self.entity_description: IntegrationSensorEntityDescription = sensor
        self._attr_unique_id = f"{self.coordinator._alias}_{sensor.key}"
        self._attr_name = f"{self.coordinator._alias} {sensor.name}"

        _LOGGER.info(self._attr_unique_id)
        self._attr_native_value = None  # Initialize the native value

    @property
    def device_info(self):
        """Return device information about this entity."""
        _LOGGER.debug("StokerCloudSensor: device_info")

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
    def state(self):
        """Return the state of the sensor."""
        return self._attr_native_value

    async def async_added_to_hass(self):
        """Handle entity addition to hass."""
        # Add the coordinator listener for data updates
        self.coordinator.async_add_listener(self._handle_coordinator_update)
        # Ensure that data is fetched initially
        await self.coordinator.async_refresh()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        data_available = False

        # if self.entity_description.key:
        if self.entity_description.key in self.coordinator.data:
            val = self.coordinator.data[self.entity_description.key]

            _MISSING_KEYS_LOGGED.discard(self.entity_description.key)

            if "state" in self.entity_description.key:
                if isinstance(val, str) and val in LNG_STATE_MAP:
                    self._attr_native_value = LNG_STATE_MAP[val]
                else:
                    normalized_state = val
                    if isinstance(val, str) and val.startswith("lng_state_"):
                        state_code = val.split("lng_state_", 1)[1]
                        normalized_state = f"state_{state_code}"
                    self._attr_native_value = STATE_STATE.get(normalized_state, [val, "mdi:information"])[0]
            else:
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


SENSORS_BOILER: tuple[IntegrationSensorEntityDescription, ...] = (
    IntegrationSensorEntityDescription(
        key="frontdata_boilertemp_value",
        name="Boiler Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_wantedboilertemp_value",
        name="Boiler Temperature Requested",
        icon="mdi:thermometer-chevron-up",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="miscdata_output",
        name="Boiler Effect",
        icon="mdi:gas-burner",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="miscdata_outputpct",
        name="Boiler Effect pct",
        icon="mdi:gas-burner",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_dhw_value",
        name="Current Water Heater Temperature",
        icon="mdi:thermometer",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_dhwwanted_value",
        name="Requested Water Heater Temperature",
        icon="mdi:thermometer-chevron-up",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    # IntegrationSensorEntityDescription(
    #     key="frontdata_0_value",
    #     name="Hopper content",
    #     icon="mdi:information",
    #     device_class=SensorDeviceClass.VOLUME,
    #     native_unit_of_measurement=UnitOfMass.KILOGRAMS,
    #     value=lambda data, key: data[key],
    # ),
    IntegrationSensorEntityDescription(
        key="hopperdata_2_value",
        name="Total Consumption",
        icon="mdi:counter",
        device_class=SensorDeviceClass.VOLUME,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="miscdata_state_value",
        name="State",
        icon="mdi:information",
        device_class=SensorDeviceClass.ENUM,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="serial",
        name="Serial no",
        icon="mdi:information",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="miscdata_clock_value",
        name="Clock",
        icon="mdi:clock-digital",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="infomessages_0",
        name="Status message",
        icon="mdi:information",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="weatherdata_0_value",
        name="Weather City",
        icon="mdi:information",
        device_class=SensorDeviceClass.ENUM,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="weatherdata_1_value",
        name="Weather Outside tempererature",
        icon="mdi:information",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="weatherdata_2_value",
        name="Weather Wind speed",
        icon="mdi:information",
        device_class=SensorDeviceClass.WIND_SPEED,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="weatherdata_3_value",
        name="Weather Wind direction",
        icon="mdi:information",
        device_class=None,
        native_unit_of_measurement=None,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_smoketemp_value",
        name="Flue Gas Temperature",
        icon="mdi:thermometer-lines",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_ashdist_value",
        name="Ash Box Fill Level",
        icon="mdi:trash-can-outline",
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="hopperdata_14_value",
        name="Pellet Fill Level",
        icon="mdi:sack",
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_byid_oxygen_value",
        name="Oxygen",
        icon="mdi:molecule",
        device_class=SensorDeviceClass.POWER_FACTOR,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_byid_pressure_value",
        name="Furnace Pressure",
        icon="mdi:gauge",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement="Pa",
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="hopperdata_byid_3_value",
        name="Consumption 24h",
        icon="mdi:counter",
        device_class=SensorDeviceClass.WEIGHT,
        native_unit_of_measurement=UnitOfMass.KILOGRAMS,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="hopperdata_byid_7_value",
        name="Power 10%",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="hopperdata_byid_8_value",
        name="Power 100%",
        icon="mdi:flash",
        device_class=SensorDeviceClass.POWER,
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        value=lambda data, key: data[key],
    ),
    IntegrationSensorEntityDescription(
        key="frontdata_hopperdistance_value",
        name="Hopper Distance",
        icon="mdi:tape-measure",
        device_class=None,
        native_unit_of_measurement=PERCENTAGE,
        value=lambda data, key: data[key],
    ),
)
