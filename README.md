# MyTankApp for Home Assistant

An unofficial, read-only Home Assistant custom integration for tanks visible at [MyTankApp](https://www.mytankapp.com).

## Entities

Each tank becomes a Home Assistant device with sensors for:

- Level
- Inventory and ullage
- Capacity
- Average daily usage
- Last report time
- Temperature and base temperature
- Estimated days to 30%, 15%, and empty
- Configurable low-level problem state

The estimates match the website's basic calculation and are unavailable when usage is zero, negative, or the tank is already below the target.

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

The default poll interval is 30 minutes. Options allow 5–180 minutes and a 1–99% low-level threshold. Because this is a private, undocumented API with no published quota, the default interval is intentionally conservative.

## Safety and limitations

- The integration does not order fuel, request service, modify alerts, or change account data.
- MyTankApp does not publish this API, so upstream changes can break the integration.
- Tank reading cadence is controlled by the physical monitor and supplier; frequent polling will not make the transmitter report more often.
- Historical graph endpoints are intentionally omitted. Home Assistant Recorder stores the sensor history locally.

## Support data

Home Assistant diagnostics redact credentials and tank identifiers. Before sharing logs, still check them for personal information.
