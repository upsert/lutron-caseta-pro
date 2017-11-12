"""
Platform for Lutron Caseta lights.

Original Author: jhanssen
Source: https://github.com/jhanssen/home-assistant/tree/caseta-0.40

Additional Authors:
upsert (https://github.com/upsert)
"""
import asyncio
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS, ATTR_TRANSITION, SUPPORT_BRIGHTNESS, SUPPORT_TRANSITION, Light)
from homeassistant.const import (CONF_DEVICES, CONF_HOST, CONF_TYPE, CONF_NAME, CONF_ID)

# pylint: disable=relative-beyond-top-level
from ..lutron_caseta_pro import (Caseta, DEFAULT_TYPE, ATTR_AREA_NAME, CONF_AREA_NAME, ATTR_INTEGRATION_ID)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['lutron_caseta_pro']


class CasetaData:
    """Data holder for a light."""

    def __init__(self, caseta):
        self._caseta = caseta
        self._devices = []

    @property
    def devices(self):
        return self._devices

    @property
    def caseta(self):
        return self._caseta

    def set_devices(self, devices):
        self._devices = devices

    @asyncio.coroutine
    def read_output(self, mode, integration, action, value):
        # find integration in devices
        if mode == Caseta.OUTPUT:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug("Got OUTPUT value: %s %d %d %f", mode, integration, action, value)
                    if action == Caseta.Action.SET:
                        device.update_state(value)
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

    data = CasetaData(bridge)
    devices = [CasetaLight(light, data) for light in discovery_info[CONF_DEVICES]]
    data.set_devices(devices)

    for device in devices:
        yield from device.query()

    async_add_devices(devices)

    bridge.register(data.read_output)
    bridge.start(hass)

    return True


class CasetaLight(Light):
    """Representation of a Caseta Light."""

    def __init__(self, light, data):
        """Initialize a Caseta Light."""
        self._data = data
        self._name = light[CONF_NAME]
        self._area_name = None
        if CONF_AREA_NAME in light:
            self._area_name = light[CONF_AREA_NAME]
            # if available, prepend area name to light
            self._name = light[CONF_AREA_NAME] + " " + light[CONF_NAME]
        self._integration = int(light[CONF_ID])
        self._is_dimmer = light[CONF_TYPE] == DEFAULT_TYPE
        self._is_on = False
        self._brightness = 0

    @asyncio.coroutine
    def query(self):
        yield from self._data.caseta.query(Caseta.OUTPUT, self._integration, Caseta.Action.SET)

    @property
    def integration(self):
        return self._integration

    @property
    def name(self):
        """Return the display name of this light."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_INTEGRATION_ID: self._integration}
        if self._area_name:
            attr[ATTR_AREA_NAME] = self._area_name
        return attr

    @property
    def brightness(self):
        """Brightness of the light (an integer in the range 1-255)."""
        return (self._brightness / 100) * 255

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    @property
    def supported_features(self):
        """Flag supported features."""
        return (SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION) if self._is_dimmer else 0

    def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        value = 100
        transition = None
        if self._is_dimmer:
            if ATTR_BRIGHTNESS in kwargs:
                value = (kwargs[ATTR_BRIGHTNESS] / 255) * 100
            if ATTR_TRANSITION in kwargs:
                transition = ":" + str(kwargs[ATTR_TRANSITION])
        _LOGGER.debug("Writing light OUTPUT value: %d %d %f %s", self._integration, Caseta.Action.SET, value,
                      str(transition))
        yield from self._data.caseta.write(Caseta.OUTPUT, self._integration, Caseta.Action.SET, value,
                                           transition)

    def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        transition = None
        if self._is_dimmer:
            if ATTR_TRANSITION in kwargs:
                transition = ":" + str(kwargs[ATTR_TRANSITION])
        _LOGGER.debug("Writing light OUTPUT value: %d %d off %s", self._integration, Caseta.Action.SET,
                      str(transition))
        yield from self._data.caseta.write(Caseta.OUTPUT, self._integration, Caseta.Action.SET, 0,
                                           transition)

    def update_state(self, brightness):
        """Update brightness value."""
        if self._is_dimmer:
            self._brightness = brightness
        self._is_on = brightness > 0
