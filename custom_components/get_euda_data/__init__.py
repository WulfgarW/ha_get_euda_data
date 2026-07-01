# -*- coding: utf-8 -*-
"""
Get_EUDA_Data integration

Read more at https://github.com/WulfgarW/ha_get_euda_data/
"""

import re
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Union
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, SOURCE_IMPORT
from homeassistant.const import (
    # CONF_NAME,
    CONF_PASSWORD,
    CONF_RESOURCES,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv, device_registry
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
# from homeassistant.helpers.redact import REDACTED, async_redact_data

from homeassistant.components.persistent_notification import (
    async_create as async_pn_create,
    async_dismiss as async_pn_dismiss,
)

from .get_euda_data.eudaconnection import EUDAConnection
from .get_euda_data.eudavehicle import EUDAVehicle
from .get_euda_data.exceptions import (
    PyCupraConfigException,
    PyCupraAuthenticationException,
    PyCupraAccountLockedException,
    PyCupraLoginFailedException,
    PyCupraInvalidRequestException,
    PyCupraRequestInProgressException,
)

from .const import (
    PLATFORMS,
    CONF_BRAND,
    CONF_VEHICLE,
    CONF_INSTRUMENTS,
    CONF_LOGPREFIX,
    DATA,
    DATA_KEY,
    MIN_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SIGNAL_STATE_UPDATED,
    UNDO_UPDATE_LISTENER,
    UPDATE_CALLBACK,
    CONF_DEBUG,
    DEFAULT_DEBUG,
)

# Set max parallel updates to 2 simultaneous (1 poll and 1 request waiting)
# PARALLEL_UPDATES = 2

_LOGGER = logging.getLogger(__name__)
COUNTER_FOR_PERSISTENT_NOTIFICATIONS = 0


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup Get_EUDA_Data component from a config entry."""
    _LOGGER.debug(f"In async_setup_entry for entry {entry.entry_id}.")
    hass.data.setdefault(DOMAIN, {})

    if entry.options.get(CONF_SCAN_INTERVAL):
        update_interval = timedelta(seconds=entry.options[CONF_SCAN_INTERVAL])
    else:
        update_interval = timedelta(seconds=DEFAULT_SCAN_INTERVAL)
    if update_interval < timedelta(seconds=MIN_SCAN_INTERVAL):
        update_interval = timedelta(seconds=MIN_SCAN_INTERVAL)

    coordinator = PyCupraCoordinator(hass, entry, update_interval)

    try:
        if not await coordinator.async_login():
            _LOGGER.debug("In async_setup_entry. async_login failed.")
            entry.async_start_reauth(hass)
            return False
    except (
        PyCupraAuthenticationException,
        PyCupraAccountLockedException,
        PyCupraLoginFailedException,
    ) as e:
        _LOGGER.debug(f"In async_setup_entry. Exception {e}")
        raise ConfigEntryAuthFailed(e) from e
    except Exception as e:
        _LOGGER.debug(f"In async_setup_entry. Others exceptions. Exception {e}")
        raise ConfigEntryNotReady(e) from e

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, coordinator.async_logout)
    )

    await coordinator.async_refresh()
    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    # Get parent device
    try:
        if entry.unique_id is not None:
            identifiers = {(DOMAIN, entry.unique_id)}
        else:
            identifiers = None
        registry = device_registry.async_get(hass)
        device = registry.async_get_device(identifiers)
        # Get user configured name for device
        if device is not None:
            name = device.name_by_user if device.name_by_user is not None else None
        else:
            name = None
    except Exception:
        name = None

    data = PyCupraData(entry.data, name, coordinator)
    instruments = coordinator.data

    conf_instruments = entry.data.get(CONF_INSTRUMENTS, {}).copy()
    if entry.options.get(CONF_DEBUG, False):
        # _LOGGER.debug(f"Configured data: {async_redact_data(entry.data, ['username', 'password', 'vehicle', 'spin'])}")
        # _LOGGER.debug(f"Configured options: {async_redact_data(entry.options, ['username', 'password', 'vehicle', 'spin'])}")
        _LOGGER.debug(
            f"Resources from options are: {entry.options.get(CONF_RESOURCES, [])}"
        )
        _LOGGER.debug(f"All instruments (data): {conf_instruments}")
    new_instruments = {}

    def is_enabled(attr):
        """Return true if the user has enabled the resource."""
        return attr in entry.data.get(CONF_RESOURCES, [attr])

    components = set()

    # Check if new instruments
    for instrument in (
        instrument
        for instrument in instruments
        if instrument.attr not in conf_instruments
    ):
        _LOGGER.info(f"Discovered new instrument {instrument.name}")
        new_instruments[instrument.attr] = instrument.name

    # Update config entry with new instruments
    if len(new_instruments) > 0:
        conf_instruments.update(new_instruments)
        # Prepare data to update config entry with
        update = {
            "data": {
                CONF_INSTRUMENTS: dict(
                    sorted(conf_instruments.items(), key=lambda item: item[1])
                )
            },
            "options": {
                CONF_RESOURCES: entry.options.get(
                    CONF_RESOURCES, entry.data.get(CONF_RESOURCES, ["none"])
                )
            },
        }

        # Enable new instruments if "activate newly enable entitys" is active
        if hasattr(entry, "pref_disable_new_entities"):
            if not entry.pref_disable_new_entities:
                _LOGGER.debug(f"Enabling new instruments {new_instruments}")
                for item in new_instruments:
                    update["options"][CONF_RESOURCES].append(item)

        _LOGGER.debug(f"Updating config entry data: {update.get('data')}")
        _LOGGER.debug(f"Updating config entry options: {update.get('options')}")
        hass.config_entries.async_update_entry(
            entry,
            data={**entry.data, **update["data"]},
            options={**entry.options, **update["options"]},
        )

    for instrument in (
        instrument
        for instrument in instruments
        if instrument.component in PLATFORMS and is_enabled(instrument.slug_attr)
    ):
        data.instruments.add(instrument)
        components.add(PLATFORMS[instrument.component])

    hass.data[DOMAIN][entry.entry_id] = {
        UPDATE_CALLBACK: update_callback,
        DATA: data,
        UNDO_UPDATE_LISTENER: entry.add_update_listener(_async_update_listener),
    }

    for component in components:
        coordinator.platforms.append(component)
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setups(entry, components)
    )

    # Register services

    return True


def update_callback(hass, coordinator):
    _LOGGER.debug("CALLBACK!")
    hass.async_create_task(coordinator.async_request_refresh())


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the component from configuration.yaml."""
    hass.data.setdefault(DOMAIN, {})

    if hass.config_entries.async_entries(DOMAIN):
        _LOGGER.debug(
            "In __init.py.async_setup(): hass.config_entries.async_entries() = True"
        )
        return True

    if DOMAIN in config:
        _LOGGER.info("Found existing Get_EUDA_Data configuration.")
        # This section should not be reached, becaused it is deprecated
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=config[DOMAIN],
            )
        )
    _LOGGER.debug(f"In __init.py.async_setup(): No config entries found for {DOMAIN}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading services")

    _LOGGER.debug("Unloading update listener")
    hass.data[DOMAIN][entry.entry_id][UNDO_UPDATE_LISTENER]()

    return await async_unload_coordinator(hass, entry)


