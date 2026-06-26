#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Extract information from data files downloaded from the EU Data Act portal of Volkswagen group.
import logging
from datetime import datetime
from typing import Any, TypedDict

from .const import (
    EUDA_DATA_CONVERSION_FLOAT,
    EUDA_DATA_CONVERSION_INT,
    EUDA_DATA_CONVERSION_BOOL,
    EUDA_DATA_CONVERSION_DIVIDE_BY_10,
    EUDA_DATA_CONVERSION_KELVIN_TO_CELSIUS,
    EUDA_DATA_CONVERSION_INT_INVERT,
    EUDA_DATA_DICT,
    EUDA_DATA_NO_SHOW_SET,
)

_LOGGER = logging.getLogger(__name__)


class EUDAVehicle:
    # Init connection class
    def __init__(self, conn, data):
        self._logPrefix = data.get("logPrefix", None)
        if self._logPrefix is not None:
            self._LOGGER = logging.getLogger(__name__ + "_" + self._logPrefix)
        else:
            self._LOGGER = _LOGGER

        self._LOGGER.debug(
            conn.anonymise(f"Creating Vehicle class object with data {data}")
        )
        self._connection = conn
        self._vin = data.get("vin", "")
        self._brand = data.get("brand", "")
        self._nickName = data.get("nickName", "")
        self._dashboard = None
        self._states = {}
        self.currentData = {}
        self.tripData = {}
        self._tripSumDictDay = {}
        self._tripSumDictMonth = {}
        self._defined_EUDA_keys = set()
        for elem in EUDA_DATA_DICT.values():
            if elem.get("key", "") != "":
                self._defined_EUDA_keys.add(elem.get("key", ""))

    def dashboard(self, **config):
        """Returns dashboard, creates new if none exist."""
        if self._dashboard is None:
            # Init new dashboard if none exist
            from .dashboard import Dashboard

            self._dashboard = Dashboard(self, **config)
        elif config != self._dashboard._config:
            # Init new dashboard on config change
            from .dashboard import Dashboard

            self._dashboard = Dashboard(self, **config)
        return self._dashboard

    @property
    def vin(self):
        return self._vin

    @property
    def unique_id(self):
        return self.vin

    @property
    def nickname(self):
        return self._nickName

    @property
    def is_nickname_supported(self) -> bool:
        """Return true if nickname is supported."""
        if self._nickName != "":
            return True
        else:
            return False

    @property
    def brand(self):
        """Return brand"""
        return self._brand

    @property
    def is_brand_supported(self) -> bool:
        """Return true if brand is supported."""
        if self._brand != "":
            return True
        else:
            return False

    @property
    def model(self):
        """Return model"""
        return GetModelFromNickName(self._nickName).lower()

    @property
    def model_year(self):
        """Return model year"""
        return "unknown"

    def getEUDADataFieldValue(self, key: str, conversion: int | None = None) -> Any:
        """Return value of an EUDA data field identified by key."""
        if key == "00000000-0000-0000-0000-0000":
            attrs = self.getEUDADataAllUndefinedFields
            return len(attrs)
        elif key == "01000000-0000-0000-0000-0000":
            return self.getEUDAFileTimestamp
        elif key.startswith("10000000-0000") or key.startswith("11000000-0000"):
            if key.startswith("10000000-0000"):
                tripSum = self.getLatestTripSumValues("day")
            else:
                tripSum = self.getLatestTripSumValues("month")
            if key.endswith("0000"):
                return tripSum.get("startMileage", 0)
            elif key.endswith("0001"):
                return tripSum.get("fuelConsumption", 0) / 10
            elif key.endswith("0002"):
                return tripSum.get("electricConsumption", 0) / 10
            elif key.endswith("0003"):
                return tripSum.get("gasConsumption", 0) / 10
            elif key.endswith("0004"):
                return tripSum.get("travelTime", 0)
            elif key.endswith("0005"):
                return tripSum.get("distance", 0)
            elif key.endswith("0006"):
                return tripSum.get("tripEnd", 0)
            else:
                self._LOGGER.warning(f"Unknown trip sum value key {key}.")
                return tripSum
        for element in self.currentData.get("Data", []):
            if element.get("key", "") == key:
                if "value" in element:
                    if conversion is None:
                        return element.get("value", "")
                    elif conversion == EUDA_DATA_CONVERSION_FLOAT:
                        return float(element.get("value", "0"))
                    elif conversion == EUDA_DATA_CONVERSION_INT:
                        if (
                            key == "cf28f7d9-6201-30b8-82e5-a461968d30dc"
                            and int(element.get("value", "0")) == 65535
                        ):
                            return -1
                        elif (
                            key == "7405c11f-4d20-36d2-8381-18364aa1f444"
                        ):  # value of battery_state_report.remaining_charging_time_complete comes with a unit
                            value = element.get("value", "0s")
                            try:
                                if value.find("s") > 0:
                                    return int(int(value[0 : value.find("s")]) / 60)
                                elif value.find("min") > 0:
                                    return int(value[0 : value.find("min")])
                                else:
                                    return int(value)
                            except Exception as e:
                                self._LOGGER.warning(
                                    f"Failed to extract numerical value from value {value} for key {key}. Error {e}"
                                )
                            return -1
                        elif element.get("value", "0") == "":
                            return 0
                        return int(element.get("value", "0"))
                    elif conversion == EUDA_DATA_CONVERSION_INT_INVERT:
                        return -int(element.get("value", "0"))
                    elif conversion == EUDA_DATA_CONVERSION_BOOL:
                        if element.get("value", "") == "true":
                            return True
                        elif element.get("value", "") == "on":
                            return True
                        elif element.get("value", "") == "locked":
                            return True
                        elif element.get("value", "") == "connected":
                            return True
                        elif element.get("value", "") == "charging":
                            return True
                        elif element.get("value", "") == "1" and element.get(
                            "dataFieldName", ""
                        ).startswith("parking_brake"):
                            return True
                        elif element.get("value", "") == "3" and element.get(
                            "dataFieldName", ""
                        ).startswith("open_state"):
                            return True
                        elif element.get("value", "") == "3" and element.get(
                            "dataFieldName", ""
                        ).startswith("state_sunroof"):
                            return True
                        elif element.get("value", "") in (
                            "3",
                            "4",
                            "5",
                        ) and element.get("dataFieldName", "").startswith(
                            "parking_lights"
                        ):
                            return True
                        elif element.get(
                            "value", ""
                        ) == "3" and "window_lifter" in element.get(
                            "dataFieldName", ""
                        ):
                            return True
                    elif conversion == EUDA_DATA_CONVERSION_DIVIDE_BY_10:
                        return int(element.get("value", "0")) / 10
                    elif conversion == EUDA_DATA_CONVERSION_KELVIN_TO_CELSIUS:
                        return (
                            float(element.get("value", "0.0")) / 10 - 273.1
                        )  # The temperature returned from the portal is in Kelvin
                    else:
                        self._LOGGER.warning(
                            f"Unknown conversion type {conversion} in getEUDADataFiledValue()"
                        )
        if conversion == EUDA_DATA_CONVERSION_FLOAT:
            return 0.0
        elif conversion == EUDA_DATA_CONVERSION_INT:
            return 0
        elif conversion == EUDA_DATA_CONVERSION_BOOL:
            return False
        elif conversion == EUDA_DATA_CONVERSION_DIVIDE_BY_10:
            return 0.0
        elif conversion == EUDA_DATA_CONVERSION_KELVIN_TO_CELSIUS:
            return 0.0
        elif conversion == EUDA_DATA_CONVERSION_INT_INVERT:
            return 0
        return ""

    def isEUDADataFieldSupported(self, key: str) -> bool:
        """Return true if the EUDA data field identified by key is supported."""
        if key == "00000000-0000-0000-0000-0000":
            return True
        elif key == "01000000-0000-0000-0000-0000" and self.currentData != {}:
            return True
        elif (
            key.startswith("10000000-0000") or key.startswith("11000000-0000")
        ) and self.tripData != {}:
            return True
        for element in self.currentData.get("Data", []):
            if element.get("key", "") == key:
                if "value" in element:
                    return True
        return False

    @property
    def getEUDAFileTimestamp(self) -> datetime:
        """Return timestamp form the newest EUDA file (from the filename)."""
        if self.currentData.get("timeStamp", "") != "":
            return self.currentData.get("timeStamp", "")
        return datetime.min

    def getEUDADataFieldTimestamp(self, key: str | None = None) -> str:
        """Return timestamp for an EUDA data field identified by key."""
        for element in self.currentData.get("Data", []):
            if element.get("key", "") == key:
                if "timestampUtc" in element:
                    return element.get("timestampUtc", "unknown")
        return "unknown"

    def getEUDADataFieldUnit(self, key: str) -> str:
        """Return the unit computed from value of an unit EUDA data field identified by key."""
        for element in self.currentData.get("Data", []):
            if element.get("key", "") == key:
                if "value" in element:
                    unitInFile = element.get("value", "")
                    if unitInFile == "MILES":
                        return "mi"
                    elif unitInFile == "KM":
                        return "km"
                    elif unitInFile == "CHARGE_RATE_UNIT_KM_PER_H":
                        return "km/h"
                    elif unitInFile == "CHARGE_RATE_UNIT_KM_PER_MIN":
                        return "km/min"
                    elif unitInFile == "CHARGE_RATE_UNIT_MILES_PER_H":
                        return "mi/h"
                    elif unitInFile == "CHARGE_RATE_UNIT_MILES_PER_MIN":
                        return "mi/min"
                    elif unitInFile == "CHARGE_RATE_UNIT_INVALID":
                        self._LOGGER.info(
                            f"Found unit field {key} in EUDA file, but it had the value {unitInFile}."
                        )
                        return ""
                    else:
                        self._LOGGER.warning(
                            f"Found unit field {key} in EUDA file, but it had the yet unknown value {unitInFile}. Please open an issue."
                        )
                        return ""
                else:
                    self._LOGGER.info(
                        f"Found unit field {key} in EUDA file, but it had no value."
                    )
                    return ""
        self._LOGGER.info(f"Could not find unit field {key} in EUDA file.")
        return ""

    @property
    def getEUDADataAllUndefinedFields(self) -> dict:
        """Return a dictionary of all EUDA data fields found in EUDA files but not defined in EUDA_DATA_DICT."""
        undefinedFields = {}
        for element in self.currentData.get("Data", []):
            if (
                element.get("key", "") not in self._defined_EUDA_keys
                and element.get("key", "") not in EUDA_DATA_NO_SHOW_SET
            ):
                if element.get("dataFieldName", "") != "":
                    undefinedFields[
                        element.get("dataFieldName", "-dataFieldNameMissing-")
                    ] = element.get("value", "")
                else:
                    undefinedFields[element.get("key", "-dataFieldNameMissing-")] = (
                        element.get("value", "")
                    )
        return dict(sorted(undefinedFields.items()))

    def getLatestTripSumValues(self, sumType: str = "day") -> dict:
        """Return the calculated latest daily sum values from the trip history."""
        if sumType == "month":
            if self._tripSumDictMonth == {}:
                self._LOGGER.warning(
                    "tripSumDictMonth is empty when getLatestTripSumValues is called. Recalculating."
                )
                self.calcLatestTripSumValues(sumType=sumType)
            return self._tripSumDictMonth
        else:
            if self._tripSumDictDay == {}:
                self._LOGGER.warning(
                    "tripSumDictDay is empty when getLatestTripSumValues is called. Recalculating."
                )
                self.calcLatestTripSumValues(sumType=sumType)
            return self._tripSumDictDay

    def calcLatestTripSumValues(self, sumType: str = "day"):
        """Calculate the latest daily sum values from the trip history."""
        try:
            SumDictType = TypedDict(
                "SumDictType",
                {
                    "startMileage": int,
                    "fuelConsumption": int,
                    "electricConsumption": int,
                    "gasConsumption": int,
                    "travelTime": int,
                    "distance": int,
                    "tripEnd": datetime,
                },
            )
            sumDict: SumDictType = {
                "startMileage": 1000000,
                "fuelConsumption": 0,
                "electricConsumption": 0,
                "gasConsumption": 0,
                "travelTime": 0,
                "distance": 0,
                "tripEnd": datetime.min,
            }
            if self.tripData != {}:
                element = self.tripData[list(self.tripData)[-1]]
                # Set the minTimeStamp
                latestTripEnd = element.get("tripEnd", datetime.min)
                if sumType == "month":
                    latestTripEnd = latestTripEnd.replace(day=1)
                minTimeStamp = datetime.combine(
                    latestTripEnd.date(), datetime.min.time()
                ).astimezone(None)
                sumDict["tripEnd"] = minTimeStamp

                for element in self.tripData.values():
                    if minTimeStamp <= element.get("tripEnd", ""):
                        if (
                            element.get("startMileage", 1000000)
                            < sumDict["startMileage"]
                        ):
                            sumDict["startMileage"] = element.get(
                                "startMileage", 1000000
                            )
                        sumDict["travelTime"] = sumDict["travelTime"] + element.get(
                            "travelTime", 0
                        )
                        sumDict["distance"] = sumDict["distance"] + element.get(
                            "distance", 0
                        )
                        sumDict["fuelConsumption"] = sumDict[
                            "fuelConsumption"
                        ] + element.get("fuelConsumption", 0) * element.get(
                            "distance", 0
                        )
                        sumDict["electricConsumption"] = sumDict[
                            "electricConsumption"
                        ] + element.get("electricConsumption", 0) * element.get(
                            "distance", 0
                        )
                        sumDict["gasConsumption"] = sumDict[
                            "gasConsumption"
                        ] + element.get("gasConsumption", 0) * element.get(
                            "distance", 0
                        )

                if sumDict["distance"] > 0:
                    sumDict["fuelConsumption"] = int(
                        sumDict["fuelConsumption"] / sumDict["distance"] + 0.5
                    )
                    sumDict["electricConsumption"] = int(
                        sumDict["electricConsumption"] / sumDict["distance"] + 0.5
                    )
                    sumDict["gasConsumption"] = int(
                        sumDict["gasConsumption"] / sumDict["distance"] + 0.5
                    )

            if sumType == "month":
                self._tripSumDictMonth = sumDict
            else:
                self._tripSumDictDay = sumDict
        except Exception as error:
            self._LOGGER.warning(
                f"Failed to calculate latest trip sum values  - {error}"
            )


def GetModelFromNickName(nickName: str) -> str:
    posSeparator = nickName.find(" ")
    if posSeparator > 0 and len(nickName) > posSeparator:
        return nickName[posSeparator + 1 :]
    return ""
