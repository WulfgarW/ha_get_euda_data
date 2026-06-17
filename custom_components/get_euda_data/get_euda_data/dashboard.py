# Utilities for integration with Home Assistant
# Thanks to molobrakos and Farfar

import logging
from datetime import datetime
from .utilities import camel2slug, convertTimerUtcToLocal
from .const import (
    EUDA_DATA_DICT, 
    EUDA_DATA_CONVERSION_INT,
    EUDA_DATA_CONVERSION_BOOL, 
    EUDA_LONG_TERM_DATA_START_MILEAGE_KEY, 
    EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY,
    EUDA_OUTSIDE_TEMPERATURE_KEY,
    EUDA_PARKING_BRAKE_KEY,
)

_LOGGER = logging.getLogger(__name__)

class EUDAInstrument:
    def __init__(self, component, attr, name, icon=None, key=None, conversion=None):
        self.attr = attr
        self.component = component
        self.name = name
        self.vehicle = None
        self.icon = icon
        self.callback = None
        self.key = key
        self.conversion = conversion

    def __repr__(self):
        return self.full_name

    def configurate(self, **args):
        pass

    @property
    def slug_attr(self):
        return camel2slug(self.attr.replace(".", "_"))

    def setup(self, vehicle, **config) -> bool:
        if vehicle._logPrefix is not None:
            self._LOGGER = logging.getLogger(__name__ + "_" + vehicle._logPrefix)
        else:
            self._LOGGER = _LOGGER

        self.vehicle = vehicle
        if not self.is_supported:
            return False

        self.configurate(**config)
        return True

    @property
    def vehicle_name(self):
        return self.vehicle.vin

    @property
    def full_name(self):
        return f"{self.vehicle_name} {self.name}"

    @property
    def is_mutable(self):
        raise NotImplementedError("Must be set")

    @property
    def str_state(self):
        return self.state

    @property
    def state(self):
        if self.vehicle.isEUDADataFieldSupported(self.key):
            val = self.vehicle.getEUDADataFieldValue(self.key, self.conversion)
            return val
        else:
            self._LOGGER.debug(f'Could not find attribute "{self.attr}"')
            return None

    @property
    def attributes(self):
        attrs = {}
        if (self.key != "00000000-0000-0000-0000-0000" and 
            self.key != "01000000-0000-0000-0000-0000" and 
            not self.key.startswith("10000000-0000") and 
            not self.key.startswith("11000000-0000")    
            ):
            attrs["EUDA field key"] = self.key
        if self.name.startswith("Last long length"):
            if self.vehicle.isEUDADataFieldSupported(EUDA_LONG_TERM_DATA_START_MILEAGE_KEY):
                attrs["start mileage"] = self.vehicle.getEUDADataFieldValue(EUDA_LONG_TERM_DATA_START_MILEAGE_KEY, EUDA_DATA_CONVERSION_INT)
                return attrs
        if self.name.startswith("Last short length"):
            if self.vehicle.isEUDADataFieldSupported(EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY):
                attrs["start mileage"] = self.vehicle.getEUDADataFieldValue(EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY, EUDA_DATA_CONVERSION_INT)
                return attrs
        if self.key == "10000000-0000-0000-0000-0005":
            tripSum = self.vehicle.getLatestTripSumValues("day")
            attrs["start mileage"] = tripSum.get("startMileage", 0)
            return attrs
        if self.key == "11000000-0000-0000-0000-0005":
            tripSum = self.vehicle.getLatestTripSumValues("month")
            attrs["start mileage"] = tripSum.get("startMileage", 0)
            return attrs
        if self.name.startswith("Other fields found"):
            attrs = self.vehicle.getEUDADataAllUndefinedFields
            return attrs
        if not self.name.startswith("Last long") and not self.name.startswith("Last short"):
            if self.vehicle.getEUDADataFieldTimestamp(self.key) != "unknown":
                attrs["time stamp"] = self.vehicle.getEUDADataFieldTimestamp(self.key)
                return attrs
        return attrs

    @property
    def is_supported(self):
        try:
            return self.vehicle.isEUDADataFieldSupported(self.key)
        except Exception as error:
            self._LOGGER.error(f"An error occurred when checking if {self.attr} is supported. Error: {error}")
            return False


class EUDASensor(EUDAInstrument):
    def __init__(self, attr, name, icon, unit=None, device_class=None, key=None, conversion=None):
        super().__init__(component="sensor", attr=attr, name=name, icon=icon, key=key, conversion=conversion)
        self.device_class = device_class
        self.unit = unit

    @property
    def is_mutable(self) -> bool:
        return False

    @property
    def str_state(self):
        if self.unit:
            return f"{self.state} {self.unit}"
        else:
            return f"{self.state}"

    def configurate(self, **config) -> None:
        pass

    @property
    def state(self):
        val = super().state
        return val


class EUDABinarySensor(EUDAInstrument):
    def __init__(self, attr, name, device_class, icon="", reverse_state=False, key=None, conversion=None):
        super().__init__(component="binary_sensor", attr=attr, name=name, icon=icon, key=key, conversion=conversion)
        self.device_class = device_class
        self.reverse_state = reverse_state

    @property
    def is_mutable(self) -> bool:
        return False

    @property
    def str_state(self):
        if self.device_class in ["door", "window"]:
            return "Closed" if self.state else "Open"
        if self.device_class == "lock":
            return "Locked" if self.state else "Unlocked"
        if self.device_class == "safety":
            return "Warning!" if self.state else "OK"
        if self.device_class == "plug":
            return "Connected" if self.state else "Disconnected"
        if self.state is None:
            self._LOGGER.error(f"Can not encode state {self.attr} {self.state}")
            return "?"
        return "On" if self.state else "Off"

    @property
    def state(self):
        val = super().state

        if isinstance(val, (bool, list)):
            if self.reverse_state:
                if bool(val):
                    return False
                else:
                    return True
            else:
                return bool(val)
        elif isinstance(val, str):
            return val != "Normal"
        return val

    @property
    def is_on(self):
        return self.state


def create_eudaInstruments():
    instList = []
    for dictElem in EUDA_DATA_DICT.values():
        if dictElem.get("conversion", None) == EUDA_DATA_CONVERSION_BOOL:
            binary_sensor = EUDABinarySensor(
                attr=dictElem.get("attr", None),
                name=dictElem.get("name", None),
                icon=dictElem.get("icon", None),
                device_class=dictElem.get("device_class", None),
                key=dictElem.get("key", None),
                conversion=dictElem.get("conversion", None),
                reverse_state=dictElem.get("reverse_state", False),
            )
            instList.append(binary_sensor)
        else:
            sensor = EUDASensor(
                attr=dictElem.get("attr", None),
                name=dictElem.get("name", None),
                icon=dictElem.get("icon", None),
                unit=dictElem.get("unit", None),
                device_class=dictElem.get("device_class", None),
                key=dictElem.get("key", None),
                conversion=dictElem.get("conversion", None),
            )
            instList.append(sensor)

    return instList


class Dashboard:
    def __init__(self, vehicle, **config):
        if vehicle._logPrefix is not None:
            self._LOGGER = logging.getLogger(__name__ + "_" + vehicle._logPrefix)
        else:
            self._LOGGER = _LOGGER

        self._config = config
        self.instruments = [
            instrument
            for instrument in create_eudaInstruments()
            if instrument.setup(vehicle, **config)
        ]

        self._LOGGER.debug(
            "Supported instruments: "
            + ", ".join(str(inst.attr) for inst in self.instruments)
        )
