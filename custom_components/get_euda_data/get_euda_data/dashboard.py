# Utilities for integration with Home Assistant
# Thanks to molobrakos and Farfar

import logging
from .utilities import camel2slug
from .const import (
    EUDA_DATA_DICT,
    EUDA_DATA_CONVERSION_INT,
    EUDA_DATA_CONVERSION_BOOL,
    EUDA_LONG_TERM_DATA_START_MILEAGE_KEY,
    EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY,
)

_LOGGER = logging.getLogger(__name__)


class EUDAInstrument:
    def __init__(
        self,
        component,
        attr,
        name,
        icon=None,
        key=None,
        conversion=None,
        values_to_treat_as_unsupported=set(),
    ):
        self.attr = attr
        self.component = component
        self.name = name
        self.vehicle = None
        self.icon = icon
        self.callback = None
        self.key = key
        self.conversion = conversion
        self.values_to_treat_as_unsupported = values_to_treat_as_unsupported

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
        if self.vehicle.isEUDADataFieldSupported(
            self.key, self.values_to_treat_as_unsupported
        ):
            val = self.vehicle.getEUDADataFieldValue(self.key, self.conversion)
            return val
        else:
            self._LOGGER.debug(
                f'Could not find attribute "{self.attr}" or its value means "unsupported" or "invalid".'
            )
            return None

    @property
    def attributes(self):
        attrs = {}
        if (
            self.key != "00000000-0000-0000-0000-0000"
            and self.key != "01000000-0000-0000-0000-0000"
            and not self.key.startswith("10000000-0000")
            and not self.key.startswith("11000000-0000")
        ):
            attrs["EUDA field key"] = self.key
        if self.name.startswith("Last long length"):
            if self.vehicle.isEUDADataFieldSupported(
                EUDA_LONG_TERM_DATA_START_MILEAGE_KEY, {}
            ):
                attrs["start mileage"] = self.vehicle.getEUDADataFieldValue(
                    EUDA_LONG_TERM_DATA_START_MILEAGE_KEY, EUDA_DATA_CONVERSION_INT
                )
                return attrs
        if self.name.startswith("Last short length"):
            if self.vehicle.isEUDADataFieldSupported(
                EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY, {}
            ):
                attrs["start mileage"] = self.vehicle.getEUDADataFieldValue(
                    EUDA_SHORT_TERM_DATA_START_MILEAGE_KEY, EUDA_DATA_CONVERSION_INT
                )
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
        if not self.name.startswith("Last long") and not self.name.startswith(
            "Last short"
        ):
            if self.vehicle.getEUDADataFieldTimestamp(self.key) != "unknown":
                attrs["time stamp"] = self.vehicle.getEUDADataFieldTimestamp(self.key)
                return attrs
        return attrs

    @property
    def is_supported(self):
        try:
            return self.vehicle.isEUDADataFieldSupported(
                self.key, self.values_to_treat_as_unsupported
            )
        except Exception as error:
            self._LOGGER.error(
                f"An error occurred when checking if {self.attr} is supported. Error: {error}"
            )
            return False


class EUDASensor(EUDAInstrument):
    def __init__(
        self,
        attr,
        name,
        icon,
        unit=None,
        device_class=None,
        key=None,
        unit_key=None,
        conversion=None,
    ):
        super().__init__(
            component="sensor",
            attr=attr,
            name=name,
            icon=icon,
            key=key,
            conversion=conversion,
        )
        self.device_class = device_class
        self._unit = unit
        self.unit_key = unit_key

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

    @property
    def unit(self):
        if self.unit_key is not None:
            unit_from_file = self.vehicle.getEUDADataFieldUnit(self.unit_key)
            if unit_from_file != "":
                return unit_from_file
            else:
                self._LOGGER.info(
                    f"Could not find valid unit information for {self.name} in EUDA file. Using the default unit."
                )
        return self._unit


class EUDABinarySensor(EUDAInstrument):
    def __init__(
        self,
        attr,
        name,
        device_class,
        icon="",
        reverse_state=False,
        key=None,
        conversion=None,
        values_to_treat_as_unsupported=set(),
    ):
        super().__init__(
            component="binary_sensor",
            attr=attr,
            name=name,
            icon=icon,
            key=key,
            conversion=conversion,
            values_to_treat_as_unsupported=values_to_treat_as_unsupported,
        )
        self.device_class = device_class
        self.reverse_state = reverse_state

    @property
    def is_mutable(self) -> bool:
        return False

    @property
    def str_state(self):
        if self.state is None:
            #self._LOGGER.error(f"Can not encode state {self.attr} {self.state}")
            #return None
            return "Unknown"
        if self.device_class in ["door", "window"]:
            return "Closed" if self.state else "Open"
        if self.device_class == "lock":
            return "Locked" if self.state else "Unlocked"
        if self.device_class == "safety":
            return "Warning!" if self.state else "OK"
        if self.device_class == "plug":
            return "Connected" if self.state else "Disconnected"
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
                values_to_treat_as_unsupported=dictElem.get(
                    "values_to_treat_as_unsupported", set()
                ),
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
                unit_key=dictElem.get("unit_key", None),
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
        self._LOGGER.debug(f"config={config}")
        configuredInstrumentsForThisVehicle = config.get("configuredInstruments", {})
        self.instruments = []
        for instrument in create_eudaInstruments():
            if instrument.setup(vehicle, **config):
                self.instruments.append(instrument)
            elif instrument.attr in configuredInstrumentsForThisVehicle:
                self._LOGGER.debug(
                    f"Instrument {instrument.name} not in current data file, "
                    + "but known from earlier files. Will therefore be shown in HA."
                )
                self.instruments.append(instrument)

        self._LOGGER.debug(
            "Supported instruments: "
            + ", ".join(str(inst.attr) for inst in self.instruments)
        )
