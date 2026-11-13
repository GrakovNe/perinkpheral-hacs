# SPDX-License-Identifier: MIT
"""The address the display asks: its secret in, its screen out."""
import hmac

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import CONF_SECRET, DOMAIN, SCREEN_PATH, layout_of
from .render import render

BEARER = "Bearer "


class ScreenView(HomeAssistantView):
    """Not behind Home Assistant's own login: the display has no user's token, only the
    secret this integration made for it - good for this one address and nothing else."""

    url = SCREEN_PATH
    name = "api:perinkpheral:screen"
    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass

    async def get(self, request: web.Request) -> web.Response:
        given = request.headers.get("Authorization", "")
        shown = given[len(BEARER):] if given.startswith(BEARER) else ""
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            secret = entry.data.get(CONF_SECRET, "")
            if secret and shown and hmac.compare_digest(secret.encode(), shown.encode()):
                screen = render(layout_of(entry), entry.options, self._hass.states.get)
                return web.Response(text=screen, content_type="text/plain", charset="utf-8")
        return web.Response(status=401, text="Unknown display.")
