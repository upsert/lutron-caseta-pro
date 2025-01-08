"""
Platform for Lutron scenes.

Provides access to the scenes defined in Lutron system.
"""

import logging

from homeassistant.components.scene import DOMAIN, Scene
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_ID, CONF_MAC, CONF_NAME

from . import ATTR_SCENE_ID, CONF_SCENE_ID, Caseta, CasetaData, CasetaEntity
from . import DOMAIN as COMPONENT_DOMAIN

_LOGGER = logging.getLogger(__name__)


class CasetaSceneData(CasetaData):
    """Caseta Data holder."""

    def set_devices(self, devices):
        """Set the device list."""
        self._devices = {device.scene_id: device for device in devices}

    async def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        # only monitor integration ID 1 for scenes
        # Expecting: ~DEVICE,1,Component Number,Action Number
        if mode != Caseta.DEVICE or integration != 1:
            return

        device = self._devices.get(action)
        if device is None:
            return

        if action == Caseta.Button.PRESS:
            _LOGGER.info("Scene %s activated.", action)
            # nothing to update in Home Assistant for scenes


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    await bridge.open()

    data = CasetaSceneData(bridge)
    devices = [
        CasetaScene(scene, data, discovery_info[CONF_MAC])
        for scene in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


class CasetaScene(CasetaEntity, Scene):
    """Representation of a Lutron scene."""

    def __init__(self, scene, data, mac):
        """Initialize a Lutron scene."""
        self._data = data
        self._name = scene[CONF_NAME]
        self._integration = int(scene[CONF_ID])
        self._scene_id = int(scene[CONF_SCENE_ID])
        self._mac = mac

    @property
    def scene_id(self):
        """Return the scene ID."""
        return self._scene_id

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        if self._mac is not None:
            return f"{COMPONENT_DOMAIN}_{DOMAIN}_{self._mac}_{self._integration}_{self._scene_id}"
        return None

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_SCENE_ID: self._scene_id}
        return attr

    async def async_activate(self):
        """Activate the scene."""
        await self._data.caseta.write(
            Caseta.DEVICE, self._integration, self._scene_id, Caseta.Button.PRESS
        )
