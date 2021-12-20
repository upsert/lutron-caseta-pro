"""
Platform for Lutron switches.

Provides switch functionality for Home Assistant.
"""
import logging

from homeassistant.components.switch import DOMAIN, SwitchEntity
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_ID, CONF_MAC, CONF_NAME

from . import (
    ATTR_AREA_NAME,
    ATTR_INTEGRATION_ID,
    CONF_AREA_NAME,
    Caseta,
    CasetaData,
    CasetaEntity,
)

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    await bridge.open()

    data = CasetaData(bridge)
    devices = [
        CasetaSwitch(switch, data, discovery_info[CONF_MAC])
        for switch in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices, True)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


class CasetaSwitch(CasetaEntity, SwitchEntity):
    """Representation of a Lutron switch."""

    def __init__(self, switch, data, mac):
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
        self._mac = mac
        self._platform_domain = DOMAIN

    async def async_added_to_hass(self):
        """Update initial state."""
        await self.query()

    async def query(self):
        """Query the bridge for the current level."""
        await self._data.caseta.query(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET
        )

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_INTEGRATION_ID: self._integration}
        if self._area_name:
            attr[ATTR_AREA_NAME] = self._area_name
        return attr

    @property
    def is_on(self):
        """Return true if switch is on."""
        return self._is_on

    async def async_turn_on(self, **kwargs):
        """Instruct the switch to turn on."""
        _LOGGER.debug(
            "Writing switch OUTPUT value: %d %d 100",
            self._integration,
            Caseta.Action.SET,
        )
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET, 100
        )

    async def async_turn_off(self, **kwargs):
        """Instruct the switch to turn off."""
        _LOGGER.debug(
            "Writing switch OUTPUT value: %d %d 0", self._integration, Caseta.Action.SET
        )
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET, 0
        )

    def update_state(self, value):
        """Update state."""
        self._is_on = value > 0
