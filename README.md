# Particle Log Monitoring Template

Reusable tools and runbooks for collecting and cleaning Particle product event streams.

## Purpose

Use this repository template to:
- collect raw product event streams
- clean noisy Particle events into readable operational lines
- monitor resets, alerts, connectivity, and status behavior

## Initial Setup

1. Clone the repository.
2. Copy `inventory/devices.example.csv` to `inventory/devices.csv`.
3. Replace example device IDs with your real Particle device IDs.
4. Create a local product folder from the sample template.
5. Start subscriptions and monitoring.

```bash
cp inventory/devices.example.csv inventory/devices.csv
cp -R products/sample-product products/my-product
```

## Repository Contents

```text
inventory/
    devices.example.csv

products/
    sample-product/

tools/
    particle_clean.py
```

`products/sample-product` is a template only. Copy it to your own local product folder and adapt it.

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

## Template Folder Layout

```text
inventory/
  devices.example.csv
  devices.csv (local only)

products/
  sample-product/
    archive/
    notes/
    latest.clean.log
    latest.raw.log
    product-events-YYYYMMDD.clean.log
    product-events-YYYYMMDD.raw.log

tools/
  particle_clean.py

particle-log-subscription-runbook.md
```

## Creating a New Product Folder

Create your local working copy from the template:

```bash
cp -R products/sample-product products/my-product
```

Then:
1. Update your Particle subscription command for your product.
2. Use your real Product ID when running monitoring commands.
3. Populate `inventory/devices.csv` with your devices.
4. Start monitoring using `latest.raw.log` or `latest.clean.log`.

## Device Inventory

`inventory/devices.csv` maps:
- `product_id`
- `device_id`
- `device_name`
- `role`
- `notes`

`tools/particle_clean.py` uses this mapping to replace device IDs with readable names.

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

Before:

```text
OFFLINE
ONLINE
update_enabled=true
update_forced=false
update_pending=false
Ubidots-Sensor-Hook-v1 | occupancy=0 ...
```

After:

```text
REPORT occ=0 daily=125 batt=80.1 pwr=Charged temp=33.9 alerts=0 resets=0 conn=1
```

## Severity and Highlighting

- Normal reports are `REPORT`.
- Noteworthy reports are `REPORT!`.

`REPORT!` is used when:
- `alerts > 0`
- `resets > 0`
- `connecttime >= 60`

Connection thresholds:
- Normal: `< 60` seconds
- Warning: `60-179` seconds
- Critical: `>= 180` seconds

Use `--color` for terminal highlighting.

## Typical Daily Workflow

1. Start subscriptions.
2. Verify raw logs are growing.
3. Open monitoring terminals.
4. Tail clean logs.
5. Watch for `REPORT!`, reset events, status alerts, and slow connections.
6. Rotate logs daily.
7. Update `latest.*` symlinks.

## Subscription and Collection

See `particle-log-subscription-runbook.md` for full setup.

In short:
- subscription tabs collect raw logs and generate clean logs
- monitoring tabs tail `latest.clean.log` or pipe `latest.raw.log` through `particle_clean.py`