async def async_unload_coordinator(hass: HomeAssistant, entry: ConfigEntry):
    """Unload auth token based entry."""
    _LOGGER.debug("Unloading coordinator")
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA].coordinator

    _LOGGER.debug("Log out from Get_EUDA_Data")
    await coordinator.async_logout()
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        _LOGGER.debug("Unloading entry")
        del hass.data[DOMAIN][entry.entry_id]

    if not hass.data[DOMAIN]:
        _LOGGER.debug("Unloading data")
        del hass.data[DOMAIN]

    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


class PyCupraData:
    """Hold component state."""

    def __init__(self, config, name=None, coordinator=None):
        """Initialize the component state."""
        self.vehicles = set()
        self.instruments = set()
        self.config = config.get(DOMAIN, config)
        self.name = name
        self.coordinator = coordinator

    def instrument(self, vin, component, attr):
        """Return corresponding instrument."""
        return next(
            (
                instrument
                for instrument in (
                    self.coordinator.data
                    if self.coordinator is not None
                    else self.instruments
                )
                if instrument.vehicle.vin == vin
                and instrument.component == component
                and instrument.attr == attr
            ),
            None,
        )

    def vehicle_name(self, vehicle):
        """Provide a friendly name for a vehicle."""
        try:
            # Return name if configured by user
            if isinstance(self.name, str):
                if len(self.name) > 0:
                    return self.name
        except Exception:
            pass

        # Default name to nickname if supported, else vin number
        try:
            if vehicle.is_nickname_supported:
                return vehicle.nickname
            elif vehicle.vin:
                return vehicle.vin
        except Exception:
            _LOGGER.info("Name set to blank")
            return ""


