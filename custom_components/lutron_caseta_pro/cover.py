"""
Platform for Lutron shades.

Provides shade functionality for Home Assistant.
"""

import logging
from typing import Any

from homeassistant.components.cover import (
    ATTR_POSITION,
    DOMAIN,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_ID, CONF_MAC, CONF_NAME

from . import (
    ATTR_AREA_NAME,
    ATTR_INTEGRATION_ID,
    CONF_AREA_NAME,
    Caseta,
    CasetaData,
    CasetaEntity,
)

COVER_SUPPORT = (
    CoverEntityFeature.CLOSE
    | CoverEntityFeature.OPEN
    | CoverEntityFeature.SET_POSITION
    | CoverEntityFeature.STOP
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
        CasetaCover(cover, data, discovery_info[CONF_MAC])
        for cover in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


class CasetaCover(CasetaEntity, CoverEntity):
    """Representation of a Lutron shade."""

    def __init__(self, cover, data, mac):
        """Initialize a Lutron shade."""
        self._data = data
        self._name = cover[CONF_NAME]
        self._area_name = None
        if CONF_AREA_NAME in cover:
            self._area_name = cover[CONF_AREA_NAME]
            # if available, prepend area name to cover
            self._name = cover[CONF_AREA_NAME] + " " + cover[CONF_NAME]
        self._integration = int(cover[CONF_ID])
        self._position = 0
        self._mac = mac
        self._platform_domain = DOMAIN

    async def async_added_to_hass(self):
        """Update initial state."""
        await self.query()

    async def query(self):
        """Query the bridge for the current state of the device."""
        await self._data.caseta.query(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET
        )

    def update_state(self, new_position):
        """Update position value."""
        self._position = new_position
        self.async_write_ha_state()

    @property
    def extra_state_attributes(self):
        """Return device specific state attributes."""
        attr = {ATTR_INTEGRATION_ID: self._integration}
        if self._area_name:
            attr[ATTR_AREA_NAME] = self._area_name
        return attr

    @property
    def is_closed(self):
        """Return if the cover is closed."""
        return self._position < 1

    @property
    def current_cover_position(self):
        """Return current position of the cover."""
        return self._position

    async def async_open_cover(self, **kwargs: Any):
        """Open the cover."""
        _LOGGER.debug(
            "Writing cover OUTPUT value: %d %d",
            self._integration,
            Caseta.Action.RAISING,
        )
        # Raising must be used for STOP to work
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.RAISING, None
        )
        # When a Caseta.Action.SET action is sent to 100, the bridge
        # will always send back the state right away to 100.
        # We need to update the state ourself as the bridge
        # will not do this on a Caseta.Action.RAISING
        self.update_state(100)

    async def async_close_cover(self, **kwargs: Any):
        """Close the cover."""
        _LOGGER.debug(
            "Writing cover OUTPUT value: %d %d",
            self._integration,
            Caseta.Action.LOWERING,
        )
        # Lowering must be used for STOP to work
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.LOWERING, None
        )
        # When a Caseta.Action.SET action is sent to 0, the bridge
        # will always send back the state right away to 0.
        # We need to update the state ourself as the bridge
        # will not do this on a Caseta.Action.LOWERING
        self.update_state(0)

    async def async_set_cover_position(self, **kwargs: Any):
        """Move the cover to a specific position."""
        if ATTR_POSITION in kwargs:
            position = kwargs[ATTR_POSITION]
            # check values
            if position < 0:
                _LOGGER.warning("Tried to set cover position to less than 0.")
                position = 0
            if position > 100:
                _LOGGER.warning(
                    "Tried to set cover position to greater than maximum value 100."
                )
                position = 100
            _LOGGER.debug(
                "Writing cover OUTPUT value: %d %d %d %d %d",
                self._integration,
                Caseta.Action.SET,
                position,
                0,
                0,
            )
            # Parameters are Level, Fade, Delay
            # Fade is ignored and Delay set to 0
            await self._data.caseta.write(
                Caseta.OUTPUT, self._integration, Caseta.Action.SET, position, 0, 0
            )

    @property
    def supported_features(self) -> CoverEntityFeature:
        """Flag supported features."""
        return COVER_SUPPORT

    async def async_stop_cover(self, **kwargs: Any):
        """Stop raising or lowering the shade."""
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.STOP, None
        )
