"""Unit tests for the standalone StokerCloud API client."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types
import unittest
from unittest.mock import patch


def _load_api_module():
    """Load stokercloud_api.py without importing Home Assistant modules."""
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    package_root = repo_root / "custom_components" / "stokercloud"

    if "custom_components" not in sys.modules:
        custom_components_pkg = types.ModuleType("custom_components")
        custom_components_pkg.__path__ = [str(repo_root / "custom_components")]
        sys.modules["custom_components"] = custom_components_pkg

    if "custom_components.stokercloud" not in sys.modules:
        integration_pkg = types.ModuleType("custom_components.stokercloud")
        integration_pkg.__path__ = [str(package_root)]
        sys.modules["custom_components.stokercloud"] = integration_pkg

    module_name = "custom_components.stokercloud.stokercloud_api"
    module_spec = importlib.util.spec_from_file_location(
        module_name,
        package_root / "stokercloud_api.py",
    )
    assert module_spec and module_spec.loader
    module = importlib.util.module_from_spec(module_spec)
    sys.modules[module_name] = module
    module_spec.loader.exec_module(module)
    return module


API_MODULE = _load_api_module()
Client = API_MODULE.Client
TokenInvalid = API_MODULE.TokenInvalid


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return self._payload


class _FakeClientSession:
    def __init__(self, dispatcher):
        self._dispatcher = dispatcher

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    def get(self, url):
        return _FakeResponse(self._dispatcher(url))


class TestStokercloudApi(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.seen_urls: list[str] = []

    def _session_factory(self, payloads):
        state = {"idx": 0}

        def _dispatcher(url: str):
            self.seen_urls.append(url)
            payload = payloads[state["idx"]]
            if state["idx"] < len(payloads) - 1:
                state["idx"] += 1
            return payload

        return lambda: _FakeClientSession(_dispatcher)

    async def test_v16_get_controller_uses_screen_and_token(self):
        client = Client(
            "user",
            "pass",
            api_variant="v16bck",
            screen="b1,0,b2,5",
        )

        payloads = [
            {"token": "tok1", "credentials": "rw"},
            {"serial": "12345", "miscdata": {"alarm": 0}},
        ]

        with patch(
            "custom_components.stokercloud.stokercloud_api.aiohttp.ClientSession",
            new=self._session_factory(payloads),
        ):
            await client.get_controller_data()

        self.assertIn("/v16bck/dataout2/login.php?", self.seen_urls[0])
        self.assertIn("user=user", self.seen_urls[0])
        self.assertIn("password=pass", self.seen_urls[0])
        self.assertIn("/v16bck/dataout2/controllerdata2.php?", self.seen_urls[1])
        self.assertIn("screen=b1%2C0%2Cb2%2C5", self.seen_urls[1])
        self.assertIn("token=tok1", self.seen_urls[1])

    async def test_update_value_uses_v16bckbeta_write_path(self):
        client = Client("user", "pass", api_variant="v16bck")
        payloads = [
            {"token": "tok2", "credentials": "rw"},
            {"updated_value": 68},
        ]

        with patch(
            "custom_components.stokercloud.stokercloud_api.aiohttp.ClientSession",
            new=self._session_factory(payloads),
        ):
            updated = await client.update_controller_value("boiler.temp", "boiler.temp", 68)

        self.assertEqual(updated, 68)
        self.assertIn("/v16bckbeta/dataout2/updatevalue.php?", self.seen_urls[-1])
        self.assertIn("menu=boiler.temp", self.seen_urls[-1])
        self.assertIn("name=boiler.temp", self.seen_urls[-1])
        self.assertIn("value=68", self.seen_urls[-1])
        self.assertIn("token=tok2", self.seen_urls[-1])

    async def test_token_expired_triggers_reauth(self):
        client = Client("user", "pass", api_variant="v2")
        payloads = [
            {"token": "old", "credentials": "rw"},
            {"weatherdata": {"weather-city": "x", "tokenexpired": 1}},
            {"token": "new", "credentials": "rw"},
            {"serial": "999", "miscdata": {"alarm": 0}},
        ]

        with patch(
            "custom_components.stokercloud.stokercloud_api.aiohttp.ClientSession",
            new=self._session_factory(payloads),
        ):
            data = await client.make_request("v2/dataout2/controllerdata2.php")

        self.assertEqual(data["serial"], "999")
        login_urls = [u for u in self.seen_urls if "/login.php?" in u]
        self.assertEqual(len(login_urls), 2)

    async def test_build_url_requires_token_when_enabled(self):
        client = Client("user", "pass")
        with self.assertRaises(TokenInvalid):
            client._build_url("v2/dataout2/controllerdata2.php", include_token=True)

    async def test_flatten_json_adds_id_based_aliases(self):
        client = Client("user", "pass")
        flat = client.flatten_json(
            {
                "frontdata": [
                    {"id": "boilertemp", "value": "22.4", "unit": "lng_degree"},
                    {"id": "-wantedboilertemp", "value": "63.0", "unit": "lng_degree"},
                    {"id": "ashdist", "value": "65", "unit": "lng_pct"},
                ],
                "hopperdata": [
                    {"id": "14", "value": "58", "unit": "lng_pct"},
                ],
            }
        )

        self.assertEqual(flat["frontdata_boilertemp_value"], "22.4")
        self.assertEqual(flat["frontdata_wantedboilertemp_value"], "63.0")
        self.assertEqual(flat["frontdata_ashdist_value"], "65")
        self.assertEqual(flat["hopperdata_14_value"], "58")
        self.assertEqual(flat["frontdata_byid_boilertemp_value"], "22.4")
        self.assertEqual(flat["frontdata_byid_wantedboilertemp_value"], "63.0")
        self.assertEqual(flat["frontdata_byid_ashdist_value"], "65")
        self.assertEqual(flat["hopperdata_byid_14_value"], "58")


if __name__ == "__main__":
    unittest.main(verbosity=2)
