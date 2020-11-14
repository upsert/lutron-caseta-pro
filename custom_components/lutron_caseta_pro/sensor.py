"""
Platform for sensor for button press from a Pico wireless remote.

Provides a sensor for each Pico remote with a value that changes
depending on the button press.
"""
import logging

from homeassistant.components.sensor import DOMAIN
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_ID, CONF_MAC, CONF_NAME
from homeassistant.helpers.entity import Entity

from . import (
    ATTR_AREA_NAME,
    ATTR_INTEGRATION_ID,
    CONF_AREA_NAME,
    CONF_BUTTONS,
    Caseta,
    CasetaData,
    CasetaEntity,
)

_LOGGER = logging.getLogger(__name__)


class CasetaSensorData(CasetaData):
    """Caseta Data holder for sensor devices."""

    async def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        if mode != Caseta.DEVICE:
            return

        device = self._devices.get(integration)
        if device is None:
            _LOGGER.debug(
                "No DEVICE found for value: %s %d %d %d",
                mode,
                integration,
                action,
                value,
            )
            return

        _LOGGER.debug(
            "Got DEVICE value: %s %d %d %d",
            mode,
            integration,
            action,
            value,
        )

        state = 0
        if value == Caseta.Button.PRESS:
            state = 1 << action - device.minbutton
            _LOGGER.debug("Got Button Press, updating value to: %s", state)
        elif value == Caseta.Button.RELEASE:
            _LOGGER.debug("Got Button Release, updating value to: %s", state)
        else:
            return

        device.update_state(state)
        device.async_write_ha_state()


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    await bridge.open()

    data = CasetaSensorData(bridge)
    devices = [
        CasetaPicoRemote(pico, data, discovery_info[CONF_MAC])
        for pico in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


# pylint: disable=too-many-instance-attributes
class CasetaPicoRemote(CasetaEntity, Entity):
    """Representation of a Lutron Pico remote."""

    def __init__(self, pico, data, mac):
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
        self._mac = mac
        self._platform_domain = DOMAIN

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
