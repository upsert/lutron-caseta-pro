"""
Platform for Lutron switches.

Author: upsert (https://github.com/upsert)
Based on work by jhanssen (https://github.com/jhanssen/home-assistant/tree/caseta-0.40)
"""
import asyncio
import logging

from homeassistant.components.switch import SwitchDevice
from homeassistant.const import (CONF_DEVICES, CONF_HOST, CONF_NAME, CONF_ID)

# pylint: disable=relative-beyond-top-level
from ..lutron_caseta_pro import (Caseta, ATTR_AREA_NAME, CONF_AREA_NAME, ATTR_INTEGRATION_ID)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['lutron_caseta_pro']


class CasetaData:
    """Data holder for a switch."""

    def __init__(self, caseta):
        """Initialize the data holder."""
        self._caseta = caseta
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

    @asyncio.coroutine
    def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        # find integration ID in devices
        if mode == Caseta.OUTPUT:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug("Got switch OUTPUT value: %s %d %d %f",
                                  mode, integration, action, value)
                    if action == Caseta.Action.SET:
                        device.update_state(value)
                        yield from device.async_update_ha_state()
                        break


# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Initialize the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    yield from bridge.open()

    data = CasetaData(bridge)
    devices = [CasetaSwitch(switch, data) for switch in discovery_info[CONF_DEVICES]]
    data.set_devices(devices)

    for device in devices:
        yield from device.query()

    async_add_devices(devices)

    bridge.register(data.read_output)
    bridge.start(hass)

    return True


class CasetaSwitch(SwitchDevice):
    """Representation of a Lutron switch."""

    def __init__(self, switch, data):
        """Initialize a Lutron switch."""
        self._data = data
        self._name = switch[CONF_NAME]
        self._area_name = None
        if CONF_AREA_NAME in switch:
            self._area_name = switch[CONF_AREA_NAME]
            # if available, prepend area name to switch
            self._name = switch[CONF_AREA_NAME] + " " + switch[CONF_NAME]
        self._integration = int(switch[CONF_ID])
        self._is_on = False

    @asyncio.coroutine
    def query(self):
        """Query the bridge for the current level."""
        yield from self._data.caseta.query(Caseta.OUTPUT, self._integration, Caseta.Action.SET)

    @property
    def integration(self):
        """Return the Integration ID."""
        return self._integration

    @property
    def name(self):
        """Return the display name of this switch."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_INTEGRATION_ID: self._integration}
        if self._area_name:
            attr[ATTR_AREA_NAME] = self._area_name
        return attr

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._is_on

    @asyncio.coroutine
    def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        _LOGGER.debug("Writing switch OUTPUT value: %d %d 100",
                      self._integration, Caseta.Action.SET)
        yield from self._data.caseta.write(Caseta.OUTPUT, self._integration, Caseta.Action.SET, 100)

    @asyncio.coroutine
    def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        _LOGGER.debug("Writing switch OUTPUT value: %d %d 0", self._integration, Caseta.Action.SET)
        yield from self._data.caseta.write(Caseta.OUTPUT, self._integration, Caseta.Action.SET, 0)

    def update_state(self, value):
        """Update state."""
        self._is_on = value > 0
