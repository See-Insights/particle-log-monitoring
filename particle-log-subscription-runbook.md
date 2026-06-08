# Particle Product Log Subscription Runbook

This document explains how to recreate the local Particle product log subscription setup used for soak testing and field monitoring.

It is intended to be stored with the firmware project, for example:

```text
docs/particle-log-subscriptions.md
```

or kept centrally on the development machine at:

```text
~/ParticleLogs/README.md
```

The setup supports:

- Subscribing to all Particle events for a product
- Saving raw logs exactly as received from Particle
- Creating readable clean logs with device names instead of device IDs
- Viewing clean logs live in color
- Reusing the same tooling across multiple Particle products

---

## 1. Directory structure

Use this structure on the Mac:

```text
~/ParticleLogs/
├── inventory/
│   └── devices.csv
├── products/
│   ├── 38211-LoRA-Particle-Gateway-P2/
│   ├── 41915-NextGen-Occupancy-P2/
│   └── 42131-NextGen-Occupancy-Boron/
└── tools/
    └── particle_clean.py
```

Each product folder should contain:

```text
latest.raw.log -> product-events-YYYYMMDD.raw.log
latest.clean.log -> product-events-YYYYMMDD.clean.log
product-events-YYYYMMDD.raw.log
product-events-YYYYMMDD.clean.log
```

---

## 2. Create the folder structure

```bash
mkdir -p ~/ParticleLogs/inventory
mkdir -p ~/ParticleLogs/tools
mkdir -p ~/ParticleLogs/products/38211-LoRA-Particle-Gateway-P2
mkdir -p ~/ParticleLogs/products/41915-NextGen-Occupancy-P2
mkdir -p ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron
```

---

## 3. Create the device inventory

Create this file:

```bash
nano ~/ParticleLogs/inventory/devices.csv
```

Paste:

```csv
product_id,device_id,device_name,role,notes
42131,e00fce68399ee6244a963935,SG-Boron-1,Boron,NextGen occupancy soak
42131,e00fce687bbfcdc64e7b5f50,SAMIT-TRAIL02,Boron,NextGen occupancy soak
42131,e00fce686548d46c4b45e380,OCCUPANCY-DEVSAM04,Boron,NextGen occupancy soak
42131,e00fce6841443bcc0f3178e4,Morrisville-Tennis-MAFC-2,Boron,NextGen occupancy soak
42131,e00fce6811b3eb6308d0788a,Morrisville-Tennis-MAFC-1,Boron,NextGen occupancy soak
41915,0a10aced202194944a043e7c,P2-NewCode-Dev,Photon2,NextGen occupancy soak
38211,0a10aced202194944a04084c,LoRA-Gateway-SG,Gateway,P2 gateway
38211,0a10aced202194944a043de8,LoRA-Gateway-NC,Gateway,P2 gateway
38211,e00fce683f6063bf254283dd,LoRA-Node-SG,Node,LoRA node
38211,e00fce68a9f4e8bb70308f79,LoRA-Node-NC,Node,LoRA node
```

---

## 4. Verify Particle CLI

```bash
particle --version
particle whoami
```

If needed:

```bash
particle login
```

---

## 5. Create the cleaner script

Create:

```bash
nano ~/ParticleLogs/tools/particle_clean.py
```

Paste the script from `tools/particle_clean.py`.

Make it executable:

```bash
chmod +x ~/ParticleLogs/tools/particle_clean.py
```

---

## 6. Set daily log symlinks

Run once each day, or before starting subscriptions:

```bash
cd ~/ParticleLogs/products/38211-LoRA-Particle-Gateway-P2
ln -sf product-events-$(date +%Y%m%d).raw.log latest.raw.log
ln -sf product-events-$(date +%Y%m%d).clean.log latest.clean.log

cd ~/ParticleLogs/products/41915-NextGen-Occupancy-P2
ln -sf product-events-$(date +%Y%m%d).raw.log latest.raw.log
ln -sf product-events-$(date +%Y%m%d).clean.log latest.clean.log

cd ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron
ln -sf product-events-$(date +%Y%m%d).raw.log latest.raw.log
ln -sf product-events-$(date +%Y%m%d).clean.log latest.clean.log
```

---

## 7. Start product subscriptions

Open three terminal tabs.

### Tab 1 — Product 38211, LoRA Particle Gateway P2

```bash
cd ~/ParticleLogs/products/38211-LoRA-Particle-Gateway-P2
particle subscribe --product 38211 | tee -a latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 38211 | tee -a latest.clean.log
```