class PyCupraEntity(Entity):
    """Base class for all PyCupra entities."""

    def __init__(self, data, vin, component, attribute, callback=None):
        """Initialize the entity."""

        def update_callbacks():
            if callback is not None:
                callback(self.hass, data.coordinator)

        self.data = data
        self.vin = vin
        self.component = component
        self.attribute = attribute
        self.coordinator = data.coordinator
        self.instrument.callback = update_callbacks
        self.callback = callback

    async def async_update(self) -> None:
        """Update the entity.

        Only used by the generic entity update service.
        """

        # Ignore manual update requests if the entity is disabled
        if not self.enabled:
            return

        await self.coordinator.update_only_selected_entity(self.instrument)
        # await self.coordinator.async_request_refresh()

    async def async_added_to_hass(self):
        """Register update dispatcher."""
        if self.coordinator is not None:
            self.async_on_remove(
                self.coordinator.async_add_listener(self.async_write_ha_state)
            )
        else:
            self.async_on_remove(
                async_dispatcher_connect(
                    self.hass, SIGNAL_STATE_UPDATED, self.async_write_ha_state
                )
            )

    @property
    def instrument(self):
        """Return corresponding instrument."""
        return self.data.instrument(self.vin, self.component, self.attribute)

    @property
    def icon(self):
        """Return the icon."""
        if self.instrument.attr in [
            "battery_level",
            "charging",
            "charging_state",
            "charging_time_left",
            "charging_estimated_end_time",
        ]:
            battery_level_instrument = self.data.instrument(self.vin, "sensor", "battery_level") 
            charging_instrument = self.data.instrument(self.vin, "binary_sensor", "charging_state")
            if battery_level_instrument is not None and charging_instrument is not None:
                return icon_for_battery_level(
                    battery_level=battery_level_instrument.state, 
                    charging=charging_instrument.state
                )
        # if self.instrument.attr in ["climatisation_time_left", "climatisation_estimated_end_time"]:
        #    if self.vehicle.electric_climatisation:
        #        return "mdi:radiator"
        #    else:
        #        return "mdi:radiator-off"
        return self.instrument.icon

    @property
    def vehicle(self):
        """Return vehicle."""
        return self.instrument.vehicle

    @property
    def _entity_name(self):
        return self.instrument.name

    @property
    def _vehicle_name(self):
        return self.data.vehicle_name(self.vehicle)

    @property
    def name(self):
        """Return full name of the entity."""
        return f"{self._entity_name}"

    @property
    def should_poll(self) -> bool:
        """Return the polling state."""
        return False

    @property
    def assumed_state(self) -> bool:
        """Return true if unable to access real state of entity."""
        return True

    @property
    def extra_state_attributes(self):
        """Return extra state attributes."""
        attributes = dict(
            self.instrument.attributes,
            model=f"{self.vehicle.model}/{self.vehicle.model_year}"
            if (self.vehicle.model_year != "unknown")
            else f"{self.vehicle.model}",
        )

        return attributes

    @property
    def device_info(self):
        """Return the device_info of the device."""
        return {
            "identifiers": {(DOMAIN, self.vin)},
            "name": self._vehicle_name,
            "manufacturer": self.vehicle.brand,
            "model": self.vehicle.model,
            "sw_version": None,
        }

    @property
    def available(self):
        """Return if sensor is available."""
        if self.data.coordinator is not None:
            return self.data.coordinator.last_update_success
        return True

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self.vin}-{self.component}-{self.attribute}"


class PyCupraCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(self, hass: HomeAssistant, entry, update_interval: timedelta):
        self.vin = entry.data[CONF_VEHICLE].upper()
        self.entry = entry
        self.platforms: list[str] = []
        self.report_last_updated = None
        self._logPrefix = self.entry.options.get(
            CONF_LOGPREFIX, self.entry.data.get(CONF_LOGPREFIX, None)
        )
        if self._logPrefix == "" or self._logPrefix == " ":
            _LOGGER.debug(
                f"Config entry for logPrefix='{self._logPrefix}'. Treating it as None."
            )
            self._logPrefix = None
        _LOGGER.debug(f"In PyCupraCoord.Init: logPrefix={self._logPrefix}")
        
        self.eudaConnection = EUDAConnection(
            session=async_create_clientsession(hass),
            brand=self.entry.data[CONF_BRAND],
            username=self.entry.data[CONF_USERNAME],
            password=self.entry.data[CONF_PASSWORD],
            fulldebug=self.entry.options.get(
                CONF_DEBUG, self.entry.data.get(CONF_DEBUG, DEFAULT_DEBUG)
            ),
            logPrefix=self._logPrefix,
            hass=hass,
        )
        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=update_interval)

    async def _async_update_data(self):
        """Update data via library."""
        eudaVehicles = await self.update()

        if not eudaVehicles:
            _LOGGER.error("No eudaVehicles found")
            raise UpdateFailed("No vehicles found.")

        conf_instruments = self.entry.data.get(CONF_INSTRUMENTS, {}).copy()
        #_LOGGER.debug(
        #        f"eudaVehicles={eudaVehicles}"
        #)
        eudaVehicle = self.eudaConnection.vehicle(self.vin)
        dashboard = eudaVehicle.dashboard(configuredInstruments=conf_instruments)

        return dashboard.instruments

    async def async_logout(self, event=None) -> bool:
        """Logout from Cupra/Seat portal"""
        _LOGGER.debug("Shutdown Get_EUDA_Data")
        try:
            if True: #self._euda:
                await self.eudaConnection.terminate()
                self.eudaConnection = None
        except Exception:
            _LOGGER.error(
                "Failed to log out and revoke tokens for Cupra/Seat portal. Some tokens might still be valid."
            )
            return False
        return True

    async def async_login(self) -> bool:
        """Login to Cupra/Seat portal"""
        # Check if we can login
        try:
            # if await self.connection.doLogin(tokenFile=TOKEN_FILE_NAME_AND_PATH) is False:
            if not await self.eudaConnection.doLogin():
                _LOGGER.error(
                    "Could not login to EUDA portal, please check your credentials and verify that the service is working"
                )
                return False
            _LOGGER.debug("called eudaConnection.do_login")
            # Get associated eudaVehicles before we continue
            await self.eudaConnection.getVehicles()
            loop = asyncio.get_running_loop()
            if not await loop.run_in_executor(
                None, self.eudaConnection.readTripStatisticsFile,self.vin
            ):
                _LOGGER.warning(
                    "readTripStatisticsFile was not successful. Is there no file? Ignoring this problem."
                )

            # Get associated vehicles before we continue
            eudaVehicle = self.eudaConnection.vehicle(self.vin)
            if eudaVehicle is None:
                _LOGGER.warning(
                    f"PyCupraCoordinator.async_login() called. But vehicle with VIN ending on '{self.vin[-4:]}' was not found."
                )

            return True
        except (PyCupraAccountLockedException, PyCupraAuthenticationException) as e:
            _LOGGER.error("In async_login.except. Exception:", e)
            # Raise auth failed error in config flow
            raise
        except Exception:
            raise

    async def update(self) -> EUDAVehicle:
        """Update data from API"""

        # Update vehicle data
        _LOGGER.debug("Updating data from Cupra/Seat API")
        try:
            eudaVehicles = None
            rc2 = False
            if True: #self._euda:
                eudaVehicles = self.eudaConnection.vehicles
                if self.eudaConnection._loginError is None:
                    try:
                        rc2 = await self.eudaConnection.update(self.vin)
                        if self.eudaConnection._loginError is not None:
                            _LOGGER.error(
                                f"An error occurred in update of EU data act data. Error: {self.eudaConnection._loginError}"
                            )
                            async_show_pycupra_notification(
                                self.hass,
                                f"An error occurred in update of EU data act data. Error: {self.eudaConnection._loginError}. If you think, it should work again, reload your PyCupra device.",
                                title="EUDA connection failed",
                                id="PyCupra_euda_error",
                            )
                    except Exception:
                        _LOGGER.error(
                            f"An error occurred in update of EU data act data. Error: {self.eudaConnection._loginError}"
                        )
                        async_show_pycupra_notification(
                            self.hass,
                            f"An error occurred in update of EU data act data. Error: {self.eudaConnection._loginError}. If you think, it should work again, reload your PyCupra device.",
                            title="EUDA connection failed",
                            id="PyCupra_euda_error",
                        )
                else:
                    rc2 = False
            if not rc2:
                _LOGGER.warning(
                    "Could not update from EUDA API. Continuing with old data"
                )
            return eudaVehicles
        except Exception as error:
            _LOGGER.warning(
                f"An error occured PyCupraCoordinator.update(). Error: {error}. Continuing with old vehicle data"
            )
            return eudaVehicles


def async_show_pycupra_notification(hass: HomeAssistant, message, title=None, id=None):
    """show a notification for pycupra messages"""
    async_pn_create(hass, message, title=title, notification_id=id)
    global COUNTER_FOR_PERSISTENT_NOTIFICATIONS
    COUNTER_FOR_PERSISTENT_NOTIFICATIONS = COUNTER_FOR_PERSISTENT_NOTIFICATIONS + 1
    if id:
        if not ("failed" in id or "error" in id):
            hass.async_create_task(
                async_sleep_and_dismiss_pycupra_notification(
                    hass, id, COUNTER_FOR_PERSISTENT_NOTIFICATIONS
                )
            )


async def async_sleep_and_dismiss_pycupra_notification(
    hass: HomeAssistant, id, counter
):
    """wait 2 minutes and then dismiss notification"""
    await asyncio.sleep(120)
    global COUNTER_FOR_PERSISTENT_NOTIFICATIONS
    if counter == COUNTER_FOR_PERSISTENT_NOTIFICATIONS:
        _LOGGER.debug("Dismissing open pycupra notification")
        async_pn_dismiss(hass, notification_id=id)
