# SPDX-License-Identifier: MIT
"""perINKpheral: screens for the desk display, put together in Home Assistant.

A screen is a layout and the entities in its places. The display asks this
integration for it, showing a secret the integration gave it when the
screen was set up; nobody types a token. A sensor shows the same text in
Home Assistant, and a button makes the display ask now.
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_DEVICE, CONF_SECRET, CONF_URL, DOMAIN
from .device import DeviceError, push_settings
from .view import ScreenView

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]
VIEW_IS_UP = DOMAIN + "_view"
LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if not hass.data.get(VIEW_IS_UP):
        hass.http.register_view(ScreenView(hass))
        hass.data[VIEW_IS_UP] = True
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_changed))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def tell_the_display(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Writes the display's settings again, which makes it ask for its screen now.
    False when there is no display to tell, or it did not answer."""
    device = entry.data.get(CONF_DEVICE)
    if not device:
        return False
    try:
        await push_settings(hass, device, entry.data[CONF_URL], entry.data[CONF_SECRET])
    except DeviceError as failure:
        LOGGER.warning("The display at %s was not told: %s", device, failure)
        return False
    return True


async def _changed(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """The places were changed: the sensor is made anew, and the display shows them."""
    await hass.config_entries.async_reload(entry.entry_id)
    await tell_the_display(hass, entry)
