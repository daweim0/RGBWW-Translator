from __future__ import annotations


from homeassistant.components.light import (
    SUPPORT_COLOR_TEMP,
    SUPPORT_BRIGHTNESS,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP,
    LightEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo


DOMAIN = "light"


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    target_light = entry.data.get("target_light")
    name = entry.data.get("name", "Fake Proxy Light")
    async_add_entities([FakeProxyLight(hass, name, target_light)])


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

    async def async_turn_on(self, **kwargs):
        data = {"entity_id": self._target}
        if ATTR_BRIGHTNESS in kwargs:
            data[ATTR_BRIGHTNESS] = kwargs[ATTR_BRIGHTNESS]
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_COLOR_TEMP in kwargs:
            data[ATTR_COLOR_TEMP] = kwargs[ATTR_COLOR_TEMP]
