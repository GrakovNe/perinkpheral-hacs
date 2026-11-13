# SPDX-License-Identifier: MIT
"""What a screen of the device is made of."""

DOMAIN = "perinkpheral"

CONF_LAYOUT = "layout"
CONF_DEVICE = "device"  # the display's address on the network; empty: set up by hand
CONF_URL = "url"        # this Home Assistant's address, as the display reaches it
CONF_SECRET = "secret"  # what the display shows to be given its screen: made here, never typed

# Where the display asks for its screen, and the application on it that asks.
SCREEN_PATH = "/api/perinkpheral/screen"
DEVICE_APP = "ha"

LAYOUT_HERO = "hero"
LAYOUT_TILES = "tiles"
LAYOUT_SINGLE = "single"
LAYOUT_LIST = "list"

# The places of every layout, in the order the device fills them.
SLOTS = {
    LAYOUT_HERO: ["hero", "detail_1", "detail_2", "column_1", "column_2", "column_3", "column_4"],
    LAYOUT_TILES: ["tile_1", "tile_2", "tile_3", "tile_4"],
    LAYOUT_SINGLE: ["value"],
    LAYOUT_LIST: ["row_%d" % number for number in range(1, 9)],
}

# The pictures HA Companion draws, by the names it knows them under.
PICTURE_AUTO = "auto"
PICTURES = [
    PICTURE_AUTO, "none", "thermometer", "drop", "co2", "gauge", "plug", "bolt", "chip",
    "network", "battery", "bulb", "door", "home", "moon", "umbrella", "wind", "bell",
    "clock", "check", "warning", "info", "play",
]



def layout_of(entry):
    """The screen's layout: the one it was made with, until another is chosen for it."""
    return entry.options.get(CONF_LAYOUT) or entry.data.get(CONF_LAYOUT, LAYOUT_HERO)


def device_of(entry):
    """The display as Home Assistant lists it: what the screen's entities belong to."""
    device = entry.data.get(CONF_DEVICE)
    described = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title,
                 "manufacturer": "perINKpheral", "model": "Desk display"}
    if device:
        described["configuration_url"] = device if "://" in device else "http://" + device
    return described


# What the device keeps of a screen, in bytes.
SCREEN_MAX_BYTES = 1000
NAME_MAX = 23
