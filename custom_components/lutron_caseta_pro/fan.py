"""
Platform for Lutron fans.

Provides fan functionality for Home Assistant.
"""
import logging

from homeassistant.components.fan import (
    DOMAIN,
    SPEED_HIGH,
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    FanEntity,
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

_LOGGER = logging.getLogger(__name__)

SPEED_MEDIUM_HIGH = "medium_high"
SPEED_MAPPING = {
    SPEED_OFF: 0.00,
    SPEED_LOW: 25.00,
    SPEED_MEDIUM: 50.00,
    SPEED_MEDIUM_HIGH: 75.00,
    SPEED_HIGH: 100.00,
}


# pylint: disable=unused-argument
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    await bridge.open()

    data = CasetaData(bridge)
    devices = [
        CasetaFan(fan, data, discovery_info[CONF_MAC])
        for fan in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices, True)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


class CasetaFan(CasetaEntity, FanEntity):
    """Representation of a Lutron fan."""

    def __init__(self, fan, data, mac):
        """Initialize a Lutron fan."""
        self._data = data
        self._name = fan[CONF_NAME]
        self._area_name = None
        if CONF_AREA_NAME in fan:
            self._area_name = fan[CONF_AREA_NAME]
            # if available, prepend area name to fan
            self._name = fan[CONF_AREA_NAME] + " " + fan[CONF_NAME]
        self._integration = int(fan[CONF_ID])
        self._is_on = False
        self._mac = mac
        self._speed = SPEED_OFF
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
        """Return true if fan is on."""
        return self._is_on

    @property
    def speed(self) -> str:
        """Return the current speed."""
        return self._speed

    @property
    def speed_list(self) -> list:
        """Get the list of available speeds."""
        return [SPEED_OFF, SPEED_LOW, SPEED_MEDIUM, SPEED_MEDIUM_HIGH, SPEED_HIGH]

    @property
    def supported_features(self) -> int:
        """Flag supported features."""
        return SUPPORT_SET_SPEED

    async def async_turn_on(self, speed: str = None, **kwargs) -> None:
        """Instruct the fan to turn on."""
        if speed is None:
            speed = SPEED_HIGH
        await self.async_set_speed(speed)

    async def async_set_speed(self, speed: str) -> None:
        """Set the speed of the fan."""
        self._speed = speed
        if speed not in SPEED_MAPPING:
            _LOGGER.debug("Unknown speed %s, setting to %s", speed, SPEED_HIGH)
            self._speed = SPEED_HIGH
        _LOGGER.debug(
            "Writing fan OUTPUT value: %d %d %.2f",
            self._integration,
            Caseta.Action.SET,
            SPEED_MAPPING[self._speed],
        )
        await self._data.caseta.write(
            Caseta.OUTPUT,
            self._integration,
            Caseta.Action.SET,
            SPEED_MAPPING[self._speed],
        )

    async def async_turn_off(self, **kwargs) -> None:
        """Instruct the fan to turn off."""
        await self.async_set_speed(SPEED_OFF)

    def update_state(self, value):
        """Update internal state and fan speed."""
        self._is_on = value > SPEED_MAPPING[SPEED_OFF]
        if value == SPEED_MAPPING[SPEED_HIGH]:
            self._speed = SPEED_HIGH
        elif value == SPEED_MAPPING[SPEED_MEDIUM_HIGH]:
            self._speed = SPEED_MEDIUM_HIGH
        elif value == SPEED_MAPPING[SPEED_MEDIUM]:
            self._speed = SPEED_MEDIUM
        elif value == SPEED_MAPPING[SPEED_LOW]:
            self._speed = SPEED_LOW
        elif value == SPEED_MAPPING[SPEED_OFF]:
            self._speed = SPEED_OFF
        _LOGGER.debug("Fan speed is %s", self._speed)
