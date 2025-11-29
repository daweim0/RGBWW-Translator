from __future__ import annotations

import logging


_LOGGER = logging.getLogger("RGBWW-Translator")
_LOGGER.warning("importing light.py")


import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (ATTR_BRIGHTNESS, PLATFORM_SCHEMA,
                                            LightEntity)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


from homeassistant.components.light import (
    SUPPORT_COLOR_TEMP,
    SUPPORT_BRIGHTNESS,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    LightEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("name"): cv.string,
    vol.Required("target_light"): cv.string,
})


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the Awesome Light platform."""
    # Assign configuration variables.
    # The configuration check takes care they are present.
    _LOGGER.error("asdf")
    name = config["name"]
    target_light = config["target_light"]
    # Add devices
    add_entities([FakeProxyLight(hass, name, target_light)])



class FakeProxyLight(LightEntity):
    def __init__(self, hass, name, target_entity_id):
        self.hass = hass
        self._name = name
        self._target = target_entity_id
        self._state = False
        self._brightness = None
        self._color_temp = None

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR_TEMP

    @property
    def brightness(self):
        return self._brightness

    @property
    def color_temp(self):
        return self._color_temp

    def turn_on(self, **kwargs):
        _LOGGER.warn("turn_on() called with {}".format(kwargs))
        data = {"entity_id": self._target}
        if ATTR_BRIGHTNESS in kwargs:
            data[ATTR_BRIGHTNESS] = kwargs[ATTR_BRIGHTNESS]
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_COLOR_TEMP in kwargs:
            data[ATTR_COLOR_TEMP] = kwargs[ATTR_COLOR_TEMP]


