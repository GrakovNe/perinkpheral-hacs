# SPDX-License-Identifier: MIT
"""Setting a screen up: its name, its layout and the display it is for; then what
stands in every place."""
import secrets

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.helpers.network import NoURLAvailableError, get_url

from .const import (CONF_DEVICE, CONF_LAYOUT, CONF_SECRET, CONF_URL, DOMAIN, LAYOUT_HERO,
                    LAYOUT_LIST, LAYOUT_SINGLE, LAYOUT_TILES, PICTURE_AUTO, PICTURES, SLOTS,
                    layout_of)
from .device import DeviceError, push_settings

CONF_NAME = "name"
DEFAULT_NAME = "perinkpheral"
LAYOUTS = [LAYOUT_HERO, LAYOUT_TILES, LAYOUT_SINGLE, LAYOUT_LIST]
SECRET_BYTES = 24


class PerinkpheralConfigFlow(ConfigFlow, domain=DOMAIN):
    """A new screen."""

    VERSION = 1

    def __init__(self) -> None:
        self._found_device = ""

    async def async_step_zeroconf(self, discovery_info):
        """A display announced itself on the network: its address is filled in."""
        self._found_device = str(discovery_info.host)
        # A display that has a screen already - added by hand, or found before -
        # is not offered again, under whichever of its names it was given.
        names = {self._found_device, discovery_info.hostname.rstrip(".").lower(),
                 discovery_info.hostname.rstrip(".").lower().removesuffix(".local")}
        for entry in self._async_current_entries():
            device = entry.data.get(CONF_DEVICE, "").lower()
            device = device.split("://")[-1].rstrip("/")
            if device in names or device.removesuffix(".local") in names:
                return self.async_abort(reason="already_configured")
        await self.async_set_unique_id(discovery_info.hostname)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": discovery_info.hostname.rstrip(".")}
        return await self.async_step_user()

    def _own_address(self) -> str:
        try:
            return get_url(self.hass, prefer_external=False)
        except NoURLAvailableError:
            return ""

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            data = {
                CONF_LAYOUT: user_input[CONF_LAYOUT],
                CONF_DEVICE: user_input.get(CONF_DEVICE, "").strip(),
                CONF_URL: user_input.get(CONF_URL, "").strip(),
                CONF_SECRET: secrets.token_urlsafe(SECRET_BYTES),
            }
            if data[CONF_DEVICE]:
                try:
                    await push_settings(self.hass, data[CONF_DEVICE], data[CONF_URL],
                                        data[CONF_SECRET])
                except DeviceError as failure:
                    errors["base"] = str(failure)
            if not errors:
                return self.async_create_entry(title=user_input[CONF_NAME], data=data)
        given = user_input or {}
        schema = vol.Schema({
            vol.Required(CONF_NAME, default=given.get(CONF_NAME, DEFAULT_NAME)):
                selector.TextSelector(),
            vol.Required(CONF_LAYOUT, default=given.get(CONF_LAYOUT, LAYOUT_HERO)):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=LAYOUTS, translation_key=CONF_LAYOUT,
                    mode=selector.SelectSelectorMode.LIST)),
            vol.Optional(CONF_DEVICE, default=given.get(CONF_DEVICE, self._found_device)):
                selector.TextSelector(),
            vol.Required(CONF_URL, default=given.get(CONF_URL, self._own_address())):
                selector.TextSelector(selector.TextSelectorConfig(
                    type=selector.TextSelectorType.URL)),
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        return PerinkpheralOptionsFlow()


class PerinkpheralOptionsFlow(OptionsFlow):
    """Changing a screen: its layout first, then what stands in the layout's places.
    What was put into the places of another layout is kept for when it is chosen again."""

    def __init__(self) -> None:
        self._layout = LAYOUT_HERO

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            self._layout = user_input[CONF_LAYOUT]
            return await self.async_step_places()
        schema = vol.Schema({
            vol.Required(CONF_LAYOUT, default=layout_of(self.config_entry)):
                selector.SelectSelector(selector.SelectSelectorConfig(
                    options=LAYOUTS, translation_key=CONF_LAYOUT,
                    mode=selector.SelectSelectorMode.LIST)),
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_places(self, user_input=None):
        slots = SLOTS[self._layout]
        if user_input is not None:
            # A field that was cleared is not in the answer at all: the place is empty.
            of_this_layout = tuple(slot + "_" for slot in slots)
            kept = {key: value for key, value in self.config_entry.options.items()
                    if not key.startswith(of_this_layout)}
            return self.async_create_entry(
                title="", data={**kept, **user_input, CONF_LAYOUT: self._layout})
        fields = {}
        for slot in slots:
            fields[vol.Optional(slot + "_entity")] = selector.EntitySelector()
            if slot != "hero" and not slot.startswith("detail"):
                fields[vol.Optional(slot + "_label")] = selector.TextSelector()
            if self._layout != LAYOUT_LIST:
                fields[vol.Optional(slot + "_picture", default=PICTURE_AUTO)] = (
                    selector.SelectSelector(selector.SelectSelectorConfig(
                        options=PICTURES, translation_key="picture",
                        mode=selector.SelectSelectorMode.DROPDOWN)))
        schema = self.add_suggested_values_to_schema(vol.Schema(fields),
                                                     self.config_entry.options)
        return self.async_show_form(step_id="places", data_schema=schema)
