"""
Platform for Lutron sensor representing a button press from a Pico
wireless remote.

Original Author: jhanssen
Source: https://github.com/jhanssen/home-assistant/tree/caseta-0.40

Additional Authors:
upsert (https://github.com/upsert)
"""
import asyncio
import logging

from homeassistant.const import (CONF_DEVICES, CONF_HOST, CONF_NAME, CONF_ID)
from homeassistant.helpers.entity import Entity

# pylint: disable=relative-beyond-top-level
from ..lutron_caseta_pro import (Caseta, CONF_BUTTONS, ATTR_AREA_NAME,
                                 CONF_AREA_NAME, ATTR_INTEGRATION_ID)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['lutron_caseta_pro']


class CasetaData:
    """Data holder for a sensor."""
    def __init__(self, caseta, hass):
        self._caseta = caseta
        self._hass = hass
        self._devices = []
        self._added = {}
        self._later = None

    @property
    def devices(self):
        """Return the device list."""
        return self._devices

    @property
    def caseta(self):
        """Return a reference to Casetify instance."""
        return self._caseta

    def set_devices(self, devices):
        """Set the device list."""
        self._devices = devices

    @asyncio.coroutine
    def _check_added(self):
        """"Process and clear the added list."""
        yield from asyncio.sleep(15)
        _LOGGER.debug("Checking Caseta added")
        for integration in self._added:
            _LOGGER.debug("Removing Caseta added %d %d", integration,
                          self._added[integration])
            for device in self._devices:
                if device.integration == integration:
                    device.update_state(device.state & ~self._added[integration])
                    yield from device.async_update_ha_state()
                    _LOGGER.debug("Removed Caseta added %d %d",
                                  integration, self._added[integration])
                    break
        self._added.clear()

    @asyncio.coroutine
    def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        if mode == Caseta.DEVICE:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug("Got DEVICE value: %s %d %d %f", mode,
                                  integration, action, value)
                    state = 1 << action - device.minbutton
                    if value == Caseta.Button.PRESS:
                        _LOGGER.debug("Got Button Press, updating value")
                        device.update_state(device.state | state)
                        if integration in self._added:
                            self._added[integration] |= state
                        else:
                            self._added[integration] = state
                        if self._later is not None:
                            self._later.cancel()
                        self._later = self._hass.loop.create_task(self._check_added())
                        yield from device.async_update_ha_state()
                    elif value == Caseta.Button.RELEASE:
                        _LOGGER.debug("Got Button Release, updating value")
                        device.update_state(device.state & ~state)
                        if integration in self._added:
                            self._added[integration] &= ~state
                        yield from device.async_update_ha_state()
                    break


# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Setup the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    yield from bridge.open()

    data = CasetaData(bridge, hass)
    devices = [CasetaPicoRemote(pico, data) for pico in discovery_info[CONF_DEVICES]]
    data.set_devices(devices)

    async_add_devices(devices)

    bridge.register(data.read_output)
    bridge.start(hass)

    return True


class CasetaPicoRemote(Entity):
    """Representation of a Lutron Pico remote."""

    def __init__(self, pico, data):
        """Initialize a Lutron Pico."""
        self._data = data
        self._name = pico[CONF_NAME]
        self._area_name = None
        if CONF_AREA_NAME in pico:
            self._area_name = pico[CONF_AREA_NAME]
            # if available, prepend area name to sensor
            self._name = pico[CONF_AREA_NAME] + " " + pico[CONF_NAME]
        self._integration = int(pico[CONF_ID])
        self._buttons = pico[CONF_BUTTONS]
        self._minbutton = 100
        for button_num in self._buttons:
            if button_num < self._minbutton:
                self._minbutton = button_num
        self._state = 0

    @property
    def integration(self):
        """Return the Integration ID."""
        return self._integration

    @property
    def name(self):
        """Return the display name of this Pico."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_INTEGRATION_ID: self._integration}
        if self._area_name:
            attr[ATTR_AREA_NAME] = self._area_name
        return attr

    @property
    def minbutton(self):
        """Return the lowest number button for this keypad."""
        return self._minbutton

    @property
    def state(self):
        """State of the Pico device."""
        return self._state

    def update_state(self, state):
        """Update state."""
        self._state = state
