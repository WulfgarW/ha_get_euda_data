"""
Support for My Cupra Platform
"""

import logging

from . import DATA_KEY, DOMAIN, PyCupraEntity
from .const import DATA
from homeassistant.components.sensor import (
    DEVICE_CLASSES,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_RESOURCES

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the PyCupra sensors."""
    if discovery_info is None:
        return
    async_add_entities([PyCupraSensor(hass.data[DATA_KEY], *discovery_info)])


async def async_setup_entry(hass, entry, async_add_devices):
    data = hass.data[DOMAIN][entry.entry_id][DATA]
    coordinator = data.coordinator
    if coordinator.data is not None:
        if CONF_RESOURCES in entry.options:
            resources = entry.options[CONF_RESOURCES]
        else:
            resources = entry.data[CONF_RESOURCES]

        async_add_devices(
            PyCupraSensor(
                data, instrument.vehicle_name, instrument.component, instrument.attr
            )
            for instrument in (
                instrument
                for instrument in data.instruments
                if instrument.component == "sensor" and instrument.attr in resources
            )
        )

    return True


class PyCupraSensor(PyCupraEntity, SensorEntity):
    """Representation of a PyCupra Sensor."""

    def __init__(self, data, vin, component, attribute):
        """Initialize the sensor."""
        super().__init__(data, vin, component, attribute)
        # Set state_class during initialization
        if self.instrument.attr in [
            "battery_level",
            "state_of_charge",
            "adblue_level",
            "fuel_level",
            "tank_level",
            "cng_level",
            "oil_level",
            "charging_time_left",
            "charging_power",
            "charge_rate",
            "distance",
            "distance_value",
            "electric_range",
            "combustion_range",
            "combined_range",
            "primary_engine_range",
            "secondary_engine_range",
            "outside_temperature",
            "outside_temperature_indication",
            "outdoor_temperature",
            "min_temperature_battery_module",
            "max_temperature_battery_module",
            "boardnet_battery_voltage",
        ]:
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    # def state(self):
    def native_value(self):
        """Return the state of the sensor."""
        if self.instrument is not None:
            return self.instrument.state
        return None

    @property
    # def unit_of_measurement(self):
    def native_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.instrument is not None:
            return self.instrument.unit
        return None

    @property
    def suggested_unit_of_measurement(self):
        """Return the unit of measurement."""
        if self.instrument is not None:
            if self.instrument.unit in ("km", "km/h"):
                return self.instrument.unit
        return None

    @property
    def device_class(self):
        """Return the class of this sensor, from DEVICE_CLASSES."""
        if self.instrument.device_class in DEVICE_CLASSES:
            return self.instrument.device_class
        return None
