"""
Platform for Lutron fans.

Provides fan functionality for Home Assistant.
"""
import asyncio
import logging

from homeassistant.components.fan import (
    SPEED_LOW,
    SPEED_MEDIUM,
    SPEED_HIGH,
    SPEED_OFF,
    SUPPORT_SET_SPEED,
    FanEntity,
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

SPEED_MEDIUM_HIGH = "medium_high"
SPEED_MAPPING = {
    SPEED_OFF: 0.00,
    SPEED_LOW: 25.10,
    SPEED_MEDIUM: 50.20,
    SPEED_MEDIUM_HIGH: 75.30,
    SPEED_HIGH: 100.00,
}


class CasetaData:
    """Data holder for a fan."""

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
                    _LOGGER.debug(
                        "Got fan OUTPUT value: %s %d %d %.2f",
                        mode,
                        integration,
                        action,
                        value,
                    )
                    if action == Caseta.Action.SET:
                        device.update_state(value)
                        if device.hass is not None:
                            yield from device.async_update_ha_state()
                        break


# pylint: disable=unused-argument
@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Configure the platform."""
    if discovery_info is None:
        return
    bridge = Caseta(discovery_info[CONF_HOST])
    yield from bridge.open()

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


class CasetaFan(FanEntity):
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

    @asyncio.coroutine
    def async_added_to_hass(self):
        """Update initial state."""
        yield from self.query()

    @asyncio.coroutine
    def query(self):
        """Query the bridge for the current level."""
        yield from self._data.caseta.query(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET
        )

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
        """Return the display name of this fan."""
        return self._name

    @property
    def should_poll(self):
        """No polling needed for fan."""
        return False

    @property
    def device_state_attributes(self):
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
        if SPEED_MAPPING[SPEED_MEDIUM_HIGH] < value <= SPEED_MAPPING[SPEED_HIGH]:
            self._speed = SPEED_HIGH
        elif SPEED_MAPPING[SPEED_MEDIUM] < value <= SPEED_MAPPING[SPEED_MEDIUM_HIGH]:
            self._speed = SPEED_MEDIUM_HIGH
        elif SPEED_MAPPING[SPEED_LOW] < value <= SPEED_MAPPING[SPEED_MEDIUM]:
            self._speed = SPEED_MEDIUM
        elif SPEED_MAPPING[SPEED_OFF] < value <= SPEED_MAPPING[SPEED_LOW]:
            self._speed = SPEED_LOW
        elif value == SPEED_MAPPING[SPEED_OFF]:
            self._speed = SPEED_OFF
        _LOGGER.debug("Fan speed is %s", self._speed)
