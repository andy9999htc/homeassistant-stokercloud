# homeassistant-stokercloud

Unofficial Home Assistant integration for NBE burners via the StokerCloud service.

This integration focuses on robust cloud polling with model-tolerant field mapping. It supports both read-only telemetry and selected write operations (setpoint/start/stop) through the StokerCloud API.

> Disclaimer: This is a community project. It is not endorsed by or affiliated with NBE.

## Changelog

### 1.2.2

- Fixed startup crash in number entities when `internaldata_pellet_energy_per_kg` is missing from coordinator data.
- Added safe initialization fallback to entity default value when no restored state or cloud value is available.
- Persist initialized internal number values to storage during startup so subsequent restarts have stable defaults.

### 1.2.1

- Reduced log noise for missing optional cloud keys by changing repeated warnings to one-time debug messages per key.
- Fixed number platform logger namespace so integration logs are emitted from `custom_components.stokercloud.number` instead of `homeassistant.core`.

### 1.2.0

- Added configurable API variant support (`v2` and `v16bck`) with `v16bckbeta` write handling.
- Added configurable `screen` selector and polling interval via config flow.
- Reworked request handling for safer query construction and token refresh behavior.
- Improved payload mapping with stable ID-based aliases to avoid index-shift issues.
- Expanded entities with additional boiler/hopper values and writable controls.
- Added `lng_state_xx` to text mapping aligned with FHEM `reading17Map`.
- Added standalone API test scripts and unit tests for mapping/request behavior.
- Expanded documentation with installation, configuration, entities, testing, and troubleshooting details.

### 1.1.1

- Original integration version by [KristianOellegaard](https://github.com/KristianOellegaard/homeassistant-stokercloud/commits?author=KristianOellegaard).

## Features

- Config flow setup in Home Assistant UI
- Supports API variants:
	- `v2`
	- `v16bck` (with `v16bckbeta` write path)
- Configurable polling interval
- Configurable `screen` selector for v16 payload shaping
- ID-based JSON flattening to avoid fragile index mappings across boiler models
- Read entities for key boiler, hopper, weather, and status metrics
- Write entities:
	- Number: boiler temperature setpoint
	- Number: hopper content
	- Button: boiler start
	- Button: boiler stop
- Standalone scripts for testing without Home Assistant
- Unit tests for API behavior and mapping logic

## Requirements

- Home Assistant with custom integration support
- NBE boiler connected to StokerCloud
- StokerCloud credentials
- Internet connectivity (cloud integration)

## Installation

### Via HACS (custom repository)

1. Open HACS in Home Assistant.
2. Open Custom Repositories.
3. Add:
   - **URL:** `https://github.com/andy9999htc/homeassistant-stokercloud.git`
   - **Category:** Integration

4. Install `NBE Stoker Cloud`.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/stokercloud` into your Home Assistant config under `custom_components`.
```bash
cd /path/to/homeassistant/config/custom_components/
git clone https://github.com/andy9999htc/homeassistant-stokercloud.git homeassistant-stokercloud_temp
cp -r homeassistant-stokercloud_temp/custom_components/stokercloud ./
rm -rf homeassistant-stokercloud_temp
```
2. Restart Home Assistant.

## Configuration

After restart:

1. Go to Settings -> Devices & Services -> Add Integration.
2. Search for `NBE Stoker Cloud`.
3. Provide:
	 - Username
	 - Password
	 - API variant (`v2` or `v16bck`)
	 - Screen selector (mainly relevant for `v16bck`)
	 - Scan interval (seconds)

### API Variant Notes

- `v16bck` is often needed for installations that work with FHEM HTTPMOD style calls.
- For `v16bck`, writes are sent to `v16bckbeta` update endpoint.

### Screen Selector Notes

- The default screen selector is tuned for broad value coverage and matches the common FHEM pattern.
- If your model exposes a different payload shape, use a custom screen selector.

## Entities

Entity IDs include your configured account alias prefix and are created automatically.

### Sensor Entities

- Boiler Temperature
- Boiler Temperature Requested
- Boiler Effect
- Boiler Effect pct
- Current Water Heater Temperature
- Requested Water Heater Temperature
- Total Consumption
- State
- Serial no
- Clock
- Status message
- Weather City
- Weather Outside tempererature
- Weather Wind speed
- Weather Wind direction
- Flue Gas Temperature
- Ash Box Fill Level
- Pellet Fill Level
- Oxygen
- Furnace Pressure
- Consumption 24h
- Power 10%
- Power 100%
- Hopper Distance

### Number Entities

- Hopper content (writable)
- Boiler Temperature Setpoint (writable)
- Pellet energy (kWh/kg) (local/internal helper value)

### Button Entities

- Boiler Start
- Boiler Stop

## State Mapping

The integration includes explicit mapping for `lng_state_xx` values (from FHEM `reading17Map` style state definitions), for example:

- `lng_state_24` -> `Stopped by external contact`

This ensures the Home Assistant state text is human readable and aligned with your existing FHEM meaning.

## Testing Without Home Assistant

This repository includes both mocked unit tests and live standalone API checks.

### Install test dependencies

```powershell
pip install -r requirements.txt
```

### Run unit tests

```powershell
pytest
```

or:

```powershell
python standalone_api_test.py
```

### Run live API checks

```powershell
$env:STOKER_USER="your_user"
$env:STOKER_PASSWORD="your_password"
$env:STOKER_API_VARIANT="v16bck"
python standalone_api_live_test.py
```

Optional custom screen selector:

```powershell
$env:STOKER_SCREEN="b1,0,b2,5,..."
python standalone_api_live_test.py
```

Optional write test:

```powershell
$env:STOKER_RUN_WRITE="1"
$env:STOKER_MENU="boiler.temp"
$env:STOKER_NAME="boiler.temp"
$env:STOKER_VALUE="68"
python standalone_api_live_test.py
```

Live script output includes both operational values and key mapping diagnostics for troubleshooting model-specific payload differences.

## Troubleshooting

### Values missing or wrong

- Ensure API variant matches your installation (`v16bck` is common for older endpoint behavior).
- Keep default screen selector unless you intentionally tune it.
- Run `standalone_api_live_test.py` and compare reported fields.

### State code shown instead of text

- The integration maps `lng_state_xx` to text.
- If you still see raw codes, capture live payload output and open an issue.

### Writes not working

- Verify credentials are read-write capable in StokerCloud.
- Confirm correct API variant (`v16bck` writes use beta endpoint).
- Use live script write mode first to validate endpoint behavior outside HA.

## Known Limitations

- Cloud dependent: no internet means no updates/control.
- Polling based: no realtime push channel.
- Some fields vary by boiler firmware/model; mapping is improved with ID-based aliases but not every installation exposes all metrics.

## Contributing

Issues and pull requests are welcome. If you report a mapping issue, include:

- API variant used
- Screen selector used
- Standalone live script output (sanitized)
- Expected vs actual values

