# Particle Product Log Subscription Runbook (Template)

This runbook explains how to set up local Particle product log collection using reusable template paths and fake example IDs.

## 1. Directory structure

```text
~/ParticleLogs/
├── inventory/
│   ├── devices.example.csv
│   └── devices.csv
├── products/
│   ├── sample-product/
│   └── my-product/ (local copy)
└── tools/
    └── particle_clean.py
```

## 2. Initial setup

```bash
cd ~/ParticleLogs
cp inventory/devices.example.csv inventory/devices.csv
cp -R products/sample-product products/my-product
```

Update `inventory/devices.csv` with your real `product_id`, `device_id`, and `device_name` values.

## 3. Verify Particle CLI

```bash
particle --version
particle whoami
```

If not logged in:

```bash
particle login
```

## 4. Set daily log symlinks

Run from your local product folder:

```bash
cd ~/ParticleLogs/products/my-product
ln -sf product-events-$(date +%Y%m%d).raw.log latest.raw.log
ln -sf product-events-$(date +%Y%m%d).clean.log latest.clean.log
```

## 5. Start subscription and cleaning

Replace `12345` with your actual Product ID.

```bash
cd ~/ParticleLogs/products/my-product
particle subscribe --product 12345 | tee -a latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 12345 | tee -a latest.clean.log
```

This pipeline:
1. subscribes to product events
2. appends raw data to `latest.raw.log`
3. filters to JSON events
4. cleans output with device name mapping
5. appends readable output to `latest.clean.log`

## 6. Live monitoring

```bash
tail -F ~/ParticleLogs/products/my-product/latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 12345 --color
```

Use `--verbose` to include routine online/offline and update events.

## 7. Replay and rebuild

Replay a raw log:

```bash
grep '^{' ~/ParticleLogs/products/my-product/latest.raw.log | python3 ~/ParticleLogs/tools/particle_clean.py 12345 --color
```

Rebuild a clean log from raw:

```bash
grep '^{' ~/ParticleLogs/products/my-product/latest.raw.log | python3 ~/ParticleLogs/tools/particle_clean.py 12345 > ~/ParticleLogs/products/my-product/latest.clean.log
```

## 8. Daily operations checklist

1. Start subscriptions.
2. Verify raw logs are growing.
3. Tail clean output.
4. Watch for `REPORT!`, reset events, status alerts, and slow connections.
5. Rotate to new dated logs daily.
6. Update `latest.*` symlinks.

## 9. What gets committed

Commit:
- runbooks and scripts
- `inventory/devices.example.csv`
- `products/sample-product` template files

Do not commit:
- `inventory/devices.csv`
- local product folders under `products/` (except `sample-product`)
- runtime operational logs from active monitoring sessions
