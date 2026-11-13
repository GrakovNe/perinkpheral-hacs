# perINKpheral for Home Assistant

Screens for the [perINKpheral](https://github.com/GrakovNe/perinkpheral) desk display, put
together in Home Assistant's own interface: choose a layout, put entities into its places.
No YAML, no templates, and no token to copy: the integration sets the display up itself.

**Status: 0.3.0, the first release.** It runs in the author's Home Assistant (2026.10):
adding a screen, the forms, the sensor, the display set up from here. Newer than that
run, and not yet seen there: the display's entry in the list of devices, the icon. Tell us
what breaks.

## Install and set up

Four steps, in this order. The second button works only after the third step: before it
Home Assistant does not know the integration and says it "does not support configuration".

1. **Add the repository to HACS:**

   [![Add the repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=GrakovNe&repository=perinkpheral-hacs&category=integration)

2. **Download it.** The button only adds the repository to HACS's list: on the page it
   opens, press **Download**.
3. **Restart Home Assistant** (Settings - System - Restart).
4. **Add the integration:**

   [![Add the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=perinkpheral)

Without HACS, instead of steps 1 and 2: copy `custom_components/perinkpheral` into the
`custom_components` folder of the configuration.

On the display: install **HA Companion** (version 0.2.0 or later) from its page.

### A screen

1. In the form of step 4: the screen's name, its layout, the display's address
   (`192.168.1.70`, or `perinkpheral.local`; a display on the network is offered by itself)
   and this Home Assistant's address as the display reaches it.

   | Layout | What it is |
   |---|---|
   | One large value, two details, up to four columns | the weather's composition |
   | Up to four tiles | one, two halves or four quarters |
   | One value | as large as it goes |
   | A list | up to eight names and values |

   The integration writes HA Companion's settings on the display: where to ask, and a
   secret made for this screen. The secret opens one address, the screen's, and nothing
   else in Home Assistant.
2. **Configure** on the integration's card, as often as you like: the layout first - it
   can be changed, and what was put into another layout's places is kept - then an entity
   for each place, a name where the layout shows one, a picture (Automatic takes it from
   what kind of sensor it is). An empty place is left out. A **unit** may be
   written for a place where the entity's own does not fit - or a dash, for none. The
   display shows the change at once.

What you get in Home Assistant: a sensor with the screen's text, to look at, and a
**refresh** button that makes the display ask now. Left alone, the display asks at the
pace set in HA Companion's settings.

Names go to the display as they are. It draws the letters it has glyphs for - Latin with
marks, Cyrillic and Greek are packs added on its page (Settings, Language) - and spells
the rest in Latin letters.

## By hand

Leave the display's address empty and the integration only makes the sensor. In HA
Companion's settings on the display's page give the server, a long-lived access token and,
as Sensor, `sensor.<the screen's name>`.

## How it talks

- The display asks `GET /api/perinkpheral/screen` with `Authorization: Bearer <secret>`
  and gets a few lines of text. Home Assistant never calls the display for data.
- The integration calls the display only to write those settings
  (`POST /api/apps/settings?app=ha`), which is also what makes it ask at once.
