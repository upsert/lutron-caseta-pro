"""
Platform for Lutron dimmers for lights.

Provides dimmable light functionality for Home Assistant.
"""
import logging

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_TRANSITION,
    SUPPORT_BRIGHTNESS,
    SUPPORT_TRANSITION,
    LightEntity,
    DOMAIN,
)
from homeassistant.const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_MAC,
    CONF_TYPE,
    CONF_NAME,
    CONF_ID,
)

from . import (
    Caseta,
    DEFAULT_TYPE,
    ATTR_AREA_NAME,
    ATTR_INTEGRATION_ID,
    CONF_AREA_NAME,
    CONF_TRANSITION_TIME,
    DOMAIN as COMPONENT_DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

# Max transition time supported is 4 hours
_MAX_TRANSITION = 14400


class CasetaData:
    """Data holder for a light."""

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

    async def read_output(self, mode, integration, action, value):
        """Receive output value from the bridge."""
        # find integration ID in devices
        if mode == Caseta.OUTPUT:
            for device in self._devices:
                if device.integration == integration:
                    _LOGGER.debug(
                        "Got light OUTPUT value: %s %d %d %f",
                        mode,
                        integration,
                        action,
                        value,
                    )
                    if action == Caseta.Action.SET:
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

    data = CasetaData(bridge)
    devices = [
        CasetaLight(
            light, data, discovery_info[CONF_MAC], discovery_info[CONF_TRANSITION_TIME]
        )
        for light in discovery_info[CONF_DEVICES]
    ]
    data.set_devices(devices)

    async_add_devices(devices)

    # register callbacks
    bridge.register(data.read_output)

    # start bridge main loop
    bridge.start(hass)


def _format_transition(transition) -> str:
    """Format a string for transition given as a float."""
    if transition is None:
        return transition

    if transition > _MAX_TRANSITION:
        _LOGGER.warning(
            "Transition exceeded maximum of 4 hours. 4 hours will be used instead."
        )
        transition = _MAX_TRANSITION
    if transition < 60:
        # format to two decimals for less than 60 seconds
        transition = "{:0>.2f}".format(transition)
    else:
        # else format HH:MM:SS
        minutes, seconds = divmod(transition, 60)
        hours, minutes = divmod(minutes, 60)
        transition = "{:0>2d}:{:0>2d}:{:0>2d}".format(
            int(hours), int(minutes), int(seconds)
        )
    return transition


# pylint: disable=too-many-instance-attributes
class CasetaLight(LightEntity):
    """Representation of a Lutron light."""

    def __init__(self, light, data, mac, transition):
        """Initialize a Lutron light."""
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
        self._mac = mac
        self._default_transition = transition

    async def async_added_to_hass(self):
        """Update initial state."""
        await self.query()

    async def query(self):
        """Query the bridge for the current level."""
        await self._data.caseta.query(
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
        return int((self._brightness / 100) * 255)

    @property
    def is_on(self):
        """Return true if light is on."""
        return self._is_on

    @property
    def supported_features(self):
        """Flag supported features."""
        return (SUPPORT_BRIGHTNESS | SUPPORT_TRANSITION) if self._is_dimmer else 0

    async def async_turn_on(self, **kwargs):
        """Instruct the light to turn on."""
        value = 100
        transition = None
        if self._is_dimmer:
            if ATTR_BRIGHTNESS in kwargs:
                value = "{:0>.2f}".format((kwargs[ATTR_BRIGHTNESS] / 255) * 100)
            if ATTR_TRANSITION in kwargs:
                transition = _format_transition(float(kwargs[ATTR_TRANSITION]))
            elif self._default_transition is not None:
                transition = _format_transition(self._default_transition)
        _LOGGER.debug(
            "Writing light OUTPUT value: %d %d %s %s",
            self._integration,
            Caseta.Action.SET,
            value,
            transition,
        )
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET, value, transition
        )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""
        transition = None
        if self._is_dimmer:
            if ATTR_TRANSITION in kwargs:
                transition = _format_transition(float(kwargs[ATTR_TRANSITION]))
            elif self._default_transition is not None:
                transition = _format_transition(self._default_transition)
        _LOGGER.debug(
            "Writing light OUTPUT value: %d %d 0 %s",
            self._integration,
            Caseta.Action.SET,
            str(transition),
        )
        await self._data.caseta.write(
            Caseta.OUTPUT, self._integration, Caseta.Action.SET, 0, transition
        )

    def update_state(self, brightness):
        """Update brightness value."""
        if self._is_dimmer:
            self._brightness = brightness
        self._is_on = brightness > 0
