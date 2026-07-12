"""Standalone live API test for NBE StokerCloud.

This script performs real API calls using environment variables.

Usage (PowerShell):
    $env:STOKER_USER="your_user"
    $env:STOKER_PASSWORD="your_password"
    python standalone_api_live_test.py

Optional configuration:
    $env:STOKER_API_VARIANT="v16bck"  # or v2
    $env:STOKER_SCREEN="b1,0,b2,5,..."

Optional write test:
    $env:STOKER_RUN_WRITE="1"
    $env:STOKER_MENU="boiler.temp"
    $env:STOKER_NAME="boiler.temp"
    $env:STOKER_VALUE="68"
    python standalone_api_live_test.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import sys
import types
from typing import Any


DEFAULT_SCREEN_FALLBACK = (
    "b1,0,b2,5,b3,4,b4,6,b5,12,b6,14,b7,15,b8,16,b9,9,b10,0,"
    "d1,0,d2,4,d3,0,d4,0,d5,0,d6,0,d7,0,d8,0,d9,0,d10,0,"
    "h1,2,h2,3,h3,4,h4,7,h5,8,h6,14,h7,0,h8,0,h9,0,h10,0,"
    "w1,2,w2,3,w3,9,w4,0,w5,0"
)

LNG_STATE_MAP = {
    "lng_state_0": "Wait a moment",
    "lng_state_1": "Ignition 1",
    "lng_state_2": "Ignition 1",
    "lng_state_3": "Ignition 2",
    "lng_state_4": "Ignition 2",
    "lng_state_5": "Power",
    "lng_state_6": "Pause",
    "lng_state_7": "DHW",
    "lng_state_8": "Temperature error boiler",
    "lng_state_9": "Stopped - temperature reached",
    "lng_state_10": "Summer stop",
    "lng_state_11": "Alarm burner is too hot do not restart before the problem is found !!",
    "lng_state_12": "Plug is disconnected",
    "lng_state_13": "Fault ignition",
    "lng_state_14": "Off",
    "lng_state_15": "Error boiler temp. sensor",
    "lng_state_16": "Error photo sensor",
    "lng_state_17": "Error burner temp. sensor",
    "lng_state_19": "Error on a motor output",
    "lng_state_20": "Error no fire out of pellets",
    "lng_state_22": "Stopped by external temperature",
    "lng_state_23": "Stopped by timer",
    "lng_state_24": "Stopped by external contact",
    "lng_state_25": "Stopped by weather comp.",
    "lng_state_26": "Fail on fan",
    "lng_state_27": "Error no fire adjustment low",
    "lng_state_28": "Door is open",
    "lng_state_29": "Overheat/auger disconnected",
    "lng_state_30": "Stopped by cascade",
    "lng_state_31": "Compressor failure",
    "lng_state_36": "Back pressure high",
}


def _load_api_symbols() -> tuple[type, object, str]:
    """Load API symbols directly from source files, bypassing HA package imports."""
    repo_root = pathlib.Path(__file__).resolve().parent
    package_root = repo_root / "custom_components" / "stokercloud"

    if "custom_components" not in sys.modules:
        custom_components_pkg = types.ModuleType("custom_components")
        custom_components_pkg.__path__ = [str(repo_root / "custom_components")]
        sys.modules["custom_components"] = custom_components_pkg

    if "custom_components.stokercloud" not in sys.modules:
        integration_pkg = types.ModuleType("custom_components.stokercloud")
        integration_pkg.__path__ = [str(package_root)]
        sys.modules["custom_components.stokercloud"] = integration_pkg

    api_name = "custom_components.stokercloud.stokercloud_api"
    api_spec = importlib.util.spec_from_file_location(api_name, package_root / "stokercloud_api.py")
    assert api_spec and api_spec.loader
    api_module = importlib.util.module_from_spec(api_spec)
    sys.modules[api_name] = api_module
    api_spec.loader.exec_module(api_module)

    return api_module.Client, api_module.TokenInvalid, DEFAULT_SCREEN_FALLBACK


Client, TokenInvalid, DEFAULT_SCREEN = _load_api_symbols()


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _coerce_value(raw: str) -> Any:
    lower = raw.strip().lower()
    if lower == "true":
        return True
    if lower == "false":
        return False

    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _preview(value: Any, max_len: int = 1000) -> str:
    try:
        text = json.dumps(value, indent=2, ensure_ascii=True, default=str)
    except Exception:
        text = repr(value)
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n... (truncated)"


def _first_non_null(values: list[Any], default: Any = None) -> Any:
    for value in values:
        if value is not None:
            return value
    return default


def _resolve_state_text(raw_state: Any) -> Any:
    if isinstance(raw_state, str):
        return LNG_STATE_MAP.get(raw_state, raw_state)
    return raw_state


def _candidate_keys(flat: dict[str, Any], prefix: str) -> dict[str, Any]:
    return {
        key: flat[key]
        for key in sorted(flat.keys())
        if key.startswith(prefix) and key.endswith("_value")
    }


def _group_entries(flat: dict[str, Any], prefix: str) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    prefix_with_sep = f"{prefix}_"
    for key, value in flat.items():
        if not key.startswith(prefix_with_sep):
            continue

        remainder = key[len(prefix_with_sep):]
        parts = remainder.split("_", 1)
        if len(parts) != 2:
            continue

        index, field = parts
        if not index.isdigit():
            continue

        grouped.setdefault(index, {})[field] = value

    return dict(sorted(grouped.items(), key=lambda item: int(item[0])))


def _pick_entries(entries: dict[str, dict[str, Any]], indexes: list[str]) -> dict[str, dict[str, Any]]:
    return {
        index: entries[index]
        for index in indexes
        if index in entries
    }


def main() -> int:
    user = _required_env("STOKER_USER")
    password = _required_env("STOKER_PASSWORD")
    api_variant = os.getenv("STOKER_API_VARIANT", "v16bck")
    screen = os.getenv("STOKER_SCREEN", DEFAULT_SCREEN if api_variant == "v16bck" else "")
    if not screen:
        screen = None

    client = Client(
        user,
        password,
        api_variant=api_variant,
        screen=screen,
    )

    print("[1/4] Authenticating...")
    # Any request can trigger auth; calling explicitly gives better diagnostics.
    # pylint: disable=protected-access
    import asyncio

    asyncio.run(client.refresh_token())
    print("[OK] Token received")

    print("[2/4] Reading controller data...")
    asyncio.run(client.get_controller_data())
    print("[OK] Raw keys:", sorted(client.cached_data.keys()) if isinstance(client.cached_data, dict) else type(client.cached_data))
    if api_variant == "v16bck":
        print("[OK] Screen selector active:", "default" if screen == DEFAULT_SCREEN else "custom")

    print("[3/4] Reading flattened controller data...")
    flat = asyncio.run(client.controller_data_json())
    raw_state = flat.get("miscdata_state_value")
    selected = {
        "serial": flat.get("serial"),
        "state": _resolve_state_text(raw_state),
        "state_code": raw_state,
        "running": flat.get("miscdata_running"),
        "alarm": flat.get("miscdata_alarm"),
        "outdoor_temp": flat.get("weatherdata_1_value"),
        "power_output_kw": _first_non_null(
            [
                flat.get("boilerdata_byid_1_value"),
                flat.get("boilerdata_1_value"),
                flat.get("miscdata_output"),
            ],
            default=0.0,
        ),
        "power_pct": _first_non_null(
            [
                flat.get("boilerdata_byid_2_value"),
                flat.get("boilerdata_2_value"),
                flat.get("miscdata_outputpct"),
            ],
            default=0,
        ),
        "boiler_temp": flat.get("frontdata_boilertemp_value"),
        "boiler_setpoint": flat.get("frontdata_wantedboilertemp_value"),
        "flue_gas_temp": flat.get("frontdata_smoketemp_value"),
        "oxygen_pct": flat.get("frontdata_byid_oxygen_value"),
        "furnace_pressure_pa": flat.get("frontdata_byid_pressure_value"),
        "consumption_24h_kg": flat.get("hopperdata_byid_3_value"),
        "consumption_total_kg": flat.get("hopperdata_byid_4_value"),
        "hopper_content_kg": flat.get("frontdata_hoppercontent_value"),
        "pellet_fill_pct": flat.get("hopperdata_byid_14_value"),
        "ash_box_pct": flat.get("frontdata_ashdist_value"),
    }
    print("[OK] Selected values:\n" + _preview(selected))

    if selected["ash_box_pct"] is None:
        frontdata_entries = _group_entries(flat, "frontdata")
        hopperdata_entries = _group_entries(flat, "hopperdata")
        diagnostics = {
            "frontdata_candidates": _candidate_keys(flat, "frontdata_"),
            "hopperdata_candidates": _candidate_keys(flat, "hopperdata_"),
            # FHEM uses paths like frontdata_14_value while this flattener is zero-based.
            # If that mapping is one-based, the likely equivalent here is frontdata_13_value.
            "suspected_zero_based_aliases": {
                "fhem_frontdata_14_value": flat.get("frontdata_13_value"),
                "fhem_frontdata_12_value": flat.get("frontdata_11_value"),
                "fhem_hopperdata_06_value": flat.get("hopperdata_5_value"),
            },
            "frontdata_nearby_entries": _pick_entries(frontdata_entries, ["11", "12", "13"]),
            "hopperdata_nearby_entries": _pick_entries(hopperdata_entries, ["4", "5"]),
            "frontdata_entries": frontdata_entries,
            "hopperdata_entries": hopperdata_entries,
        }
        print("[INFO] ash_box_pct key missing; available candidates:\n" + _preview(diagnostics, max_len=8000))

    run_write = os.getenv("STOKER_RUN_WRITE", "0") == "1"
    if run_write:
        print("[4/4] Executing write call...")
        menu = _required_env("STOKER_MENU")
        name = _required_env("STOKER_NAME")
        value = _coerce_value(_required_env("STOKER_VALUE"))
        updated = asyncio.run(client.update_controller_value(menu, name, value))
        print(f"[OK] Write acknowledged: {menu}/{name} -> {updated}")
    else:
        print("[4/4] Skipping write test (set STOKER_RUN_WRITE=1 to enable)")

    print("\nAll live checks completed.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TokenInvalid as err:
        print(f"[FAIL] Token/auth error: {err}")
        raise SystemExit(2)
    except Exception as err:
        print(f"[FAIL] {err}")
        raise SystemExit(1)
