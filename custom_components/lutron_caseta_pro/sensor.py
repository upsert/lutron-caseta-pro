"""
Platform for sensor for button press from a Pico wireless remote.

Provides a sensor for each Pico remote with a value that changes
depending on the button press.
"""
import logging

from homeassistant.components.sensor import DOMAIN
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_MAC, CONF_NAME, CONF_ID
from homeassistant.helpers.entity import Entity

from . import (
    Caseta,
    CONF_BUTTONS,
    ATTR_AREA_NAME,
    CONF_AREA_NAME,
    ATTR_INTEGRATION_ID,
    DOMAIN as COMPONENT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CasetaData:
    """Data holder for a sensor."""

    def __init__(self, caseta, hass):
        """Initialize the data holder."""
        self._caseta = caseta
        self._hass = hass
        self._devices = []

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

    async def read_output(self, mode, integration, component, value):
        """Receive output value from the bridge."""
        if mode == Caseta.DEVICE:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug(
                        "Got DEVICE value: %s %d %d %d",
                        mode,
                        integration,
                        component,
                        value,
                    )
                    state = 1 << component - device.minbutton
                    if value == Caseta.Button.PRESS:
                        _LOGGER.debug("Got Button Press, updating value to: %s", state)
                        device.update_state(state)
                        await device.async_update_ha_state()
                    elif value == Caseta.Button.RELEASE:
                        device.update_state(0)
                        _LOGGER.debug(
                            "Got Button Release, updating value to: %s", device.state
                        )
                        await device.async_update_ha_state()
                    break


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    await bridge.open()

    data = CasetaData(bridge, hass)
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
class CasetaPicoRemote(Entity):
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

    @property
    def integration(self):
        """Return the Integration ID."""
        return self._integration

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._mac is not None:
            return "{}_{}_{}_{}".format(
                COMPONENT_DOMAIN, DOMAIN, self._mac, self._integration
            )
        return None

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
