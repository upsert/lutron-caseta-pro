"""
Platform for Lutron fans.

Provides fan functionality for Home Assistant.
"""

import logging
from typing import Any

from homeassistant.components.fan import DOMAIN, FanEntity, FanEntityFeature
from homeassistant.const import CONF_DEVICES, CONF_HOST, CONF_ID, CONF_MAC, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from . import (
    ATTR_AREA_NAME,
    ATTR_INTEGRATION_ID,
    CONF_AREA_NAME,
    Caseta,
    CasetaData,
    CasetaEntity,
)

FAN_SUPPORT = (
    FanEntityFeature.SET_SPEED | FanEntityFeature.TURN_OFF | FanEntityFeature.TURN_ON
)

_LOGGER = logging.getLogger(__name__)


# pylint: disable=unused-argument
async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType = None,
) -> None:
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

    async_add_entities(devices, True)

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
        self._mac = mac
        self._percentage = None
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
        """Returns if the fan is on"""
        return self._percentage and self._percentage > 0

    @property
    def percentage(self) -> int | None:
        """Return the current speed."""
        return self._percentage

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        return FAN_SUPPORT

    @property
    def speed_count(self) -> int:
        """Return the number of supported speeds."""
        return 4

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Instruct the fan to turn on."""
        if percentage is None:
            percentage = 50
        await self.async_set_percentage(percentage)

    async def async_set_percentage(self, percentage: int) -> None:
        _LOGGER.debug(
            "Writing fan OUTPUT value: %d %d %.2f",
            self._integration,
            Caseta.Action.SET,
            percentage,
        )
        await self._data.caseta.write(
            Caseta.OUTPUT,
            self._integration,
            Caseta.Action.SET,
            percentage,
        )
        self._percentage = percentage
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Instruct the fan to turn off."""
        await self.async_set_percentage(0)

    def update_state(self, value):
        """Update internal state and fan speed."""
        self._percentage = value
        _LOGGER.debug("Fan speed is %s", self._percentage)
