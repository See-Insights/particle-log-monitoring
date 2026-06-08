# Particle Log Monitoring

Practical tools and runbooks for collecting and cleaning Particle product event streams used in See Insights deployments.

This repository supports the following product families:
- NextGen Occupancy Boron
- NextGen Occupancy Photon 2
- LoRa Particle Gateway P2

## Purpose

Use this repo to:
- Collect raw Particle event streams per product.
- Clean noisy event streams into readable operational output.
- Monitor device health, resets, alerts, firmware status, and connectivity behavior.

## Initial Setup

1. Clone the repository.
2. Copy `inventory/devices.example.csv` to `inventory/devices.csv`.
3. Replace the example device IDs with actual IDs from Particle.
4. Start monitoring.

Example command:

```bash
cp inventory/devices.example.csv inventory/devices.csv
```

## Repository Architecture

```text
Particle Product
  |
  v
Particle Event Stream
  |
  v
Subscription Process
  |
  v
product-events-YYYYMMDD.raw.log
  |
  v
particle_clean.py
  |
  v
product-events-YYYYMMDD.clean.log
  |
  v
Engineer Monitoring
```

## Repository Structure

Intended layout:

```text
inventory/
  devices.example.csv
  devices.csv

products/
  <product-id-product-name>/
    archive/
    notes/
    latest.raw.log
    latest.clean.log
    product-events-YYYYMMDD.raw.log
    product-events-YYYYMMDD.clean.log

tools/
  particle_clean.py

particle-log-subscription-runbook.md
```

Notes:
- Raw and clean log files are local runtime artifacts.
- Raw/clean logs are intentionally ignored by Git and are not committed.

## Device Inventory

`inventory/devices.csv` maps:
- `product_id`
- `device_id`
- `device_name`
- `role`
- `notes`

`inventory/devices.example.csv` is the starter template for new engineers.
The template includes the core required columns (`product_id`, `device_id`, `device_name`); `role` and `notes` can be added as needed.

`tools/particle_clean.py` uses this inventory to replace Particle device IDs with readable names so monitoring output is easier to scan during live operations.

## Clean Log Philosophy

Raw Particle streams are noisy and include routine cloud events.

By default, the cleaner suppresses:
- ONLINE/OFFLINE events
- routine update flags
- webhook transport events
- diagnostics updates
- empty events

The cleaner keeps or highlights:
- device reports
- reset causes
- firmware update events
- app hash events
- populated status payloads
- alerts
- slow connections
- unexpected non-empty events

## Example Before and After

Before (raw/noisy):

```text
OFFLINE
ONLINE
update_enabled=true
update_forced=false
update_pending=false
Ubidots-Sensor-Hook-v1 | occupancy=0 ...
```

After (cleaned):

```text
REPORT occ=0 daily=125 batt=80.1 pwr=Charged temp=33.9 alerts=0 resets=0 conn=1
```

## Clean Output Fields

Common fields in cleaned output:
- `occ`: current occupancy
- `daily`: daily count total
- `batt`: battery level/voltage indicator
- `pwr`: power/charging state
- `temp`: device temperature
- `alerts`: active alert count/state
- `resets`: reset count/state
- `conn`: connect time (seconds)
- `rssi`: signal strength
- `snr`: signal-to-noise ratio
- `payload`: raw/remaining payload details when needed

## Severity and Highlighting

- Normal reports appear as `REPORT`.
- Noteworthy reports appear as `REPORT!`.

`REPORT!` is used when any of the following is true:
- `alerts > 0`
- `resets > 0`
- `connecttime >= 60` seconds

Connection thresholds:
- Normal: `< 60` seconds
- Warning: `60-179` seconds
- Critical: `>= 180` seconds

Use `--color` to enable terminal color highlighting.

## Status Events

Firmware status payloads are condensed into a readable line, for example:

```text
STATUS ver=13.0.0 reset=30 alert=0 heap=3044800 connAge=28803 breadcrumb=3
```

This helps quickly identify:
- reset reason
- firmware version
- heap level
- alert state
- time since last connection

## Common Reset Reasons

Practical cheat sheet:
- `update`: firmware update completed
- `power_management`: expected wake from hibernate/deep sleep
- `pin_reset`: physical reset button or reset pin
- `watchdog`: watchdog recovery
- `user` / reset reason `30`: software-triggered or platform-reported reset; inspect serial log/context

## Live Monitoring Commands

Boron product `42131`:

```bash
tail -n 50 -F ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log | python3 -u ~/ParticleLogs/tools/particle_clean.py 42131 --color
```

Photon 2 product `41915`:

```bash
tail -n 50 -F ~/ParticleLogs/products/41915-NextGen-Occupancy-P2/latest.raw.log | python3 -u ~/ParticleLogs/tools/particle_clean.py 41915 --color
```

LoRa Gateway product `38211`:

```bash
tail -n 50 -F ~/ParticleLogs/products/38211-LoRA-Particle-Gateway-P2/latest.raw.log | python3 -u ~/ParticleLogs/tools/particle_clean.py 38211 --color
```

Verbose mode:
- `--verbose` shows routine Particle online/offline/update/diagnostic events.

## Subscription and Collection

See `particle-log-subscription-runbook.md` for full setup and workflow.

In short:
- Subscription tabs collect raw logs and produce clean logs.
- Monitoring tabs can tail `latest.clean.log` directly or pipe `latest.raw.log` through `particle_clean.py` for inline cleaning.

## Typical Daily Workflow

1. Start subscriptions.
2. Verify raw logs are growing.
3. Open monitoring terminals.
4. Tail clean logs.
5. Watch for:
  - `REPORT!`
  - reset events
  - status alerts
  - slow connections
6. Rotate logs daily.
7. Update `latest.*` symlinks.

## Log Retention and Rotation

- Active logs are referenced by `latest.raw.log` and `latest.clean.log` symlinks.
- These symlinks should point to the current dated files (for example, `product-events-YYYYMMDD.raw.log` and `product-events-YYYYMMDD.clean.log`).
- Move older dated logs into `archive/`.
- Archived and active runtime logs stay local and are not committed to Git.

## Roadmap

Planned enhancements:
- multi-product dashboard
- daily summary report
- alert aggregation
- connectivity trend analysis
- automated log rotation
