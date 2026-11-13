# SPDX-License-Identifier: MIT
"""A button that makes the display ask for its screen now."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import tell_the_display
from .const import CONF_DEVICE


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry,
                            async_add_entities: AddEntitiesCallback) -> None:
    if entry.data.get(CONF_DEVICE):
        async_add_entities([RefreshButton(entry)])


class RefreshButton(ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, entry: ConfigEntry) -> None:
        self._entry = entry
        self._attr_name = entry.title + " refresh"
        self._attr_unique_id = entry.entry_id + "_refresh"

    async def async_press(self) -> None:
        if not await tell_the_display(self.hass, self._entry):
            raise HomeAssistantError("The display did not answer.")
