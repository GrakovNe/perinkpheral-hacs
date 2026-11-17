# SPDX-License-Identifier: MIT
"""Telling the display where its screen is.

HA Companion on the display takes two settings the display's page does not
show: the server and a token. This writes them for the user - this Home
Assistant's address and a secret made for this screen - so that nobody copies
a token by hand. The application asks again at once whenever its settings
are written, which is also how a change made here reaches the screen
without waiting.
"""
import asyncio

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DEVICE_APP

TIMEOUT_S = 10


class DeviceError(Exception):
    """The display did not take the settings; the text is the reason."""


async def push_settings(hass: HomeAssistant, device: str, url: str, secret: str) -> None:
    address = device if "://" in device else "http://" + device
    try:
        async with asyncio.timeout(TIMEOUT_S):
            async with async_get_clientsession(hass).post(
                    "%s/api/apps/settings?app=%s" % (address.rstrip("/"), DEVICE_APP),
                    json={"server": url.rstrip("/"), "token": secret}) as answer:
                status = answer.status
                await answer.read()
    except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as failure:
        raise DeviceError("cannot_connect") from failure
    if status == 404:
        raise DeviceError("app_missing")
    if status != 200:
        raise DeviceError("refused")
