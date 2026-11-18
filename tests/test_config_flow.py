# SPDX-License-Identifier: MIT
"""Exercise the real configuration flow with an in-memory HA and device transport."""
import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest

PACKAGE = Path(__file__).resolve().parents[1] / "custom_components" / "perinkpheral"


def module(name, **attributes):
    result = types.ModuleType(name)
    result.__dict__.update(attributes)
    sys.modules[name] = result
    return result


class ConfigFlow:
    entries = []

    def __init_subclass__(cls, **kwargs):
        pass

    def _async_current_entries(self):
        return self.entries

    def async_abort(self, reason):
        return {"type": "abort", "reason": reason}

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, title, data):
        entry = types.SimpleNamespace(title=title, data=data)
        self.entries.append(entry)
        return {"type": "create_entry", "entry": entry}


module("voluptuous", Schema=lambda fields: fields,
       Required=lambda key, **kwargs: key, Optional=lambda key, **kwargs: key)
module("homeassistant")
module("homeassistant.config_entries", ConfigEntry=object, ConfigFlow=ConfigFlow, OptionsFlow=object)
module("homeassistant.core", callback=lambda function: function)
module("homeassistant.helpers", selector=types.SimpleNamespace(
    TextSelector=lambda *args: None, TextSelectorConfig=lambda **kwargs: kwargs,
    TextSelectorType=types.SimpleNamespace(URL="url"),
    SelectSelector=lambda *args: None, SelectSelectorConfig=lambda **kwargs: kwargs,
    SelectSelectorMode=types.SimpleNamespace(LIST="list"),
))
module("homeassistant.helpers.network", NoURLAvailableError=RuntimeError, get_url=lambda hass, **kwargs: "")
module("perinkpheral", __path__=[str(PACKAGE)])
pushes = []


async def push_settings(hass, device, url, secret):
    pushes.append((device, url, secret))


module("perinkpheral.device", DeviceError=RuntimeError, push_settings=push_settings)


def load(name):
    spec = importlib.util.spec_from_file_location("perinkpheral." + name, PACKAGE / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    spec.loader.exec_module(result)
    return result


const = load("const")
flow = load("config_flow")


class PairingTests(unittest.TestCase):
    def setUp(self):
        ConfigFlow.entries.clear()
        pushes.clear()
        flow.push_settings = push_settings
        self.progress = []
        manager = types.SimpleNamespace(async_has_matching_flow=lambda candidate: any(
            candidate is not other and candidate.is_matching(other) for other in self.progress))
        self.hass = types.SimpleNamespace(config_entries=types.SimpleNamespace(flow=manager))

    def new_flow(self):
        instance = flow.PerinkpheralConfigFlow()
        instance.hass = self.hass
        self.progress.append(instance)
        return instance

    def pair(self, address):
        instance = self.new_flow()
        return asyncio.run(instance.async_step_user({
            "name": "Desk", "layout": "hero", "device": address, "url": "http://ha.example",
        }))

    def test_duplicate_forms_do_not_replace_the_secret(self):
        first = self.pair("display.local")
        self.assertEqual(first["type"], "create_entry")
        secret = pushes[0][2]
        for address in ("display.local", "DISPLAY", "http://Display.local:80/", " display.local. "):
            with self.subTest(address=address):
                self.assertEqual(self.pair(address), {"type": "abort", "reason": "already_configured"})
        self.assertEqual(len(ConfigFlow.entries), 1)
        self.assertEqual(len(pushes), 1)
        self.assertEqual(ConfigFlow.entries[0].data["secret"], secret)

    def test_different_devices_and_ports_are_not_duplicates(self):
        for address in ("display.local", "other.local", "display.local:8080"):
            self.assertEqual(self.pair(address)["type"], "create_entry")
        self.assertEqual(len(pushes), 3)

    def test_discovery_uses_the_same_identity(self):
        self.pair("http://Display.local:80/")
        instance = self.new_flow()
        result = asyncio.run(instance.async_step_zeroconf(types.SimpleNamespace(
            host="192.0.2.42", hostname="display.local.",
        )))
        self.assertEqual(result, {"type": "abort", "reason": "already_configured"})
        self.assertEqual(len(pushes), 1)

    def test_concurrent_pairing_writes_one_secret(self):
        async def check():
            entered, release = asyncio.Event(), asyncio.Event()

            async def delayed_push(hass, device, url, secret):
                await push_settings(hass, device, url, secret)
                entered.set()
                await release.wait()

            flow.push_settings = delayed_push
            request = {"name": "Desk", "layout": "hero", "device": "display.local", "url": "http://ha"}
            first = self.new_flow()
            task = asyncio.create_task(first.async_step_user(request))
            await entered.wait()
            second = await self.new_flow().async_step_user({**request, "device": "http://DISPLAY:80/"})
            self.assertEqual(second, {"type": "abort", "reason": "already_configured"})
            self.assertEqual(len(pushes), 1)
            release.set()
            self.assertEqual((await task)["type"], "create_entry")
            self.assertEqual(len(ConfigFlow.entries), 1)
            self.assertEqual(ConfigFlow.entries[0].data["secret"], pushes[0][2])

        asyncio.run(check())

    def test_success_reserves_address_until_entry_is_registered(self):
        async def check():
            request = {"name": "Desk", "layout": "hero", "device": "display", "url": "http://ha"}
            first = self.new_flow()
            # HA's flow manager registers the entry after the step returns.
            first.async_create_entry = lambda **kwargs: {"type": "create_entry", **kwargs}
            result = await first.async_step_user(request)
            self.assertEqual(result["type"], "create_entry")
            self.assertEqual(ConfigFlow.entries, [])
            second = await self.new_flow().async_step_user(request)
            self.assertEqual(second["type"], "abort")
            self.assertEqual(len(pushes), 1)

        asyncio.run(check())

    def test_failed_pairing_releases_address_for_retry(self):
        async def check():
            request = {"name": "Desk", "layout": "hero", "device": "display", "url": "http://ha"}
            async def refused(*args):
                raise flow.DeviceError("cannot_connect")
            flow.push_settings = refused
            first = self.new_flow()
            result = await first.async_step_user(request)
            self.assertEqual(result["type"], "form")
            self.assertEqual(result["errors"], {"base": "cannot_connect"})
            self.assertEqual(first._pairing_device, "")
            flow.push_settings = push_settings
            self.assertEqual((await self.new_flow().async_step_user(request))["type"], "create_entry")
            self.assertEqual(len(pushes), 1)

        asyncio.run(check())

    def test_canceled_pairing_releases_address_for_retry(self):
        async def check():
            entered = asyncio.Event()
            async def delayed_push(*args):
                entered.set()
                await asyncio.Event().wait()
            flow.push_settings = delayed_push
            request = {"name": "Desk", "layout": "hero", "device": "display", "url": "http://ha"}
            first = self.new_flow()
            task = asyncio.create_task(first.async_step_user(request))
            await entered.wait()
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
            self.assertEqual(first._pairing_device, "")
            flow.push_settings = push_settings
            self.assertEqual((await self.new_flow().async_step_user(request))["type"], "create_entry")
            self.assertEqual(len(pushes), 1)

        asyncio.run(check())

    def test_invalid_address_is_left_for_transport_validation(self):
        self.assertEqual(const.device_key("http://["), "http://[")
        self.assertEqual(const.device_key("display:bad"), "display:bad")


if __name__ == "__main__":
    unittest.main()
