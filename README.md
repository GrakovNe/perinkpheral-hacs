<img src="https://raw.githubusercontent.com/Perinkpheral/perinkpheral-os/main/assets/mark/mark-on-paper-512.png" width="96" alt="The perINKpheral mark">

# perINKpheral for Home Assistant

Home Assistant integration for [perINKpheral](https://perinkpheral.dev).
Configures display layouts and entities for the HA Companion application.

[Device setup](https://perinkpheral.dev/setup) -
[Application catalog](https://github.com/perinkpheral/perinkpheral-apps/tree/main/catalog).

## Installation

Requires Home Assistant, HACS and HA Companion (`ha`) installed from the device's catalog.

1. Add this repository to HACS as an integration and download it.
2. Restart Home Assistant, then add perINKpheral under Settings - Devices & services.
3. Set the display address and the Home Assistant URL reachable from the display.
4. Configure the layout and entities in the integration options.

[![Add the repository to HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Perinkpheral&repository=perinkpheral-hacs&category=integration)
[![Add the integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=perinkpheral)

The integration writes only `server` and `token` to HA Companion. The display
fetches its screen from Home Assistant. A sensor exposes the screen text in
Home Assistant; a refresh button requests an update on the display.

[HA Companion's reference](https://github.com/perinkpheral/perinkpheral-apps/blob/main/apps/ha/README.md)
describes the screen format rendered by this integration.
Application code belongs in [perinkpheral-apps](https://github.com/perinkpheral/perinkpheral-apps);
this repository owns the Home Assistant component. The device API is documented in
[the firmware repository](https://github.com/perinkpheral/perinkpheral/blob/main/docs/api/openapi.yaml).

## Development

Rendering and pairing tests run with Python 3, without Home Assistant:

```sh
python3 tests/test_render.py
python3 tests/test_config_flow.py
```

- `custom_components/perinkpheral/` - integration, configuration flow and screen rendering.
- `tests/` - rendering and pairing tests.
- `hacs.json` - HACS package configuration.

CI runs rendering and pairing tests, hassfest and HACS validation on every push.
Each successful push to `main` releases `perinkpheral.zip` for HACS.

## License

[MIT](LICENSE).