### Tab 2 — Product 41915, NextGen Occupancy P2

```bash
cd ~/ParticleLogs/products/41915-NextGen-Occupancy-P2
particle subscribe --product 41915 | tee -a latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 41915 | tee -a latest.clean.log
```

### Tab 3 — Product 42131, NextGen Occupancy Boron

```bash
cd ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron
particle subscribe --product 42131 | tee -a latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 42131 | tee -a latest.clean.log
```

These commands:

1. Subscribe to all product events
2. Save the raw JSON stream to `latest.raw.log`
3. Remove Particle CLI banner lines
4. Convert device IDs to device names
5. Produce compact readable log lines
6. Save the clean output to `latest.clean.log`

---

## 8. Watch current clean logs in color

Open three additional terminal tabs if desired.

### Product 38211

```bash
tail -F ~/ParticleLogs/products/38211-LoRA-Particle-Gateway-P2/latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 38211 --color
```

### Product 41915

```bash
tail -F ~/ParticleLogs/products/41915-NextGen-Occupancy-P2/latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 41915 --color
```

### Product 42131

```bash
tail -F ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log | grep '^{' | python3 ~/ParticleLogs/tools/particle_clean.py 42131 --color
```

Color behavior:

```text
ONLINE     green
OFFLINE    yellow
RESET      cyan for power_management, red for other reset causes
battery    yellow below 50%, red below 30%
connecttime yellow above 180s, red above 300s
alerts     red when alerts > 0
```

---

## 9. Replay historical logs

To replay a raw log:

```bash
grep '^{' ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log | python3 ~/ParticleLogs/tools/particle_clean.py 42131 --color
```

To rebuild a clean log from raw:

```bash
grep '^{' ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log | python3 ~/ParticleLogs/tools/particle_clean.py 42131 > ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.clean.log
```

---

## 10. What to watch during soak

For the Boron cloud recovery / ledger soak, watch for:

### Healthy signs

```text
ONLINE
Ubidots-Sensor-Hook-v1 | occupancy=... battery=... alerts=0 connecttime=...
OFFLINE
RESET power_management
```

`RESET power_management` can be normal after a firmware flash or hibernate/power-management path.

### Concerning signs

```text
RESET watchdog
RESET panic
RESET hard_fault
alerts > 0
connecttime > 180
connecttime > 300
battery < 50
battery < 30
```

For local serial logs, also watch for:

```text
LedgerSleepState: pending=0 syncing=0 inflight=0
LedgerDuplicateIssue followed by LedgerIssueSkip
CloudRecover escalation
AppWDT abnormal events
```

---

## 11. Recommended repo placement

Do not commit raw or clean log files to GitHub.

Recommended `.gitignore` entries:

```gitignore
*.raw.log
*.clean.log
*.log
ParticleLogs/
```

Recommended files to commit to the firmware repo:

```text
docs/particle-log-subscriptions.md
tools/particle_clean.py
```

Recommended local-only files:

```text
~/ParticleLogs/products/*/*.raw.log
~/ParticleLogs/products/*/*.clean.log
```

The device inventory can go either way:

- Commit `devices.csv` if the device IDs and names are not sensitive for the repo audience.
- Keep it local if the repo is public or shared broadly.

For a private firmware repo, committing this is reasonable:

```text
tools/particle_clean.py
docs/particle-log-subscriptions.md
```

and keeping this local is safer:

```text
~/ParticleLogs/inventory/devices.csv
```

---

## 12. Quick validation commands

Check folder structure:

```bash
tree ~/ParticleLogs
```

Check symlinks:

```bash
ls -l ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron
```

Check raw log is receiving events:

```bash
tail -5 ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log
```

Check cleaner output:

```bash
grep -m 5 '^{' ~/ParticleLogs/products/42131-NextGen-Occupancy-Boron/latest.raw.log | python3 ~/ParticleLogs/tools/particle_clean.py 42131 --color
```

---

## 13. Notes

- `particle_clean.py` is generic across products.
- Product-specific mapping comes from `~/ParticleLogs/inventory/devices.csv`.
- The Particle CLI banner line is intentionally ignored in clean output.
- Webhook transport noise is filtered:
  - `hook-sent/...`
  - `.../hook-response/...`
- Particle update bookkeeping is retained but compacted:
  - `update_enabled=true`
  - `update_forced=false`
  - `update_pending=false`
