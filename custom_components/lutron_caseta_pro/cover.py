"""
Platform for Lutron shades.

Provides shade functionality for Home Assistant.
"""
import logging

from homeassistant.components.cover import (
    CoverEntity,
    SUPPORT_OPEN,
    SUPPORT_CLOSE,
    SUPPORT_STOP,
    ATTR_POSITION,
    SUPPORT_SET_POSITION,
    DOMAIN,
)
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_MAC, CONF_NAME, CONF_ID

from . import (
    Caseta,
    ATTR_AREA_NAME,
    CONF_AREA_NAME,
    ATTR_INTEGRATION_ID,
    DOMAIN as COMPONENT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


class CasetaData:
    """Data holder for a shade."""

    def __init__(self, caseta, hass):
        """Initialize the data holder."""
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

    async def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        # Expect: ~OUTPUT,Integration ID,Action Number,Parameters
        if mode == Caseta.OUTPUT:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug(
                        "Got cover OUTPUT value: %s %d %d %f",
                        mode,
                        integration,
                        action,
                        value,
                    )
                    if action == Caseta.Action.SET:
                        # update zone level, e.g. 90.00
                        device.update_state(value)
                        if device.hass is not None:
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
        CasetaCover(cover, data, discovery_info[CONF_MAC])
        for cover in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


class CasetaCover(CoverEntity):
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

    @property
    def integration(self):
        """Return the integration ID."""
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
        """Return the display name of this device."""
        return self._name

    @property
    def device_state_attributes(self):
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

    async def async_open_cover(self, **kwargs):
        """Open the cover."""
        # Rasing must be used for STOP to work
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.RAISING, None
        )
        # When a Caseta.Action.SET action is sent to 100, the bridge
        # will always send back the state right away to 100.
        # We need to update the state ourself as the bridge
        # will not do this on a Caseta.Action.RAISING
        self.update_state(100)

    async def async_close_cover(self, **kwargs):
        """Close the cover."""
        # Lowering must be used for STOP to work
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.LOWERING, None
        )
        # When a Caseta.Action.SET action is sent to 0, the bridge
        # will always send back the state right away to 0.
        # We need to update the state ourself as the bridge
        # will not do this on a Caseta.Action.LOWERING
        self.update_state(0)

    async def async_set_cover_position(self, **kwargs):
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
            # Parameters are Level, Fade, Delay
            # Fade is ignored and Delay set to 0
            await self._data.caseta.write(
                Caseta.OUTPUT, self._integration, Caseta.Action.SET, position, 0, 0
            )

    @property
    def supported_features(self):
        """Flag supported features."""
        return SUPPORT_OPEN | SUPPORT_CLOSE | SUPPORT_STOP | SUPPORT_SET_POSITION

    async def async_stop_cover(self, **kwargs):
        """Stop raising or lowering the shade."""
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.STOP, None
        )
