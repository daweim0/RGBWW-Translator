from __future__ import annotations

import base64
import json
import logging
import sys
import urllib, urllib.request, urllib.error


_LOGGER = logging.getLogger("RGBWW-Translator")
_LOGGER.warn("importing light.py. python version is {}".format(sys.version_info))


import voluptuous as vol

# Import the device class from the component that you want to support
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import (ATTR_BRIGHTNESS, PLATFORM_SCHEMA,
                                            LightEntity)
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType


from homeassistant.components.light import (
    ColorMode,
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    LightEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo


RED_COLOR_TEMP = 1000


# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required("name"): cv.string,
    vol.Required("wled_endpoint"): cv.string,
    vol.Required("min_displayed_temp"): cv.positive_int,
    vol.Required("light_min_temp"): cv.positive_int,
    vol.Required("light_max_temp"): cv.positive_int,
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
    wled_endpoint = config["wled_endpoint"]
    min_displayed_temp = config["min_displayed_temp"]
    light_min_temp = config["light_min_temp"]
    light_max_temp = config["light_max_temp"]
    # Add devices
    add_entities([FakeProxyLight(hass, name, wled_endpoint, min_displayed_temp, light_min_temp, light_max_temp)])



class FakeProxyLight(LightEntity):
    def __init__(self, hass, name, wled_endpoint, min_displayed_temp, light_min_temp, light_max_temp):
        self.hass = hass
        self._name = name
        self._wled_endpoint = wled_endpoint
        self._min_displayed_temp = min_displayed_temp
        self._light_min_temp =light_min_temp
        self._light_max_temp = light_max_temp
        self._state = False
        self._brightness = 0
        self._color_temp = 3000
        # self._attr_unique_id = "asdf" + base64.b64encode(bytes(wled_endpoint, 'utf-8')).decode('utf-8')

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def supported_color_modes(self) -> set[str] | None:
        """Return list of available color modes."""
        return {ColorMode.ONOFF, ColorMode.BRIGHTNESS, ColorMode.COLOR_TEMP}

    @property
    def brightness(self):
        return self._brightness

    @property
    def color_temp_kelvin(self):
        return self._color_temp

    @property
    def min_color_temp_kelvin(self):
        return self._min_displayed_temp

    @property
    def max_color_temp_kelvin(self):
        return self._light_max_temp

    def turn_on(self, **kwargs):
        _LOGGER.warn("turn_on() called with {}".format(kwargs))
        if ATTR_BRIGHTNESS in kwargs:
            self._brightness = kwargs[ATTR_BRIGHTNESS]
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            self._color_temp = kwargs[ATTR_COLOR_TEMP_KELVIN]

            
        _LOGGER.warn(f"{self._min_displayed_temp = }")
        _LOGGER.warn(f"{self._light_min_temp = }")
        _LOGGER.warn(f"{self._light_max_temp = }")
        _LOGGER.warn(f"{self._brightness = }")
        _LOGGER.warn(f"{self._color_temp = }")
            
        if self._light_min_temp <= self._color_temp and self._color_temp <= self._light_max_temp:
            payload = {"seg":[{"col":[[0,0,0, int(self._brightness)]], 
                               "cct": int(map_value(self._color_temp, self._light_min_temp, self._light_max_temp, 0, 255))}]}
        elif self._min_displayed_temp <= self._color_temp:
            alpha = map_value(self._color_temp, self._min_displayed_temp, self._light_min_temp, 0, 1)
            payload = {"seg":[{"col":[[int((1-alpha) * self._brightness),0,0, int(alpha * self._brightness)]],
                               "cct": 0}]}
        else:
            payload = {"seg":[{"col":[[0,0,0, int(self._brightness)]], "cct": 255}]}
        payload["seg"][0]["on"] = True
        _LOGGER.warn(f"{payload = }")
        send_post_http(self._wled_endpoint, payload)
        self._state = True

    def turn_off(self, **kwargs):
        _LOGGER.warn("turn_off() called with {}".format(kwargs))
        payload = {"seg":[{"on": False, "col":[[0,0,0, 0]], "cct": 128}]}
        send_post_http(self._wled_endpoint, payload)
        self._state = False

    async def async_added_to_hass(self):
        """Fetch current WLED state when HA starts."""
        _LOGGER.warn("Fetching initial WLED state at startup")

        url = self._wled_endpoint.replace("/json", "/json/state")

        try:
            result = await self.hass.async_add_executor_job(send_get_http_sync, url)
            data = json.loads(result)
            _LOGGER.warn(f"{data = }")

            # --- Parse state ---
            self._state = data.get("on", False)

            # WLED brightness is 0–255
            self._brightness = data.get("bri", 0)

            # WLED color temperature is 0–255 CCT slider
            if "cct" in data:
                cct = data["cct"]
                # convert 0–255 to Kelvin using same mapping you use in turn_on()
                kelvin = map_value(cct, 0, 255, self._light_min_temp, self._light_max_temp)
                self._color_temp = int(kelvin)

            _LOGGER.warn(f"Initial WLED state loaded: state={self._state}, "
                         f"brightness={self._brightness}, cct_kelvin={self._color_temp}")

        except Exception as e:
            _LOGGER.exception(f"Failed to fetch initial WLED state: {e}")


def send_get_http_sync(url):
    """Return the raw GET response body as string (blocking)."""
    req = urllib.request.Request(
        url,
        headers={"Content-Type": "application/json"},
        method="GET"
    )

    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def send_post_http(url, payload):
    _LOGGER.info(f"")    
    data = json.dumps(payload).encode('utf-8')
    print(f"{data = }")
    
    # Prepare the request
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json" 
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"Status Code: {response.getcode()}")
            print(f"Response: {result}")
            
    except urllib.error.HTTPError as e:
        _LOGGER.exception(f"HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        _LOGGER.exception(f"URL Error: {e.reason}")
    except Exception as e:
        _LOGGER.exception(f"General Error: {e}")


def send_get_http(url):
    _LOGGER.info(f"")
    # Prepare the request
    req = urllib.request.Request(
        url,
        headers={
            "Content-Type": "application/json" 
        },
        method='GET'
    )
    
    try:
        with urllib.request.urlopen(req) as response:
            result = response.read().decode('utf-8')
            print(f"Status Code: {response.getcode()}")
            print(f"Response: {result}")
            return result
            
    except urllib.error.HTTPError as e:
        _LOGGER.exception(f"HTTP Error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        _LOGGER.exception(f"URL Error: {e.reason}")
    except Exception as e:
        _LOGGER.exception(f"General Error: {e}")
    return ""


def map_value(x, in_min, in_max, out_min, out_max):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def map_k_to_rgb(brightness, x, k1, k2, k3):
    # Region 1: between k1 and k2 → fade from R to G
    if x <= k1:
        return [brightness, 0, 0]
    elif x >= k3:
        return [0, 0, brightness]
    elif x <= k2:
        # t goes 0 → 1 as x goes k1 → k2
        t = (x - k1) / (k2 - k1)
        r = brightness * (1 - t)
        g = brightness * t
        return [r, g, 0]
    else:
        # Region 2: between k2 and k3 → fade from G to B
        t = (x - k2) / (k3 - k2)
        g = brightness * (1 - t)
        b = brightness * t
        return [0, g, b]
