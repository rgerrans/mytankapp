# MyTankApp for Home Assistant

An unofficial, read-only Home Assistant custom integration for tanks visible at [MyTankApp](https://www.mytankapp.com).

## Entities

Each tank becomes a Home Assistant device with sensors for:

- Level
- Inventory and ullage
- Capacity
- MyTankApp-reported average daily usage (diagnostic)
- Calculated 7-day rolling daily usage from timestamped tank history
- Last report time
- Last successful integration sync time
- Last successful history refresh time (diagnostic)
- Temperature and base temperature
- Estimated days to 30%, 15%, and empty
- Cumulative propane energy consumed in kWh for the Energy Dashboard
- Cumulative propane volume consumed in liters from observed tank changes
- Estimated cumulative liquid propane consumption with coarse readings interpolated over time
- Raw timestamped propane-consumption statistics imported from MyTankApp history
- Estimated timestamped liquid-propane consumption statistics for diagnostics/comparison
- Estimated propane energy statistics in kWh for the Energy Dashboard
- Estimated propane flow rate averaged across the latest confirmed consumption interval
- Configurable low-level problem state

Days-to-threshold estimates prefer the calculated rolling usage rate when history is available, and fall back to MyTankApp's reported average when it is not. The calculated rate ignores deliveries and small upward gauge noise.

The integration keeps the raw observed consumption series for transparency. Because MyTankApp can expose tank history only in coarse whole-percent steps, version 0.11.0 also creates an **estimated propane consumption** series. Each confirmed inventory decrease is spread linearly across the elapsed interval since the prior stable level, preserving the observed total while producing more realistic daily allocation. A conservative outlier filter removes isolated large excursions that immediately rebound toward the prior level, such as a transient bad sensor reading.

For the Energy Dashboard gas chart, select **<tank name> estimated propane energy** under **Settings → Dashboards → Energy → Gas consumption**. Home Assistant accepts energy-class sources for gas consumption, so this avoids converting liquid propane volume into ft³. The raw and estimated propane-volume statistics remain available for diagnostics and comparison.

Liquid propane volume entities use Home Assistant's generic **volume** device class rather than **gas**, so U.S. Customary systems display gallons instead of ft³. For dashboards, prefer **Estimated propane flow rate** over the raw calculated flow-rate sensor. Both flow sensors prefer gal/h on gallon-based accounts and L/h on liter-based accounts. The estimated flow rate represents the average rate across the latest confirmed inventory-change interval; it is not an instantaneous burner-flow measurement.

## Installation

### HACS custom repository

1. Add this repository to HACS as an **Integration** custom repository.
2. Install **MyTankApp**.
3. Restart Home Assistant.
4. Go to **Settings → Devices & services → Add integration** and select **MyTankApp**.

### Manual

Copy `custom_components/mytankapp` into your Home Assistant `config/custom_components` directory and restart Home Assistant.

## Configuration

Enter the username and password used at `mytankapp.com`. The password is retained by Home Assistant because the website provides no refresh-token flow and the integration must log in again after restarts or expired sessions.

The default poll interval is 12 hours. Options allow 1–24 hours and a 1–99% low-level threshold. In addition to change-triggered history pulls, the integration forces a successful history refresh at least once every 24 hours; failed history pulls remain due and are retried on the next normal coordinator poll. Existing installations that still use the former six-hour default are migrated to 12 hours. Because this is a private, undocumented API with no published quota, the default interval is intentionally conservative.

Automatic login attempts use a 15-minute cooldown after transient connection failures. DNS failures, timeouts, rate limits, and 5xx responses do not trigger aggressive relogin attempts. Explicit 401/403 authorization rejection triggers Home Assistant reauthentication. Credentials submitted interactively in setup or reauthentication are still validated immediately.

## Safety and limitations

- The integration does not order fuel, request service, modify alerts, or change account data.
- MyTankApp does not publish this API, so upstream changes can break the integration.
- Tank reading cadence is controlled by the physical monitor and supplier; frequent polling will not make the transmitter report more often.
- The integration reads MyTankApp's recent transaction history to calculate usage. Home Assistant Recorder stores the resulting sensor history locally.

## Support data

Home Assistant diagnostics redact credentials and tank identifiers. Diagnostics also include up to 30 recent propane history readings per tank with only timestamp, Units, and Percent values so reporting resolution can be inspected without exposing vendor identifiers. If the history endpoint fails, diagnostics record the error type rather than failing the download. Before sharing logs, still check them for personal information.


## Versioning

This integration uses semantic versioning. The Home Assistant manifest uses `MAJOR.MINOR.PATCH` (for example, `0.9.0`), while GitHub tags and releases use the conventional leading `v` (for example, `v0.9.0`).
