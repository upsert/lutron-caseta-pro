"""
Platform for Lutron scenes.

Author: upsert (https://github.com/upsert)
Based on work by jhanssen (https://github.com/jhanssen/home-assistant/tree/caseta-0.40)
"""
import asyncio
import logging

from homeassistant.components.scene import Scene
from homeassistant.const import (CONF_DEVICES, CONF_HOST, CONF_NAME, CONF_ID)

# pylint: disable=relative-beyond-top-level
from ..lutron_caseta_pro import (Caseta, ATTR_SCENE_ID, CONF_SCENE_ID)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['lutron_caseta_pro']


class CasetaData:
    """Data holder for a scene."""

    def __init__(self, caseta, hass):
        self._caseta = caseta
        self._hass = hass
        self._devices = []
        self._added = {}
        self._later = None

    @property
    def devices(self):
        """Return list of devices."""
        return self._devices

    @property
    def caseta(self):
        """Return Caseta reference."""
        return self._caseta

    def set_devices(self, devices):
        """Set the list of devices."""
        self._devices = devices

    @asyncio.coroutine
    def read_output(self, mode, integration, component, action):
        """Receive output value from the bridge."""
        # only monitor integration ID 1 for scenes
        if mode == Caseta.DEVICE and integration == 1:
            # Expecting: ~DEVICE,1,Component Number,Action Number
            _LOGGER.debug("Got scene DEVICE value: %s %d %d %d",
                          mode, integration, component, action)
            for device in self._devices:
                if device.scene_id == component and action == Caseta.Button.PRESS:
                    _LOGGER.info("Scene %s activated.", component)
                    # nothing to update in Home Assistant for scenes
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
    devices = [CasetaScene(scene, data) for scene in discovery_info[CONF_DEVICES]]
    data.set_devices(devices)

    async_add_devices(devices)

    bridge.register(data.read_output)
    bridge.start(hass)

    return True


class CasetaScene(Scene):
    """Representation of a Lutron scene."""

    def __init__(self, scene, data):
        """Initialize a Lutron scene."""
        self._data = data
        self._name = scene[CONF_NAME]
        self._integration = int(scene[CONF_ID])
        self._scene_id = int(scene[CONF_SCENE_ID])

    @property
    def integration(self):
        """Return the integration ID."""
        return self._integration

    @property
    def scene_id(self):
        """Return the scene ID."""
        return self._scene_id

    @property
    def name(self):
        """Return the display name of this scene."""
        return self._name

    @property
    def device_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_SCENE_ID: self._scene_id}
        return attr

    @asyncio.coroutine
    def async_activate(self):
        """Activate the scene."""
        yield from self._data.caseta.write(Caseta.DEVICE, self._integration,
                                           self._scene_id, Caseta.Button.PRESS)
