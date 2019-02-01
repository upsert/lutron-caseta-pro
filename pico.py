"""
Component for Lutron Pico wireless controls.

This component creates a pico entity which can be used
to execute actions based on Pico button presses.

Original Author:
bigkraig (https://github.com/bigkraig)

"""

import logging
import voluptuous as vol
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers import script

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = 'pico'

BUTTON_0 = 'release'
BUTTON_1 = 'on'
BUTTON_2 = 'favorite'
BUTTON_4 = 'off'
BUTTON_8 = 'raise'
BUTTON_16 = 'lower'

STATE_NONE = 0
STATE_BUTTON_1 = 1
STATE_BUTTON_2 = 2
STATE_BUTTON_4 = 4
STATE_BUTTON_8 = 8
STATE_BUTTON_16 = 16

CONF_SENSOR = 'sensor'
CONF_BUTTONS = 'buttons'

CONF_BUTTON_1 = BUTTON_1
CONF_BUTTON_2 = BUTTON_2
CONF_BUTTON_4 = BUTTON_4
CONF_BUTTON_8 = BUTTON_8
CONF_BUTTON_16 = BUTTON_16

SCHEMA_BUTTONS = vol.Schema({
    vol.Optional(CONF_BUTTON_1): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_BUTTON_2): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_BUTTON_4): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_BUTTON_8): cv.SCRIPT_SCHEMA,
    vol.Optional(CONF_BUTTON_16): cv.SCRIPT_SCHEMA,
})


PICO_SCHEMA = vol.Schema({
    vol.Required(CONF_SENSOR): cv.entity_id,
    vol.Required(CONF_BUTTONS): vol.Schema(SCHEMA_BUTTONS),
})

DOMAIN = 'pico'

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: {
        cv.string: PICO_SCHEMA
    },
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass, config):
    """Set up the Pico component."""
    component = EntityComponent(_LOGGER, DOMAIN, hass)

    entities = []
    for pico_name, pico_config in config[DOMAIN].items():
        _LOGGER.info("Added pico %s", pico_name)
        entity = Pico(hass, pico_name, pico_config)
        entities.append(entity)

    await component.async_add_entities(entities)
    return True


class Pico(Entity):
    """Pico manages events from pico sensors."""

    def __init__(self, hass, name, config):
        """Initialize the Pico component."""
        self._config = config
        self._sensor = config[CONF_SENSOR]
        self._actionmap = dict()
        self._state = STATE_NONE
        self._name = name
        self._hass = hass

        for button, action in config[CONF_BUTTONS].items():
            self._actionmap[button] = _async_get_action(hass, action, button)

    # @callback
    async def state_changed(self, entity_id, _, new_state):
        value = new_state.state
        _LOGGER.debug("Received callback from %s with value %s",
                      entity_id, value)

        if int(value)&STATE_BUTTON_1 != 0 and BUTTON_1 in self._actionmap:
            _LOGGER.debug("Button 1 pressed, do action")
            await self._actionmap[BUTTON_1](entity_id)

        if int(value)&STATE_BUTTON_2 != 0 and BUTTON_2 in self._actionmap:
            _LOGGER.debug("Button 2 pressed, do action")
            await self._actionmap[BUTTON_2](self.entity_id)

        if int(value)&STATE_BUTTON_4 != 0 and BUTTON_4 in self._actionmap:
            _LOGGER.debug("Button 4 pressed, do action")
            await self._actionmap[BUTTON_4](self.entity_id)

        if int(value)&STATE_BUTTON_8 != 0 and BUTTON_8 in self._actionmap:
            _LOGGER.debug("Button 8 pressed, do action")
            await self._actionmap[BUTTON_8](self.entity_id)

        if int(value)&STATE_BUTTON_16 != 0 and BUTTON_16 in self._actionmap:
            _LOGGER.debug("Button 16 pressed, do action")
            await self._actionmap[BUTTON_16](self.entity_id)

        self._state = int(value)
        await self.async_update_ha_state()

    async def async_added_to_hass(self):
        async_track_state_change(self.hass, self._sensor, self.state_changed)

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the entity."""
        buttons = []
        if self._state&STATE_BUTTON_1:
            buttons.append(BUTTON_1)
        if self._state&STATE_BUTTON_2:
            buttons.append(BUTTON_2)
        if self._state&STATE_BUTTON_4:
            buttons.append(BUTTON_4)
        if self._state&STATE_BUTTON_8:
            buttons.append(BUTTON_8)
        if self._state&STATE_BUTTON_16:
            buttons.append(BUTTON_16)
        return ", ".join(buttons)


def _async_get_action(hass, sequence, button):
    """Return an action based on a configuration."""
    script_obj = script.Script(hass, sequence, button)

    async def action(entity_id):
        """Execute an action."""
        _LOGGER.info('Executing %s "%s" button', entity_id, button)

        try:
            await script_obj.async_run()
        except Exception as err:  # pylint: disable=broad-except
            script_obj.async_log_exception(
                _LOGGER,
                'Error while executing button action {} on {}'.format(button, entity_id), err)

    return action
